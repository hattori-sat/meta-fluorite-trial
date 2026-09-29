# FLR-0109 — isolate the blocked present/WSI owner

- Status: Waiting
- Priority: High
- Owner: Vulkan WSI + runtime-debug + target-validation roles
- Created: 2026-09-12
- Depends on: [FLR-0108](FLR-0108-production-pipeline-gdb-boundary.md), [FLR-0099](FLR-0099-draw-to-native-output-boundary.md)
- Working log: `work/logs/2026-09-12-flr0109.md`

## Work unit

Identify the owner of the first missing return after the production
`vkQueuePresentKHR` enter/begin boundary. Compare production with the existing
same-image fixture positive control using a bounded GDB backtrace and targeted
syscall/fence evidence. Separate the known `FEngine::loop` userspace OOPS from
the present wait before proposing any source change.

## Success criteria

- Read the effective Filament present/WSI patch order and relevant Vulkan
  present source boundary before changing files.
- Capture a bounded production present entry/return or a precise blocked owner,
  including process/thread identity and marker order.
- Compare the result with the fixture's queue-present return and native pixels.
- Preserve QMP-only visual evidence, fixed image identity, and one-QEMU clean
  teardown.
- Classify the first blocked owner as application/Filament, Vulkan loader,
  lavapipe/Mesa, fence/semaphore wait, or compositor/WSI. Do not create a
  source-fix ticket until the violated contract is directly evidenced.

## Hypotheses

1. The application/Filament present worker is blocked or faults before the
   Vulkan WSI call returns.
2. `vkQueuePresentKHR` enters lavapipe/WSI and waits on a semaphore, fence, or
   compositor response.
3. The known OOPS corrupts or interrupts the present path, while a separate
   composition issue keeps the native region black.

## Plan / Do / Check / Act

### Plan

1. Inspect the effective present patches and source ownership.
2. Use one bounded production observation with GDB/syscall timing and the
   fixture evidence as the positive control.
3. Capture QMP pixels, classify the first missing return, and create a new
   source-fix ticket only if the contract violation is proven.

### Do

- Static source/metadata inspection: PASS. The fixed Mini source contains
  `VulkanDriver::commit` → `VulkanSwapChain::present` →
  `VulkanPlatformSurfaceSwapChain::present` → `vkQueuePresentKHR`. Effective
  patches `0182`–`0185` provide outer, queue-return, semaphore, and fence
  markers. Evidence:
  `work/evidence/FLR-0109-static-present-wsi-2026-09-12.md`.
- Bounded present/WSI observation: PARTIAL. GDB loaded the guest debug
  symbols and stopped at `vkQueuePresentKHR` entry. The entry backtrace is
  retained, but the return was not captured because the first probe used a
  `tbreak` from inside a breakpoint command list and resumed the target before
  the remaining commands could run. This is a probe-construction failure,
  not a product diagnosis.
- Corrected callback probe: FAIL as a diagnostic probe. The first command
  file was rejected by the guest harness because its generated GDB settings
  were one physical line. After that input was corrected, GDB loaded symbols
  but ended with `Cannot execute this command while the target is running`;
  the gdbserver then reported an fd error. No callback marker was emitted.
  This is recorded as a separate probe-harness failure, not a product result.
- Normal production run with bounded strace: PASS for the observation
  procedure. The fixed image was started once, one `flutter-auto` process was
  launched, the guest was sampled while running normally, and the process was
  detached before QMP teardown. The initial command used the wrong rootfs
  hash slot and was rejected before QEMU start; the corrected rerun passed
  preflight, guest-ready, and cleanup. No second QEMU or application process
  was left behind.
- Targeted syscall observation: PARTIAL. A 20-second `strace -ff` attach
  covered 39 threads. The bounded command returned `124` by design after the
  observation window and detached cleanly. It recorded active Wayland fd 3
  `sendmsg`/`recvmsg`/`poll` activity with short returns, while selected app
  and worker threads showed repeated futex waits of about five seconds. The
  main thread's `epoll_wait` calls returned immediately in the sample.
- QMP capture and teardown: PASS. Early and late normal-running screens and
  six late frames are retained under the fixed receiver evidence role. The
  HUD changed pixels were `1294/100000` early and `1177/100000` late; the
  native candidate was `0/223200` in both captures and all six late frames
  were byte-identical. QMP quit reported zero residual targets and sockets.
- GDB attach observation: PARTIAL. GDB server attached to the live production
  PID and the client connected successfully. Guest-side symbol loading was
  very slow because the client used the default remote-file path. GDB
  produced an `info threads` view with 19 visible threads and top frames, but
  the subsequent all-thread backtrace did not complete before the run was
  ended. The attached target was kept stopped only for this bounded probe and
  was then terminated through QMP. This is a diagnostic-procedure limitation,
  not a product classification.
- Lightweight GDB retry: PARTIAL/PASS for procedure timing. With
  `sysroot=/`, an explicit debug-file directory, and a five-second remote
  timeout, the client avoided the previous remote symbol-transfer delay and
  enumerated 39 target threads. The bounded `thread apply all bt 6` completed
  quickly, but most non-current threads reported `PC not available` and no
  shared libraries were loaded, so it did not provide a usable owner stack.
  Detach also reported `Couldn't reap LWP ... while detaching`; the target
  did not remain available for a post-detach process check. This is recorded
  as a debugger-procedure limitation, not a product result.
- Launch-under-gdbserver probe: FAIL as a boundary probe. The production
  executable was launched under gdbserver and the GDB client connected, but
  `vkQueuePresentKHR` was unresolved and remained pending. The retained GDB
  output contains `[Detaching after fork from child process 679]`; the
  process that loaded the Vulkan stack was therefore not followed by the
  breakpoint session. No queue-present entry/return or owner stack was
  captured. This is a fork-following/debugger setup failure, not a product
  diagnosis.
- Fork-following retry: FAIL as a present-boundary probe, but PASS for process
  topology. With `follow-fork-mode child` and `detach-on-fork off`, GDB
  followed child PID 678, which immediately exec'd
  `gst-plugin-scanner`; the production parent PID 646 was not the selected
  Vulkan target. The client then reported that a command was issued while the
  target was running. This identifies the child as an auxiliary media probe,
  not the owner of present, and does not classify the product fault.
- Parent-following retry: FAIL as a present-boundary probe. With
  `follow-fork-mode parent` and `detach-on-fork off`, GDB still reported the
  pending `vkQueuePresentKHR` breakpoint and then returned
  `Cannot execute this command while the target is running` after a new
  inferior appeared. The guest retained both a gdbserver-managed parent and
  a second `flutter-auto` process, but no queue-present hit/return was
  captured. This is still a debugger event-handling gap, not a product
  classification.
- Normal process-map run: PASS for PID ownership and QMP procedure. A normal
  production launch had exactly one `flutter-auto` PID (632), and that PID's
  executable maps contained both `libflutter_engine.so` and
  `libvulkan_lvp.so`. QMP captured the normal-running screen before clean
  teardown. The native candidate was `0/223200` and the HUD was
  `1294/100000`; this independently reproduces the current symptom without
  any debugger attached.
- Individual-thread GDB attempt: FAIL as an evidence-collection procedure.
  The normal production PID was started and its map showed
  `libvulkan_lvp.so`; gdbserver and the GDB client were then launched for
  candidate thread stacks. The follow-up serial connection used to collect
  those logs failed at `echo-off-prompt-not-reached`, so no GDB result can be
  classified. QMP teardown still passed with zero residual targets/sockets.
- Individual-thread GDB attempt: FAIL as an evidence-collection procedure.
  The normal production PID was started and its map showed
  `libvulkan_lvp.so`; gdbserver and the GDB client were then launched for
  candidate thread stacks. The follow-up serial connection used to collect
  those logs failed at `echo-off-prompt-not-reached`, so no GDB result can be
  classified. QMP teardown still passed with zero residual targets/sockets.

### Check

- GDB reached `vkQueuePresentKHR` in `libvulkan.so.1` at
  `pc=0x7ffff5fde750`; the stopped thread was the guest `flutter-auto`
  thread whose bounded stack returned through the application and Flutter
  Engine. No `FLR0109_OUTER_ENTRY` or `FLR0109_PLATFORM_ENTRY` marker was
  present in the retained GDB output. Because the probe did not retain the
  breakpoint-resolution report and ended on a target-running error, the
  absence of those two markers is not evidence that either layer was bypassed.
- The first probe therefore proves the loader-level `vkQueuePresentKHR`
  entry only. Queue return, exact caller source line, fence/semaphore state,
  and OOPS relation remain unclassified.
- In the normal production run, the marker order reached successful submit
  returns, `FLUORITE_ENGINE_EXECUTE_ENTER`, `FLUORITE_VK_PRESENT_ENTER`,
  `FLUORITE_VK_PRESENT_FLUSH_DONE`, semaphore wait enabled, and
  `FLUORITE_VK_QUEUE_PRESENT_ENTER`/`FLR0026_VK_QUEUE_PRESENT_BEGIN`. No
  queue-present return was observed in the retained window.
- The present submit returned `result=0` with semaphore
  `0x7f7e50021180`, and the same semaphore was passed into the present path.
  This proves submit success and semaphore handoff, but not that the WSI
  consumed or signaled it correctly.
- The targeted syscall sample recorded `epoll_wait=1811`, `futex=11910`,
  `poll=163`, `recvmsg=102`, and `sendmsg=102` events. The recurring long
  waits were on guest TIDs 640 and 699; the main thread was not held in a
  long `epoll_wait`, and Wayland socket activity returned promptly. This
  weakens the simple “Wayland socket is stuck” hypothesis, but does not
  identify the futex owner or prove that the futex is the present wait.
- The same run logged a known userspace OOPS in guest TID 679 (`FEngine::loop`)
  at `RIP=0x7f7eb96d8541`. TID 679 was distinct from the observed long-futex
  TIDs, so the OOPS and futex observations are concurrent evidence only;
  causality remains UNKNOWN.
- Normal-running QMP evidence: early PPM SHA-256
  `fe470a10e62a22f3eb0af253b0f61260b5270d7ff79b15e19b77e2dc44e02961`, late
  PPM SHA-256
  `25a88c8ce44149eb6a63228efbd125b7aad3e666a1258a88f8b3d5d31da9a0fc`,
  resolution `1280x800`. The native candidate remained black while the HUD
  remained visible.
- The GDB top-frame view showed the main thread in
  `__GI___clock_nanosleep`, an application thread and four `llvmpipe-*`
  threads in glibc futex waits, Flutter I/O threads in `epoll_wait`, one
  Flutter worker in `poll`, and additional Flutter/engine workers in futex
  waits. These are the stopped-time syscall owners visible to GDB; they do
  not identify which thread initiated the missing queue-present return.
- The lightweight retry verified the full GDB thread-name set, including
  `JobSystem::loop`, `FEngine::loop`, `llvmpipe-*`, Flutter I/O, disk, and
  DartWorker threads, but it did not resolve their PCs. Therefore it cannot
  distinguish a present owner from an idle/recovery worker.
- The launch-under probe confirms the production launcher creates or follows
  a child process during startup, but the current GDB defaults detach from
  that child. The active process identity for the Vulkan present boundary is
  therefore still UNKNOWN.
- r7 confirms the relevant fork topology: the child followed by GDB is the
  GStreamer plugin scanner, while the production Flutter parent remains the
  likely Vulkan owner. The next probe must keep the parent selected and use
  fork/exec events only to exclude auxiliary children.
- r8 shows that the parent-following policy does not by itself make a
  multi-inferior `continue` synchronous in this gdbserver setup. The pending
  breakpoint cannot be called resolved until the client has advanced past all
  observed fork/exec stops and confirms the selected inferior's library map.
- r9 removes the PID ambiguity for a normal launch: the sole
  `flutter-auto` process is the Vulkan/Filament owner candidate. The earlier
  multi-inferior state belongs to the launch-under-gdbserver procedure and
  must not be used as the normal process topology.
- r10 proves the selected normal PID can be prepared for attach, but the
  two-session serial collection is not reliable while the target is stopped.
  The absence of a collected backtrace is a harness failure, not evidence of
  a missing present stack.
- r10 proves the selected normal PID can be prepared for attach, but the
  two-session serial collection is not reliable while the target is stopped.
  The absence of a collected backtrace is a harness failure, not evidence of
  a missing present stack.

## Visual evidence

- Early normal-running QMP capture: `$RECEIVER/evidence/flr0109-r3/production-early.ppm`.
- Late normal-running QMP capture: `$RECEIVER/evidence/flr0109-r3/production-late.ppm`.
- Six late QMP frames are retained under
  `$RECEIVER/evidence/flr0109-r3/production-frames/`; all share the late
  capture SHA-256. The capture is from the fixed image and a single normal
  production launch, not from a stopped debugger session.
- Visual result: 2D HUD pixels are present, but the production native 3D
  candidate is unchanged/black in both normal-running captures. This is the
  current production result, not a source-fix conclusion.

### Act

- Keep this ticket In Progress. Replace the failed return probe with a
  debugger callback that installs the caller return breakpoint while the
  inferior is stopped, then captures one bounded entry/return pair. Preserve
  the same fixed image, one-QEMU contract, QMP-only capture, and clean QMP
  teardown. Do not patch present, semaphore, fence, compositor, or scene
  semantics until that pair identifies the violated contract.
- Use the strace result to narrow the next probe: collect a lightweight
  function-level stack for the present caller and the long-futex candidates,
  with symbol-resolution status retained, before changing source. Do not
  treat prompt Wayland IPC alone as proof that compositor presentation is
  healthy, and do not treat the separate OOPS as causal without a matching
  thread/stack/marker correlation.
- Improve the GDB procedure before repeating it: set the guest root as the
  debugger sysroot, keep the debug-file directory explicit, disable automatic
  remote symbol transfer where it is not needed, and first capture
  `info threads` plus bounded top frames. Only load Filament/Vulkan symbols
  after the target thread set is known.
- Treat `sysroot=/` as necessary but insufficient: retain the successful fast
  thread enumeration, then add only the minimum register/stack read needed to
  verify whether gdbserver can expose non-current thread PCs. If a detached
  attach cannot preserve the target, prefer a launch-under-gdbserver probe
  with a bounded stop command and explicit `detach` before collecting the
  normal-running QMP frame.
- Correct the fork policy based on r7: use `follow-fork-mode parent`, keep
  `detach-on-fork off` only if the server remains stable, and continue until
  the parent reports `libvulkan` load/breakpoint resolution. Record the
  scanner child separately and do not use its exec as the production render
  process.
- Add explicit post-fork `continue` handling based on r8: retain the current
  inferior number/PID, issue bounded continues after each fork/exec event, and
  query `info sharedlibrary` only while that inferior is stopped. Do not run
  `bt` or other inspection commands immediately after an event that leaves
  the target running.
- For the next attach, use the PID obtained from the normal process-map
  probe, verify its `/proc/<pid>/maps` contains `libvulkan_lvp.so`, and then
  request only individual candidate-thread stacks. Do not use
  launch-under-gdbserver until the normal attach result is exhausted.
- Run the attach, bounded GDB client, log collection, and final status in one
  serial command session. Keep GDB foreground and use a short timeout so the
  serial prompt is not reacquired while the target is stopped. Treat the
  whole-session return marker as the collection gate.
- Run the attach, bounded GDB client, log collection, and final status in one
  serial command session. Keep GDB foreground and use a short timeout so the
  serial prompt is not reacquired while the target is stopped. Treat the
  whole-session return marker as the collection gate.
- For launch-under-gdbserver, set `follow-fork-mode child` and
  `detach-on-fork off` before `continue`, then retain fork/exec events and
  breakpoint-resolution output. Only classify the queue-present owner after
  the child that loads `libvulkan` remains under GDB.

## UNKNOWN

- The exact blocked thread and operation inside the present/WSI boundary.
- Whether the kernel OOPS is causal or concurrent.
- Whether the fixture and production differ in present semaphore/fence state.
- Whether the outer/platform breakpoints were unresolved or simply not hit in
  the failed probe.
- Whether the recurring futex waits belong to the present operation, a normal
  worker idle path, or a recovery path after the OOPS.
- Whether GDB's 19-thread view was incomplete because of thread creation
  timing or because the slow remote symbol transfer interrupted enumeration.
- Whether the r5 `PC not available` result is a gdbserver/QEMU ptrace
  limitation or a target-state change during attach.
- Which launcher child owns the Vulkan/Filament present path and whether
  gdbserver can keep that child under the breakpoint session.
- Whether the parent-following launch can resolve and stop at
  `vkQueuePresentKHR` before the timeout.
- Whether the two `flutter-auto` processes represent a launcher/renderer split
  or a transient child, and which one loads the Vulkan present library.
- Whether the normal single PID can expose a usable non-current PC when one
  candidate thread is selected individually.
- Whether same-session foreground GDB avoids the r10 serial reconnect failure
  and returns usable candidate-thread PCs.

## r11 debugger-resource failure

- The first r11 start attempt failed before QEMU because the wrong Yocto
  `oe-init-build-env` selected a nonexistent `TEMPLATECONF`; the exact
  runqemu error is retained under `$RECEIVER/evidence/flr0109-r11/`.
- The corrected attempt reused the AGL checkout's `external/poky` environment,
  started one QEMU, reached guest-ready, and launched one normal production
  `flutter-auto` PID 633 with `libvulkan_lvp.so` mapped.
- QMP-only pre-attach evidence is
  `$RECEIVER/evidence/flr0109-r11/production-before-gdb.ppm`, SHA-256
  `b703428e383691143b5d7d792b514ef685ffd006fd2af4c077b17f7076713f15`.
  The native candidate changed `0/223200` pixels; the HUD changed
  `1288/100000` pixels.
- Same-session GDB attach completed log collection, but automatic symbol
  loading caused the 2 GiB/no-swap guest to invoke the OOM killer. The kernel
  log shows `gdb` at roughly 600 MiB RSS and `flutter-auto` at roughly 1 GiB
  RSS; PID 633 was killed. GDB returned `124` and no candidate backtrace is
  usable. This is a debugger-harness failure, not a product diagnosis.
- QMP quit accepted capabilities/quit and cleanup passed with zero residual
  targets and zero residual QMP sockets.
- FLR-0110 owns the low-memory debugger procedure. FLR-0109 remains open for
  present/WSI owner classification after that procedure returns usable data.

## FLR-0110 handoff

- The bounded procedure is now available: verify the normal PID's
  `libvulkan_lvp.so` map, capture QMP, use guest GDB with `sysroot=/` and
  `auto-solib-add off`, request only selected threads, detach, capture QMP,
  and issue QMP quit.
- In the first usable low-memory snapshot, `FEngine::loop`, `llvmpipe-0`, and
  `JobSystem::loop` candidates were all in `__futex_abstimed_wait_common64`;
  the main thread was in `clock_nanosleep`. This does not yet identify the
  missing queue-present owner because the snapshot was not synchronized to a
  present marker.
- FLR-0109 resumes with this procedure. The next observation must correlate
  the selected thread PC with `FLUORITE_VK_QUEUE_PRESENT_ENTER` and the
  missing return before any source patch is proposed.

## r12 synchronized present-owner observation

- The corrected fixed-image run used one QEMU and one normal production
  `flutter-auto` PID 637. The pre-attach QMP frame was
  `$RECEIVER/evidence/flr0109-r12/production-before-sync-gdb.ppm`, SHA-256
  `0f48dbb928e85925f54ca4548e014a879a97e653243248623b44374838f7884a`;
  native candidate pixels were `0/223200` and HUD pixels were `1278/100000`.
- The guest log already contained
  `FLUORITE_VK_QUEUE_PRESENT_ENTER` and
  `FLR0026_VK_QUEUE_PRESENT_BEGIN`, with no queue-present return/done marker.
  The synchronized GDB attach then completed with client RC `0` and detached
  without killing PID 637.
- Deep bounded stacks for FEngine threads 25, 30, 31, 32, and 33 showed
  `pthread_cond_wait` followed by frames in `/usr/lib/libvulkan_lvp.so`.
  The loaded build-id was `18eb7b64f7fcae9a4b5ef5bbe1fe58a65944a403`.
  With the executable map base fixed, targeted symbolization resolved the
  Vulkan frames to Mesa 24.0.7 `cnd_wait` line 136,
  `lvp_pipe_sync_wait_locked` line 179 (with the inlined
  `lvp_pipe_sync_wait` line 234), and `lp_cs_tpool_worker` line 48.
- The UI thread was in `epoll_wait` through `libflutter_engine.so`; the
  selected Wayland/poll thread was in `poll` through `libwayland-client.so`.
  This weakens a simple Flutter UI or Wayland socket owner explanation, but
  does not prove that the lavapipe condition is the violated contract.
- Post-detach QMP remained native `0/223200` and HUD `1266/100000`; its PPM
  SHA-256 was
  `69a1e939ad70611d780cdd4df4eaaa0acc3643c2fb9597fa44d8e5b396abd33b`.
  QMP quit accepted capabilities/quit and cleanup reported zero residual
  targets and zero residual QMP sockets.

### r12 classification

- Owner layer: **lavapipe/Mesa synchronization is the highest-ranked
  candidate**, because multiple FEngine threads are stopped in symbolized
  `lvp_pipe_sync_*`/llvmpipe worker paths after the present-enter marker.
- Contract status: **UNKNOWN**. The snapshot was correlated with the
  present-enter/begin log, but the exact semaphore/command/fence that the Mesa
  condition waits for is not yet identified, and a normal worker wait can have
  the same stack.
- Next: run the pure self-made fixture with the same image/profile, retain its
  queue-present return and native QMP pixels, and compare its Mesa wait stack
  before considering a production-side source change.
- This fixture comparison is split into FLR-0111; FLR-0109 resumes after that
  independent control result is recorded.
