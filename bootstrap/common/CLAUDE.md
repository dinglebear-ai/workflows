# __REPOSITORY_NAME__

## Source of truth

`CLAUDE.md` is the agent-memory source of truth. `AGENTS.md` and `GEMINI.md`
must remain symlinks to this file.

## Development contract

- Preserve unrelated changes.
- Use locked dependency installs and deterministic checks.
- Fast Linux CI runs on the appropriate `ci-pool-*` runner-farm pool.
- Heavy build, packaging, publication, and release work is release-only on
  GitHub-hosted x86_64 runners.
- Do not add ARM build or release output.
- External GitHub Actions use full commit SHAs.
- Put long plans, specifications, sessions, and reports under `docs/`.
