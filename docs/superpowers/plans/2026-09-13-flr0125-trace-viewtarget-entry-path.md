# Trace the Example Demo ViewTarget entry path

## Goal

Find the first missing runtime boundary between Example Demo PlatformView
registration and native `ViewTarget` initialization, then restore only that
boundary if source evidence requires it.

## Constraints

- Keep FLR-0125 as the sole active ticket.
- Reuse the fixed Podman Devtool container/source workspace, Mini receiver,
  build/TMPDIR, QEMU harness, and evidence root.
- Do not patch geometry, present, or Dart production scene until ViewTarget
  entry is proven.
- Use neutral `FLUORITE_*` markers for new diagnostics.

## Steps

1. Map the static chain from `RegisterWithRegistrar` through ECS message
   routing, `ViewTargetSystem`, `InitializeFilamentInternals`, and `setupView`.
2. Compare that chain with FLR-0124 runtime evidence and identify the first
   missing marker boundary.
3. If needed, edit only the persistent Mac Devtool source, commit the source
   change, and generate the patch with official Devtool.
4. Register the unchanged generated patch in the canonical layer, run Mac
   `do_patch`, commit locally, bundle, and update the fixed Mini receiver.
5. Run Mini `do_patch`, `do_compile`, and full image gates.
6. Run one QMP-only QEMU control with the same native fixture environment and
   classify the marker boundary, then quit through QMP.

## Decision gates

- If source call sites show no defect, add bounded observation only or split a
  source-absent issue; do not infer a render failure.
- If ViewTarget setup is reached, stop this ticket and create a new pixel/present
  ticket.
- If setup remains absent, keep geometry/present out of scope and record the
  first missing boundary as FAIL or UNKNOWN with evidence.
