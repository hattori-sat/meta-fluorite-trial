# FLR-0061 — production shaded draw/resource boundary under valid compositor owner

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + Flutter/Filament roles
- Created: 2026-09-10
- Depends on: [FLR-0060](FLR-0060-production-shaded-draw-resource-boundary.md), [FLR-0059](FLR-0059-native-surface-visibility-ab.md)
- Working log: `work/logs/2026-09-10-flr0061.md`

## Work unit

Using the validated snapshot-only compositor-owner condition from FLR-0060,
identify the first production shaded draw/resource operation that diverges
after `MODEL_STAGE_SCENE_ADD_DONE`. Use owner-isolated shape-only pixels as the
positive native-draw control and the owner-isolated full shaded Sequoia result
as the negative control. Inspect existing source, runtime markers, Filament
renderable/material state, render-list/culling, and Vulkan draw submission in
that order. Do not patch or rebuild until a specific operation and expected
effect are evidenced.

## Success criteria

- [ ] Reuse the fixed image/build/TMPDIR, one runtime provider, one QEMU, and
  QMP-only evidence; do not create another container, build, TMPDIR, or QEMU.
- [ ] Reproduce the owner-isolated shape-only positive and full shaded negative
  controls from FLR-0060 before changing the diagnostic variable.
- [x] Correlate model entity/renderable/material creation, visibility/culling,
  render-list inclusion, native draw calls, frame submit, and present markers.
- [x] Identify the first divergent production operation with a falsifiable
  explanation, or record UNKNOWN with the exact missing evidence.
- [x] If a source change is justified, edit only through the persistent Mac
  Yocto Devtool workspace, finish the generated patch into
  `meta-fluorite-trial`, commit locally, bundle to the fixed Mini PC receiver,
  pass progressive BitBake gates, and repeat QMP validation.
- [ ] Keep full shaded production 3D, combined 2D+3D, and route/input UNKNOWN
  until their own QMP gates pass.

## Out of scope

- Repeating the completed light-count matrix, surface-placement A/B, or
  compositor-owner discovery without a new variable.
- Treating `FLR0027_NATIVE_SKIP_LIGHTS`, `FLR0027_NATIVE_SKIP_SHAPES`, or
  snapshot-only grpc removal as a product fix.
- Editing generated patch files, Mini PC build trees, or runtime `tmp`.
- Route/input and Planetarium validation before full shaded native pixels are
  proven in a stable frame loop.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0060 reproduced the historical Flutter HUD plus native diagnostic
  wireframe/red-lamp QMP result only after the snapshot-only compositor owner
  isolation.
- Under the same owner-isolated condition, production Sequoia scene insertion,
  camera application, frame start, queue submit, and present markers completed,
  but the QMP candidate region remained black.
- The current image already contains bounded diagnostic controls and trace
  markers; the first investigation requires no source patch or image rebuild.
- The active recipes register the existing Devtool-generated diagnostic
  patches for scene visibility (`0169`), camera geometry (`0170`), view state
  (`0172`), delayed GLB/resource sampling (`0195`), Vulkan pipeline creation
  (`0163`), CommandStream execution (`0155`–`0159`), and descriptor tracing
  (`0160`).
- Under the owner-isolated full shaded trace, scene visibility reached
  `entities=81 renderables=57 lights=13`, the Sequoia scene-add completed, and
  the runtime emitted five successful graphics pipeline creations, one `draw`,
  and 23 `draw2` executions. Vulkan submit and present returned success.
- The same run's QMP candidate region `[300,80,620,360]` remained black in all
  12 frames (`0/223200` nonblack pixels), and the existing native readback
  path stopped after a ready fence without emitting `NATIVE_READBACK_RESULT`.

### Inferences

- The smallest next cut is to compare the positive shape-only native draw path
  with the full shaded path at renderable/material/render-list/draw boundaries
  while holding compositor owner and frame conditions constant.
- A source patch is justified only if the first divergent operation is mapped
  to a minimal source change with a clear runtime prediction.

### Hypotheses

| ID | Hypothesis | Falsifiable prediction |
| --- | --- | --- |
| H1 | Production material/resource setup creates renderables but no drawable shaded primitives. | Renderable/material creation completes, but render-list or draw-call evidence is absent or empty only for full shaded mode. |
| H2 | Production visibility/culling or camera state excludes the shaded entities. | Entity/renderable state exists, but visibility, bounds, or render-list membership is zero or outside the camera while shape-only remains visible. |
| H3 | Shaded draw commands are submitted but their resource/attachment output is black before QMP. | Vulkan draw/submit succeeds with full shaded mode, but a native target/readback or attachment-level probe is black. |

### UNKNOWN

- The first *source-level* divergent operation after production scene insertion.
- Which of the observed draw commands belongs to the production shaded model.
- Whether the production shaded material instances, renderables, and render
  list contain valid state in the current image beyond the sampled entries.
- Whether full shaded pixels exist before the compositor/QMP boundary.
- Stable full shaded 3D, combined 2D+3D, and route/input behavior.

## PDCA

### Plan

Read the active layer/recipe and existing diagnostics first. Then run only the
minimum owner-isolated runtime probe needed to fill the first missing boundary,
retaining QMP screenshots, short videos, raw logs, and hashes. If the evidence
selects a source operation, use the Mac Devtool workspace to produce the patch,
register it in `meta-fluorite-trial`, commit locally, bundle it to the fixed
Mini PC receiver, and validate progressively before the next QMP run.

### Do / Check / Act

#### Entry 1 — owner-isolated shaded pipeline/draw trace (2026-09-10)

##### Plan

Reuse the fixed image, one QEMU, and the owner-isolated Weston condition. Keep
the existing full shaded controls and add only `PIPELINE_TRACE` and
`COMMAND_EXECUTION_ALL_TRACE` to expose the missing draw boundary. Save QMP
frames, raw logs, hashes, and teardown state. Do not patch until a specific
source operation is implicated.

##### Facts

- The shape-only positive control was saved under
  `$EVIDENCE_ROOT/flr0061-d88d600-20260910/shape-diagnostics.ppm` with SHA-256
  `c9b65d1eac1710694e1fa1f41eeec13be9d37f3ce1e243e37fb2c0c7241060a1`.
  Its candidate region contained `4905/223200` nonblack pixels, region SHA-256
  `a75c2c9cda279a90d46dd153584ca225929be6fd6fd6de63045270474b878424`, and
  the visual derivative shows Flutter HUD, white native wireframe, and red
  lamps together. The 12-frame video is
  `$EVIDENCE_ROOT/flr0061-d88d600-20260910/shape-diagnostics.mp4`.
- The full shaded trace was saved under
  `$EVIDENCE_ROOT/flr0061-d88d600-20260910/trace-full-boundary.ppm` with
  SHA-256 `9109a87ce88d5bf72eb19a1c535dabc67751d97e239f8aaf26a29a77feff7037`.
  The candidate region was black (`0/223200`) in all 12 frames; region SHA-256
  was `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- The raw full trace log is
  `$EVIDENCE_ROOT/flr0061-d88d600-20260910/trace-full-boundary-runtime.log`
  with SHA-256
  `b3d1c15402a9ead9de79374ec624b270670056ff4aa81177e0403d88aa4803b6`.
  It contains 1,445 `COMMAND_EXECUTE_BEGIN`, 1,444 matching `DONE`, five
  `GRAPHICS_PIPELINE_CREATE_DONE result=0`, one `draw`, and 23 `draw2` markers.
- The same log contains `MODEL_STAGE_SCENE_ADD_DONE`, valid camera/view state,
  `RENDERABLE_RESOURCE_SAMPLE` entries, `RENDERER_COMMIT_ENQUEUE`, successful
  queue submit/present markers, and the readback target/fence sequence. It has
  no `NATIVE_READBACK_RESULT` marker.
- A first trace launch failed because the guest image has no `runuser`; the
  existing `/usr/bin/su` path was then used. A second launch failed because a
  root-owned log file from that attempt blocked `agl-driver`; the exact file
  was removed and the corrected launch succeeded. An initial Mac-side guest
  SSH probe also omitted the required ProxyJump and therefore checked the
  wrong localhost; the correction is retained here so it is not repeated.
- Teardown stopped the exact app PID, restored the Weston
  `[shell-client-ext]` configuration, confirmed the compositor active with its
  grpc child, sent QMP `quit`, observed `SHUTDOWN reason=host-qmp-quit`, and
  found no QEMU, runqemu, flutter-auto, or QMP socket residual.

##### Inferences

- H1, “no drawable command exists,” is rejected at the global command level:
  the shaded run executes draw commands and successful graphics pipeline
  creation. This does not yet prove that those commands belong to the Sequoia
  model because the existing trace lacks entity-to-draw correlation.
- H2 remains open. Scene/renderable totals, camera geometry, view state, and
  sampled material instances are valid, but production-entity render-list
  membership is not directly identified by the current trace.
- H3 is strengthened: draw/pipeline/submit/present all complete while QMP is
  black and the readback result callback is absent. A target-level result is
  still missing, so the exact output boundary is UNKNOWN.

##### Decision

No source patch or image build is justified by this ticket. The first observed
divergence is after successful draw/submit/present and at the visible
output/readback boundary, but the source-level operation is not identified.
Move the next independent output-target/readback mapping task to FLR-0062.

##### Check

- PASS: fixed artifact reuse, one-QEMU contract, owner isolation, shape
  positive/full shaded negative controls, static diagnostic inventory, bounded
  pipeline/CommandStream trace, QMP-only screenshots/videos, raw logs, hashes,
  and negotiated teardown.
- FAIL: full shaded production 3D, stable continuous native 3D, combined
  production 2D+3D, and route/input remain unproven.
- UNKNOWN: production entity-to-draw mapping, target contents before QMP, and
  the missing native readback result callback.

##### Act

Move FLR-0061 to Waiting and continue with FLR-0062. FLR-0062 must first
correlate the observed draw commands with the production output target before
any corrective source patch is proposed.

## Handoff

The compositor-owner gate is a prerequisite already evidenced in FLR-0060. This
ticket owns only the completed bounded diagnosis of the full shaded production
draw/resource boundary; the missing output-target/readback mapping continues in
FLR-0062.
