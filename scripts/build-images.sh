#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image_prefix="${IMAGE_PREFIX:-workflows-ci}"
profiles=(rust python typescript)

for profile in "${profiles[@]}"; do
  docker buildx build \
    --load \
    --platform linux/amd64 \
    --file "$repo_root/images/$profile/Dockerfile" \
    --tag "$image_prefix-$profile:local" \
    "$repo_root"
done
