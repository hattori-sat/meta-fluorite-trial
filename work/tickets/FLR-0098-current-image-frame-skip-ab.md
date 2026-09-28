# FLR-0098 — recheck current-image frame-skip recovery

- Status: Done
- Priority: High
- Owner: Fluorite runtime evidence / frame-skip boundary
- Created: 2026-09-12
- Depends on: [FLR-0097](FLR-0097-post-pipeline-render-boundary.md), [FLR-0058](FLR-0058-restore-native-frame-loop.md)
- Working log: `work/logs/2026-09-12-flr0098.md`
- Evidence manifest: `work/evidence/FLR-0098-current-image-frame-skip-ab-2026-09-12.md`

## Work unit

Re-run the existing unlinked-fence-ready diagnostic control against the
current authoritative image. FLR-0097 reproduced the production frame-start
stop, while FLR-0058 showed historically that treating an unlinked fence as
ready can keep the frame loop alive but did not by itself restore native
pixels. This ticket verifies whether that conclusion still holds after the
current pipeline/fixture changes.

The old control is used only as existing image instrumentation for comparison;
this ticket creates no new legacy directory, receiver, TMPDIR, environment
variable, marker, or source patch.

## Success criteria

- Reuse the fixed image, build/TMPDIR, existing QEMU run area, and one QEMU at
  a time.
- Compare normal control with only the existing unlinked-fence-ready variable
  enabled.
- Record `FRAME_BEGIN`, fence status, draw-target, submit/present markers and
  QMP native/HUD pixel statistics for both cases.
- Determine whether frame-start recovery is sufficient for native pixels, or
  whether the first remaining divergence moves downstream.
- Stop both cases through QMP and record cleanup and hashes.

## Out of scope

- No source or recipe patch, image rebuild, synchronization fix, present fix,
  Wayland change, alpha change, cache cleanup, or second concurrent QEMU.
- Do not treat frame-loop recovery alone as the 3D success criterion.

## Facts

- FLR-0097 current-image control: valid scene/resource state, then
  `FRAME_BEGIN started=false`, no draw/submit/present, and `0/223200` native
  pixels.
- FLR-0058 historical A/B: the existing ready control changed later frame
  starts to true but remained native-black.
- The fixture is a positive control because it reaches native draw/submit/
  present and changes the native QMP region.

## Inferences

- If the current ready variant also reaches draw but remains black, frame skip
  is a scheduling contributor rather than the complete 3D cause.
- If the ready variant reaches native pixels, the current image has regressed
  relative to the historical A/B and the source boundary must be audited
  before any patch is proposed.

## Hypotheses

1. Existing unlinked-fence readiness recovers frame execution but not native
   visibility. Prediction: `FRAME_BEGIN started=true` and draw/submit/present
   appear, but native pixels remain zero.
2. Current image changes made the frame-skip boundary sufficient. Prediction:
   the ready variant reaches native pixels while control remains black.
3. The control does not alter the current path. Prediction: both variants
   retain `started=false` or have the same first missing marker.

## UNKNOWN

- Whether the current image's exact frame/fence behavior matches FLR-0058.
- Whether a recovered frame reaches an effective native draw under the current
  production pipeline set.

## Plan / Do / Check / Act

### Plan

1. Verify canonical state and target cleanup.
2. Run normal control with existing frame/draw/fence traces and QMP captures.
3. Run the one-variable unlinked-fence-ready variant with the same profile.
4. Compare first missing markers and native pixels, then decide whether a
   separate downstream ticket or Mac Devtool patch is justified.

### Do

1. Reused the fixed image, build/TMPDIR, existing QEMU run area, and one
   QEMU at a time. The first control start was correctly blocked because the
   previous short alias still existed; after confirming no residual process or
   QMP socket, the existing alias was retargeted to the control evidence.
2. Ran the normal production control, captured QMP before/early/video/late
   frames and bounded markers, then stopped it through QMP.
3. Ran the same production case with only the existing
   `FLR0026_TREAT_UNLINKED_FENCE_READY=1` control enabled, captured the same
   evidence, and stopped it through QMP.
4. Two late-capture attempts used a mistyped fixed script path. Neither
   changed runtime state; the correct path then captured the late frame,
   extracted the guest log, and completed QMP teardown. Both invocation errors
   are retained as process-improvement evidence.

### Check

 - Control remained at `FRAME_BEGIN started=false` with repeated
   `FRAME_SKIP_STATUS status=1` (`TIMEOUT_EXPIRED`), no draw-target/submit/
   present marker, and native `0/223200` pixels.
 - Ready variant reached `FRAME_BEGIN started=true`, `FRAME_END`,
   `FRAME_EVENT_RETURNED`, unlinked-fence-ready, 25 draw-target markers, 7
   renderer commit enqueues, and six successful pipeline creates. Its native
   region nevertheless remained `0/223200`; HUD remained active at
   `984/100000`.
 - The A/B confirms that frame-skip recovery changes the execution path but
   does not restore production native pixels. Frame-skip is a contributor, not
   the complete 3D cause.
 - QMP quit and residual checks passed for both cases. Full hashes and visual
   statistics are in the evidence manifest.

### Act

Close this A/B as Done. Do not turn the existing diagnostic control into a
production fix and do not patch synchronization, present, Wayland, or alpha
yet. Split the recovered draw-to-native-output boundary into FLR-0099.

## Visual evidence

The QMP-only before/early/late frames and six-frame videos for both control and
ready variant are listed with hashes and pixel-region analysis in the evidence
manifest.
