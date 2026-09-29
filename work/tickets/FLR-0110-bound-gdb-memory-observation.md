# FLR-0110 — bound guest GDB memory for production observation

- Status: Done
- Priority: High
- Owner: runtime-debug + target-validation roles
- Created: 2026-09-12
- Depends on: [FLR-0109](FLR-0109-present-wsi-blocked-owner.md), [FLR-0104](FLR-0104-runtime-debug-tools.md)
- Working log: `work/logs/2026-09-12-flr0110.md`

## Work unit

Make production GDB observation safe for the fixed 2 GiB guest. The current
full-symbol attach procedure must not consume the application or change the
visual verdict. This ticket owns the debugger-harness/resource boundary only;
it does not patch Vulkan, WSI, semaphore, fence, compositor, Filament, or
scene behavior.

## Success criteria

- Reuse the fixed debug image, receiver, build/TMPDIR, and one-QEMU contract.
- Capture a normal-running QMP frame before attaching a debugger.
- Attach to the unique normal `flutter-auto` PID after verifying its Vulkan map.
- Use a bounded, low-memory debugger configuration and retain raw output.
- The guest must not report an OOM kill of `flutter-auto`; GDB result is
  classified as usable, procedure failure, or UNKNOWN with evidence.
- QMP quit and residual target/socket checks must pass.
- Only after this ticket succeeds may FLR-0109 resume owner classification.

## Plan / Do / Check / Act

### Plan

1. Reproduce the r11 attach with the same image and normal process-map gate.
2. Disable automatic symbol loading and request only candidate thread
   registers/backtraces, keeping the command foreground and bounded.
3. Compare memory/OOM evidence and QMP frame with r11, then hand the usable
   result back to FLR-0109.

### Do

- FLR-0110 was created after r11 exposed a distinct debugger-resource failure.
- No source or image change is included in this unit.
- The first QEMU start input used a malformed rootfs SHA and was rejected by
  preflight before QEMU; the corrected invocation passed.
- The normal production PID 628 mapped `libvulkan_lvp.so` and
  `libflutter_engine.so`. QMP before GDB showed native `0/223200` and HUD
  `1294/100000` pixels.
- The first low-memory attempt kept the target alive but still transferred
  remote libraries and timed out with GDB RC `124`.
- The corrected r2 used `sysroot=/` and `auto-solib-add off`; GDB RC was `0`,
  target RSS stayed at `1124892` kB, no OOM marker appeared, and selected
  candidate PCs/backtraces were retained. Evidence:
  `work/evidence/FLR-0110-low-memory-gdb-2026-09-12.md`.

### Check

- PASS: low-memory GDB observation, post-detach QMP capture, and cleanup.

### Act

- First try guest GDB with `set auto-solib-add off` and no broad symbol load.
- Keep `/proc/meminfo`, target RSS, kernel OOM markers, and GDB return status
  in the same serial session; do not use a second serial connection while the
  target is stopped.
- Hand the bounded procedure back to FLR-0109; no source change is justified
  by this debugger-resource ticket.

## Facts inherited from r11

- The fixed rootfs is 2 GiB RAM with no swap in the QEMU profile.
- Normal production PID 633 mapped `libvulkan_lvp.so`; the pre-attach QMP
  frame had native candidate `0/223200` and HUD `1288/100000` changed pixels.
- The full-symbol GDB client reached `gdb` RSS about 600 MiB while
  `flutter-auto` was about 1 GiB; the kernel OOM killer terminated PID 633.
- The GDB client returned `124` from its bounded timeout and gdbserver reported
  an LWP reap warning. No thread backtrace from that run is usable.
- QMP quit accepted capabilities/quit and cleanup reported zero residual
  targets and zero residual QMP sockets.

## Conclusion

The low-memory guest GDB procedure is reproducible and safe for the current
2 GiB/no-swap image. FLR-0109 can resume its present/WSI owner classification
using the r2 settings and the same one-session collection contract.

## UNKNOWN

- Whether raw, no-symbol GDB can expose usable non-current PCs in this guest.
- Whether the missing queue-present return belongs to any selected candidate
  thread after the debugger no longer changes memory pressure.
