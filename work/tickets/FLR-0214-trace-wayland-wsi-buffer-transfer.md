# FLR-0214 — trace Wayland WSI buffer transfer after positive native readback

- Status: Done
- Priority: High
- Owner: Vulkan WSI / Mesa Wayland buffer-transfer role
- Created: 2026-09-20
- Predecessor: [FLR-0211](FLR-0211-reconcile-shm-geometry-and-native-wsi.md)

## Work unit

Identify the first owner after Filament's native swapchain readback and before
the QMP framebuffer. Do not create a source patch until the buffer-transfer or
compositor-import boundary is directly evidenced.

## Success criteria

- Reuse the fixed Podman/Devtool source state, Mini receiver/build/TMPDIR, and
  QEMU/QMP harness; create no new container, named volume, source tree, or
  TMPDIR.
- Preserve one authoritative QMP frame with 2D HUD and the native candidate ROI
  classification, plus bounded runtime/protocol evidence.
- Determine whether RGB is lost during Vulkan WSI export, Wayland `wl_shm`
  buffer population, or compositor import.
- Keep failed attempts, hashes, and teardown results in the working log.
- Only after the owner is known, create the smallest official Devtool patch in
  a later task if a source change is justified.

## Facts

- The corrected SHM geometry is visible at `[460,260,360,280]` in the
  predecessor control image.
- The native Filament direct readback is RGB-positive in ROI
  `[300,250,620,400]` (`nonzero_rgb=111758`), while paired QMP remains black.
- Queue idle, present-layout skipping, opaque composite alpha, readback probe
  removal, SHM-cube omission, and `clipped=VK_FALSE` did not change QMP.
- The final QMP frame still contains the 2D HUD and `Scenes` button, so this is
  not a general Flutter startup failure.
- The native-only QMP frame is retained as `evidence/FLR-0214/r/strace.ppm`;
  its SHA-256 is
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- In that frame, the native candidate ROI `[300,250,620,400]` has
  `changed_pixels=0` and `chromatic_pixels=0`, while the HUD ROI has
  `changed_pixels=2976` and `chromatic_pixels=2801`.
- The first WSI shared-memory group was transferred with `SCM_RIGHTS`; the
  first buffer is the `wl_shm` buffer attached before the native commit.
- The first WSI mapping has non-zero and chromatic RGB in both the
  `flutter-auto` process and `agl-compositor`, with identical ROI SHA and
  metrics. The retained first-five mapping report SHA-256 is
  `9362aab17d4025e918ae9bf4f3eb5269550d9fc1369362a4b5c73b79158a1baf`.
- The bounded runtime evidence log SHA-256 is
  `9c6e30be7ea60add1387944ccc16ba146efb6652f34c366a75393a8108df6825`;
  the QMP/ROI report SHA-256 is
  `484decab7fd04effbe176e8fc4ba043754e01a492bc55bce71f804f81ef9d6c0`.

## Inferences

- RGB is not lost between the native render result, the shared `wl_shm`
  mapping, and the compositor's address space. Hypothesis 1 is falsified for
  this run.
- A successful `wl_surface.attach → damage → frame → commit` and
  `vkQueuePresentKHR result=0` are not sufficient evidence that the native
  surface is selected for the final parent framebuffer.
- The first missing observable boundary is therefore after compositor import
  and before final QMP composition: surface visibility, parent/child
  relationship, stacking, role, or compositor selection remains the leading
  class of causes.

## Hypotheses

1. The compositor imports the native buffer but does not select the native
   surface for the final frame because of a parent/child role or stacking
   relationship.
2. The imported surface has a visibility, geometry, or role property that is
   different from the known-good SHM control surface.
3. A compositor-side format/metadata rule suppresses the imported surface
   despite preserving its mapped RGB bytes. This is now lower probability but
   remains UNKNOWN until compositor-side surface state is observed.

## Plan / Do / Check / Act

### Plan

1. Reproduce one run with the current rootfs and the existing QMP-only harness.
2. Collect only the bounded Wayland protocol, buffer mapping, and compositor
   evidence needed to distinguish the three hypotheses.
3. Compare the first non-zero native ROI with the final QMP ROI before editing
   Filament source.

### Do

- Reused the fixed Podman/Devtool state, the existing Mini receiver/build/TMPDIR,
  and one QEMU instance.
- Ran a control launch with the visible SHM cube, then an A/B native-only launch
  without the SHM cube.
- Ran the native-only launch under bounded `strace`; preserved the selected
  Wayland/SCM_RIGHTS lines and the first-five mapping ROI report.
- Captured the native-only QMP frame and compared its bounded ROIs.
- Stopped only the recorded guest wrapper/app PIDs, quit QEMU through QMP, and
  verified zero host residual targets.

### Check

- PASS: the native shared buffer is RGB-positive in both producer and
  compositor mappings.
- PASS: the final QMP frame is still black in the native ROI while the 2D HUD
  remains visible.
- PASS: the transfer path emitted `SCM_RIGHTS` and Wayland attach/commit
  evidence.
- PASS: teardown left `qemu-system-x86_64=0`, `runqemu=0`,
  `flutter-auto=0`, and no QMP socket.

### Act

- Close this runtime-only transfer unit and open FLR-0215 for compositor
  surface-state/visibility evidence. No source patch was created here.

## UNKNOWN

- Which compositor surface role, parent/child relationship, or visibility state
  prevents the RGB-positive native surface from appearing in QMP.
- Whether the relevant owner is in Flutter/Filament surface setup or in the
  compositor's surface-selection policy.
