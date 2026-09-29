# FLR-0108 evidence — production pipeline boundary (2026-09-12)

## Outcome

The production graphics pipeline does return successfully on the fixed debug
image. The first missing operation in this bounded run is after RenderPass
execution, at the queue-present return/WSI handoff. This closes the pipeline
creation hypothesis without claiming a source-level root cause.

## Fixed identity and control

- Layer/receiver revision: `59be8cfa625c35ea61153300a51956a01d46dd55`.
- Build role: `$BUILD_DIR`.
- TMPDIR role: `$BUILD_TMPDIR`.
- Machine: `qemux86-64`.
- Rootfs SHA-256:
  `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`.
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP run evidence root: `$RECEIVER/evidence/flr0108-r1/`.
- One QEMU was used; the existing short QMP alias was reused only as a
  symlink to the fixed evidence root.

## Runtime gates

- QEMU preflight: PASS.
- QEMU start: PASS.
- Guest SSH ready: PASS.
- GDBserver launch and bounded GDB client launch: PASS.
- QMP screendump and six-frame QMP video: PASS.
- QMP quit: PASS (`capabilities=negotiated quit=accepted`).
- Residual target processes and QMP sockets: PASS (`0/0`).

## GDB evidence

The guest GDB client loaded the installed target debug symbols and stopped at
the first production `lvp_CreateGraphicsPipelines` call:

```text
FLR0108_LVP_ENTRY hit=1 pc=0x7fffed37edd0
=> lvp_CreateGraphicsPipelines
FLR0108_LVP_REGS rdi=0x555556a76d00 rsi=0x7fffb0132870 rdx=0x1 rcx=0x7fffc43f0190
#0 lvp_CreateGraphicsPipelines (...) at lvp_pipeline.c:1046
Temporary breakpoint 2 at 0x7fffc52fa507
FLR0108_LVP_RETURN pc=0x7fffc52fa507 rax=(nil)
=> 0x7fffc52fa507: mov %eax,%ebp
[Inferior 1 (process 646) detached]
```

The GDB record identifies the process (`646`) and the first observed thread
(`646.711`). The return breakpoint was reached with `rax=(nil)`; the probe
therefore did not observe a non-returning outer lavapipe graphics-pipeline
call. The raw serial evidence is
`$RECEIVER/evidence/flr0108-r1/lvp-extract-serial.log`, SHA-256
`5e1a8afd4e49872d766c1be4174953ccf6a442f6b15c9fcfbfe80f21c6dc369c`.

## Marker order

The production marker stream recorded six effective pipeline inputs. All six
reached `FLR0026_GRAPHICS_PIPELINE_CREATE_DONE` and
`FLUORITE_VK_PIPELINE_CREATE_RESULT result=0`. Their measured durations were
approximately 49,143 microseconds, 6,853 microseconds, 2,665 microseconds,
22,032,407 microseconds, 8,179 microseconds, and 4,707 microseconds. The
fourth pipeline is very slow, but it returned success in this run.

The later RenderPass stream contained paired begin/end markers, including
production command counts `647`, `231`, `30`, `3`, `87`, and `524`. The
selected output then reached:

```text
FLUORITE_VK_QUEUE_PRESENT_ENTER index=0 wait=true ...
FLR0026_VK_QUEUE_PRESENT_BEGIN queue=... swapchain=... index=0
```

No queue-present return, outer present return, or present-done marker followed
within the bounded observation. The raw marker output is included in
`$RECEIVER/evidence/flr0108-r1/lvp-extract-serial.log`.

## QMP visual evidence

- Late QMP PPM:
  `$RECEIVER/evidence/flr0108-r1/lvp-pipeline-late.ppm`.
- PPM SHA-256:
  `374d4692378c9ab0c68233d77d439fbfa4bd705c00aff7223b03d490a3add8b2`.
- Dimensions: `1280x800`.
- Native candidate region `[300,80,620,360]`: `0/223200` changed pixels;
  bounding box `null`.
- HUD region `[200,100,400,250]`: `1256/100000` changed pixels;
  bounding box `[200,113,29,66]`.
- QMP video directory:
  `$RECEIVER/evidence/flr0108-r1/lvp-pipeline-frames/`.
- All six video frames have the same SHA-256 as the late PPM, so the captured
  output is visually static during the sample.

The frame shows the Fluorite HUD and controls over a black native region. This
is consistent with the marker boundary: pipeline creation and RenderPass
execution complete, but present does not provide a recorded return.

## Kernel and process evidence

At the end of the run there was one `flutter-auto` under one gdbserver. The
guest reported approximately `608 MiB` available memory and no swap. The
kernel also reported the known userspace OOPS at
`0x7fffee804541` in `FEngine::loop` (PID 722 in this run). No stack proving
that this OOPS caused the queue-present block was captured; causality remains
UNKNOWN. The raw bounded status evidence is
`$RECEIVER/evidence/flr0108-r1/lvp-status-serial-3.log`, SHA-256
`1a4c848a2bab535f70fc158eaedbf9d11e47b56c5e10277d017e4537fe7d9570`.

## Facts, inferences, and hypotheses

### Facts

- The first observed outer lavapipe graphics-pipeline call returned normally.
- All six pipeline-create result markers were successful.
- Selected RenderPass begin/end markers were paired.
- Queue-present enter/begin appeared without a bounded return marker.
- QMP showed HUD pixels but no native candidate pixels.

### Inferences

- The first observed missing operation is the queue-present return/WSI handoff,
  not graphics-pipeline creation.
- Composition/occlusion cannot yet be selected as the primary explanation,
  because the present operation has not produced a recorded return in this
  run.

### Hypothesis result

1. Production-specific inputs block inside pipeline creation: **rejected for
   this run**. The observed outer call returned, and all six pipeline results
   were successful.
2. Pipeline creation succeeds and divergence is later command/present:
   **supported and narrowed to present/WSI** by the missing return marker.
3. Rendering completes but composition hides it: **open as a downstream
   possibility**, not the first observed divergence.

## UNKNOWN

- The exact blocking owner inside `vkQueuePresentKHR`/WSI.
- Whether the fourth pipeline's 22-second compile is a performance symptom or
  contributes to the later state.
- Whether the kernel OOPS and the present wait are causally related.
- Whether production and fixture differ in a later semaphore, fence, or
  compositor handoff state.

## Next ticket

FLR-0109 owns the next independent diagnostic unit: identify the present/WSI
blocked owner and separate it from the known OOPS using a bounded present
backtrace/syscall observation. No source-fix patch is justified by FLR-0108
alone.
