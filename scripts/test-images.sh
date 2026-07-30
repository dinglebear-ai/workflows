#!/usr/bin/env bash
set -euo pipefail

image_prefix="${IMAGE_PREFIX:-workflows-ci}"
profiles=(rust python typescript)

for profile in "${profiles[@]}"; do
  image="$image_prefix-$profile:local"
  architecture="$(docker image inspect "$image" --format '{{.Architecture}}')"
  if [[ "$architecture" != "amd64" ]]; then
    printf 'error: %s has architecture %s\n' "$image" "$architecture" >&2
    exit 1
  fi
  docker run --rm --entrypoint ci-image-smoke "$image" "$profile"
done
