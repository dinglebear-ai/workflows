# Security model

## Trust boundaries

Reusable workflows run with the caller repository's event context, token, and
secrets. Publishing this repository makes the implementation callable; it does
not grant this repository access to caller secrets.

Callers pin a full commit SHA. A mutable branch or tag would let a later change
alter privileged behavior without a caller review.

## Self-hosted execution

Self-hosted runners may expose persistent disks, network access, cache mounts,
Docker, or privileged host capabilities. Pool labels are scheduling metadata,
not authorization.

Required controls:

- runner groups restricted to approved repositories;
- outside-collaborator approval and fork restrictions;
- no checkout of untrusted pull-request code in `pull_request_target`;
- no host Docker socket unless the repository is explicitly trusted;
- least-privilege `GITHUB_TOKEN`;
- immutable external action SHAs;
- ephemeral runners where practical.

The owner-only hosted authorization gate requested for all farm jobs remains a
planned hard requirement. It must be a hosted job that every self-hosted job
structurally `needs`; a standalone workflow cannot block an unrelated job from
being scheduled.

## Command inputs

Reusable commands are repository configuration. They are copied into an
environment variable and invoked through `bash -euo pipefail -c`. Event data,
issue text, branch names, tags, and dispatch text must never be interpolated
directly into a shell program.

## Publication

Publication runs on clean GitHub-hosted runners and uses protected environments.
Prefer OIDC trusted publishing for npm, PyPI, and MCP Registry. Long-lived
tokens are limited to registries that do not support the required OIDC flow.

The release graph validates one artifact or digest and promotes those exact
bytes. Rebuilding independently at each publication step is forbidden.

## Container supply chain

- exact amd64 base manifests;
- Linux amd64 build platform only;
- exact-digest vulnerability scan;
- SBOM and provenance from BuildKit;
- digest-pinned consumption in protected jobs;
- no project dependency snapshots baked into shared images.

## Secrets

Bootstrap files contain names and contracts, never values. The bootstrap script
does not read local secret stores or upload repository secrets. Do not add
`.env`, cloud credentials, package tokens, private keys, or runner registration
tokens to this public repository.
