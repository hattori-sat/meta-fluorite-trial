# FLR-0058 — restore native frame loop before composition

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + target-validation + Flutter/Filament roles
- Created: 2026-09-09
- Depends on: [FLR-0057](FLR-0057-production-lit-3d-and-route.md), [FLR-0049](FLR-0049-production-model-render-boundary.md)
- Working log: `work/logs/2026-09-09-flr0058.md`

## Work unit

Identify whether the current production 3D failure first diverges at the
native frame-start/fence boundary after model insertion, and establish whether
that boundary must be repaired before the independent Wayland composition
gate. This ticket is diagnostic-first; it does not turn an existing diagnostic
environment flag into a production fix.

## Success criteria

- [x] Reuse the fixed image/build/TMPDIR, one managed runtime provider, one
  QEMU, and QMP-only visual evidence.
- [x] Run a control and one-variable frame/fence diagnostic comparison with
  the same production model and environment, recording exact markers, QMP
  pixels, log hashes, and negotiated teardown.
- [x] Determine whether the first divergent event is `FRAME_BEGIN`, fence
  linkage/command execution, native draw submission, or presentation.
- [x] If a diagnostic override restores the frame loop, separately verify
  whether native 3D pixels appear; a true frame loop alone is not success.
- [ ] If a source change is justified, edit through the persistent Mac-side
  Yocto Devtool workspace, finish the generated patch into
  `meta-fluorite-trial`, commit locally, bundle to the fixed Mini PC receiver,
  pass progressive BitBake gates, and repeat the QMP proof.
- [x] Leave combined 2D+3D composition and Radar/Planetarium input as explicit
  UNKNOWN unless their own QMP gates pass.

## Out of scope

- Repeating the FLR-0057 light-count matrix.
- Creating another container, build directory, TMPDIR, receiver, or concurrent
  QEMU.
- Treating `FLR0026_TREAT_UNLINKED_FENCE_READY`,
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME`, or
  `FLR0026_NATIVE_SYNC_PRESENT` as a production fix without a proven source
  cause.
- Editing generated patch files, Mini PC build trees, or runtime `tmp`.
- Declaring a HUD-only frame or a native-above-parent frame to be combined 3D.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0057's current image revision `d88d600` produced a black production
  candidate region for light limits 1, 5, 6, and 13, although every valid case
  reached `MODEL_STAGE_COMPLETE`, `CAMERA_APPLIED`, and Vulkan
  `QUEUE_PRESENT result=0`.
- The same runs showed the first one or two `FRAME_BEGIN started=true` events,
  followed by repeated `started=false`, `FRAME_FENCE_WAIT_LINKED linked=false`,
  and forced-after-skip diagnostics.
- FLR-0049 found that
  `FLR0026_TREAT_UNLINKED_FENCE_READY=1` made later frame-start calls return
  true, but its QMP evidence remained HUD-only.
- FLR-0049 separately proved production Sequoia native 3D pixels when the
  native surface was placed above the Flutter parent, while the below-parent
  arrangement showed the Flutter HUD and hid native 3D.

### Inferences

- Light count is not the primary current-image discriminator.
- The native frame/fence boundary and 2D/3D surface composition are separate
  faults or gates; the frame boundary must be measured before composition is
  changed.
- The strongest next cut is a one-variable runtime comparison, not an
  immediate source patch.

### Hypotheses

| ID | Hypothesis | Falsifiable prediction |
| --- | --- | --- |
| H1 | An unlinked or unexecuted Filament fence causes the successor frame to be skipped. | Treating the unlinked fence as ready changes `FRAME_BEGIN`/fence markers; if native pixels remain absent, H1 explains only scheduling, not composition. |
| H2 | The existing force-render diagnostic violates the begin/render/end contract and masks the true boundary. | Unsetting the force-render flag changes the frame markers or removes the forced path; if the same boundary remains, this flag is not the primary cause. |
| H3 | Frame starts recover but the Flutter parent/surface ordering still hides native pixels. | A recovered frame loop changes native markers but QMP remains HUD-only below-parent and native-only above-parent. |
| H4 | The current shaded material/resource path fails before native draw submission. | Frame/fence markers recover without `MODEL_STAGE`/draw markers or QMP native pixels; the next ticket must isolate material/resource operations. |

## PDCA

### Plan

Use the already validated current image and one QEMU. Reconstruct the exact
control environment from FLR-0057, then compare only one existing frame/fence
diagnostic variable at a time. Capture QMP screenshots and a short QMP-derived
video for each case, correlate the first missing marker with the candidate
pixel region, and tear down through QMP before any next run. Patch only if the
comparison identifies a controllable source boundary.

## Iteration 1 — current-image frame/fence A/B (2026-09-09)

### Facts

- The fixed rootfs from image revision `d88d600` was reused on the Mini PC with
  the existing build directory, TMPDIR, QEMU run directory, and one QMP
  socket. Rootfs SHA-256 is `fa287b877a2d753e9f8b7a7fd02dd02dcaf9a414f6294f1c0a25d6302731da98`;
  kernel SHA-256 is
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- The common runtime variables were Vulkan backend, sync trace, model-stage
  trace, forced render after skipped frame, Sequoia model match/limit 2,
  light limit 13, skybox skip plus clear, and indirect-light skip. The only
  A/B variable was `FLR0026_TREAT_UNLINKED_FENCE_READY=1`.
- Trace Control reached
  `MODEL_STAGE_SCENE_ADD_DONE asset=assets/models/sequoia_ngp.glb guid=14
  mode=secondary`, `CAMERA_APPLIED`, and present boundary. It logged
  `FRAME_BEGIN started=true` twice, then `started=false` twice and
  `FRAME_FENCE_WAIT_LINKED linked=false` 17 times.
- Trace Variant reached the same model scene-add, camera, and present
  markers. It logged `FRAME_BEGIN started=true` four times, no
  `started=false`, and `FRAME_FENCE_WAIT_UNLINKED_READY` 15 times.
- Both QMP representative images are 1280x800 and contain the Flutter HUD,
  FPS, CPU/GPU/System delay, Scenes control, and bottom controls. Neither
  contains production 3D in the candidate region `[300,80,620,360]`:
  `changed_pixels=0/223200`, region SHA-256
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- QMP teardown returned `qmp=PASS capabilities=negotiated quit=accepted` and
  `cleanup=PASS residual_targets=0 residual_qmp=0`. Mini PC `ps` found no
  qemu-system, runqemu, or flutter-auto residual afterward.
- The first launch attempt wrote to `/run` as `agl-driver`, so no log was
  created; it is an invalid runtime attempt. The corrected launch writes to
  `/run/user/1001`. One later start command was rejected by a misspelled SSH
  option before QEMU execution; it is not runtime evidence.

### Inferences

- H1 is confirmed as a scheduling effect: an unlinked Fence is sufficient to
  make the normal path return `started=false`, and the ready diagnostic keeps
  the frame loop active.
- H1 is not the complete 3D cause because the ready Variant still has zero
  native pixels. Model loading, secondary scene insertion, camera application,
  and the present boundary are not sufficient for visible production 3D in
  the current Flutter composition.

### Hypotheses / decision

- H2 is not yet a production-fix candidate: forced rendering remains a
  diagnostic-only contract bypass and was common to both cases.
- H3 and H4 remain open. The next cut is current-image native-surface
  placement A/B: first prove whether the recovered native surface produces
  pixels when visible above the Flutter parent, then isolate combined
  composition in a new ticket.

### Visual evidence

| Condition | QMP image | Mac QMP video | Runtime log | Result |
| --- | --- | --- | --- | --- |
| trace Control | `$EVIDENCE_ROOT/flr0058-d88d600-20260909/control-trace-qmp.png` | `$EVIDENCE_ROOT/flr0058-d88d600-20260909/control-trace-qmp.mp4` | `$EVIDENCE_ROOT/flr0058-d88d600-20260909/control-trace-runtime.log` | HUD-only; central 3D region black |
| trace Fence ready | `$EVIDENCE_ROOT/flr0058-d88d600-20260909/fence-ready-trace-qmp.png` | `$EVIDENCE_ROOT/flr0058-d88d600-20260909/fence-ready-trace-qmp.mp4` | `$EVIDENCE_ROOT/flr0058-d88d600-20260909/fence-ready-trace-runtime.log` | HUD-only; central 3D region black |

QMP PPM / video / runtime-log SHA-256 values:

- Control: PPM `e3420a16e9ae9b081f20487372762b9beb7cb491d3135983f9088b8cbc7ef2d0`,
  video `e1400d8c14be03288f0d2ff779b4662408b8d7f99e91107ca8e6f07a2ae7c41e`,
  log `3c01aed165e45752a8c724486254ea82f5e1334842374224d52132eeeda9cfc1`.
- Fence ready: PPM `5c40028c65d3857bb3391721f90cc56376405cc84dc8f8b7f5a65832a18ffbfb`,
  video `9900112ba865fc6d6511a41e10b68ab69e88b5808e1212bebd4cb779a1122d46`,
  log `4370706ed5d0fdcbe17d0d939bef233f8481cbb0c8eb7ce83ec655680c3220e0`.

### Check / Act

- Frame/fence causal gate: PASS.
- Actual production 3D pixels and combined 2D+3D: UNKNOWN; no source patch
  was made.
- Close this ticket as Waiting. Continue in [FLR-0059](FLR-0059-native-surface-visibility-ab.md)
  with the recovered-frame condition and a surface-placement A/B.

## Visual evidence

- Required authority: QMP-only 1280x800 screenshots from the fixed image and
  the same bounded run. Mac-side video previews may be generated from those
  QMP frames but do not replace the QMP image authority.
- Required record per condition: image/layer revision, runtime variables,
  visible HUD/native region description, candidate-region pixel statistics,
  screenshot/video/log hashes, and QMP `quit` plus residual-process result.
- Evidence directory: `$EVIDENCE_ROOT/flr0058-<run-id>/` outside Git.

## Handoff

If the frame/fence gate is resolved but combined 2D+3D or route/input remains
unproven, close this ticket as Waiting and create one new Markdown ticket for
the next independently verifiable boundary.
