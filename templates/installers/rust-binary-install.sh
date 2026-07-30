#!/usr/bin/env bash
set -euo pipefail

# Replace these four values when adopting the template.
repo="dinglebear-ai/__REPOSITORY_NAME__"
binary_name="__BINARY_NAME__"
env_prefix="__ENV_PREFIX__"
default_install_dir="${HOME}/.local/bin"

read_override() {
  local suffix="$1" fallback="$2"
  local variable="${env_prefix}_${suffix}"
  printf '%s' "${!variable:-$fallback}"
}

install_dir="${INSTALL_DIR:-$default_install_dir}"
version="$(read_override VERSION latest)"
release_base_url="$(read_override RELEASE_BASE_URL "")"
repo="$(read_override REPO "$repo")"

usage() {
  cat <<USAGE
Install ${binary_name} from GitHub Releases.

Environment:
  INSTALL_DIR
  ${env_prefix}_VERSION
  ${env_prefix}_REPO
  ${env_prefix}_RELEASE_BASE_URL
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

for command in curl install mktemp sha256sum tar; do
  command -v "$command" >/dev/null 2>&1 || {
    printf 'error: %s is required\n' "$command" >&2
    exit 1
  }
done

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  printf 'error: this installer supports Linux x86_64 only\n' >&2
  exit 1
fi

asset="${binary_name}-linux-x86_64.tar.gz"
if [[ -n "$release_base_url" ]]; then
  base="${release_base_url%/}/${version}"
elif [[ "$version" == "latest" ]]; then
  base="https://github.com/${repo}/releases/latest/download"
else
  base="https://github.com/${repo}/releases/download/${version}"
fi

temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
curl --fail --location --silent --show-error --retry 3 \
  "$base/$asset" --output "$temporary/$asset"
curl --fail --location --silent --show-error --retry 3 \
  "$base/$asset.sha256" --output "$temporary/$asset.sha256"

(
  cd "$temporary"
  sha256sum --check "$asset.sha256"
)

members="$(tar -tzf "$temporary/$asset")"
if [[ "$members" != "$binary_name" ]]; then
  printf 'error: archive must contain exactly %s; got:\n%s\n' \
    "$binary_name" "$members" >&2
  exit 1
fi
tar -xzf "$temporary/$asset" -C "$temporary" "$binary_name"

mkdir -p "$install_dir"
if [[ ! -w "$install_dir" ]]; then
  printf 'error: install directory is not writable: %s\n' "$install_dir" >&2
  exit 1
fi
install -m 0755 "$temporary/$binary_name" "$install_dir/$binary_name"
printf 'Installed %s to %s/%s\n' "$binary_name" "$install_dir" "$binary_name"
