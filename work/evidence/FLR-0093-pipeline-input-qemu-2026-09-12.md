# FLR-0093 — pipeline-input QEMU evidence (2026-09-12)

## Outcome

The authoritative Mini PC image built successfully and the bounded QEMU run
reproduced the current production result: the 2D HUD is visible, while the
native 3D candidate remains black. The new pipeline-input diagnostic did not
change present or fence behavior.

## Fixed inputs

- Canonical layer commit: `a1ff02f50a4f01a9b199fdcf1c75aa433dc562e5`.
- Devtool-generated patch: `0186-diag-trace-effective-Vulkan-pipeline-inputs-devtool.patch`.
- Patch SHA-256: `f49877d34ee60619fd7e01d6f655d848f00b70e9903c65d6d24f5c5745a6b12d`.
- QEMU qemuboot SHA-256: `4a7916d972b1a57fc949c01d2e35c5058fd477960284472b8f55c8a62cd676c3`.
- QEMU kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QEMU rootfs SHA-256: `43bfd433bb9eed2310e1bb862d690a409dc98a80f9fe5aaed09c673c9ec1e26a`.

## Build gates

- Recipe metadata: PASS; the effective `filament-vk` `SRC_URI` contains the
  generated patch.
- `filament-vk:do_patch`: PASS; 104 tasks succeeded.
- `filament-vk:do_compile`: PASS; 1965 tasks were attempted and all
  succeeded.
- `agl-ivi-image-flutter`: PASS; 11748 tasks were attempted and all
  succeeded. The build emitted 17 warnings, including the known static
  library build-path QA warning; no task failed.

## QEMU evidence

All paths below are under `$RECEIVER/evidence/flr0093-pipeline/`.

- `qmp-before-demo.ppm`: QMP-only pre-launch frame,
  SHA-256 `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- `qmp-after-demo.ppm`: QMP-only final frame,
  SHA-256 `a4240ff0a712769e9625707f7bf431421fbcac1b1c0cd90a343bcd4a921046fd`.
- `qmp-video/`: 20 QMP-only PPM frames; frame 19 has the same SHA-256 as the
  final frame.
- `runtime-app.log`: guest application log,
  SHA-256 `e39d0791f84b5c55edbf2ef21ed6813d0580b1eac6ac0f5794f14e95b4808a94`.

The final frame is 1280x800. The native candidate region
`[300,80,620,360]` changed `0/223200` pixels. The HUD region
`[200,100,400,250]` changed `1236/100000` pixels with bounding box
`[200,113,29,66]`.

The runtime emitted six effective pipeline-input records and six successful
create results. The slowest create took `21509378` microseconds; all recorded
create results were `0`. The subsequent frame records remained
`started=false`, and the existing submit/present trace reached the same later
completion boundary observed in the preceding ticket.

Exactly one `agl-driver`-owned `flutter-auto` process existed after launch.
QMP capability negotiation, QMP `quit`, residual-target detection, and QMP
socket cleanup all passed.

## Classification

- 3D display acceptance: FAIL for this production run.
- 2D HUD display: PASS.
- Pipeline-create permanent-stall hypothesis: rejected by the successful
  create results.
- Later fence/present completion boundary: remains the leading next cut.
- Legacy namespace: no new directory, receiver, environment variable, or
  runtime marker was created for the historical namespace. Older strings in
  the guest log are provenance from the installed diagnostic stack and are
  not current naming.
