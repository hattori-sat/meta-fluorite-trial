# FLR-0188 — compile and validate the clean 3D runtime image

- Status: Waiting
- Priority: High
- Owner: Mini Yocto build + QEMU runtime evidence role
- Created: 2026-09-15
- Predecessor: [FLR-0187](FLR-0187-rebase-0232-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0188.md`

## Work unit

Build the image from the now-clean `flutter-auto` patch stack, then run the
authoritative QEMU flow and capture bounded runtime logs plus QMP-only screen
evidence. This ticket is the first compile/runtime step after patch-stack
reconciliation; it does not introduce a new source patch.

## Problem

The patch stack previously could not reach compilation because Yocto rejected
0232 patch fuzz. FLR-0187 proved the current-source 0232 patch applies cleanly
on Mini. The remaining question is whether the resulting image boots and
renders the known 2D HUD and the Fluorite 3D candidate in the same runtime.

## Success criteria

- [ ] `flutter-auto:do_compile` passes on the fixed Mini build/TMPDIR.
- [ ] The fixed image build completes without changing the canonical layer.
- [ ] Exactly one intended QEMU/runqemu session is started and old sessions
  are absent before launch.
- [ ] QEMU-only screenshot evidence is captured and tied to the image hash.
- [ ] Runtime facts separate 2D HUD, 3D geometry, light/material, and camera
  visibility; no 3D claim is made from logs alone.
- [ ] All processes are torn down and the result is recorded with bounded
  logs, hashes, and explicit UNKNOWN values.

## Facts

- Canonical layer commit: `44c88ec1fe69506f561ad09330da05d788eef187`.
- FLR-0187 Mini patch gate: `evidence/FLR-0187/patch-gate-flutter-auto.summary`.
- The full patch stack through 0232 applies cleanly on Mini.
- Mini `flutter-auto:do_compile` failed at `filament_view_plugin.cc` and
  `scene_text_deserializer.cc` before an image build. Evidence summary:
  `evidence/FLR-0188/compile-flutter-auto.summary`.
- The first compile failure is stale API usage from active 0235/0236 patches:
  `vInitSystems`, `vRouteMessage`, and `GetStrand` do not exist in the current
  `ECSManager`; 0235 also references an undeclared `camera_`.
- Raw compile task log:
  `/mnt/yocto/flr0023-tmp-835a04e-selfinstall/work/corei7-64-agl-linux/flutter-auto/2.0/temp/log.do_compile.3267076`.
- After FLR-0189 retired the two obsolete active registrations, Mini
  `flutter-auto:do_patch` and `do_compile` both passed at receiver
  `44c88ec1fe69506f561ad09330da05d788eef187`.
- The fixed build directory and TMPDIR are the existing Mini roles documented
  in the environment workflow; no new build or TMPDIR is allowed.
- Mini full image build succeeded: 11,758 tasks attempted and all succeeded;
  the bounded build output is outside Git at
  `/mnt/yocto/flourite-receivers/flr0023-835a04e/evidence/FLR-0188/image-build.output`.
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
  VMDK rootfs SHA-256:
  `9990669c644c50e267c129fe76230a5df3e3ccbf5badca6e38b7e5125aaa1f86`.
- QEMU run 1 used WIC.xz. `runqemu` warned that `xz` was unsupported and the
  QMP frame remained the SeaBIOS/iPXE boot screen; this run is invalid for
  app/3D classification and was stopped with QMP `quit`.
- QEMU run 2 used WIC.VMDK. QMP capture succeeded at 1280x800, but the frame
  was still SeaBIOS/iPXE, the serial boot file stayed empty, and the forwarded
  SSH port did not provide an SSH banner. QMP teardown and residual cleanup
  passed.
- Run-2 QMP frame SHA-256:
  `9ade205a6fcf5bc04d8f88e0a976077e4af9e590eadae2216a136b487a13ad9b`.
  The fixed candidate region `[300,250,620,400]` had 1,327 grayscale pixels
  and 0 chromatic pixels; these are boot-frame pixels, not 3D evidence.
- QEMU run 3 used the historical direct `bzImage` + `.ext4` profile. Serial
  reached the AGL login prompt, SSH reached the guest, and
  `/run/user/1001/wayland-0` existed for `agl-driver`.
- Run 3 launched the packaged Example Demo as `agl-driver`. The bounded
  runtime log reached Application Id, Wayland/Vulkan initialization, AOT load,
  camera parsing, and `All systems initialized`, then aborted with
  `std::runtime_error: value must be a EncodableList (name: baseColor,
  type: COLOR)` before the first application frame.
- Run-3 QMP frame evidence is retained at the Mini evidence directory as
  `qemu/frame-ext4-app-early.ppm`; it is 1280x800 and uniformly black in the
  fixed candidate region. This is not 3D evidence because the app had already
  aborted at material deserialization.
- Run 3 QMP teardown passed with `residual_targets=0` and
  `residual_qmp=0`.

## Inferences

- Compilation is now a valid next gate because the patch application boundary
  is clean.
- The patch boundary is clean but the compile boundary proves the active
  patch stack contains stale source API assumptions. This is a patch-stack
  reconciliation problem, not yet a runtime or QMP problem.
- The corrected stack now passes the Mini compile gate; image build and QEMU
  evidence are the remaining gates.
- The `.ext4` direct profile is the valid current runtime path; the earlier
  WIC.xz/VMDK firmware frames were invalid launch profiles, not application
  evidence.
- The current image reaches the application but fails before the first frame
  at the Dart/native material wire-format boundary. This is an application
  initialization failure, not yet a surface-composition or lighting result.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: the current Dart/native MaterialParameter contract is mismatched | current Dart sends a string while native requires EncodableList | final source shows both sides use the same representation |
| H2: fixing the wire format reaches the prior 2D HUD path | app remains alive after material deserialization and QMP shows HUD pixels | app aborts at a later initialization boundary |
| H3: 3D geometry and lighting are later boundaries | post-fix QMP separates HUD, geometry, and light/material pixels | app remains black or crashes before the first frame |

## 4W1H (Why excluded)

| Dimension | Record |
| --- | --- |
| What | Compile and validate the first image after a clean patch stack |
| Where | fixed Mini build/TMPDIR and QEMU runtime |
| When | after FLR-0187 clean `do_patch` |
| Who | Mini build role, QEMU runtime role, evidence role |
| How | compile → image → one QEMU session → bounded logs/QMP screenshot → teardown |

## PDCA

### Plan

1. Verify receiver tip, build configuration, and absence of stale QEMU/BitBake
   processes.
2. Run recipe-scoped compile and then the minimum image build required by the
   existing runqemu flow.
3. Launch one QEMU session, capture QMP-only screenshot evidence, and select
   only the bounded diagnostics needed to classify 2D/3D/light/camera.
4. Tear down the session and record the image/build hashes before deciding the
   next source ticket.

### Do

- Ticket opened after FLR-0187 cleanly reached the compile boundary.

### Check

- Process preflight and receiver identity are PASS.
- `do_compile` is FAIL: the C++ compiler rejects stale 0235/0236 API names and
  the undeclared `camera_` fixture field. No image or QEMU run was started.
- The corrected stack now passes Mini `do_patch` and `do_compile`; continue
  with the image build and QMP-only runtime evidence.

### Act

- The valid `.ext4` profile closed the QEMU boot boundary and exposed a new
  source/API unit. FLR-0190 owns the MaterialParameter COLOR contract; do not
  modify the 3D composition or lighting code until this crash is removed.

## Current boundary

- Compile and image generation are PASS.
- QEMU guest boot, SSH, Wayland, Vulkan initialization, and app launch are
  PASS under the `.ext4` direct profile.
- Material deserialization aborts before the first frame because Dart sends a
  hex string while native COLOR handling requires an `EncodableList`.
- 2D HUD, 3D geometry, light/material output, and camera visibility remain
  UNKNOWN until the app survives initialization.

## UNKNOWN

- Whether the corrected material wire format restores a live app is UNKNOWN.
- Whether 2D and 3D can be observed together in the current image is UNKNOWN.
- Whether light/material/camera visibility is fixed is UNKNOWN.
