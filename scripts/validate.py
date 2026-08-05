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
ACTIONS = ROOT / ".github" / "actions"
CATALOG = ROOT / "catalog.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_ARCH = re.compile(
    r"(?i)\b(arm64|aarch64|linux/arm64|setup-qemu|ubuntu-[^\s'\"]*-arm)\b"
)
STEP_OUTPUT_REF = re.compile(r"steps\.([A-Za-z0-9_-]+)\.outputs\.")


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

        triggers = data.get("on")
        if kind != "internal":
            if not isinstance(triggers, dict) or "workflow_call" not in triggers:
                errors.append(f"{path.name}: reusable workflow lacks workflow_call")

        jobs = data.get("jobs", {})
        if not isinstance(jobs, dict):
            errors.append(f"{path.name}: jobs must be a mapping")
            continue

        for job_name, job in jobs.items():
            if not isinstance(job, dict) or "uses" in job:
                continue
            if "timeout-minutes" not in job:
                errors.append(f"{path.name}:{job_name}: missing timeout-minutes")
            runner = json.dumps(job.get("runs-on", "")).lower()
            if kind == "fast" and "ubuntu-" in runner:
                errors.append(f"{path.name}:{job_name}: fast workflow is hosted")
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
                    if "@sha256:" not in use:
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


def validate_actions() -> list[str]:
    """Validate local composite actions under .github/actions/**/action.yml."""
    errors: list[str] = []

    for path in sorted(ACTIONS.glob("*/action.yml")):
        label = str(path.relative_to(ROOT))
        try:
            data = load_yaml(path)
        except Exception as error:
            errors.append(f"{label}: invalid YAML: {error}")
            continue

        for key in ("name", "description", "runs"):
            if key not in data:
                errors.append(f"{label}: missing top-level '{key}'")

        runs = data.get("runs")
        if not isinstance(runs, dict) or runs.get("using") != "composite":
            errors.append(f"{label}: runs.using must be 'composite'")
            continue

        steps = runs.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{label}: runs.steps must be a non-empty list")
            steps = []

        step_ids = {
            step["id"] for step in steps if isinstance(step, dict) and "id" in step
        }

        for name, output in (data.get("outputs") or {}).items():
            if not isinstance(output, dict) or "value" not in output:
                errors.append(f"{label}: output {name} is missing a value")
                continue
            value = output["value"]
            match = STEP_OUTPUT_REF.search(value) if isinstance(value, str) else None
            if not match:
                errors.append(
                    f"{label}: output {name} does not reference a step output"
                )
            elif match.group(1) not in step_ids:
                errors.append(
                    f"{label}: output {name} references unknown step id "
                    f"'{match.group(1)}'"
                )

        for step in iter_steps(data):
            if not isinstance(step, dict):
                continue
            use = step.get("uses")
            if isinstance(use, str) and not use.startswith("./"):
                if use.startswith("docker://"):
                    if "@sha256:" not in use:
                        errors.append(f"{label}: mutable container action {use}")
                elif "@" not in use or not SHA.fullmatch(use.rsplit("@", 1)[1]):
                    errors.append(f"{label}: mutable external action {use}")
            run = step.get("run")
            if isinstance(run, str) and (
                "${{ inputs." in run or "${{ github.event." in run
            ):
                errors.append(
                    f"{label}: input/event expression interpolated directly into run"
                )

    return errors


def main() -> int:
    errors = validate()
    errors += validate_actions()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    action_count = len(list(ACTIONS.glob("*/action.yml")))
    print(
        f"workflow library valid: "
        f"{len(list(WORKFLOWS.glob('*.yml')))} workflows, "
        f"{action_count} composite actions"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
