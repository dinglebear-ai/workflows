#!/usr/bin/env python3
"""Fail-closed validation for the canonical workflow library."""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CATALOG = ROOT / "catalog.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
DOCKER_SHA256 = re.compile(r"^docker://[^\s]+@sha256:[0-9a-f]{64}$")
FORBIDDEN_ARCH = re.compile(
    r"(?i)\b(arm64|aarch64|linux/arm64|setup-qemu|ubuntu-[^\s'\"]*-arm)\b"
)


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    loaded = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    if not isinstance(loaded, dict):
        raise ValueError("workflow root must be a mapping")
    return loaded


def iter_steps(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "steps" and isinstance(child, list):
                yield from child
            yield from iter_steps(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_steps(child)


def valid_pool_selector(value: Any) -> bool:
    labels = [value] if isinstance(value, str) else value
    if not isinstance(labels, list) or not labels:
        return False
    if not all(isinstance(label, str) and "${{" not in label for label in labels):
        return False
    pools = [label for label in labels if label.startswith("ci-pool-")]
    return (
        len(pools) == 1
        and all(
            label.startswith("ci-pool-") or label.startswith("ci-cap-")
            for label in labels
        )
    )


def valid_fast_runner(data: dict[str, Any], runs_on: Any) -> bool:
    if valid_pool_selector(runs_on):
        return True
    if runs_on != "${{ fromJSON(inputs.runner-labels-json) }}":
        return False
    call = data.get("on", {}).get("workflow_call", {})
    inputs = call.get("inputs", {}) if isinstance(call, dict) else {}
    spec = inputs.get("runner-labels-json", {}) if isinstance(inputs, dict) else {}
    default = spec.get("default") if isinstance(spec, dict) else None
    if not isinstance(default, str):
        return False
    try:
        selector = json.loads(default)
    except json.JSONDecodeError:
        return False
    return valid_pool_selector(selector)


def validate() -> list[str]:
    errors: list[str] = []
    catalog = json.loads(CATALOG.read_text())
    entries = catalog["workflows"]
    by_file = {entry["file"]: entry for entry in entries}
    if len(by_file) != len(entries):
        errors.append("catalog.json: duplicate workflow file")

    actual = {path.name for path in WORKFLOWS.glob("*.yml")}
    declared = set(by_file)
    for name in sorted(actual - declared):
        errors.append(f"{name}: missing from catalog.json")
    for name in sorted(declared - actual):
        errors.append(f"catalog.json: missing workflow file {name}")

    profile_files = {
        name for files in catalog["profiles"].values() for name in files
    }
    for name in sorted(profile_files - declared):
        errors.append(f"catalog.json: profile references unknown workflow {name}")

    for path in sorted(WORKFLOWS.glob("*.yml")):
        try:
            data = load_yaml(path)
        except Exception as error:
            errors.append(f"{path.name}: invalid YAML: {error}")
            continue

        entry = by_file.get(path.name, {"kind": "unknown"})
        kind = entry["kind"]
        text = path.read_text()

        if path.name != "fleet-policy.yml" and FORBIDDEN_ARCH.search(text):
            errors.append(f"{path.name}: forbidden ARM/QEMU contract")

        if "permissions" not in data:
            errors.append(f"{path.name}: missing top-level permissions")
        elif not isinstance(data["permissions"], dict):
            errors.append(
                f"{path.name}: top-level permissions must be an explicit mapping"
            )

        triggers = data.get("on")
        if kind != "internal":
            if not isinstance(triggers, dict) or "workflow_call" not in triggers:
                errors.append(f"{path.name}: reusable workflow lacks workflow_call")

        jobs = data.get("jobs", {})
        if not isinstance(jobs, dict):
            errors.append(f"{path.name}: jobs must be a mapping")
            continue

        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue

            job_permissions = job.get("permissions")
            if job_permissions is not None and not isinstance(job_permissions, dict):
                errors.append(
                    f"{path.name}:{job_name}: permissions must be an explicit mapping"
                )

            job_use = job.get("uses")
            if isinstance(job_use, str):
                if not job_use.startswith("./") and (
                    "@" not in job_use
                    or not SHA.fullmatch(job_use.rsplit("@", 1)[1])
                ):
                    errors.append(
                        f"{path.name}:{job_name}: mutable reusable workflow {job_use}"
                    )
                continue

            if "timeout-minutes" not in job:
                errors.append(f"{path.name}:{job_name}: missing timeout-minutes")

            runs_on = job.get("runs-on", "")
            runner = json.dumps(runs_on).lower()
            if kind == "fast" and not valid_fast_runner(data, runs_on):
                errors.append(
                    f"{path.name}:{job_name}: fast workflow must use exactly one ci-pool-* selector"
                )
            if "self-hosted" in runner and "ci-pool-" in runner:
                errors.append(
                    f"{path.name}:{job_name}: scale-set selector must not include self-hosted"
                )
            if kind == "release" and (
                "self-hosted" in runner or "ci-pool-" in runner
            ):
                errors.append(f"{path.name}:{job_name}: release workflow is farm-routed")

        for step in iter_steps(data):
            if not isinstance(step, dict):
                continue
            use = step.get("uses")
            if isinstance(use, str) and not use.startswith("./"):
                if use.startswith("docker://"):
                    if not DOCKER_SHA256.fullmatch(use):
                        errors.append(f"{path.name}: mutable container action {use}")
                elif "@" not in use or not SHA.fullmatch(use.rsplit("@", 1)[1]):
                    errors.append(f"{path.name}: mutable external action {use}")
            if isinstance(use, str) and use.startswith("actions/checkout@"):
                with_block = step.get("with", {})
                if with_block.get("persist-credentials") != "false":
                    errors.append(
                        f"{path.name}: checkout must set persist-credentials false"
                    )
            run = step.get("run")
            if isinstance(run, str) and (
                "${{ inputs." in run or "${{ github.event." in run
            ):
                errors.append(
                    f"{path.name}: event/input expression interpolated directly into run"
                )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"workflow library valid: "
        f"{len(list(WORKFLOWS.glob('*.yml')))} workflows"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
