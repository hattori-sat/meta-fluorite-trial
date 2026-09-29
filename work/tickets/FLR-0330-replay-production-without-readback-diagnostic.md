# FLR-0330 — replay production control without readback diagnostic

- Status: Done
- Priority: High
- Owner: production Sequoia render/present path versus readback diagnostic
- Created: 2026-09-25
- Predecessor: [FLR-0329](FLR-0329-classify-readback-fence-timeout.md)
- Working log: `work/logs/2026-09-25-flr0330.md`

## Objective

Determine whether the native readback diagnostic itself changes the production
QMP result. Reuse the fixed production UNLIT control and remove only
`FLUORITE_NATIVE_SWAPCHAIN_READBACK`. Do not change Light, camera, material,
Scene ownership, Wayland stacking, or route behavior.

## Success criteria

- Same fixed rootfs, build, TMPDIR, QEMU profile, and memory are reused.
- The launch command differs from FLR-0326 only by omission of the native
  readback environment variable and its readback-only markers.
- QMP full-frame evidence is saved before ROI analysis.
- Native ROI, HUD ROI, app liveness, and selected draw/present markers are
  recorded.
- QMP teardown leaves zero target processes and zero QMP sockets.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0329 proves the readback fence returns `VK_TIMEOUT` under the bounded
  diagnostic timeout, while the QMP native ROI is uniformly black.
- The historical colored Sequoia image and FLR-0070 QMP frame remain separate
  static/resource and runtime references; neither is replaced by this A/B.

### Hypotheses

1. Readback is only an observer: removing it leaves the same HUD-only/native-
   black frame, so the visible 3D fault is elsewhere.
2. Readback changes queue progress or target state: removing it restores
   visible native 3D pixels, making the diagnostic path causally relevant.

### UNKNOWN

- Whether the current production UNLIT draw reaches visible QMP pixels without
  the readback observer.

## Result

- One fixed-image QMP run omitted `FLUORITE_NATIVE_SWAPCHAIN_READBACK` and
  kept the production UNLIT override and all other controls unchanged.
- Runtime remained alive as one `flutter-auto` process and reached the
  fixed-color replacement, Scene additions, repeated `beginFrame=true`, and
  draw submit markers.
- QMP full-frame PPM:
  `/mnt/yocto/evidence/flr0330-0001/qemu/qmp-0330-no-readback-full.ppm`,
  SHA-256
  `2f6ebf7a7d8c422eed8c55224d273eea7234c3f3229bb9906a3839cc4bc03b98`.
  Native ROI `(440,220,400,360)` is uniform black (`0/144000` chromatic);
  HUD ROI is positive (`2845` chromatic).
- Bounded serial output:
  `/mnt/yocto/evidence/flr0330-0001/qemu/serial-0330-no-readback.output`,
  SHA-256
  `0f29298e31eec7586c5f0fb78294d1baaee46a31198ec41d25fe4c0231c515be`.
- QMP teardown passed with `residual_targets=0` and `residual_qmp=0`.

Readback is therefore classified as an observational failure, not the cause
of the current black native QMP region. The next boundary is the native
Wayland surface attach/commit/composition path.

## Plan / PDCA

1. Commit and bundle the one-line no-readback launch control.
2. Run one QEMU pass, capture the full QMP frame first, and analyze fixed ROIs.
3. Classify readback as causal or observational and open a separate source
   ticket only if a source change is justified.

## Stop conditions

- Do not interpret a no-readback black frame as a Light diagnosis.
- Do not patch the fence or remove diagnostics permanently before this A/B is
  recorded.
