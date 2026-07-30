# Fleet workflow reconciliation

## Scope and result

The 2026-07-30 live checkout contains 117 workflow files across 22 repositories
outside `dinglebear-ai/workflows`. This library now provides 44 reusable
mechanical workflows covering every repeated family found in that census.

This is not a promise to replace 117 files with 117 remote files. GitHub callers
must still own triggers, path classification, product-specific job graphs,
authorization conditions, and stable aggregate gates. The table records both
the reusable destination and the intentionally local boundary.

## Repository mapping

| Repository | Existing | Reusable destinations | Intentionally caller-owned |
|---|---:|---|---|
| `aurora` | 4 | fast pnpm/Bun, Android release, container release, Release Please, synthetics | monorepo path classifier and web/Android gate |
| `axon` | 12 | fast Rust/TypeScript, CodeQL, Android/container/platform release, hosted release command, Release Please, system integration | component release graph, Claude bot authorization, session-log automerge, live Qdrant/RAG topology; retire redundant auto-tag |
| `ci-runner-farm` | 4 | fast ops, Unraid plugin validate/package/release, Release Please, hosted release command | upstream-fork compatibility and self-contained `.plg` assembly contract |
| `connexin` | 2 | fast Node/Go, hosted Go release, npm publish, GitHub release | helper/product artifact composition |
| `cortex` | 4 | fast Rust/npm, security/docs/install contract, container/platform release, Release Please | MCP live integration and exact multi-artifact graph |
| `dendrite` | 1 | marketplace CI, repository policy | marketplace inventory inputs |
| `filestash` | 1 | fast Node/Go, container release, GitHub release | upstream fork policy and product SBOM graph |
| `incus-web` | 1 | fast Node, hosted Incus image, GitHub release | Incus web/product commands and deployment destination |
| `labby` | 7 | all fast language/ops lanes, labeler/stale/drift, MCP conformance, Android/container/platform/Incus release | trusted classifier, Windows/custom palette graph, upstream API semantics |
| `lavra` | 3 | fast Bun, Pages, npm publish, install contract | macOS compatibility matrix and release visibility probe |
| `rapprise` | 4 | fast Rust/npm, security/install, container/platform release, Release Please | installer package composition and MCP-specific order |
| `rarcane` | 7 | fast Rust/npm, CodeQL/MSRV/security, Dependabot, container/platform release | template validation and artifact staging |
| `rgotify` | 3 | fast Rust/npm/install, platform release, npm publish, Release Please | exact binary/npm handoff |
| `rtailscale` | 3 | fast Rust/npm/install, platform release, npm publish, Release Please | exact binary/npm handoff |
| `runifi` | 4 | fast Rust/npm, security/install, container/platform release, Release Please | exact binary/npm handoff |
| `rytdl` | 6 | fast Rust/npm, CodeQL/security, container/platform release, npm/GitHub publish | MCPB packaging and live media tests |
| `soma` | 13 | fast Rust/Node/Go, rustdoc/MSRV/security, CodeQL, native wheels, container/platform release, conformance, drift, Release Please | 34-crate classifier, Codex schema semantics, rmcp release issue policy |
| `synapse` | 7 | fast Rust/npm/web, CodeQL/MSRV/security, Dependabot, container/platform release | live workflow integration and template contract |
| `unraid` | 19 | fast Python/Rust/Node/ops, native wheels, PyPI/crates/npm/MCP publication, container, Unraid plugin, drift, release liveness | monorepo component dispatch, `.plg` compatibility, Incus/Codex/MCP product assembly |
| `yarr` | 10 | fast Rust/npm/ops, CodeQL/MSRV/security, Dependabot, container/platform release, Unraid plugin, Release Please | media-service integration, failure notification, component release order |
| `young-office` | 1 | fast Node and repository policy | application governance command |
| `zfs` | 1 | fast ops and system integration with `ci-cap-zfs` | privileged fixture setup and aggregate test summary |

## Repeated families added after the initial extraction

The first library pass omitted these generic shapes; they now have canonical
definitions:

- Dependabot auto-merge;
- pull-request labeler;
- stale lifecycle;
- upstream/schema drift monitor;
- installer/release-asset contract;
- repository/community policy;
- Rust documentation;
- native Python wheels;
- generic hosted product release command;
- canonical CI image release.

## Shapes that should not become generic reusables

- path classifiers and required aggregate gates;
- arbitrary Claude/GitHub bot authorization;
- component-specific Release Please fixups;
- live-service topology and credentials;
- upstream-fork release compatibility;
- exact artifact graphs where filenames are a product API;
- notification content and escalation policy.

Those remain small caller workflows that invoke the shared mechanics. Turning
them into a generic remote shell escape hatch would centralize risk without
creating a stable contract.

## Migration implication

The extraction is complete at the workflow-family level. Fleet migration is
still separate work: each caller must be rewritten, pinned, reviewed, run
against live pool labels, and protected before its old implementation is
deleted.
