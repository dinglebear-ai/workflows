# syntax=docker/dockerfile:1.18
FROM node:24.18.0-bookworm-slim@sha256:d45d78e7929b46875bbd4e29bea672d5bc48186c6c3588306521c815e78352d6

ARG BUN_VERSION=1.3.14
ARG PNPM_VERSION=11.15.1

LABEL org.opencontainers.image.source="https://github.com/dinglebear-ai/workflows" \
      org.opencontainers.image.description="Pinned linux/amd64 Node, pnpm, and Bun CI toolchain for dinglebear-ai" \
      org.opencontainers.image.licenses="MIT"

ENV BUN_INSTALL=/usr/local \
    DEBIAN_FRONTEND=noninteractive \
    NPM_CONFIG_AUDIT=false \
    NPM_CONFIG_FUND=false

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       bash \
       ca-certificates \
       curl \
       git \
       jq \
       shellcheck \
       unzip \
    && rm -rf /var/lib/apt/lists/*

RUN npm install --global \
      "bun@${BUN_VERSION}" \
      "pnpm@${PNPM_VERSION}" \
    && npm cache clean --force

COPY images/smoke.sh /usr/local/bin/ci-image-smoke
RUN chmod 0755 /usr/local/bin/ci-image-smoke \
    && ci-image-smoke typescript

WORKDIR /workspace
CMD ["bash"]
