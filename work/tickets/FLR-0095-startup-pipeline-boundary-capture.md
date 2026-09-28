# FLR-0095 — capture startup markers and pipeline boundary

- Status: Done
- Priority: High
- Owner: Fluorite runtime evidence / Filament Vulkan boundary
- Created: 2026-09-12
- Depends on: [FLR-0094](FLR-0094-neutral-fixture-pipeline-comparison.md)
- Working log: `work/logs/2026-09-12-flr0095.md`

## Work unit

Using the existing authoritative image and fixed QEMU harness, capture the
startup selection markers and the complete bounded set of Vulkan pipeline
input/create records for the self-made fixture and production scene. The
purpose is to identify the first stable divergence after the FLR-0094 native
fixture/production pixel split. This ticket is evidence-only: it does not
change fence/present behavior, scene code, or the image.

## Success criteria

- Reuse the fixed Mini receiver, build/TMPDIR, image artifacts, and approved
  QMP-only capture path; do not create a second QEMU, build, or temporary tree.
- Run one neutral-fixture case and one production case with the same launch
  identity, one `flutter-auto` process, and one QEMU process per case.
- Capture the startup selection marker before the bounded log tail is taken,
  and retain all pipeline-input records plus their completion markers for the
  bounded observation window.
- Preserve early/late QMP screenshots, a short QMP frame sequence, bounded
  runtime evidence, hashes, and clean QMP teardown in the fixed receiver.
- Compare the records field by field and classify the first divergence as
  before pipeline create, after create/resource setup, or frame/display
  presentation. If a marker is not captured, record `UNKNOWN`.

## Out of scope

- No source or recipe patch.
- No change to Vulkan fence, queue, present, Wayland stacking, or surface
  alpha behavior.
- No new build directory, TMPDIR, receiver directory, or legacy namespace.

## Facts

- FLR-0094 proved that the same image and QMP path produce native pixels for
  the neutral fixture but zero native-region pixels for production while the
  2D HUD remains visible.
- The installed binary and effective recipe contain the neutral controls.
- The previous fixture runtime evidence was collected as a late bounded tail,
  so it did not contain the startup neutral marker. This makes marker
  selection `UNKNOWN`, not a fixture failure.
- Production evidence contained four pipeline-input records; the first three
  had create result `0`, while the fourth had no completion marker in the
  bounded log.

## Inferences

- The next highest-value observation is a live startup-marker extraction and
  a complete pipeline record window, not another source patch.
- If the fixture records all complete and production stops at record four, the
  production-only pipeline/resource path becomes the leading boundary.

## Hypotheses

1. The fixture path completes its pipeline work and only the previous log
   collection lost the selection marker. Prediction: live extraction shows the
   neutral marker and all fixture create records complete.
2. Production stalls or fails at the fourth pipeline input. Prediction: the
   same bounded window shows a fourth production input without a matching
   completion and no native pixels.
3. Production pipeline creation completes, but the divergence is in resource
   setup, draw, or surface handoff. Prediction: every create record completes
   in the production window while native pixels remain zero.
4. The split is a timing artifact. Prediction: equivalent early/late captures
   vary across repeats or show the missing completion after a longer bounded
   window.

## UNKNOWN

- Whether a live guest-side extraction can retain all startup and pipeline
  markers without changing application timing materially.
- Whether the fourth production pipeline input is the first causal boundary
  or only the last record visible in the previous bounded tail.
- Whether the native region remains zero after a longer, still bounded,
  production observation.

## Plan / Do / Check / Act

### Plan

1. Verify the canonical revision, fixed artifact identity, and no residual
   runtime process.
2. Run the neutral fixture with live startup/pipeline extraction, QMP early and
   late frames, and QMP teardown.
3. Run the equivalent production case with the same extraction and capture
   profile.
4. Compare the bounded records and pixels, then close this evidence unit as
   Done or Waiting and create a separate source-change ticket only if needed.

### Do

1. Verified the fixed image identity and found no residual QEMU, Flutter,
   BitBake, or QMP socket before the run.
2. Reused the fixed receiver and one short socket-path alias to avoid the
   QEMU Unix socket length limit. The fixture was run with the neutral controls
   and the production case with only the pipeline trace.
3. Captured live startup/pipeline extracts before the bounded tail, early and
   late QMP frames, a 12-frame fixture sequence and 20-frame production
   sequence, process counts, and QMP teardown evidence.

### Check

The fixture marker and create result were captured. Its native region was
unchanged in the early frame but reached `41,750/223,200` changed pixels with
bounding box `[501,278,278,162]` in the last video frame. Production emitted
four inputs; the first three returned create result `0`, the fourth did not
emit a completion marker. Production remained at `0/223,200` native pixels
while the HUD changed `1,284/100,000` pixels. Both cases had one
`flutter-auto`, equivalent launch identity, and clean QMP teardown.

The complete hashes and role paths are in the
[FLR-0095 evidence manifest](../evidence/FLR-0095-startup-pipeline-boundary-2026-09-12.md).

### Act

The evidence unit is complete and the ticket is Done. The fourth production
pipeline-create completion is the next runtime boundary, but its cause is not
proven. FLR-0096 is the separate ticket for a bounded GDB/thread/syscall
snapshot while that operation is active; no source or recipe change is made
under FLR-0095.

## Visual evidence

- QMP-only fixture late frame: `$RECEIVER/evidence/flr0095-startup-pipeline/fixture-run/qmp-video/frame-00011.ppm`.
- QMP-only production late frame: `$RECEIVER/evidence/flr0095-startup-pipeline/production-run/qmp-video/frame-00019.ppm`.
- The fixture frame contains a visible native object in the fixed native
  region. The production frame contains no changed native-region pixels while
  the 2D HUD remains visible.
- Hashes, image identity, and teardown are recorded in the linked manifest.
