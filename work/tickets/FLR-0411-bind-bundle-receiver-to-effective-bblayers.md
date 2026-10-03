# FLR-0411 — bind the Mini bundle receiver to effective BBLAYERS

- Status: Inbox
- Priority: Medium
- Created: 2026-10-03
- Predecessor: [FLR-0410](FLR-0410-synchronize-event-callback-map.md)
- Scope: Clarify and test the existing Mini bundle receiver role; do not change
  the current FLR-0410 product source or build configuration.

## Problem

The Mini has a fixed bundle inbox, a staging repository, and a separate
authoritative layer checkout selected by the active QEMU build's
`bblayers.conf`. The handoff helper requires `BUILD_RECEIVER/layers/
meta-fluorite-trial` to be the layer in effective `BBLAYERS`. If the staging
repository is supplied as `BUILD_RECEIVER` while the build selects another
checkout, the helper must stop; updating staging alone would not affect the
image being built.

## Facts at discovery

- FLR-0405 and FLR-0408 record an active Mini build layer at the then-current
  revision separately from the clean staging receiver.
- The 2026-10-03 read-only Mini check found the active build input clean at
  `6e9878ba7993`, while the staging repository was clean at `969d93c331be`.
  Their Git common directories and filesystem paths are distinct.
- The current qemux86-64 `BBLAYERS` selects the active build input, not the
  staging repository. No BitBake, QEMU, or `flutter-auto` owner was running;
  the build filesystem had 61.6 GiB free.
- The fixed inbox remains the documented role path. No Mini-side state was
  changed during this discovery.
- The current handoff helper fails closed unless the supplied
  `BUILD_RECEIVER` is the layer selected by the fixed build configuration.

## Hypotheses / options

1. Point `BUILD_RECEIVER` at the effective build-owned checkout and keep the
   inbox as the transfer point. This updates the actual input without changing
   `BBLAYERS`, creating a clone, or touching the separate staging repository.
2. Change `BBLAYERS` to select the staging repository. This mutates the build
   configuration and risks changing the established build input.

Prefer option 1 if the build-owned role is confirmed. Do not infer ownership
from cleanliness alone; resolve it from the environment contract and prior
handoff records. If the role is not confirmed, remain read-only.

## Success criteria

- [ ] `BUILD_BUNDLE_INBOX`, `BUILD_RECEIVER`, `BUILD_DIR`, and `BUILD_TMPDIR`
  are unambiguously documented as separate fixed roles without personal host
  details or absolute user paths.
- [ ] A read-only resolver proves that the receiver's layer path is the exact
  effective `BBLAYERS` entry and that effective `TOPDIR`/`TMPDIR` match the
  configured build roles before any receiver update.
- [ ] A mismatch test proves the handoff stops before modifying either
  checkout; a matching test proves only the configured build-owned receiver
  advances to the requested bundle tip.
- [ ] The fixed inbox remains unchanged; the separate staging repository,
  `BBLAYERS`, build directory, caches, and `TMPDIR` are not restructured.
- [ ] The full existing handoff helper tests and privacy checks pass; local
  commit only, no push.

## Out of scope

- Changing Yocto source revisions or build configuration.
- Creating another receiver, build tree, container, or temporary directory.
- Any rendering, Flutter, Filament, QEMU, or product-code change.

## Plan / Do / Check / Act

### Plan

Inspect the current role documentation and receiver/build checks, then add a
small, fail-closed mapping test and clarify the role contract. Preserve the
active build input; do not touch staging state.

### Do

- Not started. This ticket remains Inbox while FLR-0410 owns the build/runtime
  iteration.

### Check

- Discovery only; the handoff mapping is not yet productized or regression
  tested.

### Act

- Start after FLR-0410's current candidate handoff is complete or no longer
  needs the build receiver.
