# FLR-0294 — trace FrameSkipper fence status behind beginFrame=false

- Status: Waiting
- Priority: High
- Owner: Filament FrameSkipper / Vulkan fence lifecycle
- Created: 2026-09-25
- Predecessor: [FLR-0293](FLR-0293-inspect-begin-frame-return-path.md)
- Working log: `work/logs/2026-09-25-flr0294.md`

## Objective

Enable the existing `FLR0026_SYNC_TRACE` control on the fixed FLR-0291 runtime
profile and correlate `FrameSkipper::shouldRenderFrame()` status with
`beginFrame` and fence submit markers. Determine whether the false-heavy loop
is an expected fence timeout that never recovers, or a different lifecycle
failure.

No source, recipe, patch, image, or build-directory change is allowed in this
ticket.

## Acceptance gate

One QEMU run must retain:

1. `FLR0026_FRAME_SKIP_STATUS` samples with their status values;
2. fence create/link/submit markers and their bounded counts;
3. `beginFrame` true/false counts and one QMP-only frame with native/HUD ROI;
4. a comparison against FLR-0291 and an explicit classification of whether
   fence status explains the false loop;
5. clean QMP teardown with zero residual targets.

## Facts

- Filament's current `FrameSkipper::shouldRenderFrame()` returns false when
  the oldest delayed fence reports `TIMEOUT_EXPIRED`; otherwise it returns
  true.
- `FRenderer::beginFrame()` calls `makeCurrent()` and then checks the
  FrameSkipper. A false result is not, by itself, proof of Vulkan acquire
  failure.
- FLR-0291 used the same image without `FLR0026_SYNC_TRACE`, so the fence
  status values are currently UNKNOWN.

## Ranked hypotheses

1. **Fence timeout is the direct cause.** The log will show repeated
   `FLR0026_FRAME_SKIP_STATUS status=TIMEOUT_EXPIRED` and no successful fence
   recovery.
2. **Fence status recovers but the caller fails to complete frames.** The log
   will contain `CONDITION_SATISFIED` or `NO_FENCE`, yet QMP remains uniform;
   the next boundary is caller-side frame completion or composition.
3. **The trace itself exposes a different driver error.** Fence markers will
   be absent or report `ERROR`, requiring a separate Vulkan fence ticket.

## Verification plan

- Reuse the fixed Mini receiver, build, TMPDIR, rootfs, and one-QEMU harness.
- Add only `FLR0026_SYNC_TRACE=1` to the existing FLR-0291 environment.
- Save the guest log before teardown, extract bounded marker counts/lines, and
  capture the same native/HUD ROIs and a bounded QMP video.
- Do not change swapchain alpha, light count, camera, surface stacking, or
  source patches.

## Result

- The runtime log shows `status=1` (`TIMEOUT_EXPIRED`) for `8243` samples,
  `status=0` for `2`, and no `ERROR` samples.
- The false-heavy sequence is preceded by
  `FLR0026_FRAME_FENCE_WAIT_LINKED linked=false`; Vulkan acquire itself reports
  `result=0`.
- Five later linked-fence samples show transient recovery, including two
  satisfied results, but the loop does not remain recovered.
- Therefore the ticket classifies the current `beginFrame=false` flood as a
  FrameSkipper/Vulkan fence-lifecycle boundary. It does not yet prove that an
  unlinked fence is the only root cause, and it does not provide a lighting
  conclusion.

## UNKNOWN

- Whether the delayed fence is ever submitted and reaches a signaled state in
  the current diagnostic path.
- Whether the uniform QMP frame is produced by the skipped-frame path or by a
  separate native-surface/compositor condition.

## Plan / Do / Check / Act result

- Plan/Do: completed one fixed-image, one-QEMU sync-trace run.
- Check: the fence timeout and acquire boundary were separated; transient
  linked recovery prevents a stronger root-cause claim.
- Act: move the existing unlinked-fence-ready A/B to FLR-0295. No source,
  recipe, patch, image, or build-directory change was made in FLR-0294.

## Visual evidence

- Evidence root: `/mnt/yocto/evidence/flr0294-0001`.
- QMP frame: `frame-skip.ppm`, SHA-256
  `3a5f5b2e7c9a934083620faaf14bfd52f5ed67c76f964e595c509edd7b67d374`.
- Runtime log: `frame-skip-runtime.log`, SHA-256
  `d0e13fc903bd0b72554f9425231d84dfbf9a76f57979e10041450c7835a866d1`.
- Observed frame: uniform gray native/HUD regions with two chromatic native
  pixels; this frame is diagnostic evidence of the stalled loop, not a light
  acceptance frame.
- QMP teardown: PASS; residual QEMU, runqemu, flutter-auto, and QMP socket
  count was zero.

## Visual evidence

Evidence is retained under the fixed Mini `$EVIDENCE_ROOT/flr0294-0001` role
path. Raw frames/logs remain outside Git; hashes and bounded summaries will be
recorded here after the run.
