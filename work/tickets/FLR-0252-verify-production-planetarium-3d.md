# FLR-0252 — verify production Planetarium/Sequoia 3D visibility

- Status: Done
- Priority: High
- Owner: Flutter route, Planetarium scene, camera, light, and composition
- Created: 2026-09-21
- Predecessor: [FLR-0251](FLR-0251-restore-known-good-2d-3d-display.md)

## Objective

Starting from the restored FLR-0251 control image, prove whether the
production Planetarium/Sequoia route renders visible 3D geometry, then
separate scene construction, camera/light setup, and Flutter/Wayland
composition failures with QMP evidence.

## Facts

- FLR-0251 restores the self-made native cube and 2D HUD in the same QMP
  frame, so the base Vulkan/native fixture path is proven.
- Production Planetarium/Sequoia pixels have not yet been proven on the
  restored control image.
- FLR-0235 through FLR-0246 established that route/button experiments can
  whiten the HUD while native fixture pixels remain visible; those are
  historical controls, not proof of production geometry.
- The official FLR-0252 Devtool patch `0083` restores the production payload
  (`poGetModelList`, `poGetScenesShapes`, and `poGetScenesCameras`) after the
  FLR-0251 fixture control. Mini `do_patch`, `do_compile`, and the full
  `agl-ivi-image-flutter` build all passed.
- In the current no-readback native-display run, QMP captured a 2D HUD ROI
  with `2883` chromatic pixels, while the production ROI
  `[200,100,400,250]` had only `116` grayscale edge pixels and `0`
  chromatic pixels. Initial, settled, and post-input frames were byte-
  identical with PPM SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- QMP pointer input reached the Flutter surface (`wl_surface@14`) at
  `(1189.96,39.99)` and was accepted by QEMU, but no Scenes/Planetarium
  route marker or menu-frame change appeared. The same runtime slice contains
  repeated `FLR0248_DART_CALL_TIMEOUT` records.
- QEMU teardown passed through the serial stop command and QMP quit with
  `residual_targets=0` and `residual_qmp=0`.

## Hypotheses

1. The production route is mounted but its camera/light/material/asset state
   produces no visible geometry.
2. The production scene is rendered to a surface that is not composed into the
   parent frame after route transition.
3. The route transition or readiness callbacks alter frame scheduling even
   though the native control remains visible.

## Verification plan

- Use the FLR-0251 image and fixed QEMU harness as the baseline.
- Capture a control QMP frame before input, then one frame after the Scenes
  action and after Planetarium/Sequoia readiness markers.
- Use the same HUD/native ROI analysis plus a production-scene ROI; do not
  infer geometry from logs alone.
- Collect only bounded markers for route transition, scene setup, camera,
  light, draw/present, and composition; record UNKNOWN when a marker is
  absent.
- Keep any code change as a separate official Mac Devtool patch and repeat
  the Mini bundle, do_patch, compile, image, QMP, and cleanup gates.

## Next action

Run the current e876 control image without the diagnostic fixture or readback
bridge. Capture QMP before and after the Scenes input, then compare the HUD,
native control, and production Planetarium/Sequoia ROIs with bounded route,
camera, light, draw, present, and composition markers. Do not patch until the
first missing production boundary is evidenced.

## Iteration 1 — production payload and QMP route boundary (2026-09-21)

### Verification record

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Official patch/build | `do_patch`, compile, image pass | Mini gates all passed for `0083` | PASS |
| 2D HUD | HUD/CPU area visible in QMP | `2883` chromatic HUD pixels | PASS |
| Production 3D | non-black/chromatic Sequoia ROI | `0` chromatic pixels; only `116` grayscale edge pixels | FAIL / not observed |
| QMP input reachability | pointer reaches Flutter surface | `wl_pointer.enter`/`motion` on `wl_surface@14` | PASS |

## Closure — Run 0294 production baseline (2026-09-24)

The current e876 no-readback baseline reached production asset-ready,
model-selection, Scene-add, draw-submit, and queue-present markers, but the
guest OOM killer terminated `flutter-auto` before a stable production frame or
Scenes input could be tested. The initial QMP frame showed the HUD and a
transient colored production ROI; the settled frame became white/black and is
not valid 3D evidence. The independent fixture/readback diagnostic is not
active in this run.

This verification unit is closed as a runtime-health classification. The OOM
and production asset/Scene ownership investigation is split to
[FLR-0272](FLR-0272-diagnose-production-asset-loading-oom.md).
| Scenes route transition | menu or route frame changes | all five input frames byte-identical; no route marker | FAIL / first boundary pending |
| Teardown | no QEMU residue | `residual_targets=0`, `residual_qmp=0` | PASS |

Evidence is under the fixed Mini receiver at
`evidence/FLR-0252/qemu-production/`, including `input/`,
`production-log-slice.output`, `runtime-slice.output`, and the QMP hashes.

### Inference

The QMP coordinates and Wayland pointer delivery are not the first failing
boundary in this run. The repeated Dart call timeouts are a stronger lead for
why the Flutter route does not react. This is an inference, not yet a root
cause.

### UNKNOWN

- Which Dart/native call owns the first timeout and whether it blocks the UI
  isolate or only the readiness probe.
- Whether the production GLB stage is stalled before resource upload or the
  native surface is producing transparent/black pixels after upload.

## Iteration 2 — production runtime wait-state probe (2026-09-21)

### Verification record

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| GDB attach | production `flutter-auto` remains inspectable | attach passed; 38 threads captured | PASS |
| Native/engine activity | a renderer or asset-loader thread identifies the stop | Vulkan queue, Filament engine, and llvmpipe workers are alive; one `flutter-auto` thread waits in libc++ `future` state | PARTIAL |
| Debug symbols | application frames resolve to source | system/Mesa/LLVM symbols loaded; `/usr/bin/flutter-auto` has no debug file and application frames remain `???` | FAIL / limited |
| QMP display | current runtime frame is reproducible | `gdb-settled.ppm` hash `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`; HUD `2845` chromatic pixels; production ROI `0` chromatic pixels | PASS for reproduction / 3D FAIL |
| Teardown | no QEMU residue | QMP quit accepted; harness reported `residual_targets=0`, `residual_qmp=0` | PASS |

Evidence is under the fixed Mini receiver at
`evidence/FLR-0252/qemu-production-gdb/`, with the QMP image,
`gdb-snapshot.output`, `symbol-probe.output`, and cleanup result.

### Facts

- Thread 23 is blocked in `std::__1::__assoc_sub_state::wait` in libc++
  `future.cpp`; its application frames are not symbolized.
- The static Mac Devtool source contains a blocking `scriptFuture.wait()` at
  the end of `ViewTarget::DrawFrame`, after the render/present calls, and the
  Dart `FrameEventChannel` awaits `drainFrameTasks()` before replying to the
  native `preRenderFrame` call.
- This is a source-to-stack correlation, not yet proof that thread 23 is that
  exact future. The production application binary has no matching debug info.
- The QMP image visibly contains the 2D HUD and Scenes button, while the
  central production area remains black.

### Inference

The current strongest boundary is a native↔Dart frame-event completion wait,
not the QMP pointer coordinate and not yet a camera/light-only defect. The
production asset stage and composition remain downstream UNKNOWN until this
wait is either completed or bypassed in a controlled A/B.

### Competing hypotheses

1. `preRenderFrame`/`drainFrameTasks()` leaves the native future unresolved;
   prediction: removing only the blocking wait or making its completion
   bounded allows repeated draw/model-stage markers.
2. Production asset loading stalls independently of frame-event completion;
   prediction: the native frame boundary continues to repeat while model
   stage markers stop before resource upload.
3. Wayland composition hides an otherwise completed production frame;
   prediction: draw/present and model-stage markers complete repeatedly while
   QMP production pixels remain black.

### UNKNOWN

- Exact owner of the unresolved future because the shipped
  `/usr/bin/flutter-auto` lacks application debug symbols.
- Whether the first future wait blocks before or after the Sequoia resource
  upload in this image.
- Whether a bounded frame-event A/B alone restores production 3D.
