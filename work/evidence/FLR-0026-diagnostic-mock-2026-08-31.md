# FLR-0026 diagnostic Flutter 3D mock — 2026-08-31

## Outcome sought

Make an unmistakable 3D-shaped object visible in the same central candidate
region used for native Filament validation, while keeping the native
`SceneView` in the widget tree. This is a diagnostic split, not evidence that
native Filament rendered the object.

## Facts

- The QMP-only screenshots with the transparent Filament path showed the
  expected 2D profiling overlay and controls, but the candidate region
  `[200,100,400,250]` stayed black.
- The `0058` explicit child-surface commit test produced a full-black QMP
  frame and did not resolve the native `beginFrame` starvation; it is not
  enabled for this mock build.
- The app source was edited on the Mac-side file copied from the persistent
  Devtool source, copied back into that same Devtool workspace, and committed
  there as `a107000` (`diag: show explicit Flutter 3D mock overlay`).
- Devtool generated the application patch
  `0022-filament_scene-diagnostic-flutter-3d-mock-devtool.patch`.
  Its SHA256 is
  `88d583c5161ff7624fdba71d98c92981c74a0d465eedcf1930a2c7436b526f92`.
- The previously generated native flush patch was also copied unchanged into
  `meta-fluorite-trial`; its SHA256 is
  `6b620eaa2df1c24b5847708546101ca570c89a4c9594093a95675426b37bbdab`.
- The mock is visibly labelled `FLR-0026 MOCK 3D` and is drawn with three
  coloured cube faces using Flutter `CustomPainter`.
- The first mock image kept native `SceneView` in the widget tree. The app
  log reached readiness and frame markers, but the QMP framebuffer remained
  black (`a4972e7e…`), including the candidate region. This means the first
  mock did not yet prove parent Flutter painting because the native child may
  occlude it.
- A second Devtool-generated patch,
  `0023-filament_scene-diagnostic-flutter-only-mock-devtool.patch`, now
  detaches the native `SceneView` only while the diagnostic mock switch is
  enabled. Its SHA256 is
  `c5d02d9d55ee168759bb71d42449fdeae4215ab71f1c06246017b37ca0ba2909`.
- The v2 QMP run with patch `0023` reached the app, but native readiness
  stayed false for all 30 retries and the framebuffer remained black. A third
  Devtool-generated patch,
  `0024-filament_scene-diagnostic-flutter-mock-self-contained-devtool.patch`,
  now skips native construction/readiness in mock mode and gives the Flutter
  `Scaffold` an opaque background. Its SHA256 is
  `01195fc6038a4bc971e5bdc0c20c69417621834e553a3a222aa510b4e2d8e199`.

## Inferences

- If this Flutter-only mock appears in the candidate region, Flutter widget
  painting, app packaging, compositor composition, and QMP capture are
  functioning; the remaining failure is below the Flutter overlay boundary.
- If it remains black even with native construction skipped and an opaque
  background, the screen path is not yet proven and the box observation must
  remain separate from QMP evidence.
- Removing `0058` for this run is required to preserve the known 2D baseline;
  the patch remains in the repository as failed diagnostic history.

## Hypotheses

1. The native Filament path is blocked at Vulkan swapchain acquisition or
   Wayland child-surface presentation, while Flutter painting remains healthy.
2. The native child surface can hide the parent Flutter surface even though
   Flutter can paint correctly when the child is detached.

## UNKNOWN

- Whether native Filament can produce non-transparent pixels after the
  Flutter mock is proven visible.
- Whether a production `Planetarium` route changes the native frame outcome.

## Iteration 20 — QMP-visible self-contained Flutter mock

### Facts

- The fixed mini-PC receiver advanced to `9f349fa5f21ad5fc63c6b18373cc68b5c2ed4228`.
- The Mac-created Git bundle was `/private/tmp/flr0023-9f349fa.bundle` with
  SHA256 `ead8be36c40abf639e3e6c804bc5c8dcb05e3910d2c6001de4746f3d247c372b`.
- The v3 build reused the fixed build directory and TMPDIR. `bitbake -e`
  parsed 5376 targets with 0 errors; the app `do_patch` (104 tasks), app
  `do_compile` (1674 tasks, 1668 reused), and full image (11748 tasks, 11728
  reused) all succeeded.
- The deployed rootfs was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260831141538.ext4` with SHA256
  `008151f43596f3a913c7ba95d95b6fcb55a11dd0b05a52d2938b4b57b6bb8aa9` on both
  the mini PC and Mac. The kernel SHA256 remained
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QEMU was started once with the v3 rootfs and QMP socket
  `/private/tmp/flr0023-qemu-unlit/run-mock-flutter-self-contained-20260831-2310/qmp.sock`.
  The boot QMP capture showed the AGL splash. An app capture at 8 seconds
  was still black while the Flutter AOT was loading.
- The stable QMP capture is
  `/private/tmp/flr0023-qemu-unlit/run-mock-flutter-self-contained-20260831-2310/app-qmp-final.ppm`.
  It has SHA256 `a06aec8c6613c48649672624fcedde4b2ee09a6db7b9f10496e351e6da3c5ddb`.
  Against a black background, the full 720x400 frame changed `288000/288000`
  pixels, and candidate region `[200,100,400,250]` changed `100000/100000`
  pixels.
- Visual inspection of that QMP-derived image shows the three-face coloured
  cube, the label `FLR-0026 MOCK 3D (Flutter only)`, the `Scenes` control, and
  the CPU/frame profiling overlay. This confirms the user's observed box is
  reproducible through QMP, not only through the Cocoa window.
- The guest log reached Vulkan initialization and AOT loading. In v3,
  native `SceneView` construction and readiness are intentionally skipped by
  patch `0024`; this capture therefore proves the Flutter-only composition
  path, not native Filament rendering.
- QEMU was stopped with QMP `quit`; no `qemu-system-x86_64` process remained
  and the QMP socket was removed.

### Inferences

- Flutter widget painting, packaging, Wayland/Flutter app startup, the QEMU
  display path, and QMP capture are now all proven by an explicit visible
  object. The earlier black result was timing/native-surface dependent, not a
  universal inability of the application to paint.
- The user's “box screen” observation was valid. The prior black QMP frames
  were taken before the app had completed AOT/startup or while the native
  child-surface path was still involved.

### Hypotheses

1. The remaining production 3D issue is in native Filament/Wayland child
   surface presentation or frame scheduling, because the Flutter-only mock is
   visible with native construction removed.
2. A production route such as Planetarium may still expose or alter the native
   frame path, but this has not been tested in this iteration.

### UNKNOWN

- Native Filament 3D pixels have not yet been proven visible in QMP.
- The QMP capture does not by itself prove that the displayed cube is a real
  3D render; it is explicitly a Flutter `CustomPainter` diagnostic fixture.

## Verification gate

The next image must be built on the fixed mini-PC receiver from the Mac Git
bundle. Only a QMP `screendump` is accepted as visual evidence. Report both
the full-frame and candidate-region changed-pixel counts, and inspect the
guest log separately for `FLR0026_*`, `beginFrame`, and Vulkan markers. The
expected diagnostic result is a visible labelled cube with the native
`SceneView` absent; it must not be recorded as native Filament success.
