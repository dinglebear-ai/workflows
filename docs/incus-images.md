---
title: Incus image workflow contract
created: 2026-07-30
updated: 2026-07-30
---

# Incus image workflow contract

Incus image assembly is a heavyweight release operation. It runs only from an
existing release, on GitHub-hosted Linux x86_64, and never on the self-hosted
runner farm.

## Reusable workflow

`hosted-incus-image.yml` owns the invariant mechanics:

1. check out the exact release tag or commit;
2. run the repository-owned pinned tool setup;
3. validate definitions and scripts;
4. build and export the image;
5. smoke the exported image with disposable Incus names;
6. generate an SPDX JSON SBOM;
7. generate and verify `SHA256SUMS`;
8. retain the exact directory as a workflow artifact.

The complete event-owning caller is
[`templates/callers/incus-image-release.yml`](../templates/callers/incus-image-release.yml).
It publishes the retained bytes through `github-release.yml`, which adds GitHub
artifact attestations and attaches the exact outputs to the existing release.

## Repository-owned scripts

Adopting repositories provide four executable scripts:

| Script | Responsibility |
|---|---|
| `scripts/ci/setup-incus-builder.sh` | Install exact Incus/distrobuilder dependencies and verify versions or checksums |
| `scripts/ci/validate-incus-image.sh` | Parse shell, validate distrobuilder YAML, and reject unsupported architecture declarations |
| `scripts/ci/build-incus-image.sh` | Export the x86_64 metadata/rootfs pair into `dist/` |
| `scripts/ci/smoke-incus-image.sh` | Import, launch, probe, stop, and delete a uniquely named disposable instance |

The setup script is deliberately caller-owned because current products use
different distrobuilder acquisition paths. Whatever path is chosen must pin a
version and verify a release checksum; an unpinned snap or moving package is
not a release contract.

If image assembly compiles Rust, callers may set `enable-kache: true`, pass a
product-specific `kache-manifest-key`, and forward `KACHE_S3_ACCESS_KEY` plus
`KACHE_S3_SECRET_KEY`. The reusable workflow enables kache only after the
caller-owned setup command, so that command must install the required Rust
toolchain. Non-Rust callers keep the default disabled behavior and need no
Kache secrets.

## Output contract

`dist/` may contain product-specific filenames, but it must contain only the
release image, metadata/provenance, and evidence intended for publication.
The reusable workflow adds:

- `image.spdx.json`;
- `SHA256SUMS`.

The smoke script must import and exercise the exact exported files. It must use
run-specific aliases, instances, and profiles and clean them with a trap so a
failed run cannot poison a retry.

## Adoption

1. copy the caller template to `.github/workflows/incus-image-release.yml`;
2. replace `__WORKFLOWS_SHA__` with the reviewed full commit SHA;
3. add the four scripts above;
4. ensure Release Please creates the release event;
5. grant the publish job `contents`, `attestations`, and `id-token` write
   permissions as shown in the template;
6. protect the ordinary fast CI gate separately.

Do not add pull-request, main-push, schedule, or arbitrary tag triggers to the
image build. Fast CI validates scripts and definitions without assembling the
image.
