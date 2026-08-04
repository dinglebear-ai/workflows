---
title: "ADR 0001: Use MinIO as the single shared Kache remote"
status: accepted
date: 2026-08-04
owners:
  - ci-runner-farm
  - workflows
---

# ADR 0001: Use MinIO as the single shared Kache remote

## Context

The private Rust fleet previously combined isolated local Kache stores with a
shared NFS filesystem remote. During the MinIO migration, the NFS source was
frozen at 176,205 files and approximately 257 GiB. The migration copied the
content into the `rust` prefix of the `kache` bucket.

The final comparison found 32 newer NFS objects. Every object was mutable data
under `_manifests`, not an immutable compile artifact. Those objects were
archived under the migration archive prefix, and the archive comparison
returned zero bytes of difference before the NFS source was retired.

Keeping both remotes after that point would preserve two authorities, require a
filesystem reaper, and leave cache correctness dependent on mount availability.

## Decision

The fleet uses one shared Kache remote: `s3://kache/rust` on MinIO.

1. Each Tootie runner owns an isolated 80 GiB local L1 store.
2. Dookie owns an isolated 100 GiB local L1 store.
3. Local SQLite-backed stores are never shared between runners or hosts.
4. The NFS cache is not mounted, mirrored, dual-written, or used as a fallback.
5. Private runners preserve the host-provided S3 configuration and credential
   profile. Environments without those credentials run local-only.
6. The fleet pins upstream Kache 0.13.0 or newer releases that preserve this
   S3 contract. One supervised daemon owns each runtime store.
7. Remote retention and capacity are infrastructure responsibilities. CI jobs
   must not recursively delete or garbage-collect the shared object prefix.

## Consequences

- Every repository observes one shared cache namespace and one remote protocol.
- A missing NFS mount can no longer silently split the fleet into cache islands.
- Runner replacement remains safe because warm local state is disposable and
  shared immutable artifacts live in MinIO.
- Hosted or uncredentialed jobs lose cross-runner reuse but retain correct local
  caching behavior.
- Cold canaries remain necessary because warm L1 stores can hide a broken shared
  remote.

## Verification

The migration evidence is retained on Tootie under
`/mnt/user/logs/kache-migration-20260803`. The retirement gate required:

- zero source-only objects;
- classification and archival of all 32 mutable manifest differences;
- a zero-byte archive diff;
- removal of the NFS source tree and Dookie mount only after those checks.
