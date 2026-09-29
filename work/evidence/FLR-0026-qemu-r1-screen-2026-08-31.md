# FLR-0026 QEMU r1 screen evidence — 2026-08-31

## Facts

- The existing r13 rootfs was launched unchanged in a snapshot QEMU session.
- QEMU profile: qemux86-64, q35, TCG multi-thread, 2048 MiB, 12 vCPU,
  `qemu64` with SSSE3/SSE4.1/SSE4.2/POPCNT, virtio-vga, Cocoa display,
  USB tablet/keyboard, user networking, snapshot disk.
- QMP/HMP `screendump` created valid P6 PPM output at 720x400.
- QMP framebuffer SHA-256 was identical for boot, 5 seconds, 25 seconds,
  and 55 seconds: `a4972e7e976c35a3231772ee2e8b178ef588884dcd734859f7dcf0a519beb90e`.
- Comparing the 55-second sample against the boot sample reported zero changed
  pixels over the full 720x400 region.
- A macOS full-screen screenshot containing the QEMU window was also captured;
  the QEMU window itself was black. The external role-local screenshot SHA-256
  is `d42d133fdc2fb315b8c52643344d5edc1c21201d3b459a4d833edcc81d5600b`.
- The screenshot is intentionally outside Git because the full desktop image
  contains unrelated desktop/application content. Its role locator is
  `$QEMU_ARTIFACT_ROOT/flr0026-qemu-r1-host-screen.png`.

## Guest runtime

- The bundle was explicitly launched as `agl-driver` with
  `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0`.
- Runtime reached Application Id `fluorite`, Vulkan
  `VK_KHR_surface`/`VK_KHR_wayland_surface`, llvmpipe Mesa 24.0.7 / LLVM
  18.1.8, `All systems initialized`, and `lit.filamat` loading.
- The process later exited with SIGSEGV. The kernel reported an instruction
  pointer in the `flutter-auto` executable at address zero, and coredumpctl
  recorded a core for the `agl-driver` process.
- Batch gdb showed the crashing thread at an address inside the stripped
  `flutter-auto` executable. Correlation with the matching unstripped r13
  mini-PC binary resolves the instruction to
  `filament::IndirectLight::Builder::radiance(unsigned char, float3 const*)`.
  The caller is the asynchronous `IndirectLightSystem::setIndirectLight()`
  handler; the crash occurs while loading radiance data through a null data
  pointer. Another thread was active in LLVM, but LLVM is not the resolved
  immediate source-level crash site.
- No native entity/renderable/frame-completion marker or child Wayland
  attach/commit marker was present in this uninstrumented run.

## Verdict

| Boundary | Verdict | Evidence |
| --- | --- | --- |
| QEMU launch and 12-vCPU profile | PASS | serial boot and fixed command |
| QMP framebuffer capture | PASS | valid 720x400 PPM at four timepoints |
| Cocoa QEMU window capture | PASS | external host screenshot |
| QEMU visible screen content in r1 | FAIL | QEMU window and QMP framebuffer remained black |
| Flutter/Vulkan/Filament initialization | OBSERVED | guest runtime log |
| Native entity/renderable/frame completion | UNKNOWN | no markers yet |
| Wayland child attach/commit | UNKNOWN | no protocol marker yet |
| Visible 3D pixel | FAIL for r1 | zero changed pixels and SIGSEGV |

## Interpretation

This run proves that the QMP capture path is not merely returning an invalid
image: it agrees with the direct macOS screenshot of the QEMU window. It does
not prove that the full-scene 2D path is always absent, because the earlier
full-scene reference used a different image/session and showed startup 2D
overlay/menu activity. The current r1 fixture process crashes before that
display path can be accepted.

The exact crash source is now localized to the native default indirect-light
path. The r13 fixture calls `poGetDefaultIndirectLight()`, which is deserialized
as `DefaultIndirectLight` and passed to `setIndirectLight()`. That function
posts a callback holding a raw `DefaultIndirectLight*`; the callback can then
read the owned vectors after their owner has changed or been destroyed. The
historical 0043 2D-success path used the production `HdrIndirectLight.asset`
scene instead, so it did not exercise this vector callback in the same way.
The next patch snapshots the small light payload before posting, then reruns
the same QEMU profile and pixel capture.

## r2c rerun — 2026-08-31

### Facts

- The same r13 kernel, rootfs, QEMU machine profile, and release bundle were
  used again. The guest was entered through the QEMU serial console because
  the image did not accept the host SSH key.
- `/usr/bin/flutter-auto` was launched as root with
  `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0`, using the
  installed Fluorite Example Demo bundle.
- QMP/HMP `screendump` captured QEMU-only PPM images at approximately 3, 11,
  and 26 seconds after launch. All were 720x400 with SHA-256
  `a4972e7e976c35a3231772ee2e8b178ef588884dcd734859f7dcf0a519beb90e`.
- Each image compared against RGB background `0,0,0` had
  `changed_pixels=0`, `changed_ratio=0.0`, and no changed-pixel bounding box.
- The PPM payload begins with zero-valued RGB bytes, and the converted
  inspection PNG is also fully black. The QMP capture is therefore an
  attributable QEMU display capture, not a host desktop screenshot.
- Runtime logged `Application Id: fluorite`, Vulkan Wayland extensions,
  llvmpipe Mesa 24.0.7 / LLVM 18.1.8, `All systems initialized`, and then
  `lit.filamat` loading. It exited with SIGSEGV immediately after the
  material-load phase; no 2D overlay or CPU-usage panel appeared before the
  crash.

### Verdict

| Boundary | Verdict | Evidence |
| --- | --- | --- |
| Guest boot and serial-console login | PASS | r2c terminal session |
| `flutter-auto` re-execution | PASS until crash | `/tmp/flr0026-r2c-flutter.log` in the guest session |
| 2D UI display | FAIL for r2c | all QMP frames black |
| CPU usage display | UNKNOWN | no pixels or log marker; process crashed first |
| QEMU-only screen capture | PASS | three valid P6 PPM files, zero changed pixels |
| Visible 3D pixel | FAIL for r2c | black frames and SIGSEGV |

### Comparison with prior 2D evidence

The prior 0043 stable run is explicitly recorded in
`work/evidence/FLR-0019-2026-08-23-0043-runtime.md` (historical commit
`0547f54`): it showed `FPS: 20 / 60`, changing non-zero CPU/GPU/Script metrics,
2D controls, the Scenes menu, and process survival beyond 55 seconds. The
current r2c artifact is not that production-scene artifact: it replaces the
`SceneView` payload with the self-made fixture and crashes before Flutter can
paint the overlay. Therefore the missing 2D in r2c is a confirmed diagnostic
regression caused by the fixture's earlier native crash boundary, not evidence
that the previously proven 2D path never existed. CPU usage for r2c remains
UNKNOWN because no frame reached the overlay; the historical CPU metric is
PASS for the 0043 run only.

The source-level comparison is now sufficient to test the first fix: the
production scene's `HdrIndirectLight` path and the fixture's
`DefaultIndirectLight` path are distinct, and only the latter reaches the
crashing `radiance()` callback in this run.
