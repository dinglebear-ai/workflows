#!/usr/bin/env bash
set -euo pipefail

repo="dinglebear-ai/workflows"
workflow_sha="${WORKFLOWS_SHA:-}"

for command in curl git mktemp tar; do
  command -v "$command" >/dev/null 2>&1 || {
    printf 'error: %s is required\n' "$command" >&2
    exit 1
  }
done

if [[ -z "$workflow_sha" ]]; then
  workflow_sha="$(git ls-remote "https://github.com/${repo}.git" refs/heads/main | cut -f1)"
fi
if [[ ! "$workflow_sha" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'error: could not resolve a full workflows commit SHA\n' >&2
  exit 1
fi

temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
archive="$temporary/workflows.tar.gz"
curl --fail --location --silent --show-error --retry 3 \
  "https://github.com/${repo}/archive/${workflow_sha}.tar.gz" \
  --output "$archive"
tar -xzf "$archive" -C "$temporary"

export WORKFLOWS_SHA="$workflow_sha"
exec "$temporary/workflows-${workflow_sha}/scripts/bootstrap.sh" "$@"
