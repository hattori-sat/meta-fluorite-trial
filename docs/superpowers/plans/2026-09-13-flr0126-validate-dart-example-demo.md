# Plan: validate the Dart Example Demo after the ViewTarget fix

## Goal

Use the already-built FLR-0125 image to test the normal Dart Example Demo
without native-fixture environment variables. Prove or falsify that the
ordered ViewTarget delivery fix is shared by the Dart path.

## Constraints

- Reuse the fixed Mini receiver, build, TMPDIR, QEMU harness, and evidence
  root. Do not create a new build/TMPDIR/container.
- Start exactly one QEMU and one `flutter-auto` process.
- Use QMP framebuffer captures as the visual authority.
- No source edit or patch generation before runtime evidence identifies a
  source-controlled defect.

## Steps

1. Confirm the fixed receiver is clean at canonical commit `f0406dae`, no QEMU
   target remains, and the existing rootfs hash is unchanged.
2. Launch the normal Example Demo bundle as `agl-driver` with the native
   fixture variables removed.
3. Collect application identity, camera/shape/present markers, channel errors,
   coredump state, and one-process status.
4. Capture early and late QMP framebuffer images and analyze the fixed region
   `[300,250,620,400]`.
5. Capture a short QMP frame sample if the normal Dart path is positive.
6. Quit through QMP, verify zero residual targets/sockets, and record the
   result in FLR-0126.

## Decision gate

- QMP-positive Dart result: shared native path is supported; open a new ticket
  for camera/input or production scene transitions.
- QMP-negative Dart result: use marker order to select the first Dart/native
  boundary; do not infer a compositor or lighting defect.
