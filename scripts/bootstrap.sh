#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 [--force] <rust|python|node|pnpm|bun> <repository-path>" >&2
}

force=0
if [[ "${1:-}" == "--force" ]]; then
  force=1
  shift
fi

if [[ "$#" -ne 2 ]]; then
  usage
  exit 2
fi

profile="$1"
target_repo="$(realpath "$2")"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workflow_repo="$(dirname "$script_dir")"
starter="$workflow_repo/starters/$profile.yml"
destination="$target_repo/.github/workflows/ci.yml"

if [[ ! -f "$starter" ]]; then
  echo "unknown profile: $profile" >&2
  usage
  exit 2
fi

if [[ ! -d "$target_repo/.git" ]]; then
  echo "target is not a Git repository: $target_repo" >&2
  exit 2
fi

if [[ -e "$destination" && "$force" -ne 1 ]]; then
  echo "refusing to overwrite $destination; pass --force to replace it" >&2
  exit 1
fi

workflow_sha="${WORKFLOWS_SHA:-}"
if [[ -z "$workflow_sha" ]]; then
  workflow_sha="$(git -C "$workflow_repo" rev-parse HEAD 2>/dev/null || true)"
fi
if [[ ! "$workflow_sha" =~ ^[0-9a-f]{40}$ ]]; then
  workflow_sha="$(gh api repos/dinglebear-ai/workflows/commits/main --jq .sha 2>/dev/null || true)"
fi
if [[ ! "$workflow_sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "could not resolve a 40-character workflows commit SHA" >&2
  echo "set WORKFLOWS_SHA explicitly and retry" >&2
  exit 1
fi

mkdir -p "$(dirname "$destination")"
temporary="$(mktemp)"
trap 'rm -f "$temporary"' EXIT
sed "s/__WORKFLOWS_SHA__/$workflow_sha/g" "$starter" >"$temporary"
mv "$temporary" "$destination"
trap - EXIT

echo "created $destination using $profile profile at $workflow_sha"
