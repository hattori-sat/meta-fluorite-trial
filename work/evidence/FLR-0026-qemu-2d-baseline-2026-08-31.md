# FLR-0026 — fixture 2D baseline and route evidence

## Outcome

The fixture-containing image without the later native opaque-surface
diagnostics restores the known 2D Flutter overlay in QEMU. The central
candidate 3D region remains black, so the 2D boundary is recovered but the
actual 3D pixel criterion is still unmet.

## Identity

- Source revision: `9ede3132bf2251493f14e7537a244016aeb91e45`.
- This revision includes the self-made fixture and fixture camera patches.
- It excludes the later `0055`–`0058` native opaque clear, swapchain, blend,
  and explicit subsurface-commit diagnostics.
- Authoritative rootfs SHA-256:
  `90b2bc06277f6f4bad81836e6df7038f51b7a8475737806a345288fb8843f4bf`.
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.

## Facts

- The same fixed mini-PC receiver, build directory, TMPDIR, downloads, and
  sstate cache were reused. `bitbake -e` resolved `qemux86-64` and the fixed
  TMPDIR. Forced `flutter-auto` `do_patch`, forced `do_compile`, and the full
  image all succeeded; the full image attempted 11,748 tasks and had 11,728
  tasks not rerun.
- QEMU used q35, TCG multi-threading, 2048 MiB, 12 vCPUs, the fixed qemu64
  SSE feature set, virtio-vga, a raw ext4 snapshot, and a unique QMP socket.
- The app was explicitly launched as the registered `agl-driver` role with
  `XDG_RUNTIME_DIR=/run/user/1001`, `WAYLAND_DISPLAY=wayland-0`, and the
  installed Fluorite Example Demo release bundle.
- Runtime reached `Application Id: fluorite`, Vulkan Wayland extensions,
  AOT loading, `FEngine resolved backend: Vulkan`, Filament initialization,
  `FLR0026_SHAPE_READY ... renderable=true`,
  `FLR0026_WAYLAND_SURFACE_CREATED surface=true subsurface=true parent=true`,
  camera application, frame begin/end markers, and native readiness. The
  `flutter-auto` process remained alive during the capture.
- QMP-only pre-launch frame `pre.ppm` was 720x400 with SHA-256
  `a4972e7e976c35a3231772ee2e8b178ef588884dcd734859f7dcf0a519beb90e` and
  zero pixels changed from black in the full frame.
- QMP-only post-initialization frame `after-now.ppm` was 720x400 with
  SHA-256 `355f151ef464a1ad63c2939a72e4c640cba78a1ed039415d0f8ef81e1070bcc8`.
  Against black, the full frame had 7,274 changed pixels (2.5257%) with
  bounding box `[4,7,692,193]`; the candidate 3D region `[200,100,400,250]`
  had zero changed pixels.
- The QMP frame visibly contains `Fluorite Game Engine`, FPS, Frametime, CPU,
  GPU, Script, graph, the `Scenes` button, and bottom controls. This is the
  requested historical 2D/CPU overlay evidence.
- QMP keyboard input opened the `Scenes` menu. The QMP-only menu frame shows
  `Playground`, `Radar`, `Settings`, `Planetarium`, and `Trainset`. The route
  interaction changed the 2D screen and remained QMP-captured, but the
  candidate 3D region stayed at zero changed pixels.
- Attempts to select `Planetarium` with keyboard focus were inconclusive:
  the menu remained open or another control changed. A successful
  Planetarium-route acceptance is therefore not claimed.
- The current opaque-diagnostic image at revision `5dd80c0` produced an
  all-black QMP frame with the same central zero-pixel result, while its
  runtime markers showed native frames. Comparing the two images separates
  the recovered 2D compositor boundary from the unresolved 3D content path.

## Inferences

- The release bundle, AGL boot, Wayland session, Flutter 2D renderer, and
  input path are not generally broken: the baseline restores the overlay and
  opens the scene menu.
- The `0055`–`0058` opaque diagnostics can mask the Flutter parent surface;
  they are useful diagnostics but cannot be retained as a product fix based
  on the all-black result.
- `renderable=true` and frame completion are necessary but not sufficient for
  visible 3D pixels. The unresolved boundary is between Filament render
  output and the composited child surface, or within the fixture material /
  geometry output.

## Hypotheses for the next loop

1. The transparent swapchain receives no non-transparent rendered pixels.
   Test with a renderer-level known-color or unlit material fixture while
   keeping the transparent composition contract.
2. The shape is registered but culled, out of view, or has an ineffective
   material/light path. Test the same camera and surface with a deterministic
   unlit/unculled primitive, then compare native markers and QMP pixels.
3. Production scene selection may exercise a different native scene path.
   Complete QMP input selection for `Planetarium` and compare its markers
   separately; do not merge that result with the fixture verdict.

## Verdict

| Boundary | Verdict |
| --- | --- |
| Fixed baseline build and artifact identity | PASS |
| Boot, Wayland, Vulkan, and explicit `agl-driver` launch | PASS |
| 2D overlay and CPU/FPS display | PASS |
| Scene menu route interaction | PASS |
| Planetarium route selection | UNKNOWN |
| Fixture entity/renderable/frame markers | OBSERVED |
| Visible fixture 3D pixels | FAIL |

QEMU was ended with QMP `quit` after evidence collection. The QMP PPM/PNG
artifacts remain outside Git under the local QEMU artifact directory.
