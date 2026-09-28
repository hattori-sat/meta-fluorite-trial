# FLR-0339 — capture the production Vulkan present-stall stack

- Status: Done
- Priority: High
- Owner: production FEngine / Vulkan WSI runtime diagnosis roles
- Created: 2026-09-28
- Predecessor: [FLR-0338](FLR-0338-capture-isordered-offset-context.md)
- Working log: `work/logs/2026-09-28-flr0339.md`

## Purpose

FLR-0338 run 0003 confirmed that the production diagnostic profile reaches one
`FLUORITE_VK_QUEUE_PRESENT_ENTER` and `FLR0026_VK_QUEUE_PRESENT_BEGIN` but logs
no return/done marker. The app remains alive, 19 draw-end/native Wayland
commit markers are present, and QMP shows a HUD while the entire lower 3D ROI
is black. Asset creation, emissive binding, and a magenta-unlit override
reached their diagnostic markers, but none proves that a visible frame was
presented or a texture was sampled. This ticket captures the live thread state
at that exact boundary; it does not tune light, camera, material, or texture.

## Run 0001 result

- The same boundary recurred: one `FLUORITE_VK_QUEUE_PRESENT_ENTER` and one
  `FLR0026_VK_QUEUE_PRESENT_BEGIN`, with zero return/done markers. There were
  19 draw-end and 19 native Wayland commits; the app survived to guest uptime
  93.63.
- GDB 14.2 attached to the tracked app. The 38-thread listing completed, but
  `thread apply all bt 8` exceeded the 20-second bound (`gdb_exit=124`). The
  transcript detached and was preserved. The partial backtrace reached
  Thread 25 / LWP 718, named `FEngine::loop`: frames 6–7 were Mesa 24.0.7
  `lvp_pipe_sync_wait_locked` / `lvp_pipe_sync_wait`, with
  `wait_flags=VK_SYNC_WAIT_PENDING` and `abs_timeout_ns=UINT64_MAX`. Frames
  above #7 and stacks for the remaining threads were not captured.
- The log immediately before queue-present reports `wait=true` and semaphore
  handle `0x7fba480259e0`; GDB reports a Lavapipe sync object at
  `0x7fba48025a38`. Their relationship is not established by pointer proximity.
- No matching Oops/BUG/CR2/Call Trace line appeared in the bounded selected
  kernel excerpt. This is not a complete proof that no fault occurred.

## Visual evidence

![QMP-only run 0001: HUD/metrics are visible and the 3D region is black](../evidence/FLR-0339-qmp-run-0001.png)

- Run: `flr0339-0001`; QMP framebuffer 1280×800. The image shows Fluorite
  HUD/statistics and Scenes button, with no visible Sequoia geometry.
- The lower ROI `(0,200,1280,600)` is 768,000 black pixels, zero chromatic
  pixels, zero changed pixels against the pre-launch frame, and luma `[0,0]`.
  ROI SHA-256: `0d2039545940e7775d22c8d82079282c91be29af0203faa77e2bff78a67bed0f`.
- QMP PPM SHA-256:
  `a9284701cf55f37aa99507abd4e045bec5381d18f69ebf1f0d8764900e21df63`.
  PNG: [run 0001 screenshot](../evidence/FLR-0339-qmp-run-0001.png), SHA-256
  `fc76d4a1a03d032cf608e5531b488fced200bfe3a53690d68ce0f0ad901eadb1`.
- [Eight-frame QMP replay](../evidence/FLR-0339-qmp-run-0001-sequence.mp4),
  SHA-256 `2b879b7ccad25675251d41b6d51b6a2534279081a932072d7de500a559fd08ac`;
  validated as H.264, 1280×800, 1 frame/sec, 8 frames, 8 seconds. This is a
  replay of eight QMP captures, not continuous host recording.

## Success measure

- Reuse the exact FLR-0335 rootfs, qemuboot, kernel, build/TMPDIR, QEMU memory
  profile, and the same production diagnostic launch parameters.
- Within 90 seconds after launch, observe the first Present-enter marker. Wait
  a two-second grace interval and confirm that no matching queue-present
  return marker appeared.
- Attach GDB once for at most 20 seconds; save `info threads` and a maximum
  eight-frame backtrace per thread before detaching. Correlate FEngine thread
  IDs/state with the selected app/kernel fault markers. Keep raw output on the
  Mini evidence host and expose only bounded selected lines in the working
  log.
- Capture a QMP-only full screenshot and eight-frame sequence, classify the
  full frame and lower 3D ROI, stop the exact app, QMP-quit the VM, and prove
  zero residual QEMU/runqemu/app/socket.
- If Present returns, no marker appears, the target exits, GDB attach fails, or
  the GDB bound expires, retain that bounded outcome and stop; do not retry in
  this ticket. No product source/image patch or build is in scope.

## Facts / inferences / ranked hypotheses

- **Facts:** run 0003 had one Present-enter/begin, zero return/done, 19
  draw-end and 19 native Wayland commits, a surviving app, and a QMP HUD with
  768,000 black lower-ROI pixels. The exact-image hardware breakpoint at
  `libLLVM.so.18.1+0xb1d541` was armed but did not hit within 45 seconds.
- **Inference:** the current first missing marker is inside or immediately
  after the Vulkan queue-present call. The marker placement is directly before
  `vkQueuePresentKHR`; missing return alone does not prove that call is blocked.
- **Hypothesis 1 — Vulkan WSI/driver wait:** the relevant FEngine thread is
  inside `vkQueuePresentKHR` or its driver/WSI wait path. Prediction: its GDB
  top frames name Vulkan/WSI/driver code or a corresponding wait syscall.
- **Hypothesis 2 — FEngine worker fault/exit:** the issuing worker faults at
  the recurring LLVM boundary while the parent survives. Prediction: selected
  kernel/app fault evidence correlates with a missing worker/TID; a surviving
  thread stack may not remain in Present.
- **Hypothesis 3 — app/Filament synchronization:** an app-side lock, futex,
  semaphore, or queue handoff stalls before/around driver dispatch. Prediction:
  the relevant stack terminates in synchronization/Filament code rather than
  the WSI/driver path.

## 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Present-enter with no return while the visible 3D ROI is black | FLR-0338 run 0003 app counters and QMP screenshot |
| Where | Fixed Mini QEMU guest, production Example Demo, Vulkan/llvmpipe/Wayland | Exact FLR-0335 image hashes and run identity |
| When | First Present-enter after launch; stack snapshot follows a 2-second no-return grace | Guest monotonic uptime and selected app log |
| Who | FEngine thread(s), Vulkan/WSI driver, and surviving Flutter parent | `ps -L`, GDB thread IDs/stacks, selected kernel evidence |
| How | One bounded attach at the live no-return boundary; no source or image mutation | committed command set and Mini raw evidence |

## Scope and controls

### In scope

- One unique run ID `flr0339-NNNN`; one fixed Mini evidence parent; no second
  temporary directory or QEMU.
- Exact FLR-0335/0337/0338 image identity and 6144-MiB QEMU profile. The
  existing QEMU harness, build directory, TMPDIR, downloads, and sstate remain
  unchanged.
- Existing production diagnostic parameters from FLR-0338, unchanged, so the
  first variable is the timing/location of the GDB observation.
- One GDB attach at confirmed Present-enter/no-return; `info threads` and
  `thread apply all bt 8`, with a 20-second timeout. Preserve its complete
  bounded transcript on the Mini.
- QMP pre-launch frame, post-run full frame, eight-frame one-second sequence,
  lower-ROI analysis, selected log markers, exact cleanup evidence.

### Out of scope

- Product source, recipes, patches, Devtool, BitBake, bundle/build/image
  changes; no patch creation or commit to the layer.
- Another `isOrdered+1` breakpoint, software breakpoints, broad `strace`, full
  journal dumps, or unbounded backtraces.
- Any Light/camera/material/texture adjustment or interpretation of asset
  readiness as proof of pixel output.
- Copying the QEMU disk image to Mac or changing the fixed build/TMPDIR/cache.

## PDCA

### Plan

1. Run the canonical guard and checkpoint verifier; confirm this is the only
   In Progress ticket and no QEMU/app/QMP residue exists.
2. Create only `$EVIDENCE_ROOT/flr0339-0001`; transfer the committed runner and
   one-line guest commands, never a QEMU image. Validate their checksums and
   the guest command 4096-byte limit.
3. Revalidate the fixed image/helper hashes and zero target processes/ports;
   start one QEMU using the official harness and capture QMP pre-launch.
4. Launch the unchanged FLR-0338 diagnostic profile. Poll only the selected
   Present-enter/return counts for at most 90 seconds. After enter, wait two
   seconds and recheck return; attach once only if the call remains pending.
5. Bound GDB at 20 seconds, preserve its complete thread/backtrace output on
   the Mini, then capture QMP post-run/eight frames and the selected runtime
   state. Analyze only the frame and lower 3D ROI.
6. Stop only the recorded `flutter-auto` PID, QMP-quit the tracked VM, and
   require zero residual targets/socket. Retain both successful and failed
   command evidence; do not retry this ticket.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Identity/preflight | Exact fixed image/helper hashes; one clean QEMU slot | Fixed helper hashes matched; preflight passed; one 6144-MiB QEMU | PASS |
| Present boundary | First enter observed and return absent after 2 seconds, or bounded no-event/return outcome | At uptime 57.49: enter/begin=1, return=0 after grace; app alive | PASS for bounded observation |
| GDB snapshot | One bounded attach; thread list and at most 8 frames/thread serialized on Mini | GDB attached and listed 38 threads; timeout 124 at 20 seconds; partial backtraces reached LWP 718 `FEngine::loop` → Mesa `lvp_pipe_sync_wait` | PARTIAL; callsite above frame 7 UNKNOWN |
| QMP visual evidence | Full QMP screenshot + 8-frame sequence; 3D ROI classified | HUD visible; lower ROI 768,000/768,000 black, zero changed/chromatic pixels; PNG/video retained | PASS for capture; 3D NOT SHOWN |
| Cleanup | Exact app stop, QMP quit, zero process/socket residue | `flutter_processes=0`; QMP quit accepted; Mini residual targets/socket 0 | PASS |

### Act

- Close this bounded runtime attempt with a partial GDB result; do not repeat
  the all-thread dump in this ticket. The observed Lavapipe sync wait strongly
  raises the Vulkan synchronization hypothesis but does not establish that
  LWP 718 is blocked on the exact `vkQueuePresentKHR` semaphore.
- FLR-0340 owns static mapping of the Mesa 24.0.7 sync-wait caller and the
  Filament finished-drawing semaphore signal path. No source or image change
  is justified until the wait object and signal path are reconciled.

## Unknowns

- Whether LWP 718's `lvp_pipe_sync_wait` frame is in the `vkQueuePresentKHR`
  wait-semaphore path or an independent queue/synchronization path.
- Which operation signals semaphore handle `0x7fba480259e0`, and whether the
  corresponding sync object is the one waiting in Lavapipe.
- Caller frames above frame #7; the bounded all-thread stack timed out before
  those frames were captured.
- Whether fixing this boundary will produce any visible 3D pixels; the QMP
  native scene region remains the final acceptance signal.

## PDCA checker

- Status: PASS for bounded capture/teardown; GDB stack is partial and causal path remains UNKNOWN
- Checked by: FLR-0339 run 0001 selected GDB/QMP/runtime evidence and repository verification
- Findings: the exact Present-enter/no-return boundary recurred; LWP 718 was inside Mesa Lavapipe `lvp_pipe_sync_wait` with `VK_SYNC_WAIT_PENDING`. The 20-second all-thread backtrace timed out. No patch/build; FLR-0340 maps the source path.
