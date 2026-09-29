# FLR-0059 — current-image native surface visibility A/B

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + target-validation + Flutter/Wayland roles
- Created: 2026-09-09
- Depends on: [FLR-0058](FLR-0058-restore-native-frame-loop.md), [FLR-0049](FLR-0049-production-model-render-boundary.md)
- Working log: `work/logs/2026-09-09-flr0059.md`

## Work unit

Using the current image and the recovered frame condition from FLR-0058,
separate native-surface visibility from shaded-resource output. Compare the
default native surface placement with the existing below-parent diagnostic
using one QEMU and QMP-only evidence. This ticket does not yet attempt a
combined 2D+3D production patch.

## Success criteria

- [x] Reuse the fixed image/build/TMPDIR and the one-provider/one-QEMU/QMP
  runtime contract.
- [x] Run default placement and `FLR0026_WAYLAND_BELOW_PARENT=1` with the
  recovered frame condition; vary only placement.
- [x] Determine whether the current image produces native 3D pixels when the
  native surface is made visible above the Flutter parent. Result: no native
  pixels in the fixed candidate region under either placement.
- [x] Record whether Flutter HUD and native 3D are mutually occluding, both
  visible, or both absent, with QMP pixels and hashes.
- [x] If a source change is justified, edit through the persistent Mac-side
  Yocto Devtool workspace, finish into `meta-fluorite-trial`, commit locally,
  bundle to the fixed Mini PC receiver, pass progressive BitBake gates, and
  repeat QMP validation. No source change was justified by this A/B.
- [ ] Keep combined 2D+3D, route/input, and any production fix as UNKNOWN
  until their own evidence gates pass.

## Out of scope

- Repeating light-count or frame/fence causality already closed in FLR-0057 and
  FLR-0058.
- Creating another container, build directory, TMPDIR, receiver, or concurrent
  QEMU.
- Treating native-above-parent 3D as proof of combined 2D+3D.
- Editing generated patch files, Mini PC build trees, or runtime `tmp`.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0058's trace Variant kept `FRAME_BEGIN started=true` after the model
  scene add when `FLR0026_TREAT_UNLINKED_FENCE_READY=1`, but its QMP central
  candidate region remained black.
- FLR-0049 previously observed native production Sequoia pixels above the
  Flutter parent and the Flutter HUD below it, while the combined result was
  not proven.
- The current image's ordinary QMP result shows the Flutter HUD and controls,
  so the Flutter parent is compositor-visible at least in that arrangement.

### Inferences

- Surface placement is the smallest discriminator between “native 3D is not
  rendered” and “native 3D is rendered but hidden by the parent.”
- A native-above result can close only the native visibility gate; it cannot
  close combined composition or route/input.

### Hypotheses

| ID | Hypothesis | Falsifiable prediction |
| --- | --- | --- |
| H1 | The Flutter parent is opaque/above the native child in the current arrangement. | Moving the native surface above the parent yields non-black Sequoia pixels and removes or covers the HUD. |
| H2 | The shaded production path is still black before composition. | Both placements remain black in the candidate region despite model/camera/frame/present markers. |
| H3 | Placement controls a full-surface participant rather than only z-order. | The below-parent case shows HUD-only and the above-parent case shows native-only, with no overlap; a combined fix needs a separate source boundary. |

## PDCA

### Plan

Reuse the trace image and fixed runtime variables from FLR-0058, including the
ready-fence diagnostic so frame scheduling is not the changing variable. Run a
default-placement control and a below-parent variant one at a time. Capture
QMP-only images and short videos, analyze `[300,80,620,360]`, correlate the
surface-placement marker with model/frame/present markers, and end QEMU through
negotiated QMP quit after both cases.

### Iteration 1 — current-image surface placement A/B (2026-09-09)

#### Facts

- The fixed image revision `d88d600` was reused with the existing build
  directory, TMPDIR, rootfs, qemuboot, kernel, one QEMU, and one QMP socket.
  Rootfs SHA-256 is
  `fa287b877a2d753e9f8b7a7fd02dd02dcaf9a414f6294f1c0a25d6302731da98`;
  kernel SHA-256 is
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- Common runtime conditions were Vulkan, sync/model-stage trace, forced render
  after skipped frame, `FLR0026_TREAT_UNLINKED_FENCE_READY=1`, Sequoia model
  match/limit 2, light limit 13, skipped skybox plus clear, and skipped
  indirect light. The only A/B variable was
  `FLR0026_WAYLAND_BELOW_PARENT=1`.
- Default surface placement logged
  `below_parent=false`; below-parent placement logged `below_parent=true`.
  Both cases reached `MODEL_STAGE_SCENE_ADD_DONE` for
  `assets/models/sequoia_ngp.glb`, `CAMERA_APPLIED`, Vulkan queue submit and
  present markers, and repeated `FRAME_BEGIN started=true` plus
  `FRAME_FENCE_WAIT_UNLINKED_READY`.
- Both QMP-only representative frames are 1280x800 and visibly contain the
  Flutter HUD, FPS, CPU/GPU/System delay, Scenes button, and bottom controls.
  Neither contains native Sequoia pixels in the candidate region
  `[300,80,620,360]`; each has `changed_pixels=0/223200` and the same region
  SHA-256
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- QMP-derived videos contain 12 frames each at 1280x800 and 4/3 fps. All
  frames within each condition are byte-identical in the captured QMP
  framebuffer. No fatal `SIGSEGV`, page-fault, or `Oops` marker occurred in
  either bounded runtime log; the material-property messages are existing
  informational messages.
- QMP teardown returned
  `qmp=PASS capabilities=negotiated quit=accepted` and
  `cleanup=PASS residual_targets=0 residual_qmp=0`. The Mini PC post-check
  found no QEMU, runqemu, flutter-auto, or QMP socket residual.

#### Inferences

- Changing native surface placement did not change the current-image native
  pixel result. The evidence does not support “the parent merely hides a
  successfully shaded Sequoia surface” as the sole explanation for this
  condition.
- Model insertion, camera application, frame scheduling under the diagnostic
  ready condition, queue submit, and present are upstream of the missing
  visible pixels. The smallest next boundary is the shaded draw/resource
  path, using the existing shape/light suppression controls.

#### Hypotheses / decision

- H1 (parent/surface ordering alone hides native pixels): weakened/rejected
  for this current-image condition because both placements remain black in the
  same candidate region.
- H2 (shaded production output is black before or at native presentation):
  remains the leading hypothesis. This A/B does not distinguish material,
  light, renderable, or native-buffer contents.
- H3 (surface is a full-surface participant): remains possible, but is not
  sufficient to explain the identical black candidate region.
- Decision: do not create a source patch from FLR-0059. Start a separate
  ticket for shape/light/resource separation under the recovered frame
  condition.

#### Visual evidence

| Condition | QMP image | Mac QMP video | Runtime log | PPM SHA-256 | Region result |
| --- | --- | --- | --- | --- | --- |
| default (`below_parent=false`) | `$EVIDENCE_ROOT/flr0059-d88d600-20260909/default-qmp.png` | `$EVIDENCE_ROOT/flr0059-d88d600-20260909/default-qmp.mp4` | `$EVIDENCE_ROOT/flr0059-d88d600-20260909/default-runtime.log` | `d0ffccc11da2e2cd5866bf04f49ca72ace6f71adef11a795c10647a0595b8092` | black, `0/223200` |
| below-parent (`below_parent=true`) | `$EVIDENCE_ROOT/flr0059-d88d600-20260909/below-parent-qmp.png` | `$EVIDENCE_ROOT/flr0059-d88d600-20260909/below-parent-qmp.mp4` | `$EVIDENCE_ROOT/flr0059-d88d600-20260909/below-parent-runtime.log` | `0235e5af1e57c15d2256768978a24eb1d3adfbe47b84feb7a736daf7830c9ac3` | black, `0/223200` |

Additional hashes: default PNG `2c0502c5ab909414e24bc707f85be954d6b1279b45f28b330e1b42066fc940ee`,
default video `0a2453ec88171b4cbcc7d7d28bd4f0fb0334433ea7bc001dd8829e026545372a`,
default log `aa2747c9d9bf2d7dabe7e7869b5fc0f0a125e1342b8e3a6653aa2159f41c3d68`,
below-parent PNG `f2e3b6651d22953d18d6e86d7c50f59907678d818ea79211cab9cb9448e32868`,
below-parent video `cdf2da360d37d2ebc2370741604fa80ae5ff3e359437302159c03d2fd94ee167`,
and below-parent log `0cc3112243a39ddfb68c221c5bf7d36bd18107d2fe1fbc7aee08dffbdea3d668`.

The first launch omitted the recovered-fence variable and is retained as
`$EVIDENCE_ROOT/flr0059-d88d600-20260909/default-precondition-miss-runtime.log`
with SHA-256
`7c03c7180d0408ed90ade3ff46db1ad793050bbc82435cad83e9b3e87610177f`.
It is a process-execution correction record, not A/B evidence.

#### Check / Act

- PASS: fixed-artifact preflight, one-QEMU contract, both placement cases,
  model/camera/frame/present markers, QMP-only images/videos, pixel analysis,
  and negotiated teardown.
- FAIL for the requested native-pixel criterion: neither placement produced
  visible production 3D pixels in the current image.
- UNKNOWN: whether the black result is caused by light setup, material/resource
  output, renderable draw submission, or native buffer contents; combined
  2D+3D and Radar/Planetarium route/input remain UNKNOWN.
- Next ticket: separate the existing shape-only and light-only controls from
  the full shaded production path, keeping `FLR0026_TREAT_UNLINKED_FENCE_READY=1`
  common and avoiding a source patch until the first differing draw/resource
  operation is observed.

## Handoff

The placement gate is complete for the current image. Both default and
below-parent arrangements remain HUD-visible with an unchanged black native
candidate region, so continue in the separate shaded draw/resource ticket.

## Visual evidence

- Required authority: QMP-only 1280x800 screenshots from the fixed image and
  corresponding QMP-derived video previews.
- Required record per condition: placement variable, model/frame/camera/present
  markers, visible HUD/native description, candidate-region pixel statistics,
  screenshot/video/log hashes, and QMP `quit` plus residual result.
- Evidence directory: `$EVIDENCE_ROOT/flr0059-<run-id>/` outside Git.

## Handoff

If native-above shows 3D and below-parent shows HUD-only, close this ticket as
Waiting and create a new ticket for the smallest combined-composition boundary.
If both remain black, create a new ticket for the first missing shaded draw or
material/resource operation.
