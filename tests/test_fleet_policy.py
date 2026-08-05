"""Gate-wiring invariants enforced by fleet-policy.yml.

These cover the shapes where a required check does not run and nothing fails:
an `if:` that reads an output its producing job never declares, and an
aggregate gate that waits on a job whose result it never inspects.
"""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
import textwrap
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]

CLEAN_WORKFLOW = """
name: clean
permissions:
  contents: read
jobs:
  changes:
    runs-on: ci-pool-ops
    timeout-minutes: 10
    outputs:
      web: ${{ steps.classify.outputs.web }}
    steps:
      - id: classify
        run: echo "web=true" >> "$GITHUB_OUTPUT"
  web:
    needs: changes
    if: ${{ needs.changes.outputs.web == 'true' }}
    runs-on: ci-pool-ops
    timeout-minutes: 10
    steps:
      - run: echo building
  gate:
    needs: [changes, web]
    if: ${{ always() }}
    runs-on: ci-pool-ops
    timeout-minutes: 10
    steps:
      - run: |
          echo "${{ needs.changes.result }}"
          echo "${{ needs.web.result }}"
"""


def policy_script() -> str:
    """The python program embedded in the policy step."""
    workflow = yaml.safe_load((ROOT / ".github/workflows/fleet-policy.yml").read_text())
    run = workflow["jobs"]["policy"]["steps"][-1]["run"]
    return run.split("python - <<'PY'\n", 1)[1].rsplit("PY\n", 1)[0]


def run_policy(workflows: dict[str, str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temp:
        root = pathlib.Path(temp)
        (root / ".github/workflows").mkdir(parents=True)
        for name, body in workflows.items():
            (root / ".github/workflows" / name).write_text(textwrap.dedent(body).lstrip())
        script = root / "policy.py"
        script.write_text(policy_script())
        return subprocess.run(
            ["python3", str(script)],
            cwd=root,
            env={
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "RELEASE_FILE_REGEX": r"(^|/)(release|publish|deploy)[^/]*\.ya?ml$",
                "ALLOW_HOSTED_FAST": "false",
            },
            capture_output=True,
            text=True,
            check=False,
        )


class GateWiringPolicyTests(unittest.TestCase):
    def test_correctly_wired_gates_pass(self) -> None:
        result = run_policy({"ci.yml": CLEAN_WORKFLOW})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_gate_on_an_undeclared_output_fails(self) -> None:
        # `unraid` is gated on but never declared, so the expression is always
        # the empty string and the job skips for reasons no one intended.
        broken = CLEAN_WORKFLOW.replace(
            "if: ${{ needs.changes.outputs.web == 'true' }}",
            "if: ${{ needs.changes.outputs.unraid == 'true' }}",
        )
        result = run_policy({"ci.yml": broken})
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("needs.changes.outputs.unraid is never declared", result.stdout)

    def test_reusable_workflow_outputs_are_exempt(self) -> None:
        # A called workflow's outputs are declared in the callee, which this
        # policy cannot see, so they must not be reported as undeclared.
        called = """
        name: caller
        permissions:
          contents: read
        jobs:
          upstream:
            uses: dinglebear-ai/workflows/.github/workflows/fleet-policy.yml@0123456789abcdef0123456789abcdef01234567
          consumer:
            needs: upstream
            if: ${{ needs.upstream.outputs.anything == 'true' }}
            runs-on: ci-pool-ops
            timeout-minutes: 10
            steps:
              - run: echo ok
        """
        result = run_policy({"ci.yml": called})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_aggregate_that_ignores_a_dependency_fails(self) -> None:
        # `web` stays in `needs:` but its result is no longer inspected, so the
        # gate passes whatever `web` concludes.
        broken = CLEAN_WORKFLOW.replace('          echo "${{ needs.web.result }}"\n', "")
        result = run_policy({"ci.yml": broken})
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("aggregate gate needs `web`", result.stdout)

    def test_dependencies_consumed_for_their_outputs_are_not_aggregated(self) -> None:
        # Needing a job for its outputs is not the same as gating on its
        # result; only jobs an aggregate waits on to judge must be inspected.
        routed = """
        name: routed
        permissions:
          contents: read
        jobs:
          changes:
            runs-on: ci-pool-ops
            timeout-minutes: 10
            outputs:
              web: ${{ steps.classify.outputs.web }}
            steps:
              - id: classify
                run: echo "web=true" >> "$GITHUB_OUTPUT"
          build:
            runs-on: ci-pool-ops
            timeout-minutes: 10
            steps:
              - run: echo building
          report:
            needs: [changes, build]
            if: ${{ always() && needs.changes.outputs.web == 'true' }}
            runs-on: ci-pool-ops
            timeout-minutes: 10
            steps:
              - run: echo "${{ needs.build.result }}"
        """
        result = run_policy({"ci.yml": routed})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
