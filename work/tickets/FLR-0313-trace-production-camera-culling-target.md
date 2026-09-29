# FLR-0313 — trace production camera, culling, and target visibility

- Status: Done
- Priority: High
- Owner: production camera/frustum/culling / render-target visibility roles
- Created: 2026-09-25
- Predecessor: [FLR-0312](FLR-0312-trace-production-post-load-renderable-material.md)
- Working log: `work/logs/2026-09-25-flr0313.md`

## Objective

Determine whether the valid production Sequoia renderables are transformed
into the active camera frustum and submitted to the visible target. Use the
existing runtime-only traces first; do not change camera or culling behavior
until their effective values are recorded.

## Success criteria

- One Mini-authoritative QEMU run with one `flutter-auto`, reusing the verified
  FLR-0312 image and normal light.
- Capture effective camera/profile/matrices, production world-transform
  samples, culling state, ViewTarget contract/frame markers, Vulkan submit and
  present, and kernel fault/OOM markers.
- Capture QMP screenshot plus eight-frame video and analyze the same native and
  HUD ROIs.
- Decide whether the first divergence is camera/frustum/culling, render-target
  ownership, or downstream renderer execution.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0312 proves 12 production renderables and 21 materials are valid and
  attached to the production Scene, yet the native ROI is black.
- Existing effective diagnostics include `FLR0302_PRODUCTION_TRANSFORM_TRACE`,
  `FLR0304_PRODUCTION_CAMERA_CULLING_TRACE`,
  `FLR0026_SCENE_STAGE_TRACE`, and ViewTarget frame/contract traces.
- The self-made LIT fixture remains a positive QMP control for the same
  compositor and Filament stack.

### Hypotheses

1. The production model transform or active camera places the vehicle outside
   the intended visible region.
2. Filament culling or layer/target state excludes the renderables despite
   valid material and Scene state.
3. Camera and culling are valid; the loss occurs at ViewTarget/renderer target
   execution after draw submission.

### UNKNOWN

- Effective camera matrices and vehicle world transform for this exact image.
- Whether disabling culling would change pixels; this must be a separate A/B
  only after the trace-only run.

## Plan / PDCA

### Plan

Run the existing trace-only flags with no behavior-changing override. Record
  the evidence before QMP teardown.

### Do

Ran the trace-only profile on the verified image with normal light and no
behavior-changing camera/culling override.

### Check

Compare camera/frustum/transform facts against the fixed native ROI and the
historical visible Sequoia frame; do not classify from logs alone.

### Act

Open a separate one-variable camera or culling patch ticket only if the
trace-only evidence justifies it.

## 2026-09-25 trace-only runtime result

### Facts

- The effective ViewTarget contract was
  `scene_native=false scene_default=true viewport=(0,0,1280,800)` with
  `surface=true subsurface=true parent_surface=true`.
- The effective camera was `(5,0,-5)` with non-identity projection and view
  matrices after initialization. The root transform was valid at `(0,0,0)`;
  four sampled renderable transforms were valid.
- `FLUORITE_VIEWTARGET_BEGIN_FRAME_TRUE` occurred 3 times, while
  `BEGIN_FRAME_FALSE` occurred 45,141 times. Draw submit/end and queue present
  each occurred 3 times before the known FEngine/libLLVM fault.
- QMP screenshot and all eight video frames shared SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
  Native ROI remained `0/144000` changed and `0` chromatic; the late HUD ROI
  was uniform white.
- Runtime-log SHA-256:
  `7746dd7f22d6a2477e14b49ab4bd1fb2124585299718e6d441437f6ced9e5bdc`.
- QMP quit and cleanup passed with zero residual targets and sockets.

### Inference

- The model is not absent because of an invalid transform, identity camera,
  zero-sized viewport, or missing parent surface. The current run has a
  severe frame-loop acquire/fence failure after model setup.
- Historical FLR-0296/0297 evidence shows that recovering the frame loop alone
  still left the production native ROI black. Therefore this ticket does not
  identify frame-loop failure as the sole production-3D cause.

### Act

- FLR-0313 is complete as a trace-only classification unit.
- FLR-0314 owns an existing emissive-output control, paired with the known
  frame-recovery and wide-camera controls, to test geometry/target visibility
  without relying on light response.
