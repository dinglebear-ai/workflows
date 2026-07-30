---
title: Unraid plugin workflow contract
created: 2026-07-30
updated: 2026-07-30
---

# Unraid plugin workflow contract

Unraid plugins have two distinct lanes: fast source/manifest validation on the
ops pool, and hosted release-only `.txz` packaging and publication.

## Reusable workflows

| Workflow | Runner | Responsibility |
|---|---|---|
| `unraid-plugin-validate.yml` | `ci-pool-ops` | Validate `.plg`, shell, XML, metadata, URLs, and source contracts without assembling a package |
| `unraid-plugin-ci.yml` | GitHub-hosted x86_64 | Build once, validate exact package bytes, generate `SHA256SUMS`, and retain the release candidate |
| `unraid-plugin-release.yml` | GitHub-hosted x86_64 | Download, reverify, revalidate, and attach the exact files to an existing release |

Complete callers:

- [`templates/callers/unraid-plugin-ci.yml`](../templates/callers/unraid-plugin-ci.yml)
- [`templates/callers/unraid-plugin-release.yml`](../templates/callers/unraid-plugin-release.yml)

## Expected repository contract

The templates expect:

- plugin sources below `unraid-plugin/`;
- `scripts/ci/validate-unraid-plugin.sh`;
- `scripts/ci/build-unraid-plugin.sh`;
- release output below `dist/unraid/`.

Fast validation should verify:

- all shell files parse and pass ShellCheck;
- `.plg` XML/entities parse;
- package URLs use the canonical `dinglebear-ai` repository;
- version, tag, package filename, and SHA-256 agree;
- no unsupported architecture package name, path, URL, or conditional exists;
- default environment/config files contain no credentials;
- install/remove scripts use safe absolute Unraid paths.

The hosted package step should additionally:

- build the `.txz` deterministically;
- verify the archive inventory, modes, ownership, and symlink policy;
- confirm embedded payload checksums;
- rebuild under different umasks and byte-compare when reproducibility is part
  of the product contract;
- emit the `.plg`, `.txz`, release metadata, and provenance inputs into
  `dist/unraid/`.

The reusable packager generates and verifies `dist/unraid/SHA256SUMS`. The
publisher downloads that artifact, verifies it again, runs the release
validation command against only the downloaded files, and uploads those exact
bytes.

## Release identity

The full caller starts only from an existing GitHub release created by Release
Please and checks out its tag. Component repos that use `unraid-vVERSION-BUILD`
must first prove that the tag resolves to the intended immutable commit and
that the release manifest names the same version/build. Put that
product-specific proof in the build or validation script; do not weaken the
reusable workflow with multiple tag dialects.

Manual recovery may retry an existing release. It must not mint an independent
plugin version.
