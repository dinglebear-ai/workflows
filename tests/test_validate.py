from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


class WorkflowLibraryTests(unittest.TestCase):
    def test_catalog_profiles_are_nonempty(self) -> None:
        catalog = json.loads((ROOT / "catalog.json").read_text())
        self.assertTrue(catalog["profiles"])
        for name, workflows in catalog["profiles"].items():
            with self.subTest(profile=name):
                self.assertTrue(workflows)

    def test_reusable_workflows_have_inputs_mapping(self) -> None:
        catalog = json.loads((ROOT / "catalog.json").read_text())
        kinds = {item["file"]: item["kind"] for item in catalog["workflows"]}
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            if kinds[path.name] == "internal":
                continue
            workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
            with self.subTest(workflow=path.name):
                call = workflow["on"]["workflow_call"]
                self.assertIsInstance(call, dict)

    def test_no_template_is_empty(self) -> None:
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            with self.subTest(workflow=path.name):
                self.assertGreater(path.stat().st_size, 200)

    def test_starters_use_immutable_workflow_placeholder(self) -> None:
        starters = ROOT / "starters"
        self.assertEqual(
            {path.stem for path in starters.glob("*.yml")},
            {"rust", "python", "node", "pnpm", "bun"},
        )
        for path in starters.glob("*.yml"):
            with self.subTest(starter=path.name):
                text = path.read_text()
                self.assertIn("@__WORKFLOWS_SHA__", text)
                self.assertNotIn("@main", text)

    def test_caller_inputs_match_reusable_interfaces(self) -> None:
        callers = list((ROOT / "starters").glob("*.yml"))
        callers.extend((ROOT / "templates/callers").glob("*.yml"))
        for caller in sorted(callers):
            workflow = yaml.load(caller.read_text(), Loader=yaml.BaseLoader)
            for job_name, job in workflow["jobs"].items():
                uses = job.get("uses", "")
                if "dinglebear-ai/workflows/.github/workflows/" not in uses:
                    continue
                reusable_name = uses.split("/.github/workflows/", 1)[1].split("@", 1)[0]
                reusable = yaml.load(
                    (ROOT / ".github/workflows" / reusable_name).read_text(),
                    Loader=yaml.BaseLoader,
                )
                accepted = set(
                    reusable["on"]["workflow_call"].get("inputs", {})
                )
                supplied = set(job.get("with", {}))
                with self.subTest(caller=caller.name, job=job_name):
                    self.assertFalse(supplied - accepted)

    def test_release_caller_templates_are_release_only(self) -> None:
        for caller in sorted((ROOT / "templates/callers").glob("*release.yml")):
            workflow = yaml.load(caller.read_text(), Loader=yaml.BaseLoader)
            with self.subTest(caller=caller.name):
                self.assertEqual(set(workflow["on"]), {"release"})
                self.assertEqual(
                    workflow["on"]["release"]["types"],
                    ["published"],
                )

    def test_ci_images_pin_exact_base_manifests(self) -> None:
        for profile in ("rust", "python", "typescript"):
            dockerfile = (ROOT / "images" / profile / "Dockerfile").read_text()
            with self.subTest(profile=profile):
                first_from = next(
                    line for line in dockerfile.splitlines() if line.startswith("FROM ")
                )
                self.assertRegex(first_from, r"@sha256:[0-9a-f]{64}$")
                self.assertIn("ci-image-smoke", dockerfile)

    def test_python_contract_uses_uv_ruff_ty_and_pytest(self) -> None:
        workflow = (ROOT / ".github/workflows/fast-python.yml").read_text()
        dockerfile = (ROOT / "images/python/Dockerfile").read_text()
        smoke = (ROOT / "images/smoke.sh").read_text()
        for tool in ("uv", "ruff", "ty", "pytest"):
            with self.subTest(tool=tool):
                self.assertIn(tool, workflow)
                self.assertIn(tool, dockerfile)
                self.assertIn(f"{tool} --version", smoke)

    def test_marketplace_caches_are_independently_optional(self) -> None:
        workflow = yaml.load(
            (ROOT / ".github/workflows/marketplace-ci.yml").read_text(),
            Loader=yaml.BaseLoader,
        )
        inputs = workflow["on"]["workflow_call"]["inputs"]
        self.assertEqual(inputs["enable-python-cache"]["default"], "true")
        self.assertEqual(inputs["enable-node-cache"]["default"], "true")
        self.assertEqual(inputs["validation-setup-command"]["default"], "")
        text = (ROOT / ".github/workflows/marketplace-ci.yml").read_text()
        self.assertIn(
            "cache: ${{ inputs.enable-python-cache && 'pip' || '' }}",
            text,
        )
        self.assertIn(
            "cache: ${{ inputs.enable-node-cache && 'npm' || '' }}",
            text,
        )
        self.assertLess(
            text.index("- name: Install validation tools"),
            text.index("- name: Validate manifests, schemas, generators, and tests"),
        )

    def test_kache_action_uses_shard_capable_pin(self) -> None:
        pinned = (
            "kunobi-ninja/kache-action"
            "@a257c055543c2840700a9bbca8f9c3094a421b1b"
        )
        for workflow_name in (
            "fast-rust.yml",
            "hosted-incus-image.yml",
            "hosted-rust-release.yml",
        ):
            text = (ROOT / ".github/workflows" / workflow_name).read_text()
            with self.subTest(workflow=workflow_name):
                self.assertIn(pinned, text)
                self.assertIn("\n          namespace:", text)
                self.assertIn('\n          pr-comment: "false"', text)

    def test_fast_rust_supports_optional_project_setup(self) -> None:
        workflow = yaml.load(
            (ROOT / ".github/workflows/fast-rust.yml").read_text(),
            Loader=yaml.BaseLoader,
        )
        setup = workflow["on"]["workflow_call"]["inputs"]["setup-command"]
        self.assertEqual(setup["default"], "")
        uv_version = workflow["on"]["workflow_call"]["inputs"]["uv-version"]
        self.assertEqual(uv_version["default"], "")
        text = (ROOT / ".github/workflows/fast-rust.yml").read_text()
        self.assertIn(
            "astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b",
            text,
        )
        self.assertLess(
            text.index("- name: Project setup"),
            text.index("- name: Format"),
        )

    def test_rust_security_uses_cvss4_capable_cargo_deny(self) -> None:
        workflow_path = ROOT / ".github/workflows/rust-security.yml"
        workflow = yaml.load(
            workflow_path.read_text(),
            Loader=yaml.BaseLoader,
        )
        version = workflow["on"]["workflow_call"]["inputs"]["cargo-deny-version"]
        self.assertEqual(version["default"], "0.20.2")
        self.assertIn(
            "cargo-deny@${{ inputs.cargo-deny-version }}",
            workflow_path.read_text(),
        )

    def test_hosted_incus_kache_is_opt_in(self) -> None:
        workflow = yaml.load(
            (ROOT / ".github/workflows/hosted-incus-image.yml").read_text(),
            Loader=yaml.BaseLoader,
        )
        call = workflow["on"]["workflow_call"]
        self.assertEqual(call["inputs"]["enable-kache"]["default"], "false")
        self.assertEqual(
            call["secrets"]["KACHE_S3_ACCESS_KEY"]["required"],
            "false",
        )
        self.assertEqual(
            call["secrets"]["KACHE_S3_SECRET_KEY"]["required"],
            "false",
        )

    def test_bootstrap_profiles_create_immutable_callers(self) -> None:
        bootstrap = ROOT / "scripts" / "bootstrap.sh"
        release_types = {
            "rust": "rust",
            "python": "python",
            "node": "node",
            "pnpm": "node",
            "bun": "node",
        }
        for profile, release_type in release_types.items():
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temp:
                target = pathlib.Path(temp)
                subprocess.run(
                    ["git", "init", "-q", str(target)],
                    check=True,
                )
                subprocess.run(
                    [str(bootstrap), profile, str(target)],
                    check=True,
                    env={
                        "PATH": "/usr/local/bin:/usr/bin:/bin",
                        "WORKFLOWS_SHA": "0123456789abcdef0123456789abcdef01234567",
                    },
                    stdout=subprocess.DEVNULL,
                )
                ci = (target / ".github/workflows/ci.yml").read_text()
                policy = (target / ".github/workflows/policy.yml").read_text()
                self.assertNotIn("__WORKFLOWS_SHA__", ci)
                self.assertIn(
                    "@0123456789abcdef0123456789abcdef01234567",
                    ci,
                )
                self.assertNotIn("__PROFILE__", policy)
                self.assertIn(f"profile: {profile if profile != 'pnpm' and profile != 'bun' else 'node'}", policy)
                self.assertIn("runner-labels-json:", ci)
                release_config = (
                    target / "release-please-config.json"
                ).read_text()
                self.assertIn(f'"release-type": "{release_type}"', release_config)
                self.assertNotIn("__RELEASE_TYPE__", release_config)
                self.assertTrue((target / "AGENTS.md").is_symlink())
                self.assertEqual((target / "AGENTS.md").readlink(), pathlib.Path("CLAUDE.md"))
                self.assertTrue((target / "GEMINI.md").is_symlink())


if __name__ == "__main__":
    unittest.main()
