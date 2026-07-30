---
title: New repository setup
created: 2026-07-30
updated: 2026-07-30
---

# New repository setup

## 1. Install a caller

```bash
~/workspace/workflows/scripts/bootstrap.sh rust ~/workspace/example
```

Review the generated workflow and replace repository-specific commands or
paths. The script embeds the current immutable workflow-library SHA.

## 2. Configure Actions

- Add adopted custom labels to `.github/actionlint.yaml`.
- Enable Dependabot for `github-actions`.
- Set default `GITHUB_TOKEN` permissions to read-only.
- Require pull-request approval for all outside collaborators.
- Allow GitHub-owned actions and the exact third-party actions used here.
- Protect one stable aggregate gate, not path-dependent leaf jobs.

## 3. Configure secrets and environments

Only add secrets used by the selected profile. Publication secrets belong in
protected environments, not ordinary repository secrets.

## 4. Configure release identity

Add `release-please-config.json` and `.release-please-manifest.json`. Heavy
workflows must consume Release Please's tag/SHA outputs or prove that a manual
retry names an existing Release Please release.

## 5. Prove the contract

- pull request with source changes runs the expected fast jobs;
- docs-only change intentionally skips leaves but reports a green strict gate;
- superseded pull-request run cancels;
- main and release runs never cancel;
- no ARM or QEMU term appears in executable release/install metadata;
- publication environments cannot be reached from unreviewed code.
