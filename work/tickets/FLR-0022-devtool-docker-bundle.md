# FLR-0022 — Mac devtool Docker and Git bundle synchronization

- Status: Waiting
- Priority: High
- Owner: primary role + build-host role
- Depends on: FLR-0019, FLR-0020
- External publication: none

## Problem

Mac-side patch preparation and mini-PC-side authoritative BitBake builds need a reproducible handoff. A dirty worktree, moving branch, or unverified artifact can make the two environments produce different results.

## Decision

- Mac Docker uses Ubuntu 22.04 and only runs Devtool plus recipe-scoped BitBake tasks.
- The mini PC remains the authoritative full-build environment.
- A bundle is created only from a clean feature branch with an explicit base and tip commit.
- The receiver verifies `git bundle verify`, tip ref, SHA-256, manifest identity, and checked-out revision before any build.
- SSH/SCP connection details remain in Git-ignored local role configuration.

## Success criteria

- [x] Dockerfile builds as `fluorite-yocto-devtool:22.04`.
- [x] Mac wrapper rejects image recipes and destructive clean tasks.
- [ ] Devtool-generated patch passes clean-source `git apply --check`.
- [x] Bundle creation refuses staged, unstaged, or untracked work.
- [x] Bundle manifest records base ref, tip ref, commits, file name, and SHA-256.
- [x] Receiver verifies the bundle without changing the canonical checkout.
- [ ] A clean mini-PC worktree is materialized at the verified receiver ref before
  an authoritative BitBake build; the existing dirty checkout remains untouched.

## Files

- `tools/yocto-devtool/Dockerfile`
- `tools/yocto-devtool/entrypoint.sh`
- `tools/yocto-devtool/run-recipe-task.sh`
- `tools/yocto-devtool/README.md`
- `scripts/create-fluorite-bundle.sh`
- `scripts/verify-fluorite-bundle.sh`

## Verification

```bash
bash -n scripts/create-fluorite-bundle.sh scripts/verify-fluorite-bundle.sh \
  tools/yocto-devtool/entrypoint.sh tools/yocto-devtool/run-recipe-task.sh
docker build --tag fluorite-yocto-devtool:22.04 tools/yocto-devtool
```

The Docker build is a tool-image build, not an AGL image build. Recipe task execution requires the pinned AGL source/build mounts and is performed only after the canonical source identity is recorded.

## Unknowns

- The mini PC SSH role alias and remote repository path are not configured in this Mac clone.
- The exact server-side artifact inbox is not configured.
- The existing FLR-0019 scratch changes are not committed and must not be silently included in this ticket's bundle.

## Current verification state

- The Ubuntu 22.04 tool image and fail-closed recipe-task wrapper are verified.
- The deterministic FLR-0023 fixture patch applies to a clean pinned source
  worktree, but it was generated as a diagnostic source diff because the
  mounted Mac environment has no usable BitBake/Devtool source graph yet.
- Bundle r7 is locally verified and is imported on the mini PC as a separate
  receiver ref at the exact tip commit. The dirty canonical checkout was not
  switched.
- The remaining gate is a clean receiver worktree plus a completed
  recipe-scoped Devtool/BitBake task in the configured AGL layer graph.
