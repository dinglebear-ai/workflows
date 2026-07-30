from __future__ import annotations

import json
import pathlib
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
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            if path.name == "validate-library.yml":
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


if __name__ == "__main__":
    unittest.main()
