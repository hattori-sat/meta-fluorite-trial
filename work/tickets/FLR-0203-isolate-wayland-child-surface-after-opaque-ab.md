# FLR-0203 — isolate Wayland child-surface composition after opaque A/B

- Status: Done
- Priority: High
- Owner: Mac source/runtime analysis + Mini authoritative build + QEMU runtime roles
- Created: 2026-09-19
- Predecessor: [FLR-0202](FLR-0202-test-opaque-native-swapchain-composition.md)
- Working log: `work/logs/2026-09-19-flr0203.md`

## Work unit

Identify whether the remaining missing QMP 3D pixels are caused by the
Wayland child surface's position, stacking, commit, damage, or parent-frame
composition, after both transparent and opaque native swapchain A/Bs produced
the same result.

## Facts

- The 2D HUD and `Scenes` button are visible in the same QMP frame.
- Native driver readback is non-zero in the candidate ROI.
- Transparent and opaque swapchain configurations produce the same QMP frame
  and the same all-black central 3D ROI.
- The current runtime reaches Wayland surface creation, Vulkan present result
  0, readback completion, and native ROI reporting.
- The QMP result is stable across three captured frames.

## Hypotheses

1. H1: the native child surface is committed or stacked with incorrect
   geometry/parent relationship, so driver pixels do not appear in the parent
   frame. Prediction: a source/runtime comparison will find a changed
   `wl_subsurface_set_position`, `place_above`, commit, damage, or parent
   surface operation relative to the known-good history.
2. H2: the child surface metadata is correct and the missing boundary is in
   compositor import or buffer-release behavior. Prediction: current source
   operations match the known-good path; the next probe must observe protocol
   events or compositor logs rather than modify rendering.

## Success criteria

- [x] Compare current source and active patch history for child-surface
  position, stacking, commit, damage, scale, and parent relationship.
- [x] Record at least two plausible explanations and the first discriminating
  runtime observation before editing source.
- [x] If a source change is justified, make one minimal change through the
  fixed Mac Podman Devtool, official patch generation, canonical registration,
  bundle, Mini gates, and one QMP run.
- [x] Preserve the QMP-only evidence and cleanly stop app/QEMU; no 3D success
  claim without non-zero QMP ROI.

## Plan / Do / Check / Act

### Plan

1. Inspect the current effective `view_target.cc` and relevant historical
   patches, especially the position/stack/commit/damage paths.
2. Compare the current runtime markers against the known-good FLR-0042 and
   FLR-0199 evidence without changing source.
3. Choose the smallest protocol-level discriminator; only then create a
   Devtool patch and repeat the authoritative build/QMP loop.

### Do

Static comparison found that the current effective source creates the child
surface, places it above `parent_surface_`, sets `(left_, top_)`, and selects
desynchronized subsurface mode, but contains no `wl_surface_commit` call in
`view_target.cc`; the only current occurrence is a comment saying the commit
happens elsewhere. The active recipe does not register the historical 0240
flush patch. Historical 0121/0240 evidence shows an explicit commit/flush
after the renderer path.

This makes H1 the leading hypothesis: driver pixels exist, but the native
child surface may not be explicitly attached/flushed into the parent frame.
The smallest source probe was added in the fixed Mac Devtool source and
committed through the guarded source workflow as
`53b30058270a397abd6245cae96ad7aa383f4bd1`. It is enabled only by
`FLUORITE_NATIVE_WAYLAND_COMMIT=1` and adds `wl_surface_commit(surface_)`
followed by `wl_display_flush(display_)` after `renderer->endFrame()`.

Official Devtool output was copied unchanged to
`0265-diag-gate-wayland-child-surface-commit-devtool.patch`, SHA-256
`65d8568ed1332c59ce007ba32d9c9cd287a6532e838ea3ef357dc3105bc72164`.
The patch is registered once and the baseline lock was refreshed. The fixed
Podman machine was reused; no replacement machine or source workspace was
created.

### Check

Static source/patch comparison passed. Mini `do_patch`, `do_compile`, image
build, one QEMU run, paired QMP evidence, and clean teardown all passed. The
commit/flush probe did not change the result: native driver ROI remained
non-zero, while QMP central `[300,250,620,400]` and wide
`[180,180,920,560]` ROIs remained uniformly black. The commit probe logged
`wl_display_flush result=8`.

### Act

The commit/flush operation is not sufficient. Keep the generated official
patch as provenance and continue with FLR-0204, which owns the independent
stacking-direction A/B.

## UNKNOWN

- Exact current parent/child Wayland protocol state at the final QMP capture.
- Whether the compositor imported the native buffer and then discarded it, or
  never attached it to the parent frame.
