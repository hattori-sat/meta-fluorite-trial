# FLR-0318 — A/B primary/secondary Scene attachment

- Status: Done
- Priority: High
- Owner: production model instancing / Scene attachment / depth visibility
- Created: 2026-09-25
- Predecessor: [FLR-0317](FLR-0317-trace-paintcolor-override-predicate.md)
- Working log: `work/logs/2026-09-25-flr0318.md`

## Objective

Test whether the current primary-model Scene attachment introduced after the
historical tail-light-positive run causes duplicate production geometry,
depth competition, or material visibility loss. Keep Light, camera, frame
recovery, image, and QMP profile fixed; change only an opt-in primary attach
skip.

## Success criteria

- The source change is made in the persistent Mac Devtool workspace, committed
  before official Yocto patch generation, and handed off with
  `devtool finish <recipe> <layer> --mode patch`.
- Mini `do_patch`, component compile, full image, and artifact hashes are
  recorded before runtime.
- Exactly one current-image QEMU run compares the primary-attach skip against
  the already-recorded current baseline.
- QMP evidence measures the same native ROI and explicitly checks for vehicle
  pixels and red tail-light pixels; HUD pixels and runtime Scene/renderable
  counts are retained.
- QMP quit and residual-process cleanup pass.

## Facts

- Historical FLR-0049 no-readback evidence shows a black Sequoia silhouette
  with red tail-light pixels and reports 25 entities / 14 renderables.
- Current FLR-0317 wide-camera evidence reaches frame-ready, asset load,
  Scene add, material creation, draw submit, and present, but the native ROI
  remains `0/144000` while HUD pixels survive.
- Current source commit `d138e54` changed the primary path from “not adding to
  Scene” to calling `addModelToScene`, while the secondary path still calls
  `createModelInstance` and `addModelToScene`.
- Current FLR-0317 runtime reports two Scene additions, 34 renderables, and
  42 materials for the selected Sequoia path.
- The FLR-0318 source commit `93ff371` added only the opt-in
  `FLUORITE_SKIP_PRIMARY_SCENE_ATTACH` gate. The official generated patch and
  canonical registration are at layer commit `afdbd80`.

## Hypotheses and falsifiers

1. Duplicate primary+secondary attachment is the visibility failure. If true,
   an opt-in primary-attach skip should restore nonzero native pixels and
   preferably the red tail-light pixels without changing Light or camera.
2. The primary attachment is not causal. If the skip leaves the native ROI at
   `0/144000` with the same HUD, then duplicate Scene attachment is rejected
   and the next unit must inspect GLB material/texture/sampler resources.
3. The skip changes model count but not output because the remaining secondary
   path is itself broken. This is distinguished by runtime counts and the
   unchanged QMP frame hash.

## Plan / PDCA

### Plan

1. Add one opt-in source gate around the primary `addModelToScene` call.
2. Generate the patch through the fixed Devtool workspace and official
   `devtool finish` handoff; do not hand-edit the generated patch.
3. Build on the fixed Mini receiver and run one QMP-only A/B profile.
4. Record the pixel verdict, then close this ticket and create the next unit.

### Do

- Added the opt-in primary-attachment skip in the persistent Mac Devtool
  source, committed it, and generated the layer patch through official
  `devtool finish`.
- Mini accepted the exact bundle tip `afdbd80`; `do_patch` and `do_compile`
  passed, and the full 11758-task image build completed successfully.
- Ran one QEMU with 4096 MiB, the fixed wide camera and frame-ready controls,
  and `FLUORITE_SKIP_PRIMARY_SCENE_ATTACH=1`. No Light, camera, or material
  value was changed.

### Check

- The skip marker was observed for primary model 2. The secondary model 14
  still loaded, added to Scene, created the expected PaintColor, HeadLights,
  Chrome, and other materials, and reached repeated `BEGIN_FRAME_TRUE` and
  draw-submit markers at camera `(800,450,800)`.
- QMP native ROI `(440,220,400,360)` remained `0/144000` changed, chromatic,
  or edge pixels with luma `[0,0]`. HUD ROI remained `2990` changed and
  `2845` chromatic.
- QMP frame PPM SHA-256:
  `7ba2163b67176366033b2990871586793d921b8c583c1fafef91ffab2411d3be`.
  Mac PNG SHA-256:
  `62fc205ee2df0784aa534b7d140cfdaa7784503075a541d1e42dd8a59b48cff9`.
  Eight-frame MP4 SHA-256:
  `afcb7e23ec5b746a2e798b4c9456719934c451366b29b3643b4016f8018b3807`.
  All eight raw PPM frames were byte-identical to the QMP still.
- Mini artifact hashes were recorded before runtime: rootfs
  `cf5a1df63a751e540c76cf704a2c1b6ee9529d4ba5853d6346030d5f018627fd`,
  kernel `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`,
  and qemuboot
  `fff3d407eca546eee7f1dcdf7a77a61c6c76867fa73a0e51b98da41df32c7789`.
- QMP quit was negotiated and cleanup reported zero residual targets and zero
  residual QMP sockets.

### Act

The primary-attachment hypothesis is rejected by the unchanged native ROI.
Retain the opt-in gate as diagnostic evidence only; the next unit is the
material/texture/sampler resource boundary.

## Visual evidence

QMP framebuffer artifact: `$EVIDENCE_ROOT/FLR-0318/flr0318-attach-skip.ppm`.
The screenshot shows the HUD and CPU/GPU graph but no vehicle or tail-light
pixels. The Mac-converted PNG and MP4 are retained outside Git and identified
by the hashes above.
