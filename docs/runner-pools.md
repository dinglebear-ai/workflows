# Runner pools

Every fast Linux job selects exactly one scheduling pool. Capability labels are
additional constraints, not substitutes for a pool.

| Pool | Intended work |
|---|---|
| `ci-pool-rust` | Rust format, check, Clippy, targeted tests, rustdoc, dependency policy |
| `ci-pool-python` | uv sync, lint, typecheck, targeted Python tests |
| `ci-pool-typescript` | npm, pnpm, Bun, frontend lint/typecheck/unit tests |
| `ci-pool-go` | Go module, generation, vet, vulnerability, and unit checks |
| `ci-pool-ops` | YAML/shell/policy, metadata, labeler, stale, drift, lightweight synthetics |
| `ci-pool-jvm` | Optional fast Gradle/debug Android work when dedicated capacity exists |
| `ci-pool-system` | Privileged OS, service, kernel, ZFS, KVM, or nested-runtime integration |

Capabilities currently modeled:

- `residential-egress`
- `ci-cap-zfs`
- `ci-cap-docker`
- `ci-cap-kvm`
- `ci-cap-gpu`

Examples:

```yaml
runs-on: [self-hosted, ci-pool-rust]
```

```yaml
runs-on: [self-hosted, ci-pool-system, ci-cap-zfs]
```

Heavy release jobs never use these pools. They run on GitHub-hosted x86_64
Linux, Windows, or macOS runners after a verified release identity exists.

Pool labels improve queue isolation but provide no security isolation. Runner
groups, repository allowlists, fork approval, immutable actions, minimal token
permissions, and the planned owner-authorization gate remain separate controls.
