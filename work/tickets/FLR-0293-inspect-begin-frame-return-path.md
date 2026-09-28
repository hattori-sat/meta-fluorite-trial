# FLR-0293 — inspect Filament beginFrame return path

- Status: Waiting
- Priority: High
- Owner: target debugger / Filament renderer lifecycle roles
- Created: 2026-09-25
- Predecessor: [FLR-0292](FLR-0292-ab-swapchain-configuration-before-begin-frame.md)
- Working log: `work/logs/2026-09-25-flr0293.md`

## Objective

Use the debug tools already present in the authoritative image to inspect one
actual `filament::Renderer::beginFrame` call while the runtime is in the known
false-heavy state. Determine whether the failure returns through a Vulkan
acquire/surface path, a Filament swapchain state check, or another caller-side
condition.

This is a bounded runtime observation. It must not change source, recipes,
patches, or the product rendering behavior.

## Acceptance gate

One QEMU run must retain:

1. exactly one `flutter-auto` process and the existing FLR-0291 diagnostic
   launch;
2. a bounded target-GDB attach with a backtrace at `beginFrame` and a return
   observation if symbols permit;
3. the corresponding bounded runtime log and QMP frame/hash;
4. explicit classification of symbol availability, attach result, and any
   debugger-induced interruption;
5. QMP teardown with zero residual QEMU, `flutter-auto`, and QMP targets.

## Facts

- FLR-0291 and FLR-0292 both show the same QMP frame and false-heavy
  beginFrame lifecycle.
- The rootfs contains `/usr/bin/gdb`, `/usr/bin/gdbserver`, `/usr/bin/eu-stack`,
  `/usr/bin/llvm-symbolizer`, `/usr/bin/coredumpctl`, and `/usr/bin/strace`.
- The exact Filament renderer symbol visibility in the stripped `flutter-auto`
  binary is UNKNOWN and must be tested before relying on a breakpoint.

## Ranked hypotheses

1. **Filament reaches a Vulkan acquire/surface rejection.** A breakpoint and
   short backtrace will land in a Vulkan/driver or swapchain acquire path.
2. **The binary lacks usable renderer symbols.** GDB will not resolve
   `filament::Renderer::beginFrame`; the next evidence must use available
   exported symbols, disassembly, or targeted source instrumentation.
3. **The call is returning from a generic renderer state guard.** The stack
   will remain above the backend and point to a state/ownership check.

## Verification plan

- Reuse the fixed Mini image/build/TMPDIR and one-QEMU harness.
- Launch with the existing FLR-0291 command and attach as root only after the
  false-heavy marker appears.
- Keep GDB output bounded: one symbol lookup, one breakpoint attempt, one
  backtrace, and one return observation. Do not stream the runtime log.
- Treat a debugger stop as diagnostic evidence only; do not call it a visual
  pass. Capture one QMP frame before teardown and record its ROI summary.

## UNKNOWN

- Whether the release build retains enough Filament symbols for a direct
  breakpoint.
- Whether stopping the render thread changes the surface state before the
  return observation.

## Visual evidence

Evidence is retained under the fixed Mini `$EVIDENCE_ROOT/flr0293-0001` role
path. Raw debugger output and frames remain outside Git; this ticket records
bounded hashes and conclusions.

## 2026-09-25 runtime result

One QEMU run reused the fixed FLR-0289 image and launched the existing
false-heavy FLR-0291 control. Target GDB attached successfully to the single
`flutter-auto` process and detached without a crash. The bounded debugger
output SHA-256 is
`38b4d159b53ff451cde7a0924a64588ef58b86397d786e26dd18013fa4b00e50`.

GDB resolved the process and shared-library state but reported no functions
matching `beginFrame` and no symbol for the expected Filament renderer
mangled name. The short all-thread backtrace therefore cannot identify the
internal return path. The runtime log SHA-256 is
`416b58e029dfe3fb4111aa6de62098e38d56db30d5e258df48444753f4202a59`; the QMP
frame SHA-256 remains
`3a5f5b2e7c9a934083620faaf14bfd52f5ed67c76f964e595c509edd7b67d374`.
Teardown passed with zero residual targets.

### Decision

The release image does not expose enough Filament symbols for a direct GDB
breakpoint. FLR-0293 is Waiting; FLR-0294 owns the existing
`FLR0026_SYNC_TRACE` runtime observation, which can distinguish FrameSkipper
fence timeout from another lifecycle cause without a source patch.
