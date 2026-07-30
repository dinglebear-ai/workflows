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

## Product-specific release output

Use `hosted-release-command.yml` for a product-specific build that does not
justify another reusable language workflow. The caller still owns the command,
artifact name, release identity, and downstream publication order.

Examples include a browser extension bundle, desktop palette application,
Incus image archive, or generated plugin package. Reuse the hosted checkout,
timeout, failure behavior, and artifact retention rather than cloning a whole
workflow.

## MCP

The full conformance suite is release-only because it may start a real server
and exercise the entire protocol surface. Package publication must complete
before `mcp-registry-publish.yml`, because the official registry verifies that
referenced packages are publicly resolvable.
