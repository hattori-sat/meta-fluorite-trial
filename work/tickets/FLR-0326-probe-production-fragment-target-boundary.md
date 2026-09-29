# FLR-0326 — probe production fragment output versus native target

- Status: Done
- Priority: High
- Owner: Filament production material/fragment output and native target roles
- Created: 2026-09-25
- Predecessor: [FLR-0325](FLR-0325-trace-post-override-material-output.md)
- Related waiting evidence: [FLR-0307](FLR-0307-probe-production-fragment-output-target.md)
- Working log: `work/logs/2026-09-25-flr0326.md`

## Objective

Determine whether a production Sequoia primitive with a valid bound
`PaintColor` MaterialInstance can emit a controlled visible fragment, or
whether the fragment is lost at the native target handoff. Use one opt-in
diagnostic control and preserve camera, Light, Scene ownership, Wayland
composition, and the normal 2D HUD.

## Success criteria

- The source change is made in the persistent Mac Devtool workspace, committed
  there, and converted by the official `update-recipe` flow.
- The canonical layer contains only the generated patch and required recipe
  registration; Mini receives it by Git bundle.
- Mini `do_patch`, component compile, full image build, and one QMP-first run
  pass with exact image identity recorded.
- A full QMP frame is saved before ROI analysis. The native ROI and HUD ROI are
  measured, and the bounded runtime markers are recorded.
- The first divergence is classified as fragment/material output or target
  handoff. If the native ROI becomes nonzero, preserve that frame as the new
  baseline and stop before unrelated changes.

## Facts

- FLR-0325 proves `PaintColor` reads back `(1,0,1,1)` after the setter and the
  same instance is bound to the submitted renderable.
- FLR-0325 proves begin-frame, Scene add, draw-submit, and present markers,
  while native QMP pixels remain black and the 2D HUD remains visible.
- The supplied colored Sequoia image is static GLB texture evidence, not a
  QMP runtime frame.
- The Mac `recipe-task flutter-auto do_patch` initially stopped in existing
  `0220` before reaching this ticket's patch. The Mac external
  `meta-flutter` recipe defaulted to `bc85ac...` / `451aa...`, while the
  authoritative Mini effective environment records
  `dd6d9224...` / `2163242...`. The project layer now pins the Mini pair so
  both patch-generation and authoritative build contexts resolve the same
  source pair.

## Hypotheses

| hypothesis | prediction | falsifier |
| --- | --- | --- |
| production fragment/material evaluation emits no visible color | a one-primitive opt-in emissive or unlit diagnostic remains native-black while draw/present stay positive | native ROI becomes chromatic |
| fragment output exists but native target handoff loses it | a controlled constant-color output produces native chromatic pixels in an intermediate/readback trace but QMP remains black | both intermediate and QMP output remain black |
| the diagnostic changes the draw path itself | draw/material markers or frame timing change materially and the control is not a clean discriminator | markers remain stable |

## Plan / PDCA

### Plan

Compare the two boundaries with the smallest available existing Filament
parameter/output seam. Reuse the fixed Podman Devtool container, the same Mini
build directory, one bundle handoff, one QEMU, one full-frame QMP capture, and
bounded log slices. Do not add another volume, temporary worktree, camera
change, Light change, or compositor change.

### Do

- Generated `0326` through the persistent Mac Devtool source edit → source
  commit → official `update-recipe` flow. The generated patch is registered in
  the canonical layer but its build gate is pending the source-pair alignment
  above.

### Check

- FLR-0326 experiment 1: the existing emissive control did not fire because
  `PaintColor` exposes `emissiveIndex`, not an `emissiveFactor` parameter. QMP
  SHA `a433da50516d7d320efaf1365a3f806b78bb4ed7b658cfddee130e070e8b8ee9`
  had HUD chroma `2845` and native ROI `0/144000`.
- FLR-0326 experiment 2: native swapchain readback requests were issued, but
  no result/callback marker appeared in the bounded run. QMP SHA
  `2a153cc4fa0aac2dec6d3aa33c1392c057631b2ff55c4eef97d952f79901142e`
  again had HUD chroma `2845` and native ROI `0/144000`.
- Same-run UNLIT+native-readback control applied the fixed replacement and
  continued draw/present, but again produced only repeated readback requests;
  no result/callback marker appeared. QMP SHA
  `7072643e016550022d208c29a02fb2a5d5945d196f386f37d1079cd7a52c4a58`
  had native ROI `0/144000` and HUD chroma `2845`; QMP cleanup passed.
- Mac do_patch failure at 0220 was classified as a source-pair mismatch before
  0326, not as a 0326 patch-application failure. The next check is the same
  Mac do_patch gate after the canonical source pin.
- The first missing boundary is now narrowed to native readback/target
  completion after a valid fixed-color production material replacement and
  draw/present sequence. Lighting and camera remain unmodified.

### Act

If a controlled material output produces native pixels, promote that exact
boundary to the next minimal production fix ticket. If it does not, move the
investigation to native target attachment/readback without changing the
production model again.

## Result — 2026-09-25 driver/readback boundary observation

- The first start attempt was rejected by the Mini harness before QEMU start
  because that receiver version does not accept `--memory-mb`. No target was
  changed. The corrected invocation reused the same fixed harness and image.
- The corrected run used the existing rootfs
  `2da3de48ba07af0adbcf6c7b76364b58ba38e51bcd4ef2cdce522d69b10a6263`, one
  QEMU, one recorded socket, and the existing evidence directory.
- One `flutter-auto` process was present with the requested UNLIT/readback
  environment. The controlled replacement marker, Scene add, true
  `beginFrame`, draw submit, and repeated readback requests were observed.
- The selected driver log contains
  `FLR0026_VK_READBACK_DRIVER_ENTER`,
  `FLR0026_VK_READBACK_DRIVER_COMMANDS_RECORDED`, and
  `FLR0026_VK_READBACK_DRIVER_EXIT`.
- Neither the application log nor the boot journal contained
  `FLUORITE_NATIVE_SWAPCHAIN_READBACK_DRIVER_RESULT`,
  `FLUORITE_NATIVE_SWAPCHAIN_READBACK_DRIVER_ROI`, or a native readback
  callback marker in the bounded observation.
- The QMP-only full framebuffer is
  `/mnt/yocto/evidence/flr0326-0001/qmp-0326-unlit-journal-full.ppm`, SHA-256
  `5fb543c0b4938a70f73589828e228632ddec29e73407e2b9138b24de80b25436`.
  Native ROI `(440,220,400,360)` is uniform black (`0/144000`); HUD ROI has
  `2845` chromatic pixels.
- QMP teardown was accepted and cleanup reported zero residual targets and
  zero QMP sockets.

### Boundary decision

The controlled production primitive reaches the Filament readback driver
entry and command-recording boundary, but the completion payload/callback
boundary is not observed. This is stronger than the earlier “draw/present
only” result and moves the next investigation to the readback completion
queue/fence/callback path. It does not prove whether the fragment itself is
nonzero before completion, so no production Light, camera, material, or
compositor change is justified here.

The next independent unit is [FLR-0328](FLR-0328-trace-readback-completion-boundary.md).

## UNKNOWN

- Whether the valid production MaterialInstance reaches a fragment invocation.
- Whether a nonzero fragment reaches the native target attachment used by the
  QMP-visible surface.
