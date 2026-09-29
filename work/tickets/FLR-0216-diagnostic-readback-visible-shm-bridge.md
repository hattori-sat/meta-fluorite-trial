# FLR-0216 — prove native readback through the visible SHM path

- Status: Done
- Priority: High
- Owner: Fluorite ViewTarget diagnostic role
- Created: 2026-09-20
- Predecessor: [FLR-0215](FLR-0215-trace-native-surface-compositor-visibility.md)

## Work unit

Create the smallest opt-in diagnostic path that copies the actual Filament
native swapchain readback into the already-proven visible SHM child surface.
Use the official Devtool source lifecycle from the current effective source
HEAD, then validate Mac patch generation, layer registration, Mini bundle,
Mini `do_patch`, image build, and QMP pixels.

This is a discriminator only. It must not be presented as the final native WSI
composition fix.

## Success criteria

- Existing fixed Podman machine/container, source tree, receiver, build, TMPDIR,
  and QEMU harness are reused.
- The source edit is committed in the Devtool source tree before
  `devtool update-recipe`.
- Exactly one official patch is generated from the current effective source
  history and registered under `meta-fluorite-trial`.
- Mini `do_patch` and the smallest required build gates pass.
- With the opt-in diagnostic enabled, QMP shows chromatic pixels in the SHM
  region whose bytes originate from the native readback.
- The native-only control remains recorded separately so the result cannot be
  confused with a native WSI fix.

## Hypotheses

1. The same RGB-positive bytes will be visible when delivered through the
   proven SHM compositor path; this isolates native WSI surface selection as
   the failing boundary.
2. If the SHM bridge is also black, the readback bytes are not suitable for
   the visible SHM format/orientation, and format conversion becomes the next
   narrow diagnostic.

## Facts

- The source edit was made from Devtool source HEAD
  `1da4a54ba445cdbcf1b0f177c17f354dbb6cf0fb`, committed before
  `update-recipe`.
- Official generated patch SHA-256:
  `4e06e86b622e3cbf87b05491ea0eb40f63ca09da51f6c742128ae48f96240582`.
- Layer commit and Mini receiver tip:
  `3cf59b2d5142d6b77b7db97accc69d283843f577`.
- Bundle handoff SHA-256:
  `776f3fcd7b65162151bcd607df1cbb5c68142f83837d216d6bc454971b848c82`.
- Mini `flutter-auto:do_patch`, `do_compile`, and full image all passed.
- QMP self-made SHM cube control frame SHA-256:
  `bb535413dcb084b3e31b8582f9b3c4551991a43261800b1c2cc05794b881a1f7`.
  Its cube ROI had `chromatic_pixels=24178` and visible three-face geometry;
  the HUD/Scenes ROI had `chromatic_pixels=2801`.
- Native-only QMP A/B frame SHA-256 remained
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`;
  its native ROI had `changed_pixels=0` and `chromatic_pixels=0`, while HUD
  remained visible.
- With the bridge enabled, the readback callback reported all
  `921600` pixels non-zero and the publish marker reported all `100800`
  SHM pixels non-zero but `chromatic_pixels=0`. QMP then showed a uniform
  `224,224,224` top surface, not 3D geometry. Bridge frame SHA-256:
  `a4ffc7bb0f07ccbc213989a8874f2a80755d84d808f3b85e39fdc10c68056bbb`.
- The first bridge launch also recorded `registry_failed`; after compositor
  stabilization and a retry, `wl_shm` was enumerated and publishing succeeded.

## Plan / Do / Check / Act

### Plan

Add an opt-in readback-to-SHM copy and republish the existing SHM buffer, then
run one bounded QMP test.

### Do

- Added the opt-in `FLUORITE_NATIVE_READBACK_TO_SHM` path through the repaired
  Devtool source history.
- Generated the patch officially, registered it as `0270`, handed off the
  bundle, and passed Mini `do_patch`, `do_compile`, and image build.
- Ran three bounded QMP A/B states in one QEMU: bridge initialization failure,
  bridge publish, and SHM-only control.

### Check

- PASS: the existing SHM compositor path displays the self-made three-face
  cube and 2D HUD in QMP.
- PASS: native-only remains black in the same image and QEMU instance.
- PASS: the bridge changes QMP composition, proving the SHM surface is live,
  but its source data is uniform white and not a 3D shape.
- PASS: exact guest app PID and QMP teardown left zero residual targets.
- FAIL for the discriminator's intended criterion: actual native readback
  geometry was not transferred; the callback data was uniform.

### Act

Close FLR-0216 as a diagnostic result. Open FLR-0217 to reconcile the
uniform-white readback payload with the native-only black QMP frame and the
earlier RGB-positive mapping evidence. Keep `0270` opt-in and do not call it a
native WSI fix.

## UNKNOWN

- Whether RGBA readback byte order matches the guest's `XRGB8888` SHM format.
- Whether the callback is reading a cleared/placeholder image rather than the
  presented native image.
