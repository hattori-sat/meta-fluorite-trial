# FLR-0336 — capture execution context for the recurring FEngine page fault

- Status: Waiting — kernel-only trace trial complete; [FLR-0337](FLR-0337-capture-user-and-kernel-fault-trace.md) owns the user+kernel event discriminator.
- Priority: High
- Owner: guest kernel exception / Vulkan-llvmpipe runtime diagnosis roles
- Created: 2026-09-28
- Predecessor: [FLR-0335](FLR-0335-compare-present-without-gdb.md)
- Working log: `work/logs/2026-09-28-flr0336.md`
- Preflight command: `work/commands/FLR-0336-kernel-fault-trace-preflight.cmd`

## Problem

### Purpose

Capture the actual execution context of the recurring `FEngine::loop` page
fault with an existing, low-perturbation guest kernel trace mechanism. Avoid
another symbol-only GDB attach: earlier runs show that the faulting worker is
already gone by the time GDB attaches, and GDB changes the observed timing.

### Success measure

Either capture a bounded page-fault event with its kernel/user call chain and
correlate it to queue-present/Wayland markers, or prove that the retained image
does not expose a suitable trace event and stop before running another app.
No source or image patch is authorized by this ticket.

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | `FEngine::loop` reports a supervisor-read page fault; post-fault RIP resolves to `libLLVM.so.18.1` / `isOrdered+1` | FLR-0335 evidence; FLR-0105/0107 history |
| Where | Fixed Mini QEMU guest; production Example Demo; Vulkan/llvmpipe and Wayland path | FLR-0333/0335 same image identity |
| When | After the first recorded queue-present begin; FLR-0335 fault occurred at guest uptime 284.16 s | bounded app/kernel logs |
| Who | Guest kernel exception handler; one `FEngine::loop` worker; production app and Vulkan WSI | kernel Oops and bounded process maps |
| How | No-GDB run loses one worker; surviving parent has no matching coredump; post-fault GDB resolves RIP but cannot recover the worker stack | FLR-0335 evidence |

### Priority selection

- Compared strata: asset loading/binding, light contribution, frame/present,
  and guest exception context.
- Selected focus: actual page-fault execution context.
- Selection evidence: FLR-0319/0320 prove the emissive resource exists and its
  binding becomes ready/applied; FLR-0314/0315/0309 do not show light or
  emissive controls restoring pixels; FLR-0332/0335 stop at native publish /
  present and a repeated FEngine fault.

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| App scene/frame work | production Sequoia diagnostic profile | draw and queue submission | draw-end and submit markers exist | FLR-0335 bounded app log |
| Queue present | submitted frame and wait semaphore | return/result then native Wayland buffer attach | present begin exists; return/done and child attach are absent | FLR-0332/0335 |
| Fault handling | FEngine worker exception | retain the faulting execution chain | kernel records RIP/RSP/CR2; worker disappears before GDB attach | FLR-0335 kernel/GDB extracts |
| Visual result | native output composed with Flutter HUD | non-black Sequoia plus HUD | HUD only; vehicle ROI is black | FLR-0335 QMP |

### Problem point

The first confirmed divergence is after queue-present begins and before a
present return/native Wayland child-buffer attach. Whether the Oops is the
cause of that missing return, a consequence, or a concurrent fault is UNKNOWN.

### Ideal condition

The production FEngine worker completes render/present without a page fault,
the native surface publishes a buffer, and QMP shows Sequoia plus the 2D HUD.

### Current condition — Facts

- FLR-0335 reproduces the current no-GDB fault on the exact FLR-0334 rootfs.
- The kernel reports `#PF: supervisor read access in user mode` and
  `error_code(0x0000)`; RIP is a userspace address mapped post-fault to
  `isOrdered+1`, while CR2 equals the low 32 bits of the recorded RSP.
- Historical FLR-0105 captured a normal `isOrdered` entry in an LLVM
  InstCombine stack and a later `isOrdered+1` Oops in another FEngine worker.
  FLR-0107 observed both Gallivm `LLVMRunPasses` calls return normally before
  a later Oops. This history weakens a direct LLVM-pass-failure explanation.
- FLR-0308/0309 reproduce the same fault across model-count and light-intensity
  conditions. A no-light run stalled before present, so it is not a successful
  rendering control.
- FLR-0070 once captured HUD plus production Sequoia pixels; follow-up runs
  failed to reproduce that frame, whose complete runtime identity is missing.
- FLR-0336 reused the exact FLR-0335 image and diagnostic profile. At guest
  monotonic `422.495545`, about 28.76 seconds after launch, the same
  `FEngine::loop` TID 710 Oops recurred. The kernel-only perf recording
  captured 488 events, but no event for TID 710 in the fault window.
- The app log contained 19 draw-end and 19 native Wayland commit markers,
  one queue-present begin, and no queue-present return. The parent app
  survived; TID 710 was gone.

### Gap and impact

The post-fault symbol is not proof of the faulting instruction or root cause.
Without the fault-time execution chain, a product patch to texture sampling,
lighting, Vulkan present, or LLVM would be guesswork and risks changing an
already successful fixture path.

### Point of occurrence

Guest page-fault handling in the production FEngine/llvmpipe runtime. Exact
faulting instruction context and relation to `vkQueuePresentKHR` remain
UNKNOWN.

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| The fault is a user execution/control-flow error at `isOrdered+1` | user-fault event contains the same PC and a user call chain | inspect both user and kernel page-fault events in one bounded trace | UNKNOWN; user event not enabled in FLR-0336 | FLR-0336; FLR-0337 |
| The kernel Oops occurs during a supervisor access; the printed userspace RIP is saved context rather than the actual faulting instruction | kernel-fault trace reports a kernel IP/call chain distinct from libLLVM | same bounded event trace | kernel tracepoint available, but no TID 710 event in its fault window | FLR-0336 |
| The FEngine fault and missing queue-present return are concurrent but causally separate | trace shows unrelated worker/call path and independent present/WSI wait | correlate TID and event ordering to existing markers | UNKNOWN / test pending | FLR-0332/0335 |

### Confirmed root cause

UNKNOWN. A function/symbol address, page-fault address, or temporal
correlation alone is insufficient.

### Minimal countermeasure

No countermeasure yet. First check existing `perf` and tracefs exception
events. Do not mount filesystems, change sysctls, install tools, edit source,
or rebuild the image in this ticket. If no supported trace event exists, stop
and create a separate ticket for the smallest approved debug-build change.

## Scope

### In scope

- Reuse the exact FLR-0335 rootfs, qemuboot, kernel, build/TMPDIR and
  diagnostic app profile.
- Check `perf` and existing tracefs exception event availability before
  launching `flutter-auto`.
- If supported without changing system settings, capture only the relevant
  page-fault event/call chain, bounded app markers, one QMP full frame, a short
  QMP sequence, and exact process/QMP cleanup.

### Out of scope

- Light, camera, texture, material, model, compositor, semaphore, or Vulkan
  source changes.
- Devtool, bundle transfer, BitBake, image rebuild, debug package install,
  tracefs mount, or sysctl change.
- Repeating already-completed LLVM symbol mapping, broad strace, or all-thread
  GDB collection.

## Success criteria

- Canonical repository guard and one-active-ticket check pass.
- Fixed image hashes match FLR-0335; only one QEMU starts through the existing
  harness; no new build/TMPDIR/evidence root is created.
- Trace support is checked before app launch. If unavailable or permissions
  would require changing system state, stop and record the exact missing
  capability; do not launch a redundant run.
- If supported, capture one no-GDB production run until the first matching
  fault or 400 guest seconds, whichever comes first; include only bounded
  kernel fault data/call chain and relevant present/surface markers.
- QMP full-frame and bounded sequence are saved before analysis; vehicle/HUD
  pixels are classified; guest app is stopped by its recorded PID and QMP
  teardown leaves zero residual targets/socket.
- No causal claim or source fix is made unless the trace identifies the exact
  faulting operation and its relation to present.

## Visual evidence

- QMP-only full frame SHA-256: `7b5039f54a9795c0b6d245be131f89ecb3947b1d730176f3660910105668508e`;
  pre- and post-fault frames are byte-identical. The lower 3D ROI is uniformly
  black (`changed_pixels=0`, `chromatic_pixels=0` across 768,000 pixels).
- Both saved eight-frame sequences contain one unique hash. A short MP4 replay
  was encoded from the post-fault QMP frames; it is not a continuous host
  recording.
- QMP-only post-fault screenshot, embedded from the committed evidence asset:

  ![Full QMP frame after the FEngine page fault: HUD visible, 3D viewport black](../evidence/FLR-0336-qmp-postfault.png)

- [Open the 8-second QMP frame-sequence replay](../evidence/FLR-0336-qmp-postfault-sequence.mp4).
- Run ID / image identity: same fixed image as FLR-0335; verify hashes before
  startup.
- Evidence path: `$EVIDENCE_ROOT/flr0336-0001/qemu`.

## Hypotheses

1. The user-mode RIP genuinely identifies the faulting instruction and the
   fault reflects corrupted control flow or stack/pointer state.
2. The page fault is a supervisor-mode failure in kernel/driver handling, and
   the printed `isOrdered+1` address is contextual rather than causal.
3. The Oops and missing present/Wayland publication belong to different
   threads or event paths.

## PDCA

### Plan

1. Verify canonical repository, sole In Progress ticket, and no residual QEMU.
2. Reuse the fixed image and run directory contract; inspect tracepoint
   availability with the committed preflight command before app launch.
3. If supported, capture one bounded no-GDB event trace and QMP frame set.
4. Correlate fault TID/time/PC/CR2 with queue-present and native-surface
   markers; stop and preserve all raw evidence.

### Do

- Canonical guard passed with `bash scripts/assert-canonical-repository.sh`;
  the direct executable invocation first returned permission denied.
- Recovered the exact FLR-0335 image/profile and ports from retained evidence;
  no new build/TMPDIR or image was created. One QEMU started at 6144 MiB.
- Guest readiness and read-only preflight passed: `perf` 6.6.111,
  `perf_event_paranoid=2`, both user/kernel exception events available, and
  frame-pointer/perf kernel config enabled. The one-second perf call-chain
  capability probe passed.
- Started perf kernel-event recording before one no-GDB Example Demo launch.
  The fault recurred at monotonic `422.495545`; perf reached its 400-second
  bound and produced 488 kernel-event samples. A 20-ms fault-time filter had
  no kernel event, and TID 710 did not appear in the captured event stream.
- QMP full frames and two eight-frame sequences were saved before analysis;
  the frame SHA and lower-ROI counts are recorded above and in the evidence
  note.
- Stopped only the recorded app PID after its `comm` matched `flutter-auto`,
  then QMP-quit the exact VM. Final residual target/socket counts were zero.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Trace preflight | supported event identified before app launch | Both events available; kernel event recording accepted | `serial-0336-trace-preflight.output`, `serial-0336-perf-capability.output` | PASS |
| Fault call chain | bounded page-fault event captured or capability absence proven | Kernel-only recording missed TID 710 in the Oops window; user event was not enabled | `serial-0336-perf-fault-events.output`, `serial-0336-fault-window.output` | UNKNOWN |
| QMP 2D/3D output | complete QMP frame and pixel counts | HUD visible; lower viewport all black; pre/post frames identical | QMP frame SHA and pixel analysis in evidence note | PASS for classification; 3D NOT PROVEN |
| Cleanup | one app/one QEMU, zero residual targets/socket | Exact app stopped; QMP quit accepted; zero residue | `serial-0336-stop-app.output`; host cleanup result | PASS |

### Act

- Move the exact fault-time user-versus-kernel trace question to FLR-0337.
  No product patch until a precise fault owner is evidenced.

## Decision log

- 2026-09-28: Selected kernel exception context over another texture/light
  probe because binding is ready/applied and the no-GDB present/fault boundary
  is reproduced. No system mutation is authorized by this ticket.
- 2026-09-28: Kernel-only event capture reproduced the Oops but had no
  page-fault sample for TID 710 at the matching monotonic time. This does not
  prove the fault is a user-mode event or that events were not lost. Split the
  next discriminator to FLR-0337 and keep this ticket Waiting rather than
  claiming a root cause.

## Unknowns

- Whether the target TID emits `exceptions:page_fault_user`,
  `exceptions:page_fault_kernel`, both, or neither.
- Whether the page-fault event identifies a kernel IP, a user IP, or both.
- Whether the page fault and missing native surface publish are causally
  connected.
- Whether the same current-image run can capture more than the post-fault
  symbol and surviving-thread state.

## PDCA checker

- Status: UNKNOWN — the bounded kernel-only trial did not capture the target event; follow-up FLR-0337 is active.
- Checked by:
- Findings:
