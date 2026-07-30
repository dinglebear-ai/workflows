# CI container images

The repository builds three Linux x86_64 job-container images:

| Image | Toolchain |
|---|---|
| `ghcr.io/dinglebear-ai/workflows-ci-rust` | Rust 1.97.1, Clippy, rustfmt, cargo-nextest, cargo-deny, cargo-audit, kache, native build tools |
| `ghcr.io/dinglebear-ai/workflows-ci-python` | Python 3.14.6, uv 0.11.31, Ruff 0.16.0, ty 0.0.65, Pytest 9.1.1, pip-audit, native extension build tools |
| `ghcr.io/dinglebear-ai/workflows-ci-typescript` | Node 24.18.0, npm, pnpm 11.15.1, Bun 1.3.14 |

They are job containers, not GitHub Actions runner images. The runner farm still
provides the runner process, pool label, workspace, Docker daemon, and persistent
cache mounts. A workflow can select an image with `jobs.<job>.container.image`.

Every base is pinned to the exact upstream linux/amd64 manifest digest. The
publish workflow also requests only `linux/amd64`, and the smoke test rejects
any other runtime architecture.

Project dependencies remain owned by each repository's lockfile. These images
carry only the shared compiler/runtime/package-manager floor so dependency
updates do not require rebuilding the base image.

## Local build

```bash
./scripts/build-images.sh
./scripts/test-images.sh
```

Override the local tag prefix when required:

```bash
IMAGE_PREFIX=registry.example.com/ci ./scripts/build-images.sh
```
