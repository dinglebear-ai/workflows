# Repository bootstrap

The bootstrap kit handles more than GitHub Actions. It installs the durable
repository floor identified by the fleet audits without overwriting an existing
project by default.

## One-line setup

Run from any machine with Bash, curl, git, tar, and an initialized target Git
repository:

```bash
curl -fsSL https://raw.githubusercontent.com/dinglebear-ai/workflows/main/install.sh \
  | bash -s -- rust ~/workspace/example
```

Profiles are `rust`, `python`, `node`, `pnpm`, and `bun`.

The streamed installer resolves `main` to a full commit SHA before downloading
the repository archive. Every generated reusable-workflow caller embeds that
resolved SHA. To reproduce a known bootstrap exactly:

```bash
curl -fsSL https://raw.githubusercontent.com/dinglebear-ai/workflows/main/install.sh \
  | WORKFLOWS_SHA=0123456789abcdef0123456789abcdef01234567 \
    bash -s -- rust ~/workspace/example
```

For a checked-out copy of this repository:

```bash
./scripts/bootstrap.sh rust ~/workspace/example
```

Useful modes:

```bash
./scripts/bootstrap.sh --dry-run rust ~/workspace/example
./scripts/bootstrap.sh --ci-only python ~/workspace/existing-service
./scripts/bootstrap.sh --force pnpm ~/workspace/example
```

`--force` only replaces files owned by this bootstrap kit. It does not remove
unrecognized files.

## Installed common files

- `.editorconfig` and `.gitattributes`;
- `.env.example` with every real `.env` ignored by profile;
- `CLAUDE.md`, with `AGENTS.md` and `GEMINI.md` symlinked to it;
- `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md`;
- CODEOWNERS, pull-request template, private-security contact, and bug template;
- `docs/index.md` describing the plans/sessions/specs/contracts/reports layout;
- Release Please config and an initial `0.0.0` manifest;
- Actions label configuration and profile-aware Dependabot configuration;
- CI, repository-policy, and Release Please caller workflows.

## Profile files

| Profile | Additional files |
|---|---|
| Rust | Rust `.gitignore`, `rust-toolchain.toml`, `rustfmt.toml`, Cargo Dependabot |
| Python | Python `.gitignore`, pip Dependabot |
| Node | Node `.gitignore`, `.npmrc`, npm Dependabot |
| pnpm | pnpm `.gitignore`, strict `.npmrc`, npm Dependabot |
| Bun | Bun `.gitignore`, `.npmrc`, npm Dependabot |

Project manifests are deliberately not generated. A generic `Cargo.toml`,
`pyproject.toml`, or `package.json` tends to become stale product policy.
Language-native project generators should create those files; this kit adds the
fleet contract around them.

## After bootstrap

1. Review every generated file before committing.
2. Replace the placeholder README/project description.
3. For an existing repository, seed `.release-please-manifest.json` from the
   latest real GitHub release rather than `0.0.0`.
4. Add `RELEASE_PLEASE_TOKEN` or a GitHub App token capable of triggering
   downstream release workflows.
5. Add only the publication environments and secrets actually used.
6. Configure the GitHub repository settings described below.
7. Run the generated CI and policy workflows before protecting their aggregate
   `CI` and `Policy` jobs.

## Repository settings not representable as files

- Actions default token permissions: read-only.
- Outside-collaborator workflow approval: required.
- Runner group: restricted to approved repositories.
- Merge strategy: squash and linear history.
- Delete branches after merge.
- Secret scanning, push protection, and private vulnerability reporting.
- Protected publishing environments.
- Required stable aggregate checks, not path-dependent leaf jobs.
- Wiki and Projects disabled unless the repository actually uses them.

The installer does not mutate GitHub settings or upload secrets. Those are
external-state changes and require an explicit rollout.

## Binary installer template

[`templates/installers/rust-binary-install.sh`](../templates/installers/rust-binary-install.sh)
is the complete one-line binary installer template derived from the fleet
contract. It:

- accepts canonical repository, version, mirror, and install-directory
  overrides;
- supports Linux x86_64 only;
- retries HTTPS downloads;
- verifies the published SHA-256 file;
- rejects archives containing anything except the bare binary;
- never relies on a legacy owner redirect.

Adopt it as `scripts/install.sh`, keep a thin root `install.sh` shim for the
published raw GitHub URL, and run the included asset-contract test in fast CI.
