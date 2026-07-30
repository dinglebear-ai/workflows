#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: bootstrap.sh [--force] [--ci-only] [--dry-run] <rust|python|node|pnpm|bun> <repository-path>

Options:
  --force    Replace files managed by this bootstrap kit.
  --ci-only  Install only .github workflows and Actions configuration.
  --dry-run  Print planned writes without changing the target.
USAGE
}

force=0
ci_only=0
dry_run=0
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --force) force=1 ;;
    --ci-only) ci_only=1 ;;
    --dry-run) dry_run=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'unknown option: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
  shift
done

if [[ "$#" -ne 2 ]]; then
  usage
  exit 2
fi

profile="$1"
target_repo="$(realpath "$2")"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workflow_repo="$(dirname "$script_dir")"
starter="$workflow_repo/starters/$profile.yml"
profile_dir="$workflow_repo/bootstrap/profiles/$profile"
common_dir="$workflow_repo/bootstrap/common"

if [[ ! -f "$starter" || ! -d "$profile_dir" ]]; then
  printf 'unknown profile: %s\n' "$profile" >&2
  usage
  exit 2
fi

if [[ ! -d "$target_repo/.git" ]]; then
  printf 'target is not a Git repository: %s\n' "$target_repo" >&2
  exit 2
fi

workflow_sha="${WORKFLOWS_SHA:-}"
if [[ -z "$workflow_sha" ]]; then
  workflow_sha="$(git -C "$workflow_repo" rev-parse HEAD 2>/dev/null || true)"
fi
if [[ ! "$workflow_sha" =~ ^[0-9a-f]{40}$ ]]; then
  workflow_sha="$(git ls-remote https://github.com/dinglebear-ai/workflows.git refs/heads/main 2>/dev/null | cut -f1)"
fi
if [[ ! "$workflow_sha" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'could not resolve a 40-character workflows commit SHA\n' >&2
  printf 'set WORKFLOWS_SHA explicitly and retry\n' >&2
  exit 1
fi

repo_name="$(basename "$target_repo")"
year="$(date +%Y)"
case "$profile" in
  rust) release_type="rust" ;;
  python) release_type="python" ;;
  node|pnpm|bun) release_type="node" ;;
esac
written=0
skipped=0

render_file() {
  local source="$1" destination="$2"
  if [[ -e "$destination" && "$force" -ne 1 ]]; then
    printf 'skip existing %s\n' "${destination#"$target_repo/"}"
    skipped=$((skipped + 1))
    return
  fi
  printf '%s %s\n' "$([[ -e "$destination" ]] && printf replace || printf create)" \
    "${destination#"$target_repo/"}"
  if [[ "$dry_run" -eq 1 ]]; then
    written=$((written + 1))
    return
  fi
  mkdir -p "$(dirname "$destination")"
  temporary="$(mktemp)"
  sed \
    -e "s/__WORKFLOWS_SHA__/$workflow_sha/g" \
    -e "s/__REPOSITORY_NAME__/$repo_name/g" \
    -e "s/__YEAR__/$year/g" \
    -e "s/__RELEASE_TYPE__/$release_type/g" \
    "$source" >"$temporary"
  chmod --reference="$source" "$temporary"
  mv "$temporary" "$destination"
  written=$((written + 1))
}

install_tree() {
  local source_root="$1"
  while IFS= read -r -d '' source; do
    relative="${source#"$source_root/"}"
    render_file "$source" "$target_repo/$relative"
  done < <(find "$source_root" -type f -print0 | sort -z)
}

install_memory_link() {
  local destination="$1"
  if [[ -e "$destination" || -L "$destination" ]]; then
    if [[ "$force" -ne 1 ]]; then
      printf 'skip existing %s\n' "${destination#"$target_repo/"}"
      skipped=$((skipped + 1))
      return
    fi
  fi
  printf '%s %s\n' "$([[ "$dry_run" -eq 1 ]] && printf plan || printf create)" \
    "${destination#"$target_repo/"}"
  if [[ "$dry_run" -ne 1 ]]; then
    ln -sfn CLAUDE.md "$destination"
  fi
  written=$((written + 1))
}

render_file "$starter" "$target_repo/.github/workflows/ci.yml"
render_file "$workflow_repo/bootstrap/workflows/policy.yml" \
  "$target_repo/.github/workflows/policy.yml"
render_file "$workflow_repo/bootstrap/workflows/release-please.yml" \
  "$target_repo/.github/workflows/release-please.yml"
render_file "$workflow_repo/.github/actionlint.yaml" \
  "$target_repo/.github/actionlint.yaml"
render_file "$profile_dir/.github/dependabot.yml" \
  "$target_repo/.github/dependabot.yml"

if [[ "$ci_only" -ne 1 ]]; then
  install_tree "$common_dir"
  install_tree "$profile_dir/root"
  install_memory_link "$target_repo/AGENTS.md"
  install_memory_link "$target_repo/GEMINI.md"
fi

printf 'bootstrap complete: profile=%s workflow_sha=%s writes=%d skipped=%d\n' \
  "$profile" "$workflow_sha" "$written" "$skipped"
