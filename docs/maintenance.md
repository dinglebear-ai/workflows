# Maintaining the workflow library

## Change process

1. Create a focused branch.
2. Update workflow YAML, `catalog.json`, starters, bootstrap assets, and docs
   together.
3. Run:

   ```bash
   python scripts/validate.py
   python -m unittest discover -s tests -v
   actionlint -config-file .github/actionlint.yaml
   shellcheck install.sh scripts/*.sh images/smoke.sh
   ```

4. Build/test affected CI images when toolchain files change.
5. Merge only after the hosted `validate` check succeeds.
6. Let Release Please create an immutable release.

## Caller upgrades

Callers use a full workflow-library commit SHA. To roll out a change:

1. record the new commit SHA;
2. update all `dinglebear-ai/workflows/...@<sha>` references in one reviewed
   fleet change;
3. keep the old SHA available during rollout;
4. verify each stable aggregate gate;
5. revert caller SHAs if the shared behavior regresses.

Do not move a tag to simulate an upgrade.

## Backward compatibility

Treat workflow inputs, outputs, required secrets, permissions, artifact names,
and runner placement as an API. Adding an optional input is compatible.
Removing or renaming an input, changing a default command materially, or
requiring a new permission is breaking and must be called out in release notes.

## Dependabot

Dependabot proposes immutable action SHA updates. Review the upstream release,
runtime migration, permission changes, and generated diff. Do not merge a bot
PR solely because the new SHA passes syntax validation.

## Image maintenance

Base manifest and tool versions are explicit in Dockerfiles. Re-resolve the
official amd64 manifest when updating a base tag, then rebuild and smoke all
three images. A passing Docker build is insufficient; inspect the resulting
architecture and tool versions.
