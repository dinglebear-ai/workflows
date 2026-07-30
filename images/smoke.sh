#!/usr/bin/env bash
set -euo pipefail

profile="${1:?usage: ci-image-smoke <rust|python|typescript>}"

if [[ "$(uname -m)" != "x86_64" ]]; then
  printf 'error: CI images support x86_64 only; got %s\n' "$(uname -m)" >&2
  exit 1
fi

for command in bash curl git jq shellcheck; do
  command -v "$command" >/dev/null
done

case "$profile" in
  rust)
    rustc --version
    cargo --version
    cargo audit --version
    cargo deny --version
    cargo nextest --version
    kache --version
    rustfmt --version
    cargo clippy --version
    ;;
  python)
    python --version
    pip --version
    pip-audit --version
    pytest --version
    ruff --version
    ty --version
    uv --version
    ;;
  typescript)
    node --version
    npm --version
    pnpm --version
    bun --version
    ;;
  *)
    printf 'error: unknown CI image profile: %s\n' "$profile" >&2
    exit 2
    ;;
esac
