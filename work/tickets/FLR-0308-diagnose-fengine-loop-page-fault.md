# FLR-0308 — diagnose FEngine loop page fault during production load

- Status: Waiting
- Priority: High
- Owner: Flutter engine loop / production asset-load runtime roles
- Created: 2026-09-25
- Predecessor: [FLR-0307](FLR-0307-probe-production-fragment-output-target.md)
- Working log: `work/logs/2026-09-25-flr0308.md`

## Objective

Reproduce and classify the guest page fault that stops the `FEngine::loop`
thread before production Sequoia reaches material setup. The goal is to make
the runtime reach the FLR-0307 output discriminator without guessing that
light or fragment color is the cause.

## Facts

- The FLR-0307 image passed Mini `do_patch`, component compile, and full image
  build.
- QEMU start, guest readiness, serial-exec app launch, QMP capture/video, and
  QMP teardown passed.
- The runtime selected a 60-item production model load plan and installed the
  FLR-0305 SUN.
- Before any production asset-loaded/material/draw marker or FLR-0307 marker,
  the guest journal recorded `FEngine::loop` PID 692 with `#PF` and
  `Oops: 0000 [#1]`.
- The parent `flutter-auto` remained alive; there was no OOM marker and no
  coredumpctl record.
- A one-model control (`limit=1`, `match=sequoia_ngp`, light enabled,
  emissive override disabled) reproduced the same page fault after about 35
  seconds. Therefore the 60-item queue is not sufficient as the sole cause.
- The fault RIP mapped into `/usr/lib/libLLVM.so.18.1`. The run-specific
  address was inside the executable LLVM mapping; the relative address is
  consistent with the historical FLR-0030 `0xb1d541` boundary, resolved there
  as `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)`.
- Guest LLVM symbolizers returned `??:0` for this release image because no
  matching debug symbols are installed. GDB attach itself passed and showed
  multiple `FEngine::loop`, `JobSystem::loop`, and `llvmpipe-*` threads.
- The one-model and fault-map QMP frames are byte-identical with native ROI
  `0/144000`; each captured video sequence is also stable.
- A one-model control with the FLR-0305 light environment omitted ran for 105
  seconds without a page fault, but it also produced no Vulkan present, asset,
  material, or draw marker. Its QMP frame SHA-256 was
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- FLR-0251/FLR-0286 remain positive controls for self-made 3D plus HUD, and
  FLR-0070 remains the historical production Sequoia plus HUD/color reference.

## Inferences

- The current FLR-0307 zero-pixel result is not evidence that the emissive
  parameter or light is ineffective; the material seam was never reached.
- The engine loop fault is the first observed runtime boundary in this run.

## Hypotheses

1. The full 60-item asynchronous production load queue triggers the fault.
   Result: weakened/falsified as the sole cause; `limit=1` reproduces it.
2. The current non-zero SUN probe is the first trigger for the present/LLVM
   path, while omitting the light leaves the runtime stalled before present.
   Prediction: an entity-present but zero-intensity SUN separates light
   creation from non-zero lighting/shader contribution.
3. The FLR-0307 patch is causal. Result: not supported; the one-model control
   omits `FLR0307_PRODUCTION_EMISSIVE_OVERRIDE` and reproduces the fault.

## Plan / PDCA

### Plan

Use the same fixed Mini image, one QEMU, serial-exec, and QMP evidence. Run the
smallest control first: the existing bounded production model selector with
the FLR-0305 light enabled and FLR-0307 override disabled. Compare only the
bounded markers, process state, journal fault, and QMP ROI against FLR-0307.

### Do

The one-model light-enabled control and a second fault-map reproduction were
executed on the same fixed image and QEMU contract. Both reached the initial
ViewTarget/light setup and reproduced the FEngine/LLVM fault boundary. The
light-disabled control did not fault, but it also never reached present or
asset setup. All three runs completed bounded QMP screenshot/video and clean
QMP teardown; the fault-map run also completed GDB attach, map inspection, and
LLVM symbolizer attempt.

### Check

The fault signature is reproducible and the library boundary is resolved to
`libLLVM.so.18.1`; line-level symbols remain UNKNOWN because debug symbols are
not present in the release image. The light-disabled result is a lifecycle
control, not a positive rendering result. The next check is a zero-intensity
SUN with the same one-model payload.

### Act

Add one opt-in zero-intensity mode to the existing FLR-0305 diagnostic light
through the Mac Devtool source and official patch flow. If it faults like the
normal SUN, light entity creation or present setup is implicated. If it
survives, the non-zero lighting/shader contribution is the next boundary. Do
not patch the emissive/material path before this A/B.
