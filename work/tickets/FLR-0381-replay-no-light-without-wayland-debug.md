# FLR-0381 — replay no-light Sequoia without Wayland protocol logging

- Status: Done
- Priority: High
- Created: 2026-09-30
- Predecessor: FLR-0378 current-image no-light baseline; FLR-0380 local diagnostic commit `fbed630` on `feature-flr-0380-current-wayland-surface-trace` (not pushed)
- Branch: `feature-flr-0381-replay-no-wayland-debug` (local, no push)
- Working log: [FLR-0381 working log](../logs/2026-09-30-flr0381.md)
- Candidate kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Candidate rootfs SHA-256: `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`
- Candidate qemuboot SHA-256: `8582ac80d4c58fc9e852abed0e6fd6e6077bf6e5f0f7727341033fb405d0a17c`
- Run IDs: `flr0381-0001`, `flr0381-0002`

## Objective

On the exact current candidate, repeat FLR-0380's low-volume manual no-light
Sequoia profile with only `WAYLAND_DEBUG` removed. Capture QMP while the app is
still alive, preserve the app/SSH/timeout exit status, and compare the full
frame and fixed vehicle/HUD regions. This is a controlled runtime A/B for the
all-black FLR-0380 result; it is not product acceptance or a new lighting,
camera, texture, SHM, or semaphore investigation.

## Facts

- FLR-0378 on this rootfs showed an achromatic Sequoia silhouette on a gray
  field, no HUD, and no matched Oops. Its 143,284-line stage trace was enabled,
  and its raw guest log was not retained.
- FLR-0380 on the same candidate recorded Sequoia renderable/material events,
  one successful present return and an unmatched second present. A child
  Wayland surface attached/damaged/committed, yet QMP remained fully black and
  byte-identical to pre-Flutter. The app was absent later, but its wrapper/SSH
  exit status was not saved; no selected Oops/core matched.
- FLR-0380 added `WAYLAND_DEBUG=client` and kept high-volume scene-stage
  tracing off. Therefore FLR-0378 is a visual reference, not a clean one-factor
  control. This ticket pairs directly with FLR-0380 by holding its low-volume
  environment fixed and removing only `WAYLAND_DEBUG`.
- Historical tickets already examined broad SHM bytes/compositor mappings
  (FLR-0207/0214/0215/0219) and Lavapipe present-wait/GDB/semaphore paths
  (FLR-0339/0341/0342/0343/0350/0365/0366/0374). They do not justify repeating
  those probes in this ticket.

## 4W1H (Why excluded)

| Dimension | Current evidence | This run measures |
| --- | --- | --- |
| What | FLR-0380 QMP was all black; FLR-0378 showed a silhouette | Whether removing only client protocol logging restores the FLR-0380 frame or changes the present/exit sequence |
| Where | Mini QEMU, pinned rootfs `949921c…`, Example Demo 3.32.5 | Same image, same app, same no-light Sequoia path |
| When | FLR-0380 first present returned 0; second had no return | Capture at first successful return or first present stall, while the process is live |
| Who | `agl-driver` UID 1001, existing Wayland/compositor session | One manually launched `flutter-auto`; exact process and exit status recorded |
| How | QMP plus existing low-volume model/present traces | Remove `WAYLAND_DEBUG` only; do not alter launch script or other environment controls |

## Hypotheses

1. **Protocol logging changes timing or surface behavior.** Prediction: without
   `WAYLAND_DEBUG`, QMP returns to the gray field/achromatic Sequoia silhouette
   or the present/exit sequence changes. One run establishes correlation only,
   not causality. **Observed:** the one live capture was gray rather than
   FLR-0380's black frame; this is consistent with a difference, not causal
   proof.
2. **The all-black result is independent of `WAYLAND_DEBUG`.** Prediction:
   QMP remains byte-identical black and the unmatched second present recurs.
   **Observed:** the live frame was gray, so the all-black prediction did not
   recur; the unmatched return moved to a third present call.
3. **The result is run-variable or the measurement window is insufficient.**
   Prediction: QMP, present markers, and process state disagree without a
   repeatable pattern. **Observed:** run 0001 still liveness is UNKNOWN, while
   run 0002 produced a stable gray still/video with liveness bracketed; run
   variability is not ruled out.

## Scope and success criteria

- Reuse only the pinned kernel/rootfs/qemuboot, official Mini `runqemu`
  harness, existing 6144 MiB setting, installed bundle, and fixed evidence
  root. Allocate only `$EVIDENCE_ROOT/flr0381-0001/qemu` and
  `$EVIDENCE_ROOT/flr0381-0002/qemu`; the second run was allowed because the
  first still's liveness was not bracketed. Create no additional temp/build/
  TMPDIR and copy no QEMU image to Mac.
- Preflight zero residual QEMU/runqemu/flutter-auto processes, QMP socket and
  forwarded ports, candidate hashes, guest compositor/session, and bundle.
- Manually invoke `/usr/bin/flutter-auto` as `agl-driver` over strict guest
  SSH. Keep FLR-0380's low-volume profile fixed: Sequoia match `sequoia`, model
  limit `2`, skybox/indirect-light/direct-light/shapes suppression, model
  content trace and present trace. Do not set `WAYLAND_DEBUG`, the high-volume
  scene-stage trace, unsupported force-render controls, or any camera/material/
  texture/route override.
- Keep the 45-second automatic bound. Save raw stdout/stderr on Mini and
  explicitly record both the remote app/timeout exit status and the outer SSH
  status. Capture a complete QMP still and eight-frame video at the first
  successful present or first classified stall while the app is live; if no
  such event occurs, capture the bounded final state and mark the liveness
  gate accordingly.
- Score the full 1280×800 frame, vehicle ROI `(0,100,320,310)`, and HUD ROI
  `(960,0,320,120)` separately. Compare against the FLR-0380 black frame and
  FLR-0378 silhouette metrics. Keep raw PPM/logs on Mini and transfer only
  QMP-derived PNG/MP4 review media.
- Stop only the recorded guest app and this QEMU via its owned QMP socket;
  independently verify zero processes, socket, and ports.
- No source, patch, Devtool, BitBake, image, build, persistent runner, or
  launch-script changes.

## Impact

- **Build-time / packaging:** none.
- **Runtime:** two bounded manual runs on the unchanged candidate; the second
  was a repeat because the first lacked capture-time liveness evidence.
- **Integration risk:** no persistent software mutation. A changed result is
  initially timing correlation, not proof that protocol logging is causal.

## Plan / Do / Check / Act

### Plan

1. Confirm canonical repository, sole active ticket, run ID availability,
   helper identity, candidate hashes, and clean Mini/QEMU/guest preflight.
2. Manually launch the exact FLR-0380 low-volume environment with only
   `WAYLAND_DEBUG` absent. Do not edit or add scripts.
3. Save logs and both exit statuses to Mini; capture QMP while the app is live
   at the first return/stall, then capture the eight-frame sequence.
4. Analyze full-frame/vehicle/HUD pixels independently, stop the exact app and
   QEMU, verify teardown, and compare to FLR-0380/0378.

### Do

- Both runs reused the official Mini QEMU harness, but Flutter itself was
  launched manually as `agl-driver`; no persistent launch or capture script
  was edited. The one-off observer for run 0002 captured at the first returned
  present while strict guest SSH confirmed Flutter was alive.
- Run 0001 reached the 45-second bound (status `124`). Its still was gray, but
  capture-time liveness was not bracketed; the later video was black after the
  app had exited. This run alone is not a valid live-render verdict.
- Repeated as run 0002 with the same image/profile. Both live checks passed;
  the QMP still and all eight video frames were uniformly gray. Two present
  calls returned `0`; a third had no captured return. The bounded status was
  `124`.
- Captured complete QMP frames and videos; raw logs/PPMs remain on Mini. See
  [runtime evidence](../evidence/FLR-0381-runtime.md).

### Check

- Run 0002 changed all 1,024,000 pixels from the black pre-Flutter frame, but
  produced zero edges or chromatic pixels. Vehicle and HUD ROIs were uniform;
  all eight live frames matched the still.
- Both stills were gray, but only run 0002 passed the live-capture checks.
  Removing `WAYLAND_DEBUG` therefore correlates with a gray live frame rather
  than FLR-0380's black frame; it did not restore the Sequoia or HUD, and the
  causal explanation remains unknown.
- The live app reached model selection/load planning, 34 renderable records,
  42 material records, and successful present returns. Those markers do not
  prove visible geometry.
- Both QMP sessions were quit through their owned sockets; independent process,
  socket, and forwarded-port checks passed. Run 0001 had no selected Oops/OOM/
  segfault or coredump in its bounded check. Run 0002 kernel/core status was
  not separately collected.

### Act

- Close this diagnostic ticket. Do not change a persistent launcher based on
  a result that is gray and does not meet the visual target. Continue with a
  separate one-variable ticket comparing the already observed scene-stage
  trace condition against this low-volume baseline; keep raw high-volume logs
  on Mini and summarize bounded markers only.
- Do not repeat broad texture-file, camera, light, SHM, or present-wait probes
  without new evidence. This no-light run cannot decide production lighting or
  texture appearance.
- Production colored Sequoia plus the 2D HUD in one QMP frame remains the
  acceptance criterion and is not complete.

## UNKNOWN

- Whether `WAYLAND_DEBUG` or another run-to-run/timing difference explains the
  FLR-0380 all-black frame versus the FLR-0381 live gray frame.
- Why the third queue-present call entered without a captured return before
  the bounded status `124`.
- Run 0001 still-capture liveness; it was not bracketed and remains UNKNOWN.
- Whether production Sequoia and the 2D HUD can appear together in one current
  QMP frame.
