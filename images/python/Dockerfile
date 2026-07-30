# syntax=docker/dockerfile:1.18
FROM python:3.14.6-slim-bookworm@sha256:f70215e5dbe2a47dee6d23f9c6d358bf3c148f59cce2fd165b61118e9d80f2bb

ARG PIP_AUDIT_VERSION=2.9.0
ARG PYTEST_VERSION=9.1.1
ARG RUFF_VERSION=0.16.0
ARG TY_VERSION=0.0.65
ARG UV_VERSION=0.11.31

LABEL org.opencontainers.image.source="https://github.com/dinglebear-ai/workflows" \
      org.opencontainers.image.description="Pinned linux/amd64 Python CI toolchain for dinglebear-ai" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       bash \
       build-essential \
       ca-certificates \
       curl \
       git \
       jq \
       libffi-dev \
       libssl-dev \
       pkg-config \
       shellcheck \
       unzip \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
      "pip-audit==${PIP_AUDIT_VERSION}" \
      "pytest==${PYTEST_VERSION}" \
      "ruff==${RUFF_VERSION}" \
      "ty==${TY_VERSION}" \
      "uv==${UV_VERSION}"

COPY images/smoke.sh /usr/local/bin/ci-image-smoke
RUN chmod 0755 /usr/local/bin/ci-image-smoke \
    && ci-image-smoke python

WORKDIR /workspace
CMD ["bash"]
