# FLR-0273 — isolate post-activation render/surface visibility

- Status: Done
- Priority: High
- Owner: runtime render-content / Wayland surface / QMP validation roles
- Depends on: [FLR-0272](FLR-0272-diagnose-production-asset-loading-oom.md)
- Working log: `work/logs/2026-09-24-flr0273.md`

## Problem

FLR-0272 proves bounded production loading, native camera selection, a
nonzero effective camera transform, Scene insertion, draw, and Vulkan present.
Run 0303 still produces a grayscale QMP ROI with zero chromatic pixels. The
remaining boundary must be separated between rendered production content and
Wayland child-surface/compositor visibility.

## Facts

- The 0090 rootfs and active-camera contract are fixed inputs.
- Production `setActiveCamera` reaches request and completion, and the
  effective camera is nonzero.
- QMP captures are stable but have `chromatic_pixels=0` in the production ROI.
- Earlier fixture runs proved self-made/native geometry and 2D HUD pixels can
  coexist in QMP output.

## Hypotheses

1. Production model/material/scene content is rendered as the grayscale ROI,
   while the surface path itself is healthy.
2. Production draw output exists internally but the Wayland child surface is
   not imported or composed, while the fixture path may use a different
   surface contract.
3. UNKNOWN: a shared post-activation Vulkan/Filament state affects both paths.

## Success criteria

- Run the fixture control and production control with the same 0090 image,
  QMP profile, and teardown procedure.
- Preserve bounded runtime logs, QMP still/video frames, hashes, and ROI
  analysis for both controls.
- Identify the first boundary that differs, or explicitly retain UNKNOWN with
  the next smallest discriminator.
- Do not declare Fluorite 3D complete until actual colored 3D pixels are
  proven in the requested production/scene path.

## Non-goals

- No new camera payload format.
- No route/input transition until a stable 3D pixel gate is positive.
- No cleanup of shared Yocto downloads, sstate-cache, or active TMPDIR.

## Result

- The fixture control passed on the same rootfs and through the same QMP,
  swapchain, Wayland surface, and teardown path as production Run 0303.
- Fixture QMP initial ROI: `chromatic_pixels=131`, `max_chroma=191`.
- Fixture QMP stable frame 9 ROI: `chromatic_pixels=35`, `max_chroma=191`.
- Fixture markers: `CUBE_READY=1`, `CUBE_ATTACHED=1`,
  `DRAW_SUBMIT=3`, `DRAW_END=3`, `QUEUE_PRESENT=4`.
- Evidence directory:
  `/mnt/yocto/evidence/flr0273-0001`.
- QMP teardown passed with zero residual targets and zero residual QMP socket.

## Conclusion

The shared QEMU/Wayland/QMP path is capable of displaying colored native 3D.
Because production Run 0303 remained at `chromatic_pixels=0` while the fixture
passed on the same image, the next boundary is production model/material/
lighting/camera content after activation. This ticket does not declare
production Fluorite 3D complete.

## Verification plan

1. Revalidate the fixed receiver/image and absence of residual QEMU.
2. Run the proven fixture control once through QMP, filtered serial logs, and
   the same ROI analyzer.
3. Compare fixture and production marker/pixel matrices.
4. Only then select a minimal source change, if evidence justifies one.

## Next ticket

- FLR-0274 owns the production model/material/lighting visibility discriminator.
