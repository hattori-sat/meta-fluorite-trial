# FLR-0090 — fence completion boundary

- Status: Done
- Priority: High
- Owner: Filament Vulkan submit fence / llvmpipe worker boundary
- Created: 2026-09-12
- Depends on: [FLR-0089](FLR-0089-semaphore-completion-and-native-pixels.md)
- Working log: `work/logs/2026-09-12-flr0090.md`

## Work unit

Identify why the most recent Vulkan submit fence remains `VK_NOT_READY` at the
present call and which llvmpipe/driver worker owns the unfinished work. This
unit is evidence-first. Do not add a present workaround or skip the fence
until the owner and expected completion path are proven.

## Success criteria

- Capture one bounded symbolized observation of the submit fence and the
  llvmpipe/driver worker state while the fence is not ready.
- Correlate the observation with submit, fence status, present entry, and QMP
  native/HUD pixel results.
- Distinguish a command-stream execution failure from a driver worker wait,
  a guest fault, and a WSI-only problem.
- Preserve failed and successful evidence, hashes, and QMP-only teardown.
- If a source fix is selected, create a separate patch ticket after this
  evidence unit rather than changing present behavior here.

## Facts

- FLR-0089's corrected run had `vkQueueSubmit result=0` but
  `FLUORITE_VK_FENCE_STATUS result=1` immediately before present.
- The present wait semaphore matched the submit signal semaphore.
- The QMP HUD was visible (`1288` changed pixels) while the native region was
  black (`0` changed pixels), and `vkQueuePresentKHR` did not return in the
  bounded sample.
- A bounded GDB attach on the current image found `FEngine::loop` and several
  `llvmpipe-*` threads waiting in `libvulkan_lvp.so` through futex/condition
  variable frames. The GDB output SHA-256 is
  `4f9d74126c5fd6c92b22dcbbad4d83a796d16cd29ccba6a1430bc040eb08d79c`.
- The same GDB/QMP run reached the neutral fence status `VK_NOT_READY`, and
  its QMP native region remained at `0` changed pixels while the HUD had
  `1258` changed pixels. QMP teardown passed with zero residual processes.

## Inferences

- The first missing completion is before or inside driver execution of the
  submitted command stream, not merely a Flutter/Wayland overlay placement.
- A bounded GDB or syscall observation of the active worker is more valuable
  than another light, material, or present-mode experiment.
- The current evidence supports a stalled llvmpipe/Vulkan worker path before
  fence signaling; it does not identify the exact command or shader operation.

## Hypotheses

1. The llvmpipe worker cannot complete a command in the submitted stream.
2. The application/Filament command stream reaches an invalid or faulting
   operation before signaling the fence.
3. A guest fault or scheduler/driver wait prevents completion independently of
   the native scene content.

## UNKNOWN

- The first blocking symbol and owning thread.
- Whether a guest fault occurs in the current neutral-diagnostic image.
- Whether the self-made fixture and production scene fail at the same command.

## Plan / Do / Check / Act

### Plan

Reuse the current authoritative image and fixed QEMU flow. Capture one
bounded GDB/backtrace and the smallest relevant guest journal/syscall slice at
the `VK_NOT_READY` boundary. Keep one QEMU and stop only through QMP.

### Do

The FLR-0089 evidence and fixed Mini artifacts are ready. No source change
has been made for this ticket.

### Check

The bounded observation is complete. The GDB sample contained multiple
`llvmpipe-*` workers and `FEngine::loop` in `libvulkan_lvp.so` futex/condition
variable waits, with no crash signature in the selected sample. The QMP PPM
`$EVIDENCE_ROOT/flr0090-af24ec3/qemu-gdb/qmp-gdb-trace.ppm` has SHA-256
`26f2fb831b749e7c25610a9f1cc60e31546fa70d663bf8fdce0ca6bf9d42c453`;
native-region analysis is `changed_pixels=0`, HUD analysis is
`changed_pixels=1258`, and 16 QMP video frames were saved. The runtime
submit/fence/present markers were correlated before the GDB attach.

### Act

This evidence unit is closed. The unresolved exact command/operation is split
into [FLR-0091](FLR-0091-isolate-first-unfinished-command.md). No source
patch was made in FLR-0090.
