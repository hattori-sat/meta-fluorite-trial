# FLR-0337 — capture both user and kernel page-fault context

- Status: Done — matching user-fault event captured; root cause remains UNKNOWN.
- Priority: High
- Owner: guest exception tracing / production FEngine runtime diagnosis roles
- Created: 2026-09-28
- Predecessor: [FLR-0336](FLR-0336-capture-kernel-context-of-fengine-page-fault.md)
- Working log: `work/logs/2026-09-28-flr0337.md`

## Problem

### Purpose

FLR-0336 proved that guest `perf` and both x86 page-fault tracepoints are
available. A kernel-only perf recording captured 488 unrelated/ordinary
kernel page-fault events but none for the FEngine TID that Oopsed. The kernel
log preserved a user-space RIP and `#PF: supervisor read access in user mode`.
The event class was therefore under-selected. This ticket records both
`exceptions:page_fault_user` and `exceptions:page_fault_kernel` during one
production replay. The user event matched the Oops TID, address, and IP; this
identifies the exception path but does not establish the producer or cause.

### Success measure

Either capture the recurring TID's user- or kernel-page-fault event and
callchain, correlated to the FEngine Oops and queue-present/native-commit
markers. Do not infer root cause from a saved RIP or a matching event alone.

### Facts from FLR-0336

- The no-GDB Example Demo reached 19 scene draw-end and 19 native Wayland
  commit markers; queue-present began once and did not return.
- At guest monotonic time `422.495545`, TID 710 (`FEngine::loop`) Oopsed with
  `RIP=0x7f452fe98541`, `CR2=RSP=0x00000000d1486750`, and
  `error_code=0x0000`.
- The QMP HUD remained visible; the lower 3D ROI was uniformly black.
- `exceptions:page_fault_kernel` was usable but did not record TID 710 in the
  Oops window. The user exception event was not enabled in that run.

### FLR-0337 result

- The exact FLR-0335 rootfs, qemuboot, and kernel were reused, with one
  6144-MiB QEMU and the same no-GDB production Example Demo profile.
- `exceptions:page_fault_user` recorded TID 703 (`FEngine::loop`) at
  monotonic `87.583394138`, address `0xd55d7750`, IP `0x7f0940fea541`, and
  error code `0x0`. The kernel Oops followed at `87.583812`, 418 microseconds
  later, for the same TID and IP, with `CR2=0x00000000d55d7750`,
  `RSP=0x00007f08d55d7750`, and `error_code=0x0000`.
- The event maps to `/usr/lib/libLLVM.so.18.1`, file offset `0xb1d541`,
  `llvm::CmpInst::isOrdered+1`. No matching kernel-event block appeared in
  the selected 40-ms trace window. The selected output has six user-fault
  blocks; whole-recording perf loss status is UNKNOWN.
- The parent `flutter-auto` PID 655 survived, but faulting TID 703 was absent.
  No matching coredump was listed. App markers: 19 draw-end, 19 native
  Wayland commits, one queue-present begin, zero queue-present returns, and
  zero present-done markers.
- QMP shows the HUD, FPS/CPU/GPU statistics, and Scenes button; all
  768,000 pixels in the lower 3D ROI are black. Sequoia GLB asset creation
  reports 12 renderable entities; emissive texture 6 becomes ready and is
  applied. Runtime texture sampling and fault causality remain UNKNOWN.
- Evidence and hashes: [FLR-0337 evidence](../evidence/FLR-0337-user-fault-trace-2026-09-28.md).

### 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Recurring FEngine page fault after one queue-present begin | FLR-0336 kernel journal and app log |
| Where | Fixed Mini QEMU guest; production Example Demo; Vulkan/llvmpipe/Wayland | FLR-0335/0336 exact image identity |
| When | About 29 seconds after this profile's launch in FLR-0336 | guest monotonic journal and launch uptime |
| Who | Guest page-fault exception path; `FEngine::loop` worker; production app | TID 710 Oops; post-fault thread set |
| How | Kernel-only `perf record` missed target TID; user-event path and event loss remain untested | FLR-0336 bounded perf output |

### Competing hypotheses

1. The target is a user-mode page-fault exception. Prediction: the user event
   contains TID 710, user RIP, CR2/address, and error code near the Oops time.
2. The target is a kernel-mode page fault whose saved Oops context reports the
   user RIP. Prediction: the kernel event contains the matching TID/address;
   its kernel callchain identifies the actual supervisor access.
3. The event is not captured because of trace loss, an exception-path gap, or
   an incorrect timestamp basis. Prediction: perf lost-event information or
   event timestamps do not cover the matching journal interval.

## Scope and controls

### In scope

- Reuse the exact FLR-0335/0336 rootfs, qemuboot, kernel, build/TMPDIR,
  6144-MiB QEMU profile, and saved no-GDB production diagnostic parameters.
- Start one `perf record` before the app with both exception events and frame
  pointer callchains; stop on the first matching Oops or at 400 seconds.
- Keep the trace bounded and preserve the selected event block, event counts,
  loss status, kernel context, app markers, one full QMP frame, a short QMP
  sequence, and exact cleanup evidence on the Mini PC.
- Save decoded fault-window output in the Mini evidence directory before QMP
  shutdown; do not rely only on guest `/run` artifacts.

### Out of scope

- Product source, recipe, layer, image, sysctl, mount, or installed-package
  changes; Devtool, BitBake, build, or bundle transfer.
- Light/camera/material/texture tuning, GDB attach, broad `strace`, or full
  unfiltered kernel/app journal dumps.
- Starting a second QEMU or creating a new build/TMPDIR/cache.

## Plan / PDCA

### Plan

1. Run the canonical-repository guard, confirm this is the only In Progress
   ticket, verify the fixed image hashes, and check zero QEMU/app residue.
2. Create only `$EVIDENCE_ROOT/flr0337-0001/qemu`; reuse existing build/TMPDIR
   and the official QEMU harness.
3. Verify both perf tracepoints and perf permissions before app launch.
4. Start one combined user+kernel event recording, then launch the exact
   no-GDB production profile once. Capture QMP full frame and eight frames.
5. On the first fault, collect only the matching 40-ms perf window, kernel
   context, target TID, queue-present/native-commit markers, and perf loss
   information. Save the selected output on the Mini before shutdown.
6. Stop only the recorded app PID, QMP-quit the tracked VM, and prove zero
   residual QEMU/runqemu/flutter-auto processes and socket.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Image/process preflight | Exact hashes; zero residual targets | Exact FLR-0335 image; one QEMU; preflight passed | PASS |
| User and kernel trace | Both events recordable before app launch | Both available; matching user event captured, no kernel block in selected window; total perf-loss status UNKNOWN | PASS with limitation |
| Fault context | Target event/TID, IP/address/error, bounded callchain and loss status | TID 703, matching user event/Oops IP and address; loss UNKNOWN | PASS for event capture |
| Runtime visual | Full QMP frame plus 8-frame sequence; classify HUD and 3D ROI | HUD visible; 3D ROI uniformly black; eight captures have one unique hash | PASS for capture; 3D NOT SHOWN |
| Cleanup | Exact app stop, QMP quit, zero targets/socket | Recorded app PID stopped; QMP quit; zero residual targets/socket | PASS |

### Act

- FLR-0338 owns a bounded hardware execution breakpoint at the known
  `libLLVM.so.18.1+0xb1d541` boundary to capture pre-fault registers and caller
  state. It must use a hardware breakpoint; do not overwrite the adjacent
  instruction with a software breakpoint.
- Preserve the alternative that the Oops RIP is contextual rather than the
  faulting operation. Do not patch LLVM, Mesa, Filament, textures, materials,
  lights, or the kernel based on this event alone.

## Unknowns

- Why the user fault reports supervisor-read `error_code=0` and a CR2 equal to
  the low 32 bits of the full RSP.
- Whether the captured RIP is the exact instruction being executed or saved
  exception context; prior FLR-0335 GDB disassembly at `+1` showed `iret`, but
  FLR-0337 did not single-step or disassemble the live instruction.
- Whether the page fault causes, follows, or is independent of missing
  `vkQueuePresentKHR` return/native buffer publication.
- Whole-recording perf lost-sample status; the selected output contained no
  loss indicator, which is not proof that no samples were lost.
- Whether the ready/applied emissive binding is sampled by the runtime shader.

## PDCA checker

- Status: PASS for the bounded event-capture objective; root cause UNKNOWN.
- Checked by: FLR-0337 evidence review and repository verification.
- Findings: the same-TID user event matched the Oops time/IP/address. The
  visible 2D HUD remains, while the production 3D ROI is black. FLR-0338 is
  required; no source patch is justified.
