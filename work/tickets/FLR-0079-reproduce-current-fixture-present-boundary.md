# FLR-0079 — reproduce current-image forced-fixture present boundary

- Status: Waiting
- Priority: High
- Owner: Mini QEMU runtime + Flutter/Wayland boundary roles
- Created: 2026-09-11
- Depends on: [FLR-0078](FLR-0078-isolate-light-scene-attachment-boundary.md), [FLR-0042](FLR-0042-trace-render-frame-present-boundary.md)
- Working log: `work/logs/2026-09-11-flr0079.md`

## Work unit

Reproduce the historical self-made native Filament cube control on the current
0208 image with the complete forced-frame profile, then identify the first
runtime boundary that differs. This is a control-path ticket: it must be
resolved before the explicit-light Scene-add A/B in FLR-0078 is interpreted.

## Success criteria

- Use the fixed Mini image, build/TMPDIR, QEMU profile, and one-QEMU contract.
- Launch `/usr/bin/flutter-auto` as `agl-driver` and prove its PID before any
  pixel verdict.
- Use `FLR0026_NATIVE_PURE_FIXTURE=1`,
  `FLR0026_NATIVE_MINIMAL_GEOMETRY=1`, `FLR0026_SYNC_TRACE=1`, and
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`.
- Capture QMP-only frames and analyze the native candidate and HUD regions.
- Correlate `FRAME`, queue submit/present, present-boundary, Wayland commit, and
  frame-skip markers. Preserve failed runs and clean QMP teardown.
- Classify the first missing boundary as runtime launch, frame-loop/fence,
  present/Wayland composition, or UNKNOWN. Do not change product source until
  the first divergence is evidenced.

## Facts

- Historical FLR-0026 fixture evidence rendered a self-made blue cube with
  QMP PPM SHA-256
  `9294659aeb9743c8d36d3076ec70161ce6a3f2b6d77a2b05e77674db1df73471` and
  candidate region `15212/100000`, bbox `[291,139,138,122]`.
- FLR-0042 independently recorded a visible self-made cube and completed
  present/Wayland evidence on an earlier fixed image.
- The current 0208 image identity is rootfs SHA-256
  `92c656e4cfca05f69f25429569bcc2700192240d163cb8bee0d5b60db77a5445`.
- The Mini QEMU harness runs on the Mini PC: its `localhost` serial, SSH, and
  QMP endpoints must never be probed from the Mac host directly.

## Ranked hypotheses and falsifiers

1. **The current fixture reaches queue present but not the present boundary.**
   Prediction: forced-frame markers and queue-present count are nonzero, while
   `PRESENT_BOUNDARY_DONE` remains zero and QMP remains black.
2. **The fixture app is not attached to the expected Wayland surface.**
   Prediction: the PID exists but surface creation/commit markers or the HUD
   are absent; a correctly attached surface changes QMP pixels without source
   changes.
3. **The current image differs from the historical fixture at an unrecorded
   artifact/profile boundary.** Prediction: a provenance/profile comparison
   finds a different rootfs, qemuboot, launch environment, or patch stack before
   the runtime marker divergence.

## UNKNOWN

- Whether the current black fixture is caused by the current 0208 image,
  frame/fence state, Wayland surface composition, or an artifact/profile
  difference.
- Whether the historical combined HUD+Sequoia frame can be reproduced with a
  complete artifact identity and a non-trace side effect.

## Plan / Do / Check / Act

### Plan

Run one bounded control loop from preflight through QMP teardown. Keep raw
frames/logs outside Git and record only selected markers, hashes, and region
statistics in this ticket and its working log.

### Do

- p10: QEMU start, guest-ready, and serial-login passed, but a serial reconnect
  was attempted from the wrong host context; no app PID was proven. Five QMP
  frames were retained as a black control with SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- p11: a Mini-side persistent serial connection launched the app and the guest
  query proved two `flutter-auto` processes owned by `agl-driver`. The fixture
  reached `NATIVE_PURE_FIXTURE_SETUP_DONE`, Wayland surface creation, and
  `NATIVE_MINIMAL_GEOMETRY_READY vertices=8 indices=36`.
- p11 QMP early and late frames were all the same black PPM. Candidate region
  `[300,80,620,360]` was `0/223200`; HUD region `[200,100,400,250]` was
  `0/100000`.
- p11 selected runtime counts were `VK_QUEUE_PRESENT=3`,
  `PRESENT_BOUNDARY_DONE=0`, `FRAME_FORCED_AFTER_SKIP=1073`,
  `FRAME_SKIP_STATUS=1076`. QMP quit and residual cleanup both passed.
- p12 live-verified the committed `serial-exec` mode on the Mini: command
  output and `command_status=0` were captured, the forced fixture was launched,
  and the captured process query proved an `agl-driver`-owned `flutter-auto`
  PID. QMP early/late frames were again black with the same SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- p12 selected runtime counts were `VK_QUEUE_PRESENT=3`,
  `PRESENT_BOUNDARY_DONE=0`, `FRAME_FORCED_AFTER_SKIP=427`,
  `FRAME_SKIP_STATUS=429`, and `NATIVE_MINIMAL_GEOMETRY_READY=1`. QMP quit
  and residual cleanup both passed.
- p13 passed the fixed preflight, start, guest-ready, and serial gates. The
  prelaunch process query recorded no existing `flutter-auto`; after launch,
  exactly one `agl-driver`-owned `flutter-auto` PID was recorded. This
  falsifies duplicate app launch for this run.
- p13 recorded `VK_QUEUE_PRESENT=3`, `PRESENT_BOUNDARY_DONE=0`,
  `FRAME_FORCED_AFTER_SKIP=542`, `FRAME_SKIP_STATUS=544`,
  `FRAME_FENCE_WAIT_LINKED=542`, `FRAME_FENCE_WAIT_RESULT=0`,
  `VK_COMMIT_BEGIN=2`, and `VK_COMMIT_DONE=1`. The bounded runtime tail
  repeatedly showed `FRAME_FENCE_WAIT_LINKED linked=false` and
  `FRAME_SKIP_STATUS status=1` before forced-frame and renderer enqueue
  markers. `Light not found` messages were also observed and remain
  unclassified.
- The first p13 full-log summary command timed out before its serial completion
  marker because it scanned a growing guest log. Its partial output is
  retained; a tail-only follow-up completed successfully. This is recorded as
  an evidence-command failure, not as a rendering failure.
- p13 QMP early/late five-frame captures were all the same black PPM with
  SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  The native candidate region `[300,80,620,360]` and HUD region
  `[200,100,400,250]` were both `0` changed pixels. QMP quit and residual
  cleanup passed.

### Check

The current control is FAIL for visible fixture pixels and PASS for the
single-app process gate, fixture setup, serial output capture, QMP capture, and
teardown. The p13 runtime evidence narrows the first observed divergence to a
repeated unlinked fence/status path before the present boundary, but does not
yet prove whether the cause is the current artifact/profile, the fence/commit
implementation, or Wayland composition. This is not yet evidence against
FLR-0078's source patch because the control itself did not reach the historical
visible-pixel boundary.

### Act

The p13 control classifies the first observed divergence as the current
frame/fence-to-present boundary: the app and geometry start, queue-present
markers appear, but the repeated unlinked fence/status path does not reach the
present boundary. This is a runtime classification, not a product root-cause
claim, because the same `linked=false` pattern appears in earlier production
black runs. Keep this ticket Waiting and continue in the independent
one-variable frame-recovery ticket [FLR-0080](FLR-0080-current-image-frame-recovery.md).

## Visual evidence

- Raw p10/p11 QMP frames remain on the Mini under
  `$QEMU_EVIDENCE_ROOT/flr0078/p10` and `p11`.
- p13 raw QMP frames remain on the Mini under
  `$QEMU_EVIDENCE_ROOT/flr0079/p13/frames`; all five have the same SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- p13 runtime outputs remain under `$QEMU_EVIDENCE_ROOT/flr0079/p13`,
  including the preserved full-summary timeout output and the successful
  tail-only marker capture.
- p10 and p11 final QMP frame SHA-256:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- The image is explicitly classified as black control evidence, not as a
  successful or failed production 3D rendering claim.
