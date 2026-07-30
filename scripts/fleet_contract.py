#!/usr/bin/env python3
"""Validate durable repository contracts shared across the fleet."""

from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass


ARM_CONTRACT = re.compile(r"(?i)\b(arm64|aarch64|linux/arm64|setup-qemu)\b")
STALE_OWNER = re.compile(
    r"(?i)(?:github\.com|raw\.githubusercontent\.com|ghcr\.io)/jmagar/"
)
FRONTMATTER_KEYS = {"title", "created", "updated"}
RUSTDOC_LEVELS = {
    "broken_intra_doc_links": "deny",
    "invalid_codeblock_attributes": "deny",
    "invalid_html_tags": "deny",
    "bare_urls": "warn",
    "private_intra_doc_links": "warn",
    "redundant_explicit_links": "warn",
    "unescaped_backticks": "warn",
}
RUST_LEVELS = {
    "missing_crate_level_docs": "deny",
    "unsafe_op_in_unsafe_fn": "deny",
}
CLIPPY_LEVELS = {"missing_safety_doc": "deny"}
EXACT_DEPENDENCIES = {"rmcp", "rmcp-macros", "schemars"}
AGENT_LITTER = {
    ".claude/settings.local.json",
    ".full-review",
    ".lavra",
    "todo.md",
}


@dataclass(frozen=True)
class Finding:
    check: str
    path: str
    message: str

    def render(self) -> str:
        location = f": {self.path}" if self.path else ""
        return f"{self.check}{location}: {self.message}"


def git(repo: pathlib.Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def tracked_files(repo: pathlib.Path) -> list[pathlib.Path]:
    output = git(repo, "ls-files", "-z")
    return [repo / path for path in output.rstrip("\0").split("\0") if path]


def relative(repo: pathlib.Path, path: pathlib.Path) -> str:
    return path.relative_to(repo).as_posix()


def load_toml(path: pathlib.Path) -> dict:
    try:
        return tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def check_toolchain(repo: pathlib.Path) -> list[Finding]:
    path = repo / "rust-toolchain.toml"
    data = load_toml(path)
    toolchain = data.get("toolchain", {})
    findings: list[Finding] = []
    if toolchain.get("channel") != "1.97.1":
        findings.append(
            Finding(
                "toolchain-pinned",
                "rust-toolchain.toml",
                'channel must equal "1.97.1"',
            )
        )
    components = set(toolchain.get("components", []))
    missing = {"rustfmt", "clippy"} - components
    if missing:
        findings.append(
            Finding(
                "toolchain-pinned",
                "rust-toolchain.toml",
                f"missing components: {', '.join(sorted(missing))}",
            )
        )
    return findings


def cargo_manifests(repo: pathlib.Path) -> list[pathlib.Path]:
    return [
        path
        for path in tracked_files(repo)
        if path.name == "Cargo.toml"
        and not any(part in {"target", "vendor"} for part in path.parts)
    ]


def check_edition(repo: pathlib.Path) -> list[Finding]:
    findings: list[Finding] = []
    root = load_toml(repo / "Cargo.toml")
    workspace_edition = root.get("workspace", {}).get("package", {}).get("edition")
    for manifest in cargo_manifests(repo):
        package = load_toml(manifest).get("package")
        if not isinstance(package, dict):
            continue
        edition = package.get("edition")
        if isinstance(edition, dict) and edition.get("workspace") is True:
            edition = workspace_edition
        if edition != "2024":
            findings.append(
                Finding(
                    "edition-2024",
                    relative(repo, manifest),
                    f"package edition resolves to {edition!r}",
                )
            )
    return findings


def lint_level(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        level = value.get("level")
        return level if isinstance(level, str) else None
    return None


def check_workspace_lints(repo: pathlib.Path) -> list[Finding]:
    root_path = repo / "Cargo.toml"
    root = load_toml(root_path)
    workspace_lints = root.get("workspace", {}).get("lints")
    findings: list[Finding] = []
    if not isinstance(workspace_lints, dict):
        return [
            Finding(
                "workspace-lints",
                "Cargo.toml",
                "missing [workspace.lints]",
            )
        ]

    for group, expected in (
        ("rust", RUST_LEVELS),
        ("rustdoc", RUSTDOC_LEVELS),
        ("clippy", CLIPPY_LEVELS),
    ):
        actual = workspace_lints.get(group, {})
        for name, level in expected.items():
            if lint_level(actual.get(name)) != level:
                findings.append(
                    Finding(
                        "rustdoc-phase0",
                        "Cargo.toml",
                        f"{group}.{name} must be {level}",
                    )
                )

    for manifest in cargo_manifests(repo):
        manifest_data = load_toml(manifest)
        package = manifest_data.get("package")
        if not isinstance(package, dict):
            continue
        lints = manifest_data.get("lints", {})
        if lints.get("workspace") is not True:
            # A narrowly scoped FFI crate cannot inherit a workspace-level
            # `unsafe_code = "forbid"` and then relax it. Permit only the
            # explicit local override needed for that boundary; every other
            # non-inheriting package remains a contract violation.
            local_rust = lints.get("rust", {})
            workspace_rust = workspace_lints.get("rust", {})
            fleet_metadata = package.get("metadata", {}).get("fleet", {})
            sanctioned_ffi_boundary = (
                isinstance(fleet_metadata, dict)
                and fleet_metadata.get("workspace-lints-exception") == "unsafe-ffi"
                and lint_level(workspace_rust.get("unsafe_code")) == "forbid"
                and isinstance(local_rust, dict)
                and lint_level(local_rust.get("unsafe_code")) == "allow"
                and set(local_rust) == {"unsafe_code"}
                and set(lints) == {"rust"}
            )
            if sanctioned_ffi_boundary:
                continue
            findings.append(
                Finding(
                    "workspace-lints",
                    relative(repo, manifest),
                    "package must declare [lints] workspace = true",
                )
            )
    return findings


def dependency_version(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        version = value.get("version")
        return version if isinstance(version, str) else None
    return None


def dependency_tables(manifest: dict) -> list[dict]:
    tables: list[dict] = []
    for name in ("dependencies", "dev-dependencies", "build-dependencies"):
        value = manifest.get(name)
        if isinstance(value, dict):
            tables.append(value)
    workspace = manifest.get("workspace", {})
    if isinstance(workspace, dict):
        value = workspace.get("dependencies")
        if isinstance(value, dict):
            tables.append(value)
    target = manifest.get("target", {})
    if isinstance(target, dict):
        for config in target.values():
            if not isinstance(config, dict):
                continue
            for name in ("dependencies", "dev-dependencies", "build-dependencies"):
                value = config.get(name)
                if isinstance(value, dict):
                    tables.append(value)
    return tables


def check_exact_dependencies(repo: pathlib.Path) -> list[Finding]:
    lock = load_toml(repo / "Cargo.lock")
    locked: dict[str, set[str]] = {}
    for package in lock.get("package", []):
        if not isinstance(package, dict):
            continue
        name = package.get("name")
        version = package.get("version")
        if isinstance(name, str) and isinstance(version, str):
            locked.setdefault(name, set()).add(version)

    findings: list[Finding] = []
    for manifest_path in cargo_manifests(repo):
        manifest = load_toml(manifest_path)
        for table in dependency_tables(manifest):
            for name in EXACT_DEPENDENCIES & set(table):
                value = table[name]
                if isinstance(value, dict) and value.get("workspace") is True:
                    continue
                version = dependency_version(value)
                expected = version[1:] if version and version.startswith("=") else None
                if expected is None:
                    findings.append(
                        Finding(
                            "deps-exact-pinned",
                            relative(repo, manifest_path),
                            f"{name} must use an exact =version pin",
                        )
                    )
                elif expected not in locked.get(name, set()):
                    findings.append(
                        Finding(
                            "deps-exact-pinned",
                            relative(repo, manifest_path),
                            f"{name} pin {expected} does not match Cargo.lock",
                        )
                    )
    return findings


def check_symlinks(repo: pathlib.Path) -> list[Finding]:
    findings: list[Finding] = []
    records = git(repo, "ls-files", "-s", "-z").rstrip("\0").split("\0")
    by_path: dict[str, tuple[str, str]] = {}
    for record in records:
        if not record:
            continue
        metadata, path = record.split("\t", 1)
        mode, blob, _stage = metadata.split()
        by_path[path] = (mode, blob)

    for claude in (
        path
        for path in by_path
        if pathlib.PurePosixPath(path).name == "CLAUDE.md"
        and not path.startswith("bootstrap/")
    ):
        parent = pathlib.PurePosixPath(claude).parent
        for name in ("AGENTS.md", "GEMINI.md"):
            peer = (parent / name).as_posix()
            mode_blob = by_path.get(peer)
            if mode_blob is None:
                findings.append(
                    Finding(
                        "symlink-convention",
                        peer,
                        "missing tracked symlink to CLAUDE.md",
                    )
                )
                continue
            mode, blob = mode_blob
            target = git(repo, "cat-file", "-p", blob).strip()
            if mode != "120000" or target != "CLAUDE.md":
                findings.append(
                    Finding(
                        "symlink-convention",
                        peer,
                        "must be index mode 120000 targeting CLAUDE.md",
                    )
                )
    return findings


def check_scoped_text(repo: pathlib.Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in tracked_files(repo):
        rel = relative(repo, path)
        compose_manifest = path.suffix in {".yaml", ".yml"} and (
            path.name in {"compose.yaml", "compose.yml"}
            or path.name.startswith("docker-compose")
        )
        stale_scope = (
            path.name in {"Cargo.toml", "package.json", "server.json", "plugin.json"}
            or compose_manifest
            or path.suffix in {".plg"}
        )
        arm_scope = (
            path.name in {"install.sh", "server.json", "package.json"}
            or path.suffix in {".plg"}
            or rel.startswith("scripts/install")
        )
        if not (stale_scope or arm_scope) or not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue

        if stale_scope and STALE_OWNER.search(text):
            findings.append(
                Finding(
                    "no-stale-org-refs",
                    rel,
                    "replace jmagar artifact/repository owner with dinglebear-ai",
                )
            )

        if arm_scope and ARM_CONTRACT.search(text):
            findings.append(
                Finding(
                    "no-arm-contract",
                    rel,
                    "ARM64/AArch64/QEMU is outside the fleet contract",
                )
            )
    return findings


def readme_lead(text: str) -> str | None:
    paragraphs = re.split(r"\n\s*\n", text)
    for paragraph in paragraphs:
        lines = [
            line.strip()
            for line in paragraph.splitlines()
            if line.strip() and not line.lstrip().startswith(("#", "<!--", "[![", "!["))
        ]
        if lines:
            return " ".join(lines)
    return None


def check_descriptions(repo: pathlib.Path) -> list[Finding]:
    root = load_toml(repo / "Cargo.toml")
    canonical = root.get("package", {}).get("description")
    if not isinstance(canonical, str):
        canonical = root.get("workspace", {}).get("package", {}).get("description")
    if not isinstance(canonical, str):
        return []

    findings: list[Finding] = []
    readme = repo / "README.md"
    if readme.is_file():
        lead = readme_lead(readme.read_text())
        if lead is not None and lead != canonical:
            findings.append(
                Finding(
                    "description-consistency",
                    "README.md",
                    "lead paragraph must exactly match Cargo description",
                )
            )

    for filename in ("package.json", "server.json"):
        path = repo / filename
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        description = data.get("description")
        if isinstance(description, str) and description != canonical:
            findings.append(
                Finding(
                    "description-consistency",
                    filename,
                    "description must exactly match Cargo description",
                )
            )
    return findings


def check_tracked_paths(repo: pathlib.Path) -> list[Finding]:
    findings: list[Finding] = []
    tracked = tracked_files(repo)
    relative_paths = [relative(repo, path) for path in tracked]
    ignored_result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "check-ignore",
            "--no-index",
            "-z",
            "--stdin",
        ],
        input="\0".join(relative_paths) + "\0",
        text=True,
        capture_output=True,
        check=False,
    )
    ignored_paths = {
        path for path in ignored_result.stdout.rstrip("\0").split("\0") if path
    }

    for path, rel in zip(tracked, relative_paths, strict=True):
        ignored = rel in ignored_paths
        parts = pathlib.PurePosixPath(rel).parts
        litter = rel in AGENT_LITTER or any(part in AGENT_LITTER for part in parts)
        if ignored or litter:
            reason = "tracked and ignored" if ignored else "agent-local path is tracked"
            findings.append(Finding("tracked-path-hygiene", rel, reason))
    return findings


def check_env_schema(repo: pathlib.Path) -> list[Finding]:
    example = repo / ".env.example"
    if not example.is_file():
        return []
    keys = {
        match.group(1)
        for line in example.read_text().splitlines()
        if (match := re.match(r"^\s*([A-Z][A-Z0-9_]*)\s*=", line))
    }
    if not keys:
        return []

    unused = set(keys)
    source_suffixes = {
        ".c",
        ".cc",
        ".go",
        ".h",
        ".js",
        ".json",
        ".jsx",
        ".py",
        ".rs",
        ".sh",
        ".toml",
        ".ts",
        ".tsx",
        ".yaml",
        ".yml",
    }
    for path in tracked_files(repo):
        rel = relative(repo, path)
        if (
            not unused
            or path == example
            or path.suffix not in source_suffixes
            or not path.is_file()
            or path.is_symlink()
            or any(
                part
                in {"docs", "fixtures", "generated", "node_modules", "target", "vendor"}
                for part in pathlib.PurePosixPath(rel).parts
            )
            or path.stat().st_size > 1_000_000
        ):
            continue
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        unused = {
            key for key in unused if not re.search(rf"\b{re.escape(key)}\b", text)
        }
    if not unused:
        return []
    return [
        Finding(
            "env-schema",
            ".env.example",
            f"keys have no tracked consumer: {', '.join(sorted(unused))}",
        )
    ]


def frontmatter_keys(text: str) -> set[str]:
    if not text.startswith("---\n"):
        return set()
    try:
        block = text.split("---\n", 2)[1]
    except IndexError:
        return set()
    return {line.split(":", 1)[0].strip() for line in block.splitlines() if ":" in line}


def check_docs(repo: pathlib.Path) -> list[Finding]:
    findings: list[Finding] = []
    config = load_toml(repo / ".fleet-contract.toml")
    configured_excludes = config.get("docs", {}).get("frontmatter-exclude", [])
    if not isinstance(configured_excludes, list) or not all(
        isinstance(pattern, str) for pattern in configured_excludes
    ):
        configured_excludes = []
    for path in tracked_files(repo):
        rel = relative(repo, path)
        parts = pathlib.PurePosixPath(rel).parts
        if (
            not rel.startswith("docs/")
            or path.suffix != ".md"
            or path.name in {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"}
            or any(
                part
                in {
                    "archive",
                    "fixtures",
                    "generated",
                    "perf",
                    "pipeline-unification",
                    "plans",
                    "reference",
                    "references",
                    "reports",
                    "sessions",
                    "superpowers",
                    "upstream",
                    "upstream-api",
                    "vendor",
                }
                for part in parts
            )
            or any(fnmatch.fnmatchcase(rel, pattern) for pattern in configured_excludes)
        ):
            continue
        missing = FRONTMATTER_KEYS - frontmatter_keys(path.read_text())
        if missing:
            findings.append(
                Finding(
                    "docs-frontmatter",
                    rel,
                    f"missing keys: {', '.join(sorted(missing))}",
                )
            )
    return findings


def check(repo: pathlib.Path, profile: str) -> list[Finding]:
    findings: list[Finding] = []
    if profile == "rust":
        findings.extend(check_toolchain(repo))
        findings.extend(check_edition(repo))
        findings.extend(check_workspace_lints(repo))
        findings.extend(check_exact_dependencies(repo))
        findings.extend(check_descriptions(repo))
    findings.extend(check_symlinks(repo))
    findings.extend(check_scoped_text(repo))
    findings.extend(check_tracked_paths(repo))
    findings.extend(check_env_schema(repo))
    findings.extend(check_docs(repo))
    return sorted(findings, key=lambda item: (item.check, item.path, item.message))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path("."))
    check_parser.add_argument(
        "--profile",
        choices=("rust", "python", "node", "go", "ops"),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    findings = check(repo, args.profile)
    if findings:
        for finding in findings:
            print(finding.render())
        return 1
    print(f"fleet contract valid: {repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
