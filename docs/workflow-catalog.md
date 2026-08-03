---
title: Workflow catalog
created: 2026-07-30
updated: 2026-07-30
---

# Workflow catalog

The catalog contains 45 reusable workflows plus four repository-internal
control-plane workflows. [`catalog.json`](../catalog.json) is authoritative.

## Calling a reusable workflow

```yaml
jobs:
  rust:
    permissions:
      contents: read
      packages: read
    uses: dinglebear-ai/workflows/.github/workflows/fast-rust.yml@0123456789abcdef0123456789abcdef01234567
    with:
      test-command: cargo nextest run --workspace --locked
    secrets: inherit
```

Rules:

- use a full 40-character commit SHA;
- declare job permissions in the caller;
- pass only repository-controlled commands;
- own events, path classification, and the aggregate required gate locally;
- retain product-specific artifact and publication ordering locally.

`marketplace-ci.yml` keeps both caches enabled by default for compatibility.
Manifest-only marketplaces without a Python dependency manifest, npm lockfile,
or both must pass `enable-python-cache: false`, `enable-node-cache: false`, or
both. The validation and installation commands still run; only setup-action
caching is skipped.

If validation itself invokes a Node-based marketplace CLI,
`validation-setup-command` installs that pinned tool after Node and Python are
available but before the validation command runs.

Mixed-language Rust repositories can use `fast-rust.yml`'s `setup-command` for
locked dependency preparation such as `uv sync --frozen`. It runs after the
toolchain and Kache setup but before every Rust validation command. Pass an
exact `uv-version` when that setup command invokes uv; an empty value keeps
pure-Rust callers free of Python tooling.

## Inventory

| Workflow | Kind | Category | Purpose |
|---|---|---|---|
| `cargo-publish.yml` | release | Rust | Verify and publish one immutable crates.io version |
| `codeql.yml` | fast | Security | Run one language-specific CodeQL lane |
| `dependabot-automerge.yml` | fast | Automation | Approve and auto-merge explicitly allowed Dependabot updates |
| `drift-monitor.yml` | fast | Automation | Run an upstream/schema drift command and retain evidence |
| `fast-bun.yml` | fast | TypeScript | Locked Bun audit, lint, typecheck, tests, optional build |
| `fast-go.yml` | fast | Go | Vulnerability, module, generation, vet, and unit checks |
| `fast-node.yml` | fast | TypeScript | Locked npm audit, lint, typecheck, tests, contracts; cache can be disabled and an optional Python toolchain can support mixed Node/Python projects |
| `fast-ops.yml` | fast | Operations | Actionlint, ShellCheck, Bash parsing, policy command |
| `fast-pnpm.yml` | fast | TypeScript | Locked pnpm audit, lint, typecheck, tests, contracts |
| `fast-python.yml` | fast | Python | Frozen uv sync, Ruff lint/format, ty typecheck, Pytest |
| `fast-rust.yml` | fast | Rust | Optional project setup, fmt, check, Clippy, targeted tests, MinIO kache |
| `fleet-policy.yml` | fast | Policy | Runner, action, permission, timeout, architecture, release policy |
| `github-release.yml` | release | Release | Attest and attach exact artifacts to an existing release |
| `hosted-android-release.yml` | release | Android | Hosted release lint, tests, assembly, device evidence |
| `hosted-bun-web-release.yml` | release | TypeScript | Bun coverage, production build, performance, E2E |
| `hosted-ci-images-release.yml` | release | Container | Build, scan, and publish the three canonical CI images |
| `hosted-container-release.yml` | release | Container | Build, smoke, scan, and promote one amd64 digest |
| `hosted-go-release.yml` | release | Go | Build x86_64 Go archives and checksums |
| `hosted-incus-image.yml` | release | Incus | Hosted x86_64 image build, optional MinIO kache for Rust assembly, smoke, SBOM, and checksums |
| `hosted-python-package-release.yml` | release | Python | Build, verify, and trusted-publish wheel/sdist |
| `hosted-python-wheels.yml` | release | Python | Native x86_64 wheels on hosted Linux/macOS/Windows |
| `hosted-release-command.yml` | release | Release | Product command with exact hosted artifact retention |
| `hosted-rust-platform-release.yml` | release | Rust | Native Linux/macOS/Windows x86_64 Rust artifacts |
| `hosted-rust-release.yml` | release | Rust | Hosted Linux Rust artifact with MinIO kache |
| `hosted-web-release.yml` | release | TypeScript | npm/pnpm coverage, build, performance, browser E2E |
| `install-contract.yml` | fast | Policy | Installer and release-asset agreement |
| `marketplace-ci.yml` | fast | Marketplace | Structural validation and installation smoke with independently optional pip/npm caches |
| `mcp-conformance.yml` | release | MCP | Pinned official full MCP conformance evidence |
| `mcp-registry-publish.yml` | release | MCP | Canonical DingleBear identity and package validation, idempotent official Registry publication, and public active-state verification |
| `npm-trusted-publish.yml` | release | TypeScript | Pack, verify, and OIDC-publish exact npm tarball, including dependency-free packages without lockfiles |
| `pages-deploy.yml` | deployment | TypeScript | Build and deploy Pages with split permissions |
| `python-security.yml` | fast | Python | Audit a frozen dependency export |
| `release-please.yml` | fast | Release | Serialize Release Please and emit release identity |
| `repository-labeler.yml` | fast | Automation | Apply labels from caller-owned path rules |
| `repository-policy.yml` | fast | Policy | Required files, memory symlinks, tracked file size |
| `rust-docs.yml` | fast | Rust | Workspace rustdoc with warnings denied |
| `rust-msrv.yml` | fast | Rust | Explicit minimum Rust validation |
| `rust-security.yml` | fast | Rust | cargo-deny policy |
| `stale.yml` | fast | Automation | Consistent stale lifecycle |
| `synthetic-check.yml` | capability | Operations | Residential-egress synthetic |
| `system-integration.yml` | capability | Operations | Privileged system/capability integration |
| `unraid-plugin-ci.yml` | release | Unraid | Hosted package, exact validation, checksums, and retention |
| `unraid-plugin-release.yml` | release | Unraid | Publish exact validated plugin bytes |
| `unraid-plugin-validate.yml` | fast | Unraid | Static plugin, manifest, and script contracts |

Internal workflows:

- `validate-library.yml` keeps the control plane repairable on hosted Linux;
- `manage-release.yml` owns this repository's Release Please event;
- `publish-ci-images.yml` publishes images only from a GitHub release;
- `hosted-kache-canary.yml` seeds MinIO on one hosted runner and requires
  remote cache reuse on a second fresh runner.

## Profiles

Profiles in `catalog.json` are curated sets, not workflow composition engines.
The caller chooses the subset the product needs. For example, a Rust MCP server
usually combines Rust fast CI/security/docs, CodeQL, hosted Rust release, npm
launcher publication, MCP conformance, MCP Registry publication, and GitHub
release assets.
