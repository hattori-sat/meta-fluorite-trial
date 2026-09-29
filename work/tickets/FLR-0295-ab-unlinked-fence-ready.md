# FLR-0295 — A/B unlinked FrameSkipper fence readiness

- Status: Waiting
- Priority: High
- Owner: Filament FrameSkipper / Vulkan fence lifecycle
- Created: 2026-09-25
- Predecessor: [FLR-0294](FLR-0294-trace-frame-skip-fence-status.md)
- Working log: `work/logs/2026-09-25-flr0295.md`

## Objective

Run one one-variable runtime A/B using the existing opt-in
`FLR0026_TREAT_UNLINKED_FENCE_READY=1` control. Determine whether the
unlinked-fence timeout is sufficient to keep `beginFrame` progressing and to
restore the known HUD/native 3D pixels. This is a diagnostic classification
unit, not a product fix.

## Acceptance gate

One fixed-image QEMU run must retain:

1. the exact launch identity and the single added environment variable;
2. bounded counts for unlinked-ready, fence status, beginFrame, submit, and
   present markers;
3. QMP-only frame/video evidence with native and HUD ROI analysis;
4. a comparison with FLR-0294 and a falsifiable decision;
5. clean QMP teardown with zero residual targets.

## Constraints

- No source edit, generated patch, recipe change, image rebuild, or new
  container.
- Reuse the fixed Mini receiver, build, TMPDIR, rootfs, and one-QEMU harness.
- Do not change camera, lights, model, swapchain, compositor ownership, or
  surface stacking.

## Ranked hypotheses

1. If an unlinked fence is the direct gate, treating it as ready will sharply
   increase `beginFrame=true` and restore stable submit/present activity.
2. If the unlinked fence is only a symptom, `beginFrame` may progress but QMP
   will remain uniform or another fence/driver boundary will fail.
3. If the control masks a real ordering defect, frame activity may increase
   while fence status or QMP evidence becomes inconsistent; no product patch
   is justified from that result.

## UNKNOWN

- Whether the existing control is safe beyond diagnosis.
- Whether a stable frame loop is sufficient for production Sequoia pixels.

## Plan / PDCA

- Plan: replay FLR-0294 with exactly one existing opt-in variable.
- Do: collect bounded runtime markers and QMP evidence.
- Check: compare frame-loop progress and pixel evidence against FLR-0294.
- Act: either isolate the next boundary or open a source-fix ticket only if
  the evidence identifies a specific lifecycle defect.

## Visual evidence

Evidence root: `/mnt/yocto/evidence/flr0295-0001`.

- QMP frame: `unlinked-fence-ready.ppm`, SHA-256
  `3a5f5b2e7c9a934083620faaf14bfd52f5ed67c76f964e595c509edd7b67d374`.
- QMP video: `unlinked-fence-ready-video/` (12 frames).
- Runtime log: `unlinked-fence-ready-runtime.log`, SHA-256
  `13b420167e918a9e045f731fe3bb0dcbf1a78b1bef6b493cc78d5394b2b6a2de`.
- Observed: `beginFrame=true=44`, draw submit `44`, present begin `24`,
  present return `23`, but the native ROI remains almost entirely uniform
  `(224,224,224)` and the HUD ROI has zero chromatic pixels.
- QMP teardown: PASS with zero residual QEMU, runqemu, flutter-auto, and QMP
  socket targets.

## Result

- H1 is supported for the frame-loop boundary: treating an unlinked fence as
  ready removes the false-heavy skip loop.
- H2 remains open for the image boundary: submit/present progress does not
  restore the expected pixels.
- H3 is not a product-fix basis: the control is diagnostic and leaves the
  captured image byte-identical to FLR-0294.
