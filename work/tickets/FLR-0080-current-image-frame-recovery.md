# FLR-0080 — current-image frame recovery for self-made fixture

- Status: Waiting
- Priority: High
- Owner: Mini QEMU runtime + Filament frame-loop roles
- Created: 2026-09-11
- Depends on: [FLR-0079](FLR-0079-reproduce-current-fixture-present-boundary.md), [FLR-0058](FLR-0058-restore-native-frame-loop.md)
- Working log: `work/logs/2026-09-11-flr0080.md`

## Work unit

Test whether the existing diagnostic treatment for an unlinked Filament fence
recovers the current 0208 image's self-made native fixture. Keep the p13 image,
QEMU profile, launch owner, fixture flags, force-render flag, QMP regions, and
teardown constant. Add only `FLR0026_TREAT_UNLINKED_FENCE_READY=1`.

This is a runtime diagnosis. The variable is not a production fix and must not
be promoted without a source-level contract and a real-pixel result.

## Success criteria

- Reuse the fixed Mini build/TMPDIR, rootfs, one-QEMU contract, and one
  compositor owner.
- Prove no pre-existing `flutter-auto`, then prove exactly one fixture PID.
- Record the setup, frame/fence, queue/present, present-boundary, and commit
  markers for control and the one-variable condition.
- Capture QMP-only frames and analyze the native candidate and HUD regions.
- Decide whether the diagnostic restores only frame scheduling or also produces
  recognizable self-made 3D pixels. Keep any failure evidence and negotiate
  QMP teardown with zero residual targets.
- Do not edit source or create a patch in this ticket unless the runtime
  comparison identifies a source-controllable boundary.

## Facts

- The p13 current-image control used the pure fixture, minimal geometry,
  `FLR0026_SYNC_TRACE=1`, and
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`, but did not set
  `FLR0026_TREAT_UNLINKED_FENCE_READY`.
- p13 proved one app process and recorded black QMP frames with
  `VK_QUEUE_PRESENT=3` and `PRESENT_BOUNDARY_DONE=0`.
- Earlier FLR-0058 evidence showed that this diagnostic can restore frame-start
  calls while leaving the QMP production candidate black. The current image
  must be tested separately because its rootfs and patch stack differ.

## Hypotheses

1. **Frame scheduling is the current-image gate.** The ready diagnostic changes
   frame-start/fence markers and restores the self-made cube pixels.
2. **Frame scheduling is upstream but incomplete.** The markers recover, but
   QMP remains black; the next boundary is native draw/resource or surface
   composition.
3. **The diagnostic does not change the current image.** The same fence/present
   boundary remains, indicating an artifact/driver or source execution issue.

## UNKNOWN

- Whether the current 0208 artifact can produce self-made 3D pixels under the
  recovered frame condition.
- Whether any recovered frame loop is safe for production use.

## Plan / Do / Check / Act

### Plan

Run the p13 control profile with one added environment variable, then capture
the same evidence fields and compare only the runtime marker and QMP result.
Use the Mini-side serial/QMP localhost endpoints and the existing evidence
root; do not create another TMPDIR or container.

### Do

- p14 used the fixed current 0208 image and added only
  `FLR0026_TREAT_UNLINKED_FENCE_READY=1` to the p13 runtime profile. The
  prelaunch check found no `flutter-auto`; the launch query found exactly one
  `agl-driver`-owned process.
- The runtime changed from p13's `FRAME_FENCE_WAIT_LINKED linked=false` /
  `FRAME_SKIP_STATUS status=1` to repeated
  `FRAME_FENCE_WAIT_UNLINKED_READY` / `FRAME_SKIP_STATUS status=0`.
- p14 still recorded no `VK_QUEUE_PRESENT`, no `PRESENT_BOUNDARY_DONE`, and no
  `VK_COMMIT_DONE` in the bounded marker scan. The serial summary command's
  completion-status anomaly is preserved; a tail-only command completed and
  recorded the ready markers and repeated `Light not found` messages.
- All five p14 QMP frames were the black SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  Both native candidate `[300,80,620,360]` and HUD `[200,100,400,250]`
  regions were `0` changed pixels. QMP teardown and residual cleanup passed.

### Check

The ready-fence diagnostic changes frame scheduling but does not produce a
queue-present marker or visible pixels in the current pure-fixture profile.
This is FAIL for the self-made 3D pixel criterion and PASS for process, QEMU,
QMP, and cleanup gates. The diagnostic is not a product fix.

### Act

Keep FLR-0080 Waiting and continue in
[FLR-0081](FLR-0081-current-image-minimal-geometry.md), which removes the
pure-fixture scene-content shortcut and tests the existing minimal-geometry
control. Do not patch source from this runtime-only result.

## Visual evidence

Raw frames and runtime logs remain outside Git under
`$QEMU_EVIDENCE_ROOT/flr0080`; record paths, hashes, region counts, selected
markers, and teardown output here after the run.
