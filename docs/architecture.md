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

