# FLR-0364 — reproduce Flutter launch over guest SSH

- Status: Done
- Priority: High
- Owner: Mini QEMU / guest SSH / Flutter runtime / QMP evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Predecessor: [FLR-0363 guest-script staging](FLR-0363-fix-flr0350-guest-script-stage.md)
- Working log: [FLR-0364 working log](../logs/2026-09-29-flr0364.md)
- Historical controls: [FLR-0237 guest-SSH recovery](../logs/2026-09-20-flr0237.md), [FLR-0211 Example Demo launch](../logs/2026-09-20-flr0211.md), [FLR-0116 production launch](../logs/2026-09-13-flr0116.md)
- Run ID: `flr0364-0001` (used; never retry)

## Objective

Boot the already-built, pinned QEMU image on the Mini, connect to the guest over SSH, and manually launch the installed Fluorite Example Demo as `agl-driver`. Capture a complete post-launch QMP frame and short frame sequence, then determine whether the app launched and whether its 2D HUD and 3D content are visible together. This is a runtime reproduction, not a harness repair or product change.

## Facts

- The latest FLR-0363 automated attempt reached guest-ready but stopped while staging a helper, before Flutter launch. Its black QMP frame was pre-launch and says nothing about current 2D/3D rendering.
- FLR-0237 records that serial login initially misidentified the guest prompt; direct guest SSH then launched Flutter and produced the valid same-frame 2D+3D baseline.
- FLR-0211 records the installed Example Demo launched once as `agl-driver` with `flutter-auto -b`, one process, and native present markers.
- The FLR-0363 wrapper's `guest_run` constructs `$run_dir/$file`, then falls back to `$parent/$file`. Its new call supplies an absolute path, so its path contract is still inconsistent. That runner is intentionally not used for this manual trial.
- The previous QEMU attempt was torn down with zero residual QEMU, runqemu, Flutter, or QMP targets; recheck before starting this fresh run.
- The installed Example Demo bundle recorded by prior runtime commands is `/usr/share/flutter/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/3.38.3/release`.

## Problem stratification — 4W1H (Why excluded)

| Dimension | Current evidence | Discriminator |
| --- | --- | --- |
| What | Recent run never launched Flutter; visible state is unknown | Verify guest process, bounded app log, and post-launch pixels |
| Where | Guest app startup over forwarded SSH, then the QMP display | Start from the guest's own SSH shell, not serial prompt parsing |
| When | After pinned QEMU guest-ready and before cleanup | One fresh run ID; capture only after launch identity is proven |
| Who | Mini runtime operator, guest session, agl-driver app process | Record role/UID/PID and keep a single app instance |
| How | Inspect first, launch the installed bundle once, then observe QMP | No diagnostic overrides or helper runner in this trial |

## Hypotheses

1. **Historical-path hypothesis:** direct guest SSH and one agl-driver launch starts the app; QMP shows the HUD and may reproduce the historical HUD+3D frame.
2. **Runtime/render hypothesis:** the process starts and emits Flutter/scene/frame markers, but the current image shows only HUD or incomplete/black 3D. This would be a real post-launch observation, unlike the pre-launch black frame.
3. **Startup hypothesis:** SSH succeeds but the app exits or fails before frame activity. Process identity, bounded app log, and targeted system/coredump evidence will distinguish this from a rendering result.

## Scope

### In scope

- One fresh pinned-image QEMU session and direct SSH to its guest.
- Read-only prelaunch checks for app count, bundle availability, and Wayland socket.
- One manual Example Demo launch as agl-driver; bounded process/log checks.
- Full-frame QMP screenshot plus a short QMP frame sequence/video; pixel and visual classification; exact cleanup.

### Out of scope

- Editing the shell runner, adding automation, or modifying Flutter/Filament/Yocto recipes.
- Rebuilding the image, Devtool operations, diagnostic environment overrides, or changing camera/light/material.
- Treating QEMU boot or a prelaunch screenshot as application/render evidence.
- Reusing this run ID, launching a second QEMU/app, or copying QEMU disk images to the Mac.

## Success criteria

1. The pinned QEMU image reaches guest-ready with no pre-existing QEMU/runqemu/flutter-auto process or occupied QMP/SSH port.
2. Guest SSH succeeds. Before launch, the installed bundle and Wayland socket exist and the guest has zero flutter-auto instances.
3. Exactly one agl-driver-owned `/usr/bin/flutter-auto -b` process is launched; PID/UID/command line and a bounded startup log are retained.
4. Capture a complete post-launch QMP-only still and short frame sequence. Inspect the whole image, not just a crop.
5. Report HUD CPU/FPS/Scenes and native 3D geometry/color separately. Credit simultaneous 2D+3D only if both are present in the same frame.
6. If app frame/present evidence exists but 3D is absent, record that as the next renderer boundary; do not label the prelaunch failure as a regression or assume lighting is the cause.
7. Stop the app by its recorded PID, quit QEMU through its recorded QMP socket, and verify zero residual processes/sockets. Preserve logs, image/video, dimensions, and hashes.

## Impact

- **Build-time:** none; reuse the pinned existing image.
- **Packaging:** none.
- **Runtime:** one isolated QEMU session and one guest app process.
- **Integration risk:** low; no source, recipe, or harness changes.

## Plan / Do / Check / Act

### Plan

- Read historical guest-SSH evidence and the installed launch contract.
- Start QEMU through the existing pinned-image helper only; bypass the failed Flutter runner.
- Inspect guest state, launch once over SSH, collect bounded logs and post-launch QMP evidence, then clean up.

### Do

- Pending. Do not modify the runner before the manual path is measured.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Pinned QEMU and guest SSH | One guest, SSH ready | QEMU helper PASS; guest host key pinned in run-scoped file; strict SSH PASS | PASS |
| Prelaunch app/session state | Zero app instances; bundle and Wayland socket present | zero flutter-auto; bundle and Wayland socket present | PASS |
| Manual launch and runtime markers | One agl-driver process; bounded log captured | PID 695, UID 1001, count 1; 102124-byte raw log saved | PASS |
| Post-launch QMP image/video | Full frame and short sequence after launch | 1280x800 still and eight frames; all eight frames identical | PASS |
| Same-frame 2D + 3D | Both HUD and colored native content visible | No HUD; no chromatic pixels; one large monochrome polygon is not identifiable as Sequoia | FAIL |
| Teardown | QMP quit and residual counts zero | app stopped by recorded PID; QMP quit accepted; residual processes, sockets, and ports zero | PASS |

### Act

- Only after the manual path is proven, derive any runner changes from the observed successful command and its measured preconditions. If direct SSH exposes a product/runtime issue, open a separate ticket for that single boundary.

## Evidence

- Mini evidence root: `$EVIDENCE_ROOT/flr0364-0001/qemu`
- Pinned rootfs SHA-256: `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`; QEMU helper preflight verified the exact image.
- Prelaunch QMP PPM SHA-256: `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- Post-launch QMP PPM SHA-256: `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`. Post-GDB frame hash was identical.
- Full guest log: 102124 bytes, SHA-256 `516ea25280664eb1174c91e2dfd4120fdf6e03153773e394f711f5d0beb8998e`.
- Bounded QMP video: 1280x800, 8 frames, 2.0 seconds at 4 fps; SHA-256 `b3c7a3360229ec09b89b0a9b88533ff53b70452bfbc75418164714691314af2a`. All 8 source frame hashes are identical.
- Selected runtime marker slice SHA-256: `733f0f6b5ae6aad1a66dac646714761cfb94e3d6df68b36a22085c47d2d68ce9`. GDB 38-thread short backtrace SHA-256: `44f7739012085c5e3eea554f78cec3cfec0bfca240a19365f5c65ee88998cc55`.
- Local review artifacts are retained under `$LOCAL_REVIEW_DIR` as `FLR0364-post-launch.png` and `FLR0364-post-launch.mp4`. The still was visually inspected as a full QMP frame; no QEMU disk image was copied.

## Result

- The manually launched app was alive and produced scene/light-order updates and Vulkan present activity, so this was not a QEMU-only or pre-launch observation.
- The post-launch frame changed from all-black prelaunch to a white field with a large black polygon. It contained no CPU/FPS/Scenes HUD and no chromatic pixels (full-frame `chromatic_pixels=0`, `max_chroma=4`). The polygon edges are measurable, but shape identity and actual Sequoia geometry are UNKNOWN.
- Runtime log counts were two `FLR0026_VK_QUEUE_PRESENT_BEGIN` markers and one `FLR0026_VK_QUEUE_PRESENT result=0` marker. The second begin has no matching result in the captured log; GDB did not expose a symbolized `vkQueuePresentKHR` stack. Treat a stalled second present as a hypothesis, not a confirmed root cause.
- No coredump was listed. The only relevant recent system record was an SELinux `execmem` audit with `permissive=1`; causality is not established.
- FLR-0347 used the same pinned FLR-0335 rootfs and showed a visible HUD while the lower production 3D ROI was black. That run used the historical diagnostic launch profile, including `--xdg-shell-app-id fluorite --width 1280 --height 800` and diagnostic environment variables. This run used only the bundle and Wayland session variables. The launch-profile difference is the next discriminator; no product fix is justified by this ticket alone.
- FLR-0237's 2D+native baseline was a fixture/native-ROI composition result, not proof that production Sequoia and HUD were simultaneously accepted. Its rootfs hash also differs from this run.
- Execution/teardown criteria are complete; the visual acceptance criterion failed. The overall Fluorite 2D+3D goal remains open. Do not change the runner until a separate manual launch-profile test establishes the working command.
