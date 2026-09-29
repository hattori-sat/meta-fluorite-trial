# FLR-0060 — production shaded draw/resource boundary

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + target-validation + Flutter/Filament roles
- Created: 2026-09-09
- Depends on: [FLR-0059](FLR-0059-native-surface-visibility-ab.md), [FLR-0057](FLR-0057-production-lit-3d-and-route.md)
- Working log: `work/logs/2026-09-09-flr0060.md`

## Work unit

Using the current image and the recovered frame condition, identify the first
divergence between the visible diagnostic/shape path and the black full shaded
production Fluorite path. Use the existing `FLR0027_NATIVE_SKIP_LIGHTS` and
`FLR0027_NATIVE_SKIP_SHAPES` runtime controls as orthogonal probes. Do not
change source or rebuild until a draw/resource boundary is attributed.

## Success criteria

- [x] Reuse the fixed image/build/TMPDIR, one runtime provider, one QEMU, and
  QMP-only evidence.
- [x] Reproduce the full shaded control with
  `FLR0026_TREAT_UNLINKED_FENCE_READY=1` and record the black candidate region.
- [x] Compare shape-only and light-only probes, varying only one suppression
  control per case; correlate model, renderable, material/resource, frame,
  submit, and present markers.
- [ ] Determine the first production shaded divergence after the valid
  compositor-owner condition; the current evidence separates owner gating from
  the remaining shaded draw/resource boundary but does not identify the first
  source operation.
- [x] If a source change is justified, edit only through the persistent Mac
  Yocto Devtool workspace, finish the generated patch into
  `meta-fluorite-trial`, commit locally, bundle to the fixed Mini PC receiver,
  pass progressive BitBake gates, and repeat QMP validation.
- [x] Keep full shaded production 3D, combined 2D+3D, and route/input UNKNOWN
  until their own QMP gates pass.

## Out of scope

- Repeating the FLR-0057 light-count matrix or FLR-0059 surface-placement A/B.
- Creating another container, build directory, TMPDIR, receiver, or QEMU.
- Treating suppression controls as a production fix.
- Editing generated patch files, Mini PC build trees, or runtime `tmp`.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0059 showed identical black native candidate regions for default and
  below-parent surface placement, despite Sequoia scene-add, camera, recovered
  frame, queue submit, and present markers.
- FLR-0050's earlier diagnostic path produced combined HUD plus native
  wireframe/red-lamp pixels when production shapes/lights were selectively
  suppressed.
- `FLR0027_NATIVE_SKIP_LIGHTS` and `FLR0027_NATIVE_SKIP_SHAPES` are already
  present as opt-in runtime controls in the current image; no source change is
  required for the first diagnostic split.
- The earlier current-image shape-only and light-only probes under the normal
  grpc shell-client owner remained black in the candidate region, even though
  model, camera, frame, submit, and present markers were present.
- In a snapshot-only compositor-owner A/B, backing up the guest Weston config,
  removing only its `[shell-client-ext]` block, and restarting
  `agl-compositor.service` removed the `agl-shell-grpc-server` child while the
  service stayed active. No rootfs or layer file changed.
- Under that owner-isolated condition, shape-only produced QMP-visible
  wireframe and red-lamp pixels with the Flutter HUD. The same owner condition
  with the production shaded path and no shape/light suppression remained HUD
  plus black in the candidate region.

### Inferences

- The smallest useful experiment was a runtime-only shape/light split under the
  recovered frame condition, followed by reconciliation against the historical
  positive compositor-owner condition.

### Hypotheses

| ID | Hypothesis | Falsifiable prediction |
| --- | --- | --- |
| H1 | Production lights or their resources make the shaded output black. | Shape-only produces native pixels while the full control remains black. |
| H2 | Shape/material/resource setup is the first failing operation. | Shape-only remains black or lacks renderable/material completion even with lights suppressed. |
| H3 | Pixels exist before native presentation but are hidden by a later buffer/compositor step. | Native draw/resource markers succeed and native-above QMP differs from the below-parent result. |

### UNKNOWN

- First divergent operation inside the full shaded production path after the
  valid compositor-owner condition.
- Full shaded production 3D, combined 2D+3D, and route/input behavior.

## PDCA

### Plan

Run the full shaded control, then shape-only and light-only probes one at a
time with the fixed image and QMP harness. Retain black and failed cases as
evidence. Select a source patch only if the runtime evidence identifies a
specific operation and the patch has a clear expected effect.

### Do / Check / Act

#### Entry 1 — current-image probes and compositor-owner reconciliation (2026-09-10)

##### Plan

Reuse the fixed image and existing evidence directory. First restore the
historical compositor-owner condition as a snapshot-only runtime variable,
then run the shape-only positive probe and the full shaded control with the
same Wayland, Vulkan, model, and frame settings. Save QMP-only screenshots,
12-frame videos, selected raw guest logs, pixel-region analysis, and teardown
results. Do not create a source patch until a production draw/resource
operation is shown to diverge.

##### Facts

- The initial QEMU process from the previous FLR-0060 attempt was found by the
  exact QMP socket and ended with a negotiated QMP `quit`; post-check found no
  QEMU, runqemu, flutter-auto, or QMP socket residual.
- The fixed-image preflight initially rejected an incorrect qemuboot path. The
  verified artifact is under the existing fixed TMPDIR; no build or TMPDIR was
  created. The corrected preflight and start both passed.
- Before the A/B, `/etc/xdg/weston/weston.ini` contained the
  `[shell-client-ext]` command for `agl-shell-grpc-server`. The config was
  copied to `/run/flr0060-weston.ini.before`, only that block was removed, and
  the compositor was restarted. The resulting service was `active` and the
  grpc child was absent. The original config was restored before teardown and
  the compositor returned to active with the grpc child present.
- A first shape-only launch omitted `XDG_RUNTIME_DIR` and `WAYLAND_DISPLAY`.
  The raw guest log recorded `Failed to connect to Wayland display. Permission
  denied`; this is retained as a precondition-miss artifact, not A/B evidence.
- The corrected owner-isolated shape-only launch reached Sequoia model
  completion, camera application, Vulkan surface/swapchain creation,
  `FRAME_BEGIN started=true`, `FRAME_FENCE_WAIT_LINKED linked=false`, forced
  frame handling, queue submit, and present markers.
- The shape-only QMP capture required a second attempt because the first
  command supplied a relative screendump path and QEMU created no non-empty
  PPM. The successful retry used absolute paths; this execution correction is
  retained in the working log.
- Owner-isolated shape-only final QMP evidence is
  `$EVIDENCE_ROOT/flr0060-d88d600-20260909/owner-shape-r2.png` and its video is
  `$EVIDENCE_ROOT/flr0060-d88d600-20260909/owner-shape-r2.mp4`. The final PPM
  has SHA-256
  `63d215455acbdb1e37099855e072e1c10fefef212d5af0f24f4b394d37416a12`.
  Region `[300,80,620,360]` has `4905/223200` changed pixels, region SHA-256
  `a75c2c9cda279a90d46dd153584ca225929be6fd6fd6de63045270474b878424`, and
  bounding box `[300,80,620,280]`. Visual inspection shows the Flutter HUD,
  white native wireframe, and red lamps together.
- The 12 owner-isolated shape-only frames are not stable: 9 frames share PPM
  SHA-256
  `223c077d005f79ab5c912b4d230a1bafc58a7c2822724a2eeb9329b108f722e7` and
  contain only a bottom boundary line (`620/223200` changed pixels), while 3
  frames share the final full diagnostic shape result. Therefore this is a
  positive pixel-path proof, not a stable frame-rate proof.
- Owner-isolated full shaded control used the same runtime variables plus
  `FLR0026_TREAT_UNLINKED_FENCE_READY=1` and no shape/light suppression. It
  reached `MODEL_STAGE_SCENE_ADD_DONE`, `CAMERA_APPLIED`, repeated
  `FRAME_BEGIN started=true`, `FRAME_FENCE_WAIT_UNLINKED_READY`, queue submit,
  and present markers. Its QMP PPM has SHA-256
  `4a366c72d321088d686dc9a10d7737b7b2bbbfe47c4bed22ec9b8d51f787f041`; region
  SHA-256 is
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2` with
  `0/223200` changed pixels. All 12 full-control frames were byte-identical
  and visually HUD plus black.
- QMP teardown after the A/B completed with a host-QMP `SHUTDOWN` event. The
  Mini PC post-check found no QEMU, runqemu, flutter-auto, or QMP socket.

##### Inferences

- The historical combined 2D-plus-diagnostic-3D image is reproducible and was
  not a mistaken recollection: the missing variable was the compositor owner
  runtime configuration, not only native surface z-order.
- The normal grpc shell-client owner is a real upstream gate for native pixels
  in the current image: its presence correlates with the black shape-only and
  light-only probes, while the owner-isolated shape probe exposes native pixels
  beside the HUD.
- Owner isolation is not sufficient for the requested production result. The
  full shaded Sequoia path remains black after scene insertion and valid frame,
  submit, and present markers. The remaining fault is downstream of or inside
  production shaded draw/resource execution, but the first operation is not
  yet identified.

##### Hypotheses / decision

- H1, “lights alone make the shaded output black,” is not supported: the
  default-owner shape-only probe is black, and the owner-isolated full shaded
  probe is also black.
- H2, “the production shape/material/resource path is the first failing
  operation,” remains open. Scene insertion completes, but direct renderable
  draw/material-instance success is not yet logged.
- H3, “native pixels exist before presentation but are hidden later,” is
  weakened for the owner-isolated shape path because QMP sees those pixels, but
  remains possible for the full shaded path.
- H4, “the normal grpc shell client prevents the native child from becoming a
  compositor-visible participant,” is supported as a runtime gating factor,
  but it is not a complete product diagnosis because full shaded output stays
  black after owner isolation.
- Decision: do not patch the layer or rebuild from FLR-0060. Move the ticket to
  Waiting and continue in FLR-0061 with a separate production shaded
  draw/resource boundary investigation under the validated owner-isolated
  runtime.

##### Check

- PASS: fixed artifact reuse, one-QEMU contract, snapshot-only owner A/B,
  corrected guest launch, model/camera/frame/submit/present marker collection,
  QMP-only screenshots, 12-frame videos, pixel analysis, raw failed/success
  logs, and negotiated teardown.
- PASS: historical 2D HUD plus native diagnostic wireframe/red-lamp result
  reproduced under owner isolation.
- FAIL: full shaded production vehicle and stable continuous native 3D are not
  visible; combined production 2D+3D and route/input remain UNKNOWN.
- UNKNOWN: first production renderable/material/draw operation that diverges
  after `MODEL_STAGE_SCENE_ADD_DONE`.

##### Act

Create FLR-0061 for the production shaded draw/resource boundary. Start with
static/runtime evidence for renderable visibility, material instances,
render-list/culling, and native draw submission under the owner-isolated
condition. Keep shape suppression as a positive control and do not promote
runtime suppression or grpc removal to a product fix.
