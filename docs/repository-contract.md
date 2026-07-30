---
title: Repository contract
created: 2026-07-30
updated: 2026-07-30
---

# Repository contract

`fleet-contract.yml` enforces the durable repository floor independently of
language build and test jobs. It runs on `ci-pool-ops`, checks out both the
caller and the exact workflow-library commit, and runs the checker shipped at
that immutable commit.

## Profiles

The supported profiles are `rust`, `python`, `node`, `go`, and `ops`. All
profiles enforce:

- tracked `CLAUDE.md` sibling links;
- tracked-path and secret hygiene;
- canonical organization references;
- the x86_64-only installer and package contract;
- `.env.example` keys with real tracked consumers;
- `title`, `created`, and `updated` frontmatter on tracked `docs/**/*.md`.

The Rust profile additionally enforces:

- Rust 1.97.1 with Rustfmt and Clippy;
- edition 2024 for every package;
- workspace lint inheritance and the phase-zero rustdoc correctness floor;
- exact `rmcp`, `rmcp-macros`, and `schemars` pins matching `Cargo.lock`;
- one description across the present Cargo, README, npm, and MCP surfaces.

## Adoption

The bootstrap-generated `policy.yml` calls the contract at the same immutable
workflow-library SHA as the other policy jobs. Its stable `Policy` aggregate
must be required by branch protection.

Cross-repository callers must pass that same full SHA as
`implementation-ref`. GitHub associates the called workflow's `github`
context with the caller, so `github.workflow_sha` cannot identify the reusable
workflow implementation.

Run the implementation locally before opening a pull request:

```bash
python ~/workspace/workflows/scripts/fleet_contract.py check \
  --repo . \
  --profile rust
```

Fix findings rather than adding repository-specific exceptions. A rule with a
legitimate fleet-wide exception belongs in this library, with tests and an
explicitly documented boundary.
