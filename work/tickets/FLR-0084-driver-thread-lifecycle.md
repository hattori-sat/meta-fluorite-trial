# FLR-0084 — trace the current driver-thread lifecycle

- Status: Done
- Priority: High
- Owner: Filament Engine thread + command-queue runtime roles
- Created: 2026-09-11
- Depends on: [FLR-0083](FLR-0083-current-image-command-stream-boundary.md), [FLR-0058](FLR-0058-restore-native-frame-loop.md)
- Working log: `work/logs/2026-09-11-flr0084.md`

## Work unit

Use the official Mac Devtool source workflow to add the smallest opt-in
diagnostic around `FEngine::loop()`, driver readiness/barrier, and the entrance
and return of `FEngine::execute()`/`waitForCommands()`. The goal is to explain
why p17 flushes 62 command buffers while the queue consumer emits no marker.

This is a diagnostic patch only. It must remain disabled by default and must
not change frame scheduling, fence semantics, or production rendering.

## Success criteria

- Refresh or verify the Devtool source against the effective current recipe
  before editing; do not generate a patch from an unrecorded stale tree.
- Edit the source through the persistent Mac Devtool source tree, create the
  official Devtool patch, and register only that patch in
  `meta-fluorite-trial`.
- Mini PC verifies `do_patch`, component compile, and the full image before
  QEMU.
- One bounded QEMU run with the new opt-in flag distinguishes thread start,
  barrier, wait entry/return, and engine execute.
- No 3D success claim is made unless QMP contains recognizable current-image
  pixels; retain all failed evidence and clean teardown.

## Facts

- p17 proves producer-side `CommandBufferQueue::flush()` but no consumer-side
  `waitForCommands()`/`FEngine::execute()` marker.
- `FEngine::loop()` starts the driver thread, creates the driver, latches the
  readiness barrier, and then loops over `execute()`.
- The existing 0158 patch traces only after `waitForCommands()` returns, so it
  cannot distinguish “never entered wait” from “blocked before return”.

## Hypotheses

1. The driver thread does not reach the loop after driver creation/barrier.
2. The driver thread reaches `execute()` but blocks before or inside
   `waitForCommands()`.
3. The trace path is bypassed by an alternate engine/Filament binary. Prediction:
   the new source marker is absent even though the current binary contains the
   existing queue markers.

## UNKNOWN

- Whether the missing consumer is a thread-start/barrier issue, a queue wait
  entry issue, or an alternate binary/instance.
- Whether the runtime can recover without a product code change after the
  boundary is observed.

## Plan / Do / Check / Act

### Plan

Refresh the source with the official persistent Devtool workflow, make one
opt-in marker patch, register it in the layer, bundle the local commit to the
Mini, and use the existing progressive build and QMP harness.

### Do

- The first bundle handoff attempt used a non-existent remote inbox and was
  retained as a process failure; no receiver checkout was changed by that
  failed copy.
- After confirming the existing fixed inbox, the active bundle was handed off
  successfully and the Mini receiver reached the exact `fbda119` revision.
- Two consecutive bounded Podman status probes passed while reusing one
  machine, one container, and the existing project/AGL/state binds.

### Check

- The first Mini `filament-vk:do_patch` attempt failed at existing patch `0158`:
  three of four hunks in `CommandBufferQueue.cpp` and one of two hunks in
  `Engine.cpp` rejected after the initial lifecycle patch was applied. The
  failure was caused by overlapping patch context, not by an invalid BitBake
  recipe parse.
- Inspection showed that the initial Devtool source commit had been made on a
  tree with old diagnostic changes already applied. Its generated patch
  therefore reintroduced legacy `FLR0026_COMMAND_QUEUE_TRACE` additions and
  competed with `0158`; this path is rejected and is not reused.
- A clean source branch was created from the verified Filament source head.
  The lifecycle changes were re-applied without legacy markers, committed in
  the Devtool-managed source, and finished through official `devtool finish
  --mode patch`. The final registered layer files are
  `0180-filament-driver-lifecycle-trace-devtool.patch` and
  `0181-filament-command-queue-lifecycle-trace-devtool.patch`; these new
  outputs add only `FLUORITE_*` controls and contain no new `FLR0026` marker.
- Mac Podman `recipe-task filament-vk do_patch` then passed: all 104 tasks
  succeeded with two warnings after the two official patches were appended to
  the effective existing recipe patch series. The authoritative Mini
  `do_patch`, component compile, full image, and QEMU runtime evidence remain
  UNKNOWN until the committed layer is handed off.
- Do not patch fence readiness or compositor stacking in this unit.

### Act

Commit the corrected layer and evidence, bundle that commit to the fixed Mini
receiver, rerun metadata and `filament-vk:do_patch`, then compile the
component. Use the observed lifecycle boundary to create the next independent
runtime or product-fix ticket only after the corrected patch is proven. Keep
all new diagnostic controls opt-in.

## Final runtime result

- The authoritative Mini gates passed for the committed source: Filament
  `do_patch` 104/104, Filament compile 1965/1965, and the full
  `agl-ivi-image-flutter` image 11748/11748. The QEMU image used below has
  kernel SHA-256
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74` and
  rootfs SHA-256
  `b1e61009458f8b79d98c09eafab222d96d6e314a0953db1b284560bbd194a494`.
- The fixed QEMU run directory was
  `/mnt/yocto/flourite-receivers/evidence/flr0084-14ca78c`, with preflight,
  start, guest-ready, explicit bundle launch, QMP capture, and QMP teardown
  all passing. The app was launched once as `agl-driver` from the installed
  bundle whose `config.toml` declares `app_id = "fluorite"`.
- The new markers proved the complete driver lifecycle:
  `FLUORITE_ENGINE_LOOP_ENTER=1`, `DRIVER_CREATED=1`, `BARRIER_RELEASED=1`,
  `EXECUTE_ENTER=2`, `QUEUE_WAIT_ENTER=2`, and `EXECUTE_AFTER_WAIT=2`.
  This falsifies the hypothesis that the driver thread never starts or never
  returns from its first queue wait.
- The same log reached two `VK_QUEUE_SUBMIT_DONE` events and one
  `VK_QUEUE_PRESENT_BEGIN`, but no present-boundary completion marker. The
  QMP-only frame `qmp-lifecycle-late.ppm` is 1280x800 with SHA-256
  `09bb56a3ffc6052fb16628274ecafab919836d9c560f4defd6079acd110a883a`.
  Its native candidate `[300,80,620,360]` changed `0/223200` pixels, while
  the HUD region `[200,100,400,250]` changed `1284/100000` pixels.
- Visual inspection shows the Fluorite HUD, FPS, Frametime, CPU/GPU/Script
  metrics, Scenes button, and lower controls. No 3D object is visible; no 3D
  success claim is made.
- A root GDB backtrace was retained as `gdb-backtrace-lifecycle.txt` with
  SHA-256
  `45aac97a5aa78bd160d8ebeb59b1268e7ca20ade7f6fccd2a6f22212a9487487`.
  The relevant `FEngine::loop` activity remained alive in llvmpipe/Vulkan
  condition-variable frames. This supports a present-side wait hypothesis but
  does not prove the exact semaphore or Wayland cause.
- QMP `quit` reported `quit=accepted`; the harness reported
  `residual_targets=0` and `residual_qmp=0`, and a follow-up process check
  found no QEMU or QMP socket.

## Act

FLR-0084 is complete as the driver-thread lifecycle diagnosis. The remaining
problem is split into [FLR-0086](FLR-0086-present-call-boundary.md), which
will isolate the `vkQueuePresentKHR` to Wayland completion boundary with new
neutral `FLUORITE_*` diagnostics before considering a behavior change.
