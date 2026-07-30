# dinglebear-ai/workflows

Canonical GitHub Actions workflows for the dinglebear-ai fleet and new
repositories.

This public repository is the source of truth for reusable CI, release,
publishing, MCP, security, deployment, and policy workflows. Repositories call
these workflows directly at an immutable full commit SHA. They do not copy and
then independently maintain the implementation.

## Non-negotiable policy

- Fast Linux validation runs on the self-hosted runner farm with one explicit
  `ci-pool-*` scheduling label.
- Heavy release work runs only from a verified release and only on
  GitHub-hosted x86_64 runners.
- No workflow builds, packages, downloads, publishes, or advertises ARM output.
- Full checks move to the correct trigger; they are not silently deleted to
  improve speed.
- External actions use full 40-character commit SHAs.
- Permissions are least privilege, checkout credentials are not persisted,
  installs are locked, jobs have timeouts, and pull-request runs cancel when
  superseded.
- Release jobs build once, validate the exact result, and publish those bytes or
  that digest.
- Callers pin this repository to a full commit SHA. `@main` and moving version
  tags are forbidden.

## Quick start

Choose a starter and install it into a new checkout:

```bash
cd ~/workspace/workflows
./scripts/bootstrap.sh rust ~/workspace/my-new-repo
```

Available starters:

- `rust`
- `python`
- `node`
- `pnpm`
- `bun`

The bootstrap script resolves the current `dinglebear-ai/workflows` commit and
embeds that immutable SHA in the caller. It refuses to overwrite an existing
workflow unless `--force` is supplied.

A direct caller looks like:

```yaml
jobs:
  ci:
    uses: dinglebear-ai/workflows/.github/workflows/fast-rust.yml@0123456789abcdef0123456789abcdef01234567
    with:
      check-command: cargo check --workspace --all-targets --all-features --locked
    secrets: inherit
```

GitHub reusable-workflow permissions can only stay the same or become more
restrictive through a call chain. The caller job must grant every permission
the called workflow needs, especially `id-token: write`, `packages: write`,
`security-events: write`, or `contents: write` for release jobs.

## Workflow catalog

[`catalog.json`](catalog.json) is the machine-readable inventory and profile
map. The library currently covers:

### Fast CI

- Rust: fmt, check, Clippy, targeted tests, kache, cargo-deny, optional MSRV.
- Python: frozen uv sync, Ruff, typecheck, Pytest, and pip-audit.
- TypeScript/Node: npm, pnpm, and Bun variants with locked installs, audits,
  lint, typecheck, tests, contracts, and optional fast builds.
- Go: module verification, generation drift, vet, tests, and govulncheck.
- CodeQL: one language/pool per call.
- Shell/operations: actionlint, ShellCheck, `bash -n`, and policy commands.
- Marketplace/plugin validation and residential synthetics.

### Hosted release and deployment

- Rust Linux and native Linux/macOS/Windows x86_64 artifacts.
- Go x86_64 archives.
- Python wheels/sdists and trusted PyPI publishing.
- npm trusted publishing.
- crates.io publishing.
- Bun/npm/pnpm web coverage, production builds, performance, and browser E2E.
- Android release checks and managed-device evidence.
- amd64 container build, smoke, scan, SBOM, provenance, and digest promotion.
- GitHub release assets and attestations.
- GitHub Pages.
- Unraid plugin validation and release.

### MCP

- Pinned official MCP conformance suite with retained evidence.
- Official MCP Registry publication through GitHub OIDC or DNS ownership.
- Package visibility checks before registry publication.
- Exact `server.json` version validation and post-publication verification.

### Release orchestration

- Release Please as the immutable release identity owner.
- Non-canceling release serialization.
- Exact tag/SHA handoff into hosted heavy workflows.

## Runner labels

Scheduling pools:

| Label | Work |
|---|---|
| `ci-pool-rust` | Rust fast CI |
| `ci-pool-python` | Python fast CI |
| `ci-pool-typescript` | npm, pnpm, Bun, frontend fast CI |
| `ci-pool-go` | Go fast CI |
| `ci-pool-ops` | tiny shell, YAML, policy, metadata, synthetics |
| `ci-pool-jvm` | optional fast Gradle/debug Android lane |
| `ci-pool-system` | privileged OS/kernel/service integration |

Capability labels supplement a pool and never replace it:
`residential-egress`, `ci-cap-zfs`, `ci-cap-docker`, `ci-cap-kvm`, and
`ci-cap-gpu`.

The workflow library validates itself on GitHub-hosted Linux as an explicit
control-plane exception. It must remain repairable when the self-hosted farm or
its labels are unavailable.

## Kache and MinIO

Rust workflows use private local kache stores with the shared S3-compatible
remote at `https://s3.tootie.tv`, bucket `kache`.

Required organization secrets:

- `KACHE_S3_ACCESS_KEY`
- `KACHE_S3_SECRET_KEY`

The MinIO identity must have only `ListBucket`, `GetObject`, and `PutObject`
rights on the kache bucket. The bucket needs a lifecycle policy because kache
does not evict remote objects.

A shared endpoint does not guarantee shared hits. Compiler, target, profile,
features, linker flags, Cargo config, and compatible system libraries must
match. Release artifacts do not reuse debug/check-profile objects merely
because they share a bucket.

## Publishing environments

Create protected GitHub environments before enabling publication:

- `npm`
- `pypi`
- `crates-io`
- `mcp-registry-publish`
- `github-pages`

Restrict environments to the default branch and release tags. Add a required
reviewer for irreversible publishing where practical.

Required secrets vary by workflow:

- crates.io: `CRATES_IO_TOKEN`
- MinIO kache: `KACHE_S3_ACCESS_KEY`, `KACHE_S3_SECRET_KEY`
- MCP DNS ownership only: `MCP_PRIVATE_KEY`
- container registry: `REGISTRY_USERNAME`, `REGISTRY_TOKEN`

npm, PyPI, and the preferred MCP Registry flow use OIDC and do not need
long-lived publication tokens.

## Updating callers

1. Change and validate this repository.
2. Merge to `main`.
3. Record the resulting full commit SHA.
4. Update caller `uses:` references through one reviewed fleet change.
5. Let branch protection prove the update before removing the old SHA.

Do not force-move a tag to update callers. Immutable SHA references make each
repository's effective workflow version auditable.

## Repository layout

```text
.github/workflows/   reusable workflow implementations
starters/            event-owning caller workflows for new repositories
scripts/             bootstrap and validation tools
tests/               library contract tests
docs/                architecture and operating guidance
catalog.json         workflow and profile inventory
```

## Validation

```bash
python -m pip install PyYAML==6.0.2
python scripts/validate.py
python -m unittest discover -s tests -v
actionlint -config-file .github/actionlint.yaml
```

The validator fails on uncatalogued workflows, mutable actions, missing
permissions/timeouts, unsafe checkout credentials, direct event/input
interpolation into shell, forbidden architecture contracts, fast hosted jobs,
or self-hosted release jobs.

## Upstream references

- [GitHub reusable workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)
- [GitHub secure use](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [MCP Registry GitHub Actions guide](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/github-actions.mdx)
- [Official MCP conformance suite](https://github.com/modelcontextprotocol/conformance)
- [Cargo publishing](https://doc.rust-lang.org/cargo/reference/publishing.html)

