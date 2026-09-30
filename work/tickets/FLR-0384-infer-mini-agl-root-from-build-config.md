# FLR-0384 — infer the Mini AGL root from the active build configuration

- Status: Inbox
- Priority: Medium
- Discovered in: [FLR-0383](FLR-0383-sequoia-known-material.md)
- Owner: Mini recipe-gate helper / regression-test roles

## Problem

`scripts/run-mini-recipe-patch-gate.sh` stops with
`BUILD_AGL_ROOT is required when BUILD_DIR has no build-* suffix` for the
existing QEMU build directory, even though its persisted `conf/templateconf.cfg`
uniquely identifies the existing AGL `external/poky/oe-init-build-env` tree.
This makes a routine recipe gate depend on a manually resolved private path.

FLR-0383 safely recovered by querying the existing build's `TEMPLATECONF`,
resolving exactly one matching AGL root, and rerunning the same patch gate.
`do_patch` then passed. The first failed invocation did not run BitBake or clean
the recipe workdir; it only created the ticket-scoped evidence directory.

## Objective

Make the recipe-patch gate deterministically resolve the current AGL root from
the existing build configuration when `BUILD_AGL_ROOT` is omitted. Reuse the
same fail-closed selection contract already established by
`scripts/reuse-mini-build-receiver.sh`; do not infer from directory naming or
select a standalone Poky tree whose template does not match.

## Success criteria

1. A regression test covers a fixed build directory that does not end in
   `build-*` and an AGL source tree located separately from the build.
2. Exactly one candidate whose template matches the build's persisted
   `TEMPLATECONF` is selected.
3. Missing and ambiguous matches fail before the recipe workdir or receiver is
   mutated, with a concise stage-specific error.
4. Existing explicit `BUILD_AGL_ROOT` behavior remains valid and the focused
   helper tests pass.

## Scope

Only the Mini recipe-patch-gate helper, its focused regression tests, and this
ticket's evidence. Do not rerun FLR-0383 image/runtime work or create another
receiver, build directory, TMPDIR, or cache tree to resolve this helper issue.

## UNKNOWN

- Whether the source-root selection contract should be extracted into one
  shared helper or copied minimally from `reuse-mini-build-receiver.sh` should
  be decided during implementation after inspecting existing tests and call
  sites.
