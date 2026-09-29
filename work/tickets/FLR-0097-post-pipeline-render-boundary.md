# FLR-0097 — isolate the post-pipeline render boundary

- Status: Done
- Priority: High
- Owner: Fluorite runtime evidence / render-resource boundary
- Created: 2026-09-12
- Depends on: [FLR-0096](FLR-0096-production-pipeline-runtime-snapshot.md)
- Working log: `work/logs/2026-09-12-flr0097.md`
- Evidence manifest: `work/evidence/FLR-0097-post-pipeline-render-boundary-2026-09-12.md`

## Work unit

Determine what happens after production Vulkan pipeline creation completes.
Compare the self-made fixture, which already produces native pixels, with the
production scene, which completes pipeline creation but remains native-black.
The first missing post-pipeline operation must be identified before any
source patch or synchronization change is proposed.

This ticket uses the canonical repository and fixed Mini receiver only. It
does not create or reuse a legacy `FLR0026` directory, marker, environment
variable, receiver, bundle, or TMPDIR. Historical `FLR0026` traces may be
cited as read-only provenance only.

## Success criteria

- Static inspection identifies the existing post-pipeline hooks for model
  resource readiness, renderable/material state, frame/draw, and native-surface
  handoff, including their recipe patch order and effective-image status.
- One paired fixture/production runtime observation reuses one image, one
  QEMU, one short QMP socket, and bounded selected-marker extraction.
- The comparison identifies the first missing or divergent operation after
  successful pipeline creation, or records `UNKNOWN` with the exact evidence
  gap.
- QMP-only visual evidence, runtime log hashes, and negotiated teardown are
  recorded.
- No synchronization, present, Wayland, alpha, or production behavior patch
  is claimed unless the first missing boundary is proven.

## Out of scope

- No new source patch or image rebuild until the runtime boundary is classified.
- No new legacy-named controls or markers.
- No global kill, `cleanall`, `cleansstate`, cache deletion, second QEMU, or
  per-ticket TMPDIR.

## Facts

- FLR-0096 proved that production pipeline creates 1 through 6 eventually
  return `result=0`; create 4 takes about 21.4 seconds under software Vulkan.
- The same late production frame remains native-black (`0/223200`) while HUD
  pixels change (`1264/100000`).
- The neutral fixture reaches native pixels later than startup and therefore
  provides a positive control for the post-pipeline path.
- Existing layer patches already contain diagnostic hooks around model stages,
  camera/geometry, renderable resources, frame/draw targets, and native
  surface handoff. Their effective activation and ordering must be checked
  before deciding whether a neutral diagnostic alias is needed.

## Inferences

- Pipeline creation is no longer the first proven production-only missing
  operation. The next useful discriminator is the first post-pipeline marker
  present in the fixture but absent or delayed in production.
- A paired run is lower cost and more informative than another light-count or
  present/fence experiment because those boundaries are downstream of the
  unresolved render-resource/frame state.

## Hypotheses

1. Production renderable/material resources are not ready or are not attached
   when the frame is drawn. Prediction: model/resource markers diverge before
   draw-target markers.
2. Production reaches draw but emits no effective native draw commands.
   Prediction: renderable and frame markers match the fixture, but draw-target
   or command markers diverge.
3. Production draws native content but the native surface handoff remains
   absent or points at an unchanged buffer. Prediction: draw/submit markers
   match while surface identity/commit markers diverge and QMP stays black.
4. The current markers are insufficient or observation timing is inadequate.
   Prediction: both paths have indistinguishable markers, requiring a small
   neutral Devtool-generated observation patch as a separate ticket.

## UNKNOWN

- Which existing post-pipeline markers are enabled in the authoritative image
  under the default runtime profile.
- Whether the fixture and production runs can be paired without a fresh
  build, or whether a neutral Devtool alias is required.
- The first post-pipeline operation that is absent from production.

## Plan / Do / Check / Act

### Plan

1. Verify the canonical checkout and exactly one active ticket.
2. Inspect recipe patch order and source hooks without changing source.
3. Reuse the fixed image for one bounded fixture/production comparison with
   QMP-only frames and selected logs.
4. Classify the first post-pipeline divergence and open a separate source
   ticket only if a controllable seam is proven.

### Do

1. Verified the canonical repository and used only the fixed Mini receiver,
   fixed build/TMPDIR, fixed image artifacts, and the existing short QMP run
   alias. No legacy-named directory was created.
2. Ran one neutral fixture case and one production case sequentially. Each
   case used one QEMU, one `flutter-auto`, the same launch identity, QMP-only
   before/early/late captures, and bounded serial extraction.
3. Enabled the existing scene, camera/view, resource, frame, draw-target, and
   driver observations. The fixture reached draw/submit/present; production
   reached scene/camera/view/resource state but stopped at
   `FRAME_BEGIN started=false`.
4. An initial host-side summary call used a guest log path and failed closed
   with `log-not-readable`. The guest log was then extracted with serial-exec
   and the run was completed successfully; the invocation mistake is retained
   in the manifest.

### Check

 - Fixture native candidate region: `41,750/223,200` changed pixels with
   bounding box `[501,278,278,162]`; its trace contained `TARGET_DRAW2`, queue
   submit, queue present, and present-boundary completion.
 - Production scene state was valid: `1115` entities, `837` renderables,
   `13` lights, valid camera/view state, and six sampled resources with
   `material_valid=true`.
 - Production emitted `FRAME_BEGIN started=false` and repeated
   `FRAME_SKIP_STATUS status=1` (`TIMEOUT_EXPIRED`); no draw-target,
   submit, or present marker appeared. Its native region remained
   `0/223,200`, while HUD pixels changed `1,236/100,000`.
 - The first missing operation in this current-image comparison is therefore
   the production frame-start/draw boundary, not the native surface composition
   boundary. This reproduces the class of boundary previously observed by
   FLR-0058, so it is not yet a new source-fix justification.
 - Both QEMU cases were stopped through QMP and residual checks passed.
 - QMP images, selected logs, hashes, and the exact interpretation are in the
   linked evidence manifest.

### Act

Do not patch post-pipeline resources, synchronization, present, Wayland, or
alpha under this ticket. Open FLR-0098 to re-run the existing
unlinked-fence-ready control on the current image. Only after that A/B is
reconciled with the native pixel result should a Mac Devtool source patch be
considered.

## Visual evidence

The QMP-only fixture and production before/early/late frames are listed with
SHA-256 and candidate-region statistics in the evidence manifest.
