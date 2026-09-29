# FLR-0329 — classify native readback fence timeout behavior

- Status: Done
- Priority: High
- Owner: Filament Vulkan readback fence / llvmpipe queue completion
- Created: 2026-09-25
- Predecessor: [FLR-0328](FLR-0328-trace-readback-completion-boundary.md)
- Working log: `work/logs/2026-09-25-flr0329.md`

## Objective

Use the existing fixed image and one environment-only runtime A/B to determine
whether the readback fence is blocked indefinitely or returns a bounded
timeout. Do not change source, Light, camera, material, Scene ownership,
Wayland stacking, or route behavior.

## Success criteria

- The same rootfs/build/TMPDIR contract is reused; no new image or TMPDIR.
- The only runtime variable is the existing `FLR0026_TARGET_PROBE` fence
  timeout control.
- QMP full-frame evidence is captured before ROI analysis.
- The bounded log records `FENCE_WAIT result`, timeout/error handling, or an
  explicit absence with process state.
- QMP teardown leaves zero target processes and zero QMP sockets.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0328 reached `FENCE_WAIT_BEGIN` after a successful readback queue submit
  and task post, but no fence result within the observation window.
- The same frame had visible HUD pixels and a uniform black native ROI.

### Hypotheses

1. The fence returns `VK_TIMEOUT` under the bounded diagnostic timeout; the
   normal `UINT64_MAX` wait hides this as an apparent hang.
2. The fence never completes because the readback command cannot progress on
   the current queue/image path; the bounded probe will still return only if
   the driver honors the timeout.
3. The marker output is delayed or lost independently of the fence result;
   process/thread state and the timeout marker distinguish this from a real
   wait behavior.

### UNKNOWN

- Whether the fence is signaled by a later queue/finish cycle.
- Whether the fence issue is the cause of the missing visible 3D pixels or
  only a diagnostic readback symptom.

## Result

- One fixed-image QMP run changed only the existing
  `FLR0026_TARGET_PROBE=1` environment control.
- The runtime reached `FLR0026_VK_READBACK_QUEUE_SUBMIT result=0`,
  `FLR0026_VK_READBACK_TASK_POSTED`, and
  `FLR0026_VK_READBACK_FENCE_WAIT_BEGIN`, then returned
  `FLR0026_VK_READBACK_FENCE_WAIT result=2` followed by
  `FLR0026_VK_READBACK_FENCE_TIMEOUT` and
  `FLR0026_VK_READBACK_CLEANUP_BEGIN/END`.
- `result=2` is `VK_TIMEOUT` for this Vulkan call. The earlier unbounded run
  therefore did not merely omit a log line; it waited indefinitely until QEMU
  teardown.
- QMP full-frame PPM:
  `/mnt/yocto/evidence/flr0329-0001/qemu/qmp-0329-bounded-fence-full.ppm`,
  SHA-256
  `8cd43ba1fc78f88da019677a247fe968dc9c7a356b87413310c08f1a3313cf15`.
  Native ROI `(440,220,400,360)` is uniform black (`0/144000` chromatic);
  HUD ROI is positive (`2845` chromatic).
- Bounded serial output:
  `/mnt/yocto/evidence/flr0329-0001/qemu/serial-0329-bounded-fence.output`,
  SHA-256
  `c1e66170916cb792680100702e4a73067659614911553ef66d067f59e0b3b1c7`.
- QMP teardown passed with `residual_targets=0` and `residual_qmp=0`.

This classifies the readback fence behavior but does not prove that the fence
is the root cause of missing visible 3D pixels. FLR-0330 owns a no-readback
runtime A/B against the same production control.

## Plan / PDCA

1. Reuse the fixed image and one QMP run.
2. Launch the same production UNLIT/readback control with
   `FLR0026_TARGET_PROBE=1` as the only new variable.
3. Capture one full QMP frame, extract only the bounded fence markers, and
   classify the first observed completion event.
4. If a source change becomes necessary, stop and create a separate source
   ticket using the Mac Devtool → source commit → official patch → layer
   commit → bundle → Mini build flow.

## Stop conditions

- Do not treat a fence timeout as proof that Light or camera is broken.
- Do not patch around the fence before the bounded result and Vulkan call
  contract are recorded.
