# Workflow library

This public repository is the canonical source for dinglebear-ai GitHub Actions
workflows. Callers use full commit SHAs; never document or introduce `@main` or
moving workflow tags.

## Invariants

- Fast Linux validation: self-hosted with exactly one `ci-pool-*` label.
- Heavy release work: release-only and GitHub-hosted.
- ARM64/AArch64 workflow and repository contracts require the reusable
  workflows' explicit `allow-arm64` opt-in; callers remain x86_64/amd64-only
  by default.
- External actions use full 40-character SHAs.
- Top-level least-privilege permissions, job timeouts, locked installs, and
  `persist-credentials: false` are mandatory.
- Pass caller-controlled command inputs through `env`; never interpolate event
  or input expressions directly into `run`.
- Publication builds once and publishes the exact validated bytes/digest.
- Keep `catalog.json`, starters, README, and tests aligned with workflow changes.

## Required checks

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
actionlint -config-file .github/actionlint.yaml
```

Use `apply_patch` for edits. Preserve unrelated dirt. Create/claim a bead before
non-trivial implementation.
