# FLR-0219 — trace final native Wayland composition after RGB-positive readback

- Status: Done
- Priority: High
- Owner: Wayland native-surface composition role
- Created: 2026-09-20
- Predecessor: [FLR-0218](FLR-0218-trace-swapchain-image-index-identity.md)
- Links: [working log](../logs/2026-09-20-flr0219.md)

## Work unit

Determine why the native swapchain image used for acquire, draw, readback, and
present contains RGB-positive pixels, while the final QMP frame shows the 2D
HUD but a black native 3D ROI. This ticket is diagnostic first; no source patch
is allowed until the first post-readback composition divergence is evidenced.

## Success criteria

- Reuse the fixed Podman/Devtool state, Mini receiver/build/TMPDIR, and QEMU
  harness from FLR-0218.
- Capture bounded evidence for the native surface lifecycle after present:
  Wayland attach/damage/frame/commit, compositor import or rejection, surface
  stacking/alpha/position, and final QMP pixels.
- Compare at least two composition hypotheses with a falsifiable observation.
- Retain one QMP-only screenshot and a bounded frame/hash index proving the
  final visible result.
- If a source change is required, use the locked official Devtool sequence:
  latest effective baseline → `modify --no-extract` → source commit →
  `update-recipe` → `finish` → canonical layer commit → bundle → Mini gates.

## Facts inherited from FLR-0218

- `FLUORITE_SWAPCHAIN_CURRENT_COLOR` reported image index 0 and image handle
  `0x7f1ec04558b0`; draw and readback reported the same handle.
- Native driver readback was RGB-positive for all `248000` native ROI pixels,
  with alpha 255 throughout.
- QMP showed a visible 2D HUD but a uniformly black native ROI; eight sampled
  frames were identical.
- Acquire and present both used index 0 and `vkQueuePresentKHR` returned 0.
- Image build, QEMU start/guest-ready, and teardown all passed.
- In the same run, `WAYLAND_DEBUG=client` recorded native
  `wl_surface@39.attach(wl_buffer@50)`, full damage, frame callback, and
  commit. `FLUORITE_VK_QUEUE_PRESENT_RETURN result=0` followed it.
- `agl-compositor.service` was active (MainPID 451); its address space had
  shared `memfd:mesa-shared` mappings and the bounded journal filter contained
  no import/error/warning line.
- Filament reported many renderable `FLR0026_SHAPE_READY` entities, but the
  final native draw marker was one `primitive_handle=231` with `index_count=3`.
- Native probe result was
  `nonzero_pixels=248000 chromatic_pixels=0 byte_sum=252960000
  max_rgb_byte=255`: RGB-positive but uniform, not proof of 3D geometry.
- FLR-0219 QMP-only frame SHA-256 is
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
  Native ROI `[300,250,620,400]` is uniform black while the HUD ROI is
  visible; eight captured frames have the same hash.
- The evidence hash index is
  `$EVIDENCE_ROOT/FLR-0219/flr0219-artifact-sha256.txt`.

## Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Native 3D pixels disappear between RGB-positive readback and final QMP frame | FLR-0218 runtime/QMP evidence |
| Where | Wayland native surface, compositor import/stacking, or QEMU scanout after present | First unproven boundary |
| When | After draw/readback and present, during final composition/display | Same image identity at draw/readback |
| Who | Filament Vulkan producer, Wayland client surface, compositor, QEMU display path | Component ownership |
| How | HUD is visible but native ROI is black | QMP ROI analysis |

## Hypotheses

1. The swapchain readback is a clear/placeholder or fallback output because the
   intended shape is not rasterized.
2. The render target contains geometry but the diagnostic readback path
   normalizes it to uniform white.
3. Wayland/compositor import or stacking removes the native buffer after the
   client commit.

## Plan / Do / Check / Act

### Plan

- Start with bounded runtime evidence only: `WAYLAND_DEBUG` lifecycle lines,
  compositor journal/systemd output, and one process-scoped syscall/debugger
  probe if needed.
- Compare the native surface identity and geometry with the QMP ROI.
- Stop once the first divergence is identified; do not add a speculative
  rendering patch.

### Do

- Reused the existing fixed artifact, receiver, build/TMPDIR, QEMU harness, and
  one QEMU run.
- Used the TCP serial path because the guest SSH service was not usable after
  the readiness probe; no second guest or QEMU was started.
- Launched Example Demo once with bounded Wayland, Filament target/readback,
  scene, and ViewTarget traces.
- Captured one QMP-only screenshot and eight 0.25-second frames, analyzed the
  native/HUD ROIs, saved the selected runtime and compositor state logs, then
  stopped the recorded app PID and quit QEMU through QMP.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Native surface lifecycle | attach/damage/frame/commit and present are correlated | PASS; import/release remains indirect | PASS WITH CONDITIONS |
| Native target content | readback proves actual geometry, not only non-zero bytes | uniform white, `chromatic_pixels=0` | FAIL for 3D proof |
| Composition result | final QMP frame is recorded | HUD visible, native ROI black, eight-frame stable | PASS |
| Teardown | only the recorded QEMU instance is stopped and residuals are zero | PASS | PASS |

### Act

- Close FLR-0219 as a bounded Wayland lifecycle diagnostic. The client-side
  lifecycle is positive, but the native readback is uniform white and therefore
  does not prove a rendered object. FLR-0220 owns the render-target content and
  shape discriminator; no Wayland source patch is justified by this run.

## Visual evidence

- QMP-only screenshot:
  `$EVIDENCE_ROOT/FLR-0219/q/flr0219-latest.ppm`
- Visible: 2D HUD and Scenes button. Not visible: native 3D ROI.
- Run/image identity: FLR-0219 fixed image and QEMU run.
- Native ROI: `changed_pixels=0`, `chromatic_pixels=0`; HUD ROI:
  `changed_pixels=2976`, `chromatic_pixels=2801`.
- Inherited screenshot SHA-256:
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.

## Decision

The client-side Wayland protocol sequence and Vulkan present return are not the
first observed failure. However, the native readback candidate is uniform
white, so the premise that an RGB-positive buffer contains 3D geometry is
false for this run. The next diagnostic must separate clear/placeholder output,
camera/material/primitive selection, and readback conversion before changing
Wayland composition.

## Unknowns

- Exact compositor import/release result for the attached native image.
- Whether the native surface's final stacking, alpha, position, or parent
  relationship matches the QMP ROI.
- Whether QMP captures the same output surface that the compositor presents.
- Whether the uniform-white native readback is clear/placeholder output or a
  real render-target result with lost geometry.

## PDCA checker

- Status: PASS WITH CONDITIONS
- Checked by:
- Findings: client attach/commit and Vulkan present passed; QMP evidence is
  stable; native readback is uniform white and does not establish 3D geometry.
  FLR-0220 owns the next boundary.
