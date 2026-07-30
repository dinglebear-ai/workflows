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

    def test_starter_inputs_match_reusable_interfaces(self) -> None:
        for starter in sorted((ROOT / "starters").glob("*.yml")):
            workflow = yaml.load(starter.read_text(), Loader=yaml.BaseLoader)
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
                with self.subTest(starter=starter.name, job=job_name):
                    self.assertFalse(supplied - accepted)

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
                self.assertNotIn("__WORKFLOWS_SHA__", ci)
                self.assertIn(
                    "@0123456789abcdef0123456789abcdef01234567",
                    ci,
                )
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
