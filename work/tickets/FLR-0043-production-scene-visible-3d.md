# FLR-0043 — isolate production scene setup from proven native 3D path

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament scene/resource + Flutter/Wayland + target-validation roles
- Depends on: [FLR-0042](FLR-0042-trace-render-frame-present-boundary.md)
- Working log: `work/logs/2026-09-07-flr0043.md`

## Problem

FLR-0042 proved that the current image can display a self-made native Filament
cube and an independent Wayland SHM cube. The released Example Demo production
scene still shows the 2D HUD with a black native region in the same general
profile. The remaining problem is inside production scene/resource setup or
its interaction with the native render path.

## Success measure

- Identify the first production setup operation that diverges from the visible
  native fixture path, using runtime logs and QMP-only photos.
- Determine whether the production GLB, environment (skybox/indirect light),
  lights/shapes, camera selection, or their interaction prevents visible 3D.
- Produce a QMP-only screenshot with actual production 3D pixels, or record a
  bounded, evidence-backed blocker and the smallest next ticket.
- Keep Mac Devtool → official generated patch → `meta-fluorite-trial` commit →
  bundle → fixed Mini PC build as the only source-change path.

## Plan / PDCA

### Plan

- Reuse the fixed rootfs/profile and run one QEMU at a time.
- Start with runtime-only A/B variants already supported by the image, then
  patch only the first confirmed production boundary.
- Compare pure fixture, production setup with fixture, and production scene
  using the same candidate-region analysis.

### Facts

- Pure fixture: visible blue Filament cube, native candidate changed
  `5608/100000` in FLR-0042.
- SHM mock: visible 240x160 cube above the 2D HUD, region changed `38400/38400`.
- Previous production runs reached native Scene registration and Vulkan submit
  but remained HUD-only; environment/model interaction is still the leading
  production hypothesis, not a confirmed root cause.

### Hypotheses

1. Production environment setup (skybox or indirect light) blocks or delays
   the production render/present sequence.
2. A production GLB/material/resource upload remains incomplete or interacts
   with the environment path.
3. Production camera/scene selection produces a valid but visually empty view.

### UNKNOWN

- The exact production resource or operation that first diverges.
- Whether the released production scene itself can reach visible pixels after
  the minimal fixture boundary is retained as a control.

## Current result

- On the fixed current rootfs, production setup with model limit `0`, skybox
  skipped, indirect light skipped, and the native cube added to the production
  Scene remained HUD-only. The candidate region changed only `1270/100000`
  pixels, with the bbox confined to the HUD edge.
- Repeating the same A/B with production light limit `0` still produced
  HUD-only. All 37 production shapes reported `renderable=true`, while the
  candidate region changed only `819/100000` pixels, again confined to the HUD.
- These runs show that removing models, environment, and lights is not enough;
  production shape setup or production-scene coexistence remains a live
  boundary. This is not yet a production 3D success.

## Completed result

- The invalid 0194 patch was removed after the authoritative `do_patch` gate
  showed that the earlier 0187 patch already provides
  `FLR0027_NATIVE_SKIP_SHAPES`.
- Commit `240df8a` was bundled and applied to the fixed receiver. The
  authoritative `flutter-auto` patch, compile, package, and image tasks all
  succeeded; the rootfs used for the decisive run was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260907130705.ext4` with SHA-256
  `b98c48343db42e36915b3262f4e27c420915bb24d662ade0514f09f6d25e52f0`.
- With model and light limits set to `0`, skybox and indirect light skipped,
  `FLR0027_NATIVE_SKIP_SHAPES=1`, and
  `FLR0026_NATIVE_MINIMAL_GEOMETRY_IN_PRODUCTION=1`, the production Scene
  displayed the self-made blue Filament cube as QEMU pixels.
- The QMP-only screenshot is
  `work/evidence/flr0043/prod-shape-skip-current/prod-shape-skip.png`.
  In region `[200,100,400,250]`, `5608/100000` pixels changed and the cube
  bounding box was `[501,285,99,65]`. This matches the positive pure-native
  fixture geometry from FLR-0042.
- Runtime markers recorded `FLR0027_NATIVE_SKIP_SHAPES enabled=true`, native
  frame start, `QUEUE_PRESENT result=0`, `PRESENT_BOUNDARY_DONE`, and
  `COMMIT_DONE`. QMP shutdown completed with `host-qmp-quit`, and no QEMU or
  flutter-auto process remained.

This closes the setup-isolation question: the production Scene and native
present path can display 3D pixels when production shape setup is removed.
It does not yet prove that the released production GLB/shapes render.

## Next action

The Mac Devtool source experiment was committed as `6dcda4b`, and the official
Yocto `oe.patch.GitApplyTree` API generated a patch from it. The authoritative
recipe rejected that patch at `do_patch`: the earlier registered 0187 patch
already wraps shape setup with `FLR0027_NATIVE_SKIP_SHAPES`, while the Devtool
source parent used to generate 0194 did not contain that recipe-applied
change. The 0194 patch is therefore not registered in this layer.

FLR-0044 now owns the production shape/render path. It must compare shape
setup enabled versus skipped, then make the smallest source change only after
the first failing shape/resource operation is identified.
