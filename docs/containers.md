---
title: CI container images
created: 2026-07-30
updated: 2026-07-30
---

# CI container images

The runner farm provides scheduling and execution. These images provide a
stable toolchain inside a GitHub Actions job container.

## Release images

| Image | Pinned floor |
|---|---|
| `ghcr.io/dinglebear-ai/workflows-ci-rust` | Rust 1.97.1, Clippy, rustfmt, cargo-nextest 0.9.140, cargo-deny 0.20.2, cargo-audit 0.22.2, kache 0.12.0 |
| `ghcr.io/dinglebear-ai/workflows-ci-python` | Python 3.14.6, uv 0.11.31, Ruff 0.16.0, ty 0.0.65, Pytest 9.1.1, pip-audit 2.9.0 |
| `ghcr.io/dinglebear-ai/workflows-ci-typescript` | Node 24.18.0, npm, pnpm 11.15.1, Bun 1.3.14 |

Base images are pinned to the exact upstream Linux amd64 manifest digest.
Builds request only `linux/amd64`, and the shared smoke test rejects any other
runtime architecture.

## Use in a caller

Pin the published image by digest for protected CI:

```yaml
jobs:
  test:
    runs-on: ci-pool-python
    container:
      image: ghcr.io/dinglebear-ai/workflows-ci-python@sha256:<digest>
    steps:
      - uses: actions/checkout@<full-action-sha>
        with:
          persist-credentials: false
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run ty check
      - run: uv run pytest
```

The pool label and container image solve different problems:

- the pool selects capacity and warm cache mounts;
- the image selects userspace, compilers, and package managers;
- the repository lockfile selects project dependencies.

Do not use `latest` in a protected caller. Release tags are convenient for
manual use, while digests provide the immutable contract.

## Cache mounts

The images intentionally do not bake project dependencies. Configure the
runner farm to mount the appropriate cache paths:

| Image | Useful persistent paths |
|---|---|
| Rust | `/usr/local/cargo/registry`, `/usr/local/cargo/git`, a private kache local store |
| Python | `/root/.cache/uv`, `/root/.cache/pip` |
| TypeScript | `/root/.npm`, `/root/.local/share/pnpm/store`, `/root/.bun/install/cache` |

Kache's local database/store remains private to a compatible runner. Only its
S3 content-addressed remote is shared across devhost, the farm, and hosted
release builders.

## Build and test locally

```bash
./scripts/build-images.sh
./scripts/test-images.sh
```

The local tags are `workflows-ci-{rust,python,typescript}:local`.

## Publication

`publish-ci-images.yml` runs only when a GitHub release is published. It calls
the hosted release workflow, builds all three images on GitHub-hosted Linux,
scans the exact pushed digest, emits provenance/SBOM data, and publishes
release, commit, and `latest` tags. The first GHCR versions do not exist until
the first workflow-library release containing these Dockerfiles completes.

Toolchain bumps are ordinary reviewed changes:

1. update the Dockerfile argument or pinned base manifest;
2. build and smoke all images locally;
3. merge after repository validation;
4. let Release Please create the release;
5. consume the new published digest through a reviewed caller update.
