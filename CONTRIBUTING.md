# Contributing

Workflow changes affect every consuming repository and are treated as
production infrastructure changes.

1. Create or claim a bead.
2. Add or change the reusable workflow.
3. Update `catalog.json`, documentation, and starters when the public contract
   changes.
4. Keep all new inputs typed and give safe deterministic defaults.
5. Pin external actions to full commit SHAs with a release comment.
6. Run the complete validation suite from the README.
7. Review the full diff for permission expansion, secret exposure, untrusted
   shell interpolation, runner placement, release provenance, and architecture
   expansion.
8. Merge, then update callers to the new immutable commit SHA.

Breaking input/output changes require a migration note and a coordinated caller
rollout. Prefer adding a new input with a safe default over silently changing an
existing contract.

