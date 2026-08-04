---
title: Architecture
created: 2026-07-30
updated: 2026-08-04
---

# Architecture

## Two layers

Caller workflows own events, repository-specific path classification, branch
protection, commands, and the stable aggregate gate.

Reusable workflows own repeatable mechanics: toolchain setup, caches,
permissions, runner placement, validation stages, packaging, attestations, and
publication.

This separation is required because GitHub reusable workflows cannot define the
caller's event trigger or dynamically become a required branch-protection
context.

## Trust model

The library is public so public and private repositories can call it. Public
does not mean mutable: callers use a reviewed full commit SHA.

The caller supplies commands and secrets. Command inputs are trusted
repository configuration, not user/event data. Each reusable workflow copies
commands into an environment variable before execution.

Fast jobs run on persistent privileged self-hosted runners only after the
repository's normal actor/fork authorization boundary. Heavy release and
publication jobs run on clean GitHub-hosted machines.

An owner-only self-hosted authorization gate remains a separate planned
control. When implemented, every farm job must structurally `needs` a hosted
authorization job, and fleet policy must reject callers that omit it.

## Version model

The repository `main` branch is development state. The effective API version
for a caller is the exact commit SHA in its `uses:` line. Human-readable
releases/changelogs may group changes, but moving tags are never caller
dependencies.

## Rust cache model

The private Linux fleet uses one Kache topology across repositories:

- Each Tootie runner owns an isolated 80 GiB local L1 store. Dookie owns a
  separate 100 GiB local L1 store.
- The only shared remote is the MinIO S3 prefix `s3://kache/rust`.
- The retired NFS cache is not mounted, mirrored, or retained as a fallback.
- Runners preserve the host-provided Kache configuration and run one supervised
  daemon. Dookie runs one user-systemd-owned daemon.
- Jobs without the private S3 profile remain local-only. They must not invent a
  filesystem remote or overwrite an existing host configuration.

The full rationale, migration evidence, and operational consequences are in
[ADR 0001](./adr/0001-kache-minio-single-remote.md).

## Release graph

```text
fast protected gate
  -> Release Please on main
  -> immutable release tag and SHA
  -> hosted quality/build jobs
  -> package registries
  -> official MCP Registry
  -> GitHub release assets and attestations
```

Package publication must complete before MCP Registry publication because the
official registry validates referenced packages.
