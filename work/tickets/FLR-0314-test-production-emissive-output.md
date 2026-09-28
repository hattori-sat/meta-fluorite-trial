# FLR-0314 — test production Sequoia emissive output visibility

- Status: Done
- Priority: High
- Owner: production material output / camera and target visibility roles
- Created: 2026-09-25
- Predecessor: [FLR-0313](FLR-0313-trace-production-camera-culling-target.md)
- Working log: `work/logs/2026-09-25-flr0314.md`

## Objective

Test whether the production Sequoia geometry reaches the visible target when
the first body material receives the existing opt-in emissive override. Keep
the production model and HUD, but use the established frame-recovery and wide
camera diagnostics so a missing light response is not mistaken for missing
geometry.

## Success criteria

- One Mini-authoritative QEMU run with one `flutter-auto` and no source/image
  change.
- The only new behavior variable is
  `FLR0307_PRODUCTION_EMISSIVE_OVERRIDE=1`; frame recovery and wide camera are
  recorded diagnostic controls from prior tickets.
- Capture bounded material-override, Scene/draw/present, frame-loop, kernel,
  and OOM markers before teardown.
- QMP screenshot/video proves or falsifies colored production pixels in the
  same native ROI, with HUD ROI and clean teardown recorded.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0312 proves 12 production renderables and 21 valid materials.
- FLR-0313 proves valid camera/transform/target metadata but a severe
  `beginFrame=false` flood.
- FLR-0296/0297 prove the fence-ready diagnostic can restore frame progress,
  but did not prove production vehicle pixels without emissive output.
- The source already contains the opt-in `FLR0307_PRODUCTION_EMISSIVE_OVERRIDE`
  branch for `sequoia_ngp.glb` material `emissiveFactor`.

### Hypotheses

1. Emissive output produces visible vehicle pixels, isolating the failure to
   light/shaded-material evaluation.
2. Emissive output remains black, so the failure is downstream in target,
   camera, culling, or renderer execution.

### UNKNOWN

- Whether the current image's selected body material exposes
  `emissiveFactor` at runtime.
- Whether the late FEngine fault allows enough recovered frames for a visual
  verdict.

## Plan / PDCA

### Plan

Reuse the verified image and QMP profile. Add the emissive override to the
normal-light production run, retain the frame-ready and wide-camera controls,
and capture the guest log before QMP quit.

### Do

Ran the existing emissive override with frame recovery, wide camera, normal
light, and the verified one-model production profile.

### Check

Compare material override marker, native chromatic pixels, and frame/present
counts against FLR-0313 and FLR-0296.

### Act

If emissive pixels appear, open a separate minimal light/material fix ticket.
If they do not, keep light from the critical path and trace the target/renderer
contract instead.

## 2026-09-25 runtime result

### Facts

- Frame recovery succeeded: `FLUORITE_VIEWTARGET_BEGIN_FRAME_TRUE=19` and
  `BEGIN_FRAME_FALSE=0`; one queue present was recorded before the known
  FEngine/libLLVM fault.
- The existing override marker was emitted once for
  `entity=352 primitive=0 material=Glass value=(1,0,1)`. It did not target
  the vehicle body material `PaintColor` on entity 336.
- QMP screenshot and all eight video frames shared SHA-256
  `5aceb5d3c9f997ac2f832b6f8389e4fc6fbd205da2df2c13eca92a85c3f1fe74`.
- Native ROI remained `0/144000` changed and `0` chromatic; HUD ROI had
  `2990` changed and `2845` chromatic pixels.
- Runtime-log SHA-256:
  `d86e5e45ee0eedf40e5f4cc6ad22f1b5bcbfd1f49e75a49ece572dc71e2ad4fc`.
- QMP quit and cleanup passed with zero residual targets and sockets.

### Inference

- The test did not prove that body emissive output is invisible, because the
  existing opt-in branch intentionally stops at the first material and that
  material is `Glass`, not `PaintColor`.
- It did prove that frame recovery and a one-time emissive change on the first
  production material do not by themselves produce native pixels.

### Act

- FLR-0314 is complete as a control-scope check.
- FLR-0315 owns the minimal Mac Devtool source change that targets the known
  production body material `PaintColor` only when the existing opt-in variable
  is set. The generated patch must be applied and verified on Mini before any
  conclusion about light response.
