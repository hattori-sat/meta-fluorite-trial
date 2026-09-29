# FLR-0366 — capture the FEngine loop page fault under GDB

- Status: Done
- Priority: High
- Owner: Mini QEMU / guest SSH / GDB / Vulkan present / QMP evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Predecessor: [FLR-0365 manual app-id/size profile](FLR-0365-test-manual-flutter-appid-size-profile.md)
- Historical controls: [FLR-0347 HUD-visible exact-image run](FLR-0347-retest-empty-log-arm-poll-on-exact-image.md), [FLR-0344 launch command](../commands/FLR-0344-launch-production.cmd)
- Working log: [FLR-0366 working log](../logs/2026-09-29-flr0366.md)
- Run ID: `flr0366-0001` (one fresh attempt)

## Objective

On the pinned FLR-0335 rootfs, manually start the installed Example Demo under GDB using the FLR-0365 app-id/size command and no diagnostic environment overrides. Capture the `FEngine::loop` page fault reported in libLLVM and correlate its thread/backtrace with the unmatched second Vulkan queue-present. Preserve QMP-only full-screen evidence. This is a bounded runtime diagnosis; it is not a product fix or a 2D+3D acceptance claim.

## Facts

- FLR-0365 used rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`. Direct guest SSH manually launched exactly one `agl-driver` process with the Example Demo bundle, app-id `fluorite`, dimensions 1280×800, and no FLR/FLUORITE diagnostic variables.
- Its QMP frame had a white field and a large black polygon, no CPU/FPS/Scenes HUD, zero chromatic pixels, and no identifiable Sequoia. Eight frames were identical.
- The app log read `sequoia_ngp.glb`; the second of two `FLR0026_VK_QUEUE_PRESENT_BEGIN` markers had no `result=0` return. At `13:18:05`, guest kernel 6.6.111 reported a page fault/Oops for TID 764 `FEngine::loop`; RIP `0x7f869bf6d541` fell inside the mapped `/usr/lib/libLLVM.so.18.1`. The thread later disappeared while the parent process survived.
- The prior run did not have GDB attached at fault time and produced no captured backtrace. The temporal relationship between the fault, unmatched present, and pixels is not causal proof.
- GDB, strace, and coredumpctl are present in the pinned guest. Whether usable LLVM symbols/debug files exist is UNKNOWN.
- FLR-0366 repeated the kernel Oops under a manually GDB-launched Example Demo. GDB recorded no SIGSEGV/SIGBUS; the kernel identified `FEngine::loop` TID 806 while its parent `flutter-auto` PID 753 remained alive.
- The Oops RIP mapped to Build-ID `359c1108040bc6bc1af64bb639d0b25385858051` in `/usr/lib/libLLVM.so.18.1`. Correct ELF VA `0xb1d541` resolves to `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)`; the instruction sequence is register-only (`dec %edi; cmp $7,%edi; setb %al; ret`). Kernel CR2 was `0x000000008d207750`; RSP was `0x00007fff8d207750`, whose low 32 bits match CR2. This mismatch means the symbol cannot be called the proven invalid-memory access site.
- QMP full-screen output was a white field with one large black polygon; no HUD, recognizable Sequoia, or chromatic pixels. Pre-fault and all eight post-fault frames were byte-identical at PPM SHA-256 `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
- Two `FLR0026_VK_QUEUE_PRESENT_BEGIN` markers had one `result=0`; the kernel Oops occurred later. Ordering is observed; causality is UNKNOWN.

## Problem stratification — 4W1H (Why excluded)

| Dimension | Evidence | Discriminator |
| --- | --- | --- |
| What | Monochrome polygon/no HUD; unmatched queue-present; FEngine thread Oops | GDB signal/backtrace plus QMP frame and exact marker sequence |
| Where | Guest thread `FEngine::loop`, RIP mapped in libLLVM, Vulkan queue-present | GDB registers, thread list, shared-library mapping, kernel trace |
| When | Fault at 13:18:05 after the second present began | Capture a fresh run from process start through fault or bounded timeout |
| Who | One agl-driver Example Demo and guest kernel/graphics stack | Verify exact UID/PID/TID and bundle identity |
| How | Manual GDB-launched Flutter with the proven CLI args; no diagnostic overrides | Keep image, bundle, session, and CLI fixed; change only debugger supervision |

## Ranked hypotheses

1. **Invalid stack/pointer in the FEngine loop:** GDB stops at SIGSEGV/SIGBUS around the same event; registers and backtrace show the faulting address and caller chain, potentially in LLVM.
2. **Renderer wait/present boundary precedes the thread failure:** the captured stack is in Lavapipe/LLVM wait or queue-present code and marker order places the fault after the unmatched begin.
3. **The page fault is independent of the missing HUD/3D output:** GDB catches the fault, but QMP remains unchanged or the event does not recur; a separate surface/content boundary is still required.
4. **The prior kernel report was not a repeatable app fault:** the bounded GDB run shows no matching signal/Oops and the thread remains present; preserve the no-hit evidence and do not infer a fix.

## Scope

### In scope

- One fresh QEMU run on the exact pinned image, direct strict guest SSH, and manual GDB supervision of the same installed Example Demo and FLR-0365 CLI profile.
- Read-only identity checks for target image, process, guest tools, bundle, Wayland session, ELF Build-ID/symbol availability, and run-owned ports/socket.
- Bounded GDB signal/backtrace/register/shared-library evidence, targeted app/Vulkan markers, bounded kernel Oops/journal evidence, coredump listing, QMP full-frame still/eight-frame video, and cleanup.

### Out of scope

- Editing any shell runner or generating a reusable launch script.
- Applying the full FLR-0344 diagnostic environment bundle, changing camera/light/model/material/texture inputs, or editing source/recipes.
- Rebuilding/transferring an image or copying the QEMU disk image to Mac.
- Claiming the fault caused the visual output without a discriminating observation.

## Success criteria

1. Canonical and one-active-ticket checks pass; the fresh run uses rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`, with no pre-existing app/QEMU/port collision.
2. Strict guest SSH passes using the run-scoped known-hosts file; the installed bundle, Wayland socket, GDB, and app binary are verified before launch.
3. Exactly one agl-driver Example Demo starts under GDB with app-id/size flags and zero FLR/FLUORITE diagnostic variables.
4. Capture a bounded fault-time signal/backtrace/register/shared-library snapshot. If no matching signal occurs by the declared deadline, record a bounded no-hit and the exact observed state; do not retry this run ID.
5. Preserve targeted app Vulkan/asset markers, kernel Oops excerpt, coredump status, QMP still/eight frames, fixed HUD/3D ROI metrics, and hashes. Visually inspect the full QMP frame.
6. Report separately whether the page fault recurs, whether the second present returns, whether the FEngine thread survives, whether HUD/Sequoia pixels appear, and whether a symbol resolves.
7. Stop only the recorded app/GDB target, quit the exact QMP instance, and verify zero run-owned app/QEMU/socket/port residuals.

## Impact

- **Build-time:** none.
- **Packaging:** none; no image or package changes.
- **Runtime:** one manually supervised app run; GDB may perturb timing, which must be called out.
- **Integration risk:** low; no persistent script/source change. A GDB no-hit does not falsify the uninstrumented FLR-0365 result by itself.

## Plan / Do / Check / Act

### Plan

- Reuse the successful direct guest-SSH route and same pinned image/bundle/CLI as FLR-0365; manually run under GDB, not through the app runner.
- Enable only bounded stops for relevant fault signals, capture the fault context and exact mapped ELF identity, and retain QMP evidence.
- Do not add diagnostic environment variables or change any visual input.

### Do

- Run `flr0366-0001` used the pinned rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`, 6144 MiB, the installed Example Demo, and a manually composed GDB command. App launch added only app-id `fluorite` and 1280×800 dimensions; the diagnostic environment-variable count was zero.
- The copied FLR-0350 wrapper's preflight failed before QEMU because it resolved its repository root relative to the evidence directory and could not find `scripts/flr0350_launch_gate.py`. The direct validator at the receiver passed; the already-committed QEMU harness was then invoked directly. No launcher was edited.
- Guest identity/preflight passed; GDB PID 746 and `flutter-auto` PID 753 ran as UID 1001. Two bounded 15-second observations showed two present begins and one return, then the kernel Oops. GDB's signal-marker count remained zero; the faulting FEngine thread disappeared while the parent app remained alive with 38 threads.
- Corrected ELF mapping arithmetic using the PT_LOAD segment/load bias: an initial `0xb63541` calculation was wrong; the verified VA is `0xb1d541`. No source line/debug sections or split-debug file were present. Bounded `coredumpctl` listing had no entries.
- A guest-shell preflight command first failed due to quoting before guest mutation; a simpler preflight passed. At cleanup, two strict guest SSH attempts as `agl-driver` were denied public-key authentication, so the recorded QMP socket was used to shut down only this VM. The QMP harness reported `cleanup=PASS residual_targets=0 residual_qmp=0`; independent checks found recorded QEMU PIDs 2753106/2753133 absent, QMP socket absent, and ports 10930–10932 unbound.
- QMP evidence was copied as image data only; no disk image/rootfs/kernel was copied to Mac. Full-frame still and eight-frame video are linked below.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Image/guest preflight | Pinned rootfs and guest tools verified | Rootfs hash, app/bundle/session, GDB 14.2, LLVM Build-ID, symbol tools verified; zero prior app | PASS |
| Manual GDB app launch | One agl-driver process; diagnostic env absent | GDB PID 746, inferior PID 753, UID 1001; zero diagnostic variables; app-id/size fixed | PASS |
| Fault-time GDB evidence | Signal/backtrace/register/map or bounded no-hit | Kernel Oops recurred; GDB caught no signal and no fault-time backtrace. RIP resolves to register-only LLVM predicate; CR2=RSP. Fault mechanism remains UNKNOWN | BOUNDED RESULT |
| Vulkan/kernel correlation | Exact present sequence and bounded Oops evidence | 2 present begins / 1 successful result; later Oops in `FEngine::loop`; causal relation not established | PASS — correlation only |
| QMP visual evidence | Full still/eight frames and HUD/3D verdict | White field + black polygon; no HUD/recognizable Sequoia/chroma; eight post-fault frames identical. PNG/MP4 saved and visually reviewed | PASS — visual failure recorded |
| Teardown | App/QEMU/QMP/port residuals zero | Guest SSH cleanup was denied; exact QMP quit shut down the guest. Harness and independent host checks show zero recorded PIDs/socket/ports | PASS — VM shutdown cleanup |

### Act

- Close this bounded diagnosis without claiming `isOrdered` is the root cause. Do not patch LLVM or the renderer from this evidence. [FLR-0367](FLR-0367-replay-manual-known-good-fixture-on-current-image.md) now replays the historical manually launched lit Filament fixture on the exact current image as a positive control. Flutter launch remains a direct guest-SSH command; no launch-script edit is authorized by this result.

## Evidence

- Mini evidence root: `$EVIDENCE_ROOT/flr0366-0001/qemu`
- Predecessor visual/log evidence: [FLR-0365 QMP still](../evidence/FLR-0365-qmp-run-0001.png), [FLR-0365 QMP video](../evidence/FLR-0365-qmp-run-0001.mp4), and the exact Mini evidence root in FLR-0365.
![FLR-0366 QMP full-frame capture after the FEngine Oops](../evidence/FLR-0366-qmp-run-0001.png)

- QMP PNG SHA-256 `3d5f4eda7adc85171514bb0c112dc3658342262e831c1b8e528f56740aefaf99`.
- [FLR-0366 QMP eight-frame video](../evidence/FLR-0366-qmp-run-0001-sequence.mp4), 1280×800, 1 fps, 8 seconds, SHA-256 `b67aeeede624b417948d1a6b2bba9ae9ce8e0f166f261572fd3d20c3dad18cbf`.
- Raw QMP PPM SHA-256 `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`; all eight post-fault frames matched it. Guest kernel excerpt, marker counts, ELF mapping/disassembly, and preflight remain under the Mini evidence root above.

## UNKNOWN

- Why a register-only `isOrdered` instruction coincides with a supervisor read page fault at CR2=RSP, and whether kernel register/stack context is corrupted.
- Whether the Oops causes or merely coincides with the unmatched present and monochrome/no-HUD QMP result.
- Whether debugger timing changes the failure window; GDB observed no signal despite the repeated kernel Oops.
- Whether production Sequoia appears with HUD removed on the current image; this ticket made no HUD-off run.
