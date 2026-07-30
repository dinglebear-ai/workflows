# syntax=docker/dockerfile:1.18
FROM rust:1.97.1-bookworm@sha256:389c1ae98c20fbcadca68a685482749267cec3c90893ae4671c5a37cc894c416

ARG CARGO_AUDIT_VERSION=0.22.2
ARG CARGO_DENY_VERSION=0.20.2
ARG CARGO_NEXTEST_VERSION=0.9.140
ARG KACHE_VERSION=0.12.0

LABEL org.opencontainers.image.source="https://github.com/dinglebear-ai/workflows" \
      org.opencontainers.image.description="Pinned linux/amd64 Rust CI toolchain for dinglebear-ai" \
      org.opencontainers.image.licenses="MIT"

ENV CARGO_HOME=/usr/local/cargo \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_TERM_COLOR=always \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       bash \
       build-essential \
       ca-certificates \
       clang \
       cmake \
       curl \
       git \
       jq \
       libssl-dev \
       mold \
       pkg-config \
       protobuf-compiler \
       shellcheck \
       unzip \
       xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN rustup component add clippy rustfmt \
    && cargo install --locked cargo-audit --version "${CARGO_AUDIT_VERSION}" \
    && cargo install --locked cargo-deny --version "${CARGO_DENY_VERSION}" \
    && cargo install --locked cargo-nextest --version "${CARGO_NEXTEST_VERSION}" \
    && cargo install --locked kache --version "${KACHE_VERSION}" \
    && rm -rf "${CARGO_HOME}/registry" "${CARGO_HOME}/git"

COPY images/smoke.sh /usr/local/bin/ci-image-smoke
RUN chmod 0755 /usr/local/bin/ci-image-smoke \
    && ci-image-smoke rust

WORKDIR /workspace
CMD ["bash"]
