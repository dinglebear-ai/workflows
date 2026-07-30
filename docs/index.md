# Documentation

`dinglebear-ai/workflows` is both the canonical GitHub Actions library and the
new-repository bootstrap kit for the fleet.

## Start here

| Document | Purpose |
|---|---|
| [Architecture](architecture.md) | Caller/reusable boundaries and release graph |
| [Workflow catalog](workflow-catalog.md) | Workflow families, selection, and calling conventions |
| [Runner pools](runner-pools.md) | Pool and capability label contracts |
| [Bootstrap](bootstrap.md) | One-line setup, installed files, profiles, and migration |
| [CI images](containers.md) | Rust, Python, and TypeScript job containers |
| [Incus images](incus-images.md) | Hosted image build, smoke, evidence, and publication contract |
| [Unraid plugins](unraid-plugins.md) | Fast manifest validation and hosted package/release contract |
| [Release recipes](release-recipes.md) | Release Please, artifacts, registries, and MCP ordering |
| [Security](security.md) | Threat model, permissions, pinning, and self-hosted boundaries |
| [Fleet reconciliation](fleet-reconciliation.md) | Mapping of all existing workflow families |
| [Maintenance](maintenance.md) | Versioning, changes, caller upgrades, and rollback |

Machine-readable workflow metadata lives in
[`catalog.json`](../catalog.json). Complete new-repository caller workflows live
in [`starters/`](../starters/), and non-CI repository files live in
[`bootstrap/`](../bootstrap/).
