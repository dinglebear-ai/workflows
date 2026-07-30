---
title: Release and publication recipes
created: 2026-07-30
updated: 2026-07-30
---

# Release and publication recipes

## Canonical graph

```text
protected fast CI
  -> Release Please
  -> immutable release tag and commit
  -> hosted quality/build jobs
  -> package registries
  -> official MCP Registry
  -> GitHub release assets and attestations
```

Heavy work is release-only. A manual recovery run must identify an existing
Release Please release; it cannot invent an independent version.

## Rust binary

1. `release-please.yml`
2. `hosted-rust-release.yml` or `hosted-rust-platform-release.yml`
3. `github-release.yml`
4. optional `npm-trusted-publish.yml` for an npm launcher
5. optional `mcp-registry-publish.yml`

Use `install-contract.yml` in fast CI when a one-line installer or npm launcher
consumes the assets.

## Python package

1. Release Please
2. `hosted-python-package-release.yml` for pure Python wheel/sdist
3. `hosted-python-wheels.yml` for native x86_64 wheels
4. PyPI trusted publication
5. MCP Registry publication after PyPI visibility
6. GitHub release evidence

## Node, pnpm, or Bun

1. Release Please
2. hosted web quality/build workflow when a production application is shipped
3. `npm-trusted-publish.yml`
4. MCP Registry publication after npm visibility
5. Pages or container deployment when applicable

## Container

`hosted-container-release.yml` builds one `linux/amd64` candidate, pushes it by
immutable commit tag, smokes and scans its exact digest, then promotes that
digest to the release tag.

## Incus image

`hosted-incus-image.yml` checks out the release identity, runs pinned
repository-owned setup/validation/build/smoke scripts, generates an SBOM and
checksum inventory, and retains the exact image directory. The full caller in
`templates/callers/incus-image-release.yml` publishes it through
`github-release.yml`.

## Unraid plugin

`unraid-plugin-validate.yml` keeps `.plg`, script, URL, version, and checksum
contracts in fast CI. The release caller uses hosted `unraid-plugin-ci.yml` to
package and checksum exact bytes, then `unraid-plugin-release.yml` to reverify
and attach them to the existing release.

## Product-specific release output

Use `hosted-release-command.yml` for a product-specific build that does not
justify another reusable language workflow. The caller still owns the command,
artifact name, release identity, and downstream publication order.

Examples include a browser extension bundle or desktop palette application.
Incus images and Unraid plugins have dedicated workflows because their
build/smoke/checksum contracts repeat across the fleet.

## MCP

The full conformance suite is release-only because it may start a real server
and exercise the entire protocol surface. Package publication must complete
before `mcp-registry-publish.yml`, because the official registry verifies that
referenced packages are publicly resolvable.
