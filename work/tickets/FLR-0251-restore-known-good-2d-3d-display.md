# FLR-0251 — restore the known-good simultaneous 2D HUD and native 3D display

- Status: Done
- Priority: High
- Owner: Flutter/Wayland composition and native fixture visibility
- Created: 2026-09-21
- Predecessor: [FLR-0249](FLR-0249-fix-readiness-method-channel-registration.md)

## Objective

Restore the previously proven same-frame 2D HUD plus self-made native 3D cube
on the exact FLR-0249 image, then use that stable control to resume the
production Planetarium/Sequoia scene investigation.

## Facts

- The known-good FLR-0248 QMP frame has HUD `2883` chromatic pixels and native
  fixture `100800` chromatic pixels; its SHA-256 is
  `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.
- The FLR-0249 production QMP frames are byte-identical with SHA-256
  `2097d8f3aa89cb4083d5414e2636bbd9cf88d6a261844a2d8b9a947554376311` and
  uniformly `RGB 224,224,224`.
- The FLR-0249 fixture-mode QMP frame has SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`;
  full-frame analysis finds HUD pixels only and zero chromatic pixels in the
  native fixture ROI.
- FLR-0249 readiness markers pass in the same guest:
  `FLR0249_READINESS_START_AFTER_PLATFORM_VIEW`,
  `FLR0247_READINESS_READY`, and
  `FLR0247_READINESS_CALLBACK_DISPATCHED`.
- The same run recorded native Vulkan render/present activity, but no
  `FLR0248_NATIVE_CALL_RECEIVED` or `FLR0248_NATIVE_CALL_RESPONDED` marker.
- QEMU teardown passed with `residual_targets=0 residual_qmp=0`.

## Inferences

- FLR-0249 fixed the Dart readiness reachability boundary, but it did not
  preserve the previously proven visible composition.
- The display regression is below the readiness success marker and above the
  final QMP frame; it must not be treated as proof that production geometry,
  camera, or light is wrong.

## Hypotheses

1. Removing the `initState` readiness start changed Flutter PlatformView/frame
   scheduling even though the deferred call reaches `READY`.
2. The current QEMU/image display profile differs from the known-good runtime,
   although the QMP harness and guest render markers are active.
3. Native draw/present succeeds but the Wayland/Flutter composition surface is
   not visible in the final parent frame.

## Verification plan

- Compare the exact `0081` source delta with the known-good source state.
- Run one minimal official Devtool A/B that preserves idempotent readiness while
  measuring the same HUD/native ROIs.
- Require one QMP frame with both HUD and native fixture chromatic pixels
  before reopening production scene/camera/light work.
- Keep production Planetarium/Sequoia visibility as a separate follow-up
  criterion; do not infer it from the fixture.

## Do — official A/B patch

- The fixed Mac Podman source Git created an A/B branch from the existing
  `88324284058b89b1bfce230636e8329ac4eab246` source commit and a revert commit
  `14ac959fb35f9659cf4777107c3e8906c90f3409`.
- The source was registered at `8832428` with official
  `devtool modify --no-extract`, advanced to `14ac959`, and processed by
  official `devtool update-recipe` and `finish-source`.
- Canonical patch:
  `0082-flr0251-revert-readiness-scheduling-ab-devtool.patch`
- Canonical patch SHA-256:
  `3adbc5b38736b12f236990e0bb3c3bdfe6cc805ab0f656b55e1e443e613dc0c6`
- The generated diff is byte-for-byte the inverse of 0081; no hand-authored
  patch was used.

## Evidence

- FLR-0249 runtime root: `$EVIDENCE_ROOT/FLR-0249/qemu/`
- Mac-visible QMP screenshot: `/private/tmp/flr0249-qmp/settled.png`
- Known-good comparison screenshot: `/private/tmp/flr0249-qmp/flr0248-initial.png`

## Check — authoritative Mini A/B result

- Bundle receiver tip: `f852c497f2d5c4b7586b20b372b5dd1c89c3b93d`.
- Mini `do_patch` passed, target `do_compile` passed (`1674/1674`), and the
  full `agl-ivi-image-flutter` build passed (`11758/11758`).
- The fixed QEMU harness passed preflight, guest-ready, and one-time
  `flutter-auto` launch. The QMP-only evidence is under
  `$EVIDENCE_ROOT/FLR-0251/qemu-ab/`.
- QMP `initial.ppm` and `settled.ppm` are byte-identical to the known-good
  FLR-0248 frame: SHA-256
  `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.
- Native fixture ROI `460,260,360,280`: `100800` chromatic pixels,
  `geometry_indicator=present`, edge bounding box `[545,335,190,175]`.
- HUD ROI `1120,0,160,80`: `2883` chromatic pixels,
  `geometry_indicator=present`, bounding box `[1157,24,99,32]`.
- The settled-vs-initial full-frame comparison changed `0` pixels.
- Readiness evidence still contains the expected historical two initial
  `MissingPluginException` results and later bounded timeout records; this
  control run is a display-restoration A/B, not a claim that production
  readiness is complete.
- QEMU teardown passed `qmp=PASS` and `cleanup=PASS residual_targets=0
  residual_qmp=0`.
- Mac-visible QMP screenshot: `/private/tmp/flr0251-qmp/settled.png`.

## Conclusion

The official Devtool reverse patch restores the previously proven simultaneous
2D HUD and self-made native 3D cube on the FLR-0249 build path. This isolates
the regression to the FLR-0249 readiness-scheduling change (or its associated
frame scheduling effect), rather than a general Vulkan, native draw, or QMP
capture failure. Production Planetarium/Sequoia 3D geometry, camera, light,
and route behavior remain UNKNOWN and are handed to a separate follow-up.
