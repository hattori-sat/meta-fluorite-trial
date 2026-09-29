# FLR-0026 opaque-clear diagnostic — 2026-08-31

## Outcome

The Mac → devtool source commit → generated patch → Git bundle → isolated mini-PC
receiver → authoritative image → Mac QEMU loop completed. The opaque diagnostic
clear did not appear in the QEMU framebuffer, while the Flutter 2D overlay and
CPU/GPU/Script metrics did appear. This moves the active boundary toward the
native Filament child-surface frame/present or Wayland composition path; visible
3D is still UNKNOWN.

## Facts

- Project feature tip: `9d7748ae0d2c1583a996974bcd0a63dcdcde5d36`.
- Devtool source commits: `22d78d9` (transparent-clear context baseline) and
  `81aaf71` (opaque diagnostic).
- Devtool generated patch was copied unchanged into
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0052-filament-view-opaque-clear-diagnostic.patch`.
- Generated/project patch SHA-256:
  `974b577bd7bacdf1b6f96b8fbac0be6987ff95b5a93dc169b4e351e6d5d41769`.
- Bundle SHA-256:
  `9f0f4b0ca59e2d0fceec6ec6b12d5a11347991ea2fd8c9bbc349c2252376b7e4`.
- Mini-PC receiver revision matched the project tip. `bitbake -e`, forced
  `flutter-auto:do_patch`, forced `flutter-auto:do_compile`, and full
  `agl-ivi-image-flutter` all succeeded.
- Image artifact hashes:
  - rootfs: `b43bbd13fd8b9cf7b8745f54c5664ebba2a60d760d21b257153aae955efbbeb0`
  - kernel: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
  - qemuboot: `83b022ed9171319dcaba0e5f646763716eb5f00c67c90a3414e1c08d021911cf`
- Fixed QEMU profile produced a 720×400 QMP PPM. The app was launched as the
  registered Wayland user, survived for more than one minute, and logged
  `vkCreateSwapchain: 720x400`.
- QEMU-only screenshot: `$QEMU_ARTIFACT_ROOT/opaque-22s.ppm` and the review copy
  `$QEMU_ARTIFACT_ROOT/opaque-22s.png`.
- Opaque diagnostic frame PPM SHA-256:
  `26b98a1b5588305e9fb0006ee5fed90df1dd181a900f7c0afd271e5d2b84d6da`.
- Whole-frame background comparison: `changed_pixels=24506`,
  `changed_ratio=0.08509027777777778`, bounding box `[0,7,696,393]`.
  The changed pixels are the 2D overlay and controls; exact green `(0,255,0)`
  pixel count was `0`.

## Interpretation

- **Fact:** 2D Flutter overlay, FPS, and non-zero CPU/GPU/Script metrics are
  visible; native initialization reaches swapchain creation; the process remains
  alive.
- **Inference:** the diagnostic clear is not reaching the visible QEMU
  framebuffer, so a pure Cube material/camera explanation is insufficient.
- **Hypothesis:** the Filament child surface is not presented, committed, placed,
  or composed into the visible region. The next diagnostic must observe
  `beginFrame/render/endFrame`, WSI present, and Wayland child commit/geometry.
- **UNKNOWN:** whether the first missing event is Filament `beginFrame`, Vulkan
  present, `wl_surface` buffer commit, or compositor z-order/geometry.

## Cleanup

QEMU was terminated through QMP `quit` after the run; no unrelated QEMU process
was retained.
