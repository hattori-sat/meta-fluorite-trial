# FLR-0291 — isolate beginFrame failure after native-surface attach

- Status: Waiting
- Priority: High
- Owner: Filament renderer beginFrame / Vulkan swapchain lifecycle
- Created: 2026-09-25
- Predecessor: [FLR-0290](FLR-0290-observe-diagnostic-surface-alpha-stacking.md)
- Working log: `work/logs/2026-09-25-flr0291.md`

## Objective

Identify why Filament `renderer->beginFrame` returns false almost continuously
after the diagnostic native surface is attached, even though Wayland has no
protocol error and the swapchain/native surface objects exist.

## Acceptance gate

Correlate a bounded `beginFrame=false` sample with swapchain, driver lifecycle,
present, and Wayland state. Identify the first missing or rejected lifecycle
step. Do not call a QMP black frame a surface-alpha result until beginFrame is
healthy.

## Facts

- FLR-0290 saw `beginFrame=false` 26534 times and `true` 4 times.
- Wayland attach/damage/commit/release and `place_above` succeeded with zero
  protocol errors.
- The renderer, swapchain, native display/surface, parent surface, and
  subsurface were all present in the begin-frame probe.
- The same fixed image's direct Filament fixture can render HUD plus colored
  3D, so this is a diagnostic native-surface lifecycle boundary.

## Hypotheses

1. The native surface/swapchain is not in a presentable state when Filament
   begins the frame.
2. Vulkan acquire or surface status rejects the frame without a Wayland error.
3. The diagnostic scene's repeated scene/light setup changes renderer state
   before beginFrame.

## Verification plan

- Reuse the fixed FLR-0289 image and one-QEMU harness.
- Add only existing driver/swapchain lifecycle traces and retain the same
  translucent diagnostic control.
- Correlate the first `beginFrame=false` with acquire, swapchain, present, and
  Wayland markers; keep raw logs outside Git and commit only bounded hashes and
  conclusions.
- If a source change is needed, create another ticket after the first rejected
  lifecycle step is proven.

## Unknowns

- Whether `beginFrame=false` is caused by swapchain image acquisition,
  surface size/visibility, or a repeated scene setup side effect.

## 2026-09-25 runtime result

The fixed FLR-0289 image was run once with the existing translucent diagnostic
control, one QEMU, and 4096 MiB. QEMU start, guest readiness, explicit
`flutter-auto` launch, QMP capture, and QMP teardown all passed. The full guest
log was saved before teardown at the fixed Mini evidence path; log SHA-256 is
`9b2a331f1bef14a4bca7c2125ecbae5f35af2d88985799b9b2417be3004c33e2`.

The QMP frame SHA-256 is
`3a5f5b2e7c9a934083620faaf14bfd52f5ed67c76f964e595c509edd7b67d374`; all
twelve bounded video frames have the same hash. Native ROI `(440,220,400,360)`
was `144000/144000` changed but only `2/144000` chromatic, with
`143998/144000` pixels at `(224,224,224)`. The two chromatic pixels were a
small blue marker, not recognizable Sequoia or a light. HUD ROI
`(1120,0,160,80)` was uniform `(224,224,224)` with zero edge and chromatic
pixels. A QMP-only view of this frame is retained outside Git at
`/mnt/yocto/evidence/flr0291-0001/begin-frame.ppm`.

The bounded log contains 4 `FLUORITE_VIEWTARGET_BEGIN_FRAME_TRUE` markers and
9,113 `FLUORITE_VIEWTARGET_BEGIN_FRAME_FALSE` markers. The begin-frame probe
reports all renderer/swapchain/native/parent/subsurface objects present,
`wayland_error=0`, and `native_size=1280x800`, while `frame_started=false`.
Scene draw submit/end markers are paired 4/4 and queue-present-begin occurs
twice. QMP quit was accepted and cleanup found no residual QEMU, runqemu,
flutter-auto, or QMP socket.

### Decision

FLR-0291 proves the current first actionable boundary: after native-surface
attachment, Filament cannot sustain `beginFrame`. This run does not justify a
light, camera, material, or alpha patch. The production Sequoia light verdict
remains UNKNOWN until the swapchain/acquire rejection is exposed or the exact
historical one-light control is replayed under a healthy frame lifecycle.

FLR-0291 is Waiting. FLR-0292 owns the next one-variable swapchain
configuration A/B.
