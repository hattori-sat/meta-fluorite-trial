# FLR-0100 — identify the non-returning Vulkan present call

- Status: Done
- Priority: High
- Owner: Fluorite runtime evidence / Vulkan queue-present execution
- Created: 2026-09-12
- Depends on: [FLR-0099](FLR-0099-draw-to-native-output-boundary.md)
- Working log: `work/logs/2026-09-12-flr0100.md`

## Work unit

Identify which production thread, semaphore wait, software-Vulkan operation,
or kernel wait prevents `vkQueuePresentKHR` from returning after the recovered
production scene reaches a visible swapchain target draw. Use the fixed image
and runtime evidence first. A source patch is out of scope until the blocked
operation is proven.

The current work uses the canonical repository, fixed Mini receiver, fixed
build/TMPDIR, and neutral ticket/evidence names. Historical marker names in
the deployed image are read-only instrumentation; no new legacy namespace
directory, receiver, TMPDIR, control, or marker may be created.

## Success criteria

- One bounded recovered-production runtime run captures the exact process
  identity, thread backtraces, and syscall timing around the present boundary.
- The positive fixture and recovered production are compared with the same
  image and QMP-only evidence contract where practical.
- The blocked operation is identified, or the gap is explicitly recorded as
  UNKNOWN with the next smallest observation seam.
- No source patch or production behavior change is claimed from a backtrace
  alone; the evidence is mapped to the existing Filament source seam.
- QMP teardown, residual checks, selected logs, hashes, and any failed
  invocation evidence are recorded.

## Out of scope

- No new synchronization, semaphore, present, Wayland, alpha, light, or
  material fix by assumption.
- No concurrent QEMU, new TMPDIR, new receiver, cache deletion, or global kill.
- No reuse of the historical initial 3D ticket as the working record.

## Facts

- FLR-0099 fixture returned from `vkQueuePresentKHR` with `result=0` and
  changed `41,750/223,200` native candidate pixels.
- FLR-0099 recovered production reached a visible swapchain draw record and
  `FLUORITE_VK_QUEUE_PRESENT_ENTER wait=true`, but no queue-present return,
  outer present return, or present-done marker appeared; native pixels stayed
  `0/223,200`.
- Both cases reported one `flutter-auto` process and one compositor process,
  and both QEMU instances were cleanly stopped through QMP.
- The first bounded GDB invocation collected a 48,350-byte all-thread output,
  but the harness did not observe its completion marker within the serial
  window. The GDB process itself exited with `GDB_RC=0`; this is a collection
  failure, not a runtime conclusion.
- The corrected retry reached `FLUORITE_VK_PRESENT_ENTER`,
  `FLUORITE_VK_PRESENT_CALL_BEGIN`,
  `FLUORITE_VK_QUEUE_PRESENT_ENTER wait=true`, and
  `FLR0026_VK_QUEUE_PRESENT_BEGIN`, then the guest reported:
  `BUG: unable to handle page fault for address: 00000000d8a41750`,
  `CPU: 1 PID: 680 Comm: FEngine::loop`,
  `RIP: 0033:0x7f753fde4541`, and
  `CR2: 00000000d8a41750`. No queue-present return or serial completion
  marker followed.
- On the same authoritative rootfs, Mini `nm -D` places
  `llvm::CmpInst::isOrdered` in `/usr/lib/libLLVM.so.18.1` at offset
  `0xb1d540`; the retry RIP arithmetic gives a plausible mapping base and
  the fault location is offset `0xb1d541`.
- FLR-0030 directly captured the same library/symbol boundary with
  `/proc/<pid>/maps` and `eu-addr2line`; the current retry therefore
  reproduces the previously mapped fault pattern, although the current
  retry did not retain its own `/proc/<pid>/maps` snapshot.
- Retry QMP evidence retained before/early frames, and QMP teardown reported
  `capabilities=negotiated quit=accepted` plus
  `cleanup=PASS residual_targets=0 residual_qmp=0`.

## Inferences

- The next useful observation is runtime ownership of the non-returning call,
  not another target-extent or scene-state marker.
- A process-wide backtrace and bounded syscall timing can distinguish a
  userspace Vulkan wait from a kernel/device wait without changing behavior.
- The missing `vkQueuePresentKHR` return is a symptom of the guest process
  fault, not evidence that QMP capture, Wayland composition, or the QMP socket
  swallowed a successful return.
- The guest kernel is reporting a userspace fault (`Comm: FEngine::loop` and
  user-space RIP), not a kernel-space page fault. The symbol mapping is strong
  because FLR-0030 directly mapped the same offset, but it does not prove that
  `isOrdered` is the original producer of corrupted control flow or state.

## Hypotheses

1. Production is waiting on an unsignaled submission/present semaphore.
   Prediction: the present caller is blocked in Vulkan/llvmpipe synchronization
   and syscall timing shows a wait or poll that does not complete.
2. Production is blocked inside software-Vulkan command execution or target
   transition before the queue-present return. Prediction: the owning thread's
   backtrace points to llvmpipe/Mesa/Vulkan work rather than a semaphore wait.
3. The marker collection window misses a delayed return. Prediction: a longer
   bounded observation returns from present and QMP native pixels change.

## UNKNOWN

- The exact current-run `/proc/<pid>/maps` base and a successful stop-on-fault
  backtrace captured before the guest serial connection dropped.
- Whether the fault is caused by a production model/material/light/pipeline
  input, resource lifetime, or another state corruption before present.
- The exact producer of the invalid control-flow or stack state; the symbol
  location is an ownership boundary, not a root-cause proof.

## Plan / Do / Check / Act

### Plan

1. Verify the canonical state, fixed image identity, and zero residual target
   processes.
2. Run recovered production once with the existing ready condition and the
   smallest neutral marker set; capture QMP before/early/late.
3. During the present-boundary window, collect bounded `gdb` all-thread
   backtraces and `strace -f -tt -T` timing for the single `flutter-auto` PID.
4. Compare the stack/syscall evidence with FLR-0099's fixture/production
   marker order and decide whether a minimal Mac Devtool observation or fix
   ticket is justified.

### Do

1. Verified the fixed image and ran one bounded recovered-production capture.
2. The first GDB capture failed the harness completion-marker contract because
   its all-thread output was larger than the serial window; its output and
   `GDB_RC=0` were retained as a failed collection attempt.
3. A follow-up invocation initially used a malformed local extraction command;
   it changed no Mini/QEMU state and was not used as runtime evidence.
4. Re-ran with marker polling and captured the guest Oops, the present-entry
   marker order, the current-rootfs `nm` symbol offset, QMP before/early
   frames, and QMP teardown.

### Check

PASS for the boundary: the current image faults in `FEngine::loop` after
queue-present entry and before the return marker; the fault is consistent
with the already directly mapped `libLLVM.so.18.1` / `isOrdered` boundary.
The production native region remained zero in the bounded capture. QMP quit
and residual-process cleanup passed. The exact producer and current-run
backtrace remain UNKNOWN, so no source or present-semantics fix is claimed.

Evidence and hashes are recorded in
`work/evidence/FLR-0100-present-return-boundary-2026-09-12.md` and the fixed
Mini evidence roots:

- `$RECEIVER/evidence/flr0100-present-return/production/`
- `$RECEIVER/evidence/flr0100-present-return/retry/`

### Act

Close FLR-0100 as the present-return/fault-boundary evidence unit. Open
[FLR-0101](FLR-0101-isolate-libllvm-fault-trigger.md) for a one-variable
runtime A/B using the already deployed diagnostic controls. Do not generate a
source patch until that A/B identifies the smallest production input or state
seam. Keep the historical namespace read-only; it is not a current directory,
receiver, environment, or evidence naming convention.
