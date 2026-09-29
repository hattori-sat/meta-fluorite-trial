# FLR-0321 — trace post-binding vehicle visibility and draw-to-surface output

- Status: Done
- Priority: High
- Owner: Filament renderable visibility / camera-frustum / Vulkan-Wayland surface roles
- Created: 2026-09-25
- Predecessor: [FLR-0320](FLR-0320-trace-gltfio-texture-readiness-binding.md)
- Working log: `work/logs/2026-09-25-flr0321.md`

## Objective

Find the first boundary after successful gltfio material binding where the
production Sequoia geometry stops becoming visible QMP pixels. The accepted
path is:

`material binding → renderable visibility/camera → Filament draw → Vulkan target
pixels → Wayland/Flutter composition → QMP framebuffer`.

Do not add a new Light, replace the GLB, or force body color in this ticket.

## Success criteria

- Reuse the exact FLR-0320 Mini image/build/TMPDIR roles and one QMP run.
- Compare at least two plausible post-binding boundaries using bounded markers
  or existing runtime evidence before changing source.
- Distinguish camera/frustum or transform exclusion from draw/target/compositor
  loss using native ROI and existing draw/present markers.
- If source instrumentation is necessary, create it through the Mac Devtool
  source-Git → official `update-recipe` → canonical patch → Mini bundle flow.
- Record a QMP-only frame, bounded runtime slice, artifact identity, and QMP
  teardown. Keep this ticket open unless a same-frame vehicle pixel is proven
  or the first missing boundary is conclusively identified.
- The authoritative task path is Mini PC `do_patch` → component compile → full
  image → QEMU. Mac-side recipe tasks are optional diagnostics only and are not
  acceptance gates.
- Before any ROI or static-asset interpretation, save and display the complete
  QMP framebuffer. A GLB texture preview is not a runtime screenshot.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0320 proved the embedded emissive texture reaches the production
  `HeadLights` material instance after readiness.
- The same run reached `BEGIN_FRAME_TRUE`, Scene draw submit, Vulkan queue submit,
  and present markers, while native ROI `(440,220,400,360)` remained uniform
  black and the HUD ROI was visible.
- Historical FLR-0049 contains a same-frame vehicle silhouette and red light
  band, so the requested geometry is not inherently absent from the asset.
- The predecessor full QMP frame was captured at
  `/private/tmp/flr0320-qmp-manual.png` (1280x800): HUD/Scenes UI is visible,
  but the native candidate ROI is uniform black. The extracted GLB emission
  texture is a static resource preview, not QMP visual evidence.

### Candidate boundaries

| boundary | prediction if missing | bounded evidence |
| --- | --- | --- |
| camera/frustum/transform | renderable/material exists, but no vehicle draw reaches the native ROI | camera, culling, renderable-count and bounds markers; ROI remains black |
| Filament draw/target | renderable is visible and submitted, but target pixels remain black | draw/render-pass/readback markers; ROI remains black while HUD persists |
| Wayland/Flutter composition | native target has pixels, but final QMP ROI is black | native target/readback evidence differs from QMP frame |

### Hypotheses

1. The wide production camera or model transform places Sequoia outside the
   tested ROI, despite successful material binding.
2. The renderable exists but is culled or not attached to the submitted Scene
   after the primary/secondary attachment diagnostics.
3. Filament produces the draw but the Vulkan/Wayland path drops the native
   target before Flutter composition; HUD remains because it is a separate 2D
   path.

## Plan / PDCA

### Plan

1. Read existing camera, culling, renderable-count, draw, target, and
   composition markers and compare them with FLR-0049's positive evidence.
2. Run one bounded QMP reproduction without changing source.
3. Select the first missing boundary. Only then make a minimal Devtool source
   diagnostic or fix, if required.

### Do

Pending first post-binding boundary probe.

### Check

- PASS: predecessor proves gltfio texture readiness and emissiveMap binding.
- PASS: the same image's self-made LIT fixture produces `119716/144000`
  chromatic native ROI pixels with HUD, so the QEMU/Wayland/QMP target path is
  live.
- PASS: normal production Scene add, material enumeration, binding, true frame,
  draw submit, queue submit, and present all occur while the production native
  ROI remains `0/144000`; the HUD remains `2845` chromatic.
- PASS: the existing camera/culling and primary/secondary attachment A/Bs do
  not change that result.
- PASS: the attached 1024x1024 image is a static GLB texture atlas, not a QMP
  framebuffer; it proves embedded red-light data, not runtime visibility.
- DECISION: the first missing boundary is narrowed to production material or
  fragment-output participation after binding and before target pixels. This
  ticket's post-binding boundary gate is complete; the exact PaintColor
  predicate is a separate unit.

### Act

Close this boundary and continue in [FLR-0322](FLR-0322-trace-paintcolor-runtime-predicate.md).

- Keep the fixed handoff loop unchanged: Mac Devtool source commit and official
  patch generation, layer commit, Git bundle, then Mini authoritative gates.

## Visual evidence

The exact Mini image used for Iteration 1 is rootfs
`6f42b308555670880c523ab6e71ea6cc35d1aa60b79262144bdcaa3bfd99b15c`.

- Positive self-made fixture QMP full frame:
  `/mnt/yocto/evidence/flr0321-0001/qmp-full.ppm`, SHA-256
  `8e90907b5ca8dfb86eb2832f5e18d2d27bef0a10620fb8b37df941e43991bfbe`.
  Native ROI `(440,220,400,360)` is `119716/144000` chromatic; HUD ROI is
  `2845` chromatic.
- Normal primary-attached production QMP full frame:
  `/mnt/yocto/evidence/flr0321-0001/production-attached-qmp-full.ppm`,
  SHA-256 `6217e147d50b77adda17de936acabb9a93b5cdf9df240d34b88bf0e1acfaf6a0`.
  Native ROI is `0/144000` black; HUD ROI is `2845` chromatic.
- The user-supplied 1024x1024 image is an asset-texture preview, not a QMP
  screenshot. It is retained as resource evidence only; it cannot satisfy the
  same-frame vehicle-pixel acceptance gate.

The ticket is complete for its boundary question. Acceptance of production
Sequoia pixels remains open in FLR-0322 and its successors; this ticket does
not claim production 3D success.
