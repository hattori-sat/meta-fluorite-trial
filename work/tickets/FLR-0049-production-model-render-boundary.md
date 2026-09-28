# FLR-0049 — production model render boundary and scene transition

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + Filament scene/resource + target-validation roles
- Depends on: [FLR-0048](FLR-0048-isolate-light-count-vs-identity.md)
- Working log: `work/logs/2026-09-08-flr0049.md`
- Mac handoff: `work/FLR-0049-latest-mac-verification.md`
- Latest artifact handoff: `work/latest-mac/flr0049-002f86e/handoff.md`
- Follow-up: [FLR-0050 — Flutter parent alpha and frame-loop boundary](FLR-0050-flutter-parent-alpha-frame-loop.md)

## Problem

The current rootfs successfully selects production GLB assets, creates the
Filament asset instance, and adds at least one model to the active Scene. A
runtime visibility trace also reports a valid camera, Scene, entity count, and
renderable count. Nevertheless, the QMP framebuffer remains white or HUD-only
in the initial Playground view. This unit separates an initial-camera/route
issue from a common GLB resource/render issue before any new production patch
is proposed.

## 4W1H

- What: production GLB scene insertion, visibility, resource/render completion,
  and routed scene pixel output.
- Where: Fluorite Example Demo native Filament Scene and its QEMU/Wayland
  presentation path.
- When: after asynchronous model completion and after button-driven scene
  transition.
- Who: Dart scene producer, native ModelSystem/Filament roles, and target
  runtime validation role.
- Why is excluded here: the causal reason is not yet known; this ticket first
  identifies the earliest divergence.

## Success criteria

- Reuse the fixed rootfs, build directory, TMPDIR, persistent Mac Devtool
  container, and one-QEMU-at-a-time contract.
- Use QMP-only screenshots and retain the QMP PPM hash, runtime log, and clean
  QMP teardown evidence.
- Navigate from the initial screen to Radar through QMP input, then capture
  after the Radar camera/route is active. Record whether the small Radar GLB
  becomes visible.
- Compare the route result with the Sequoia model result while preserving the
  known valid model-selection and scene-add markers.
- Do not create a source patch until the first divergent boundary is identified
  and the patch scope is controllable.

## Facts

- `MODEL_SELECTED`, `MODEL_STAGE_ASSET_CREATED`, `MODEL_STAGE_INSTANCE_READY`,
  and `MODEL_STAGE_SCENE_ADD_DONE` are present for the Sequoia comparison.
- The visibility trace reports `same_scene=true`, a valid camera, and
  renderables after model insertion.
- With shapes excluded, the QMP frame is white; with shapes enabled, the
  visible black polygon is not yet proven to be the production GLB.
- The tiny Radar model is positioned far from the initial Playground camera;
  the clean initial Radar candidate therefore does not prove that its asset
  failed to render.
- The QMP evidence is captured from the QEMU framebuffer, not from a host
  window screenshot.

## Inferences

- Flutter 2D, the HUD/CPU metrics, QEMU capture, and basic native Scene
  registration are not the current first suspect.
- A successful scene/entity count is indirect evidence only; it does not prove
  material upload, render-list participation, fragment generation, or visible
  presentation.

## Hypotheses

1. Radar/Sequoia are rendered but the initial camera or route keeps the object
   outside the captured view.
2. A common production GLB material/resource/pipeline operation prevents
   renderable pixels after Scene insertion.
3. The scene is visible to Filament but the native output is lost at the
   frame/present/compositor boundary.

## UNKNOWN

- Whether QMP input activates the Radar route and its camera in the current
  rootfs.
- Whether Radar produces native 3D pixels after the route camera is active.
- The first resource/render/present operation that diverges after
  `MODEL_STAGE_SCENE_ADD_DONE`.

## Verification matrix

| Case | Model | Route/camera | Shapes | Evidence gate |
| --- | --- | --- | --- | --- |
| A | Sequoia | initial Playground | off | scene trace + QMP pixels |
| B | Radar | initial Playground | off | control for camera placement |
| C | Radar | QMP button route | off | route marker + QMP pixels |
| D | Radar | routed camera | on only if needed | distinguish model from shape output |

## Decision rule

If routed Radar remains blank while Scene/entity/camera state is valid, keep the
problem at the common GLB resource/render boundary and investigate runtime logs
before changing source. If routed Radar shows a native model, continue with the
Sequoia asset/camera/material comparison. A source change, if needed, must be
created in the Mac Devtool source workspace and handed off as an official
Devtool-generated patch through the fixed bundle/build flow.

## Iteration 2 — native surface A/B without scene draw and without stack call (2026-09-08)

### Do

The same fixed rootfs and one-QEMU contract were reused. The first A/B run set
`FLR0026_NATIVE_SKIP_SCENE_RENDER=1`, while retaining the SHM cube probe. The
second run added the existing opt-in `FLR0026_WAYLAND_SKIP_STACK=1` so that the
initial `wl_subsurface_place_above` call was omitted. No source or recipe was
changed for either run.

### Facts

- With scene rendering disabled, runtime still reported
  `FLR0026_NATIVE_SKIP_SCENE_RENDER enabled=true`, model scene insertion,
  `scene=true`, `entities=11`, `renderables=2`, `lights=8`, a valid camera,
  and successful Vulkan queue/present-result markers.
- The QMP-only image
  `work/evidence/flr0049-radar-route-shm-skip-render-10s.png` contains only
  the SHM cube in the bounding box `[240,120,240,160]`; the rest of the
  framebuffer is black and the Flutter HUD is absent. Its PPM SHA-256 is
  `b38564eb25f37f21745ca433a66a70c59403210dc6629439da40b81d8eec5d8a`.
- Omitting the stack call logged `skip_stack=true`, but the QMP-only PPM was
  bit-for-bit identical to the scene-skip run: SHA-256
  `b38564eb25f37f21745ca433a66a70c59403210dc6629439da40b81d8eec5d8a`, with
  only the SHM cube rectangle `[240,120,240,160]` visible and no Flutter HUD.
  This is not sufficient evidence for a z-order-only fix.
- Runtime logs are retained as
  `work/evidence/flr0049-radar-route-shm-skip-render-app.log` and the
  corresponding skip-stack log remains on the target evidence run directory.
- Both QEMU instances were terminated by QMP and their sockets/processes were
  verified absent.

### Inferences

- The native surface is still an active full-screen presentation participant
  even when the Filament Scene draw call is skipped; therefore the missing HUD
  cannot be attributed only to production model geometry.
- The SHM child is visible when it is explicitly stacked above the native
  surface, proving that the compositor can display a child buffer, but this
  does not prove that the Filament Vulkan swapchain buffer has usable alpha or
  that its content is the expected model image.

### Hypotheses

1. The transparent Vulkan swapchain is being presented as a black/opaque
   full-surface buffer, masking the Flutter parent after the first native
   commit.
2. Filament's scene render target receives no usable model pixels even though
   Scene registration and present markers succeed.
3. The Flutter route/input issue is independent and cannot be judged from the
   current black native surface until the surface contract is isolated.

### UNKNOWN

- Whether the production model pixels exist in the presented Vulkan image
  before Wayland composition.
- Whether an empty native surface (no renderer end-frame/attach) restores the
  Flutter HUD; the current `SKIP_SCENE_RENDER` probe still presents a native
  frame and is therefore not that test.
- Whether the current route stimulus reaches Flutter after the native surface
  is committed.

### Act

Before changing production model code, inspect and test the native surface
buffer/alpha and no-attach boundary with one new controlled diagnostic. The
next source change, if required, must be made in the persistent Mac Devtool
workspace and handed off through an official Devtool-generated patch; do not
hand-edit a patch file.

## Iteration 3 — offscreen readback timing and primary-template selection (2026-09-08)

### Do

The fixed rootfs was run with the existing offscreen readback probe,
`FLR0026_NATIVE_MODEL_MATCH=sequoia`, `FLR0026_NATIVE_MODEL_LIMIT=1`,
environment and shapes excluded, and the usual scene/camera traces. The
readback result was copied into the SHM evidence surface and captured through
QMP.

### Facts

- The selector chose only `ordinal=0 asset=assets/models/sequoia_ngp.glb` and
  queued one asset. It emitted `MODEL_STAGE_ASSET_CREATED` with 22 entities
  and `MODEL_STAGE_INSTANCE_READY`, but no `MODEL_STAGE_SCENE_ADD_DONE`.
- The runtime scene stayed at `entities=9 renderables=1`; the traced first
  renderable had zero bounds. Static source analysis identifies ordinal 0 as
  the primary instanceable template, which is intentionally not added to the
  scene for rendering.
- The readback callback completed with
  `bytes=153600 nonblack=38400 max_channel=231 shm_copy=true`, but the copied
  QMP image `work/evidence/flr0049-readback-sequoia-20s.png` was a uniform
  gray 240x160 rectangle. It is the readback clear, not proven GLB geometry.
  Its PPM SHA-256 is
  `31edee2e19cbe8e351233fb41896aaff446e4fa71e8d189d7375c78918e15ee6`.
- The readback view is queued only once, on the first native frame. That frame
  has the initial camera `(0,0,0)` with zero near/far values, before the later
  Playground camera is applied and before the asynchronous model can be
  inserted.
- The readback QEMU used guest port fallback `2223` because an earlier
  diagnostic QEMU had not yet been closed. The earlier QEMU was then closed by
  QMP, the readback QEMU was used on its actual port, and final socket/process
  cleanup passed. This run is valid for the readback timing result; no
  overlapping QEMU was left running.

### Inferences

- `MODEL_LIMIT=1` cannot prove Sequoia rendering: it selects a non-rendered
  primary template. A valid model comparison must include the later rendered
  occurrence (the established limit=2 path) and require
  `MODEL_STAGE_SCENE_ADD_DONE`.
- The successful readback callback currently proves only that the offscreen
  target and callback path can return a non-black clear; it does not prove
  that production GLB pixels reached that target.
- A one-shot readback at the first frame is temporally invalid for this
  asynchronous scene and camera pipeline.

### Hypotheses

1. With the secondary Sequoia instance inserted and a readback delayed until
   the active camera is applied, the offscreen image will contain production
   geometry; the remaining screen failure would then be surface composition.
2. The secondary instance will still produce only clear pixels, localizing
   the failure to GLB material/resource/render execution.
3. The readback callback will remain valid but the scene may be outside the
   selected camera, requiring a routed camera or controlled camera diagnostic.

### UNKNOWN

- Whether a delayed readback of the rendered secondary Sequoia contains model
  pixels.
- Whether `MODEL_STAGE_SCENE_ADD_DONE` is sufficient for a production GLB
  renderable in the current Filament backend.

### Act

Add one opt-in source diagnostic that delays the existing readback queue until
the model scene is complete and the camera has valid near/far values. Create it
in the persistent Mac Devtool source, generate the official patch, then run
the limit=2 comparison through the fixed Mini PC build and QMP evidence loop.

## Iteration 4 — opaque native surface versus production GLB pixels (2026-09-08)

### Do

Using the same fixed rootfs and one-QEMU contract, run the Sequoia selector with
`MODEL_LIMIT=2`, disable environment, shapes, and lights, force the native view
to opaque, and retain model/scene/camera traces. Capture the complete QEMU
framebuffer through QMP and keep the application log.

### Facts

- The selector created the Sequoia asset with 22 entities and emitted
  `MODEL_STAGE_SCENE_ADD_DONE` for the secondary instance.
- At sequence 20 and later, the runtime reported `scene=true`, 25 entities,
  14 renderables, zero lights, `same_scene=true`, camera position `(5,0,-5)`,
  near `0.05`, far `1000`, and `blend_opaque=true`.
- The runtime `FLR0026_RENDERABLE_SAMPLE` entries for model entities 43 through
  47 reported non-zero AABBs and world positions near the active camera. The
  sampled bounds are unusually large, so this rules out an empty-bound result
  but does not yet prove correct frustum visibility or actual draw commands.
- Despite those markers, the QMP-only framebuffer was uniformly white. The
  display copy is `work/evidence/flr0049-model-force-opaque.png`; its PPM
  SHA-256 is
  `2097d8f3aa89cb4083d5414e2636bbd9cf88d6a261844a2d8b9a947554376311`.
- The application log is
  `work/evidence/flr0049-model-force-opaque-app.log`; its SHA-256 is
  `d9f956ff2b6d63f1c4a0ab87b6fbd0f6975d71ba1f44a549beaf054569db3e0f`.
- The QEMU was terminated through QMP with `reason=host-qmp-quit`; the QMP
  socket and `qemu-system`, `runqemu`, and `flutter-auto` processes were absent
  after teardown.

### Inferences

- A valid camera, opaque native view, secondary model scene insertion, and
  continued frame/present activity are insufficient to produce model pixels.
- This result weakens the initial-camera and transparent-swapchain hypotheses
  for the model failure. It does not by itself exclude a compositor problem in
  the normal transparent production configuration.
- The first unproven boundary is now after `SCENE_ADD_DONE`: primitive and
  material/resource readiness or the Filament draw path. The sampled model
  bounds make an all-empty-AABB explanation unlikely, while their unusually
  large extents remain a separate geometry/culling concern. Repeated
  `Light not found` messages are recorded as a separate runtime symptom, not
  yet as the root cause.

### Hypotheses

1. The GLB renderables are registered but their material, vertex, or texture
   resources are not ready/valid when the frame is rendered.
2. The renderable entities are valid but are omitted or rejected by Filament's
   render-list/pipeline path on this backend.
3. The opaque surface still presents a blank buffer, so a delayed offscreen
   readback is required to separate render failure from presentation failure.

### UNKNOWN

- Whether the secondary Sequoia renderables have valid primitive counts,
  material instances, vertex/index resources, and shader-ready state at draw
  time.
- Whether the unusually large sampled AABBs are the intended asset geometry or
  a malformed transform/bounds input.
- Whether delayed offscreen readback after camera and scene completion contains
  any model pixels.
- Whether the repeated `Light not found` messages affect model render setup or
  are unrelated stale scene operations.

### Act

Do not patch the GLB path from Scene counts alone. First restore the Mac
persistent Devtool container, then add an opt-in Devtool-source diagnostic that
records renderable bounds/material readiness and delays readback until the
secondary model and valid camera are present. Generate the official patch,
build it on the fixed Mini PC environment, and use QMP evidence to choose the
next minimal production fix.

## Iteration 5 — GLB structural control and Devtool prerequisite check (2026-09-08)

### Facts

- Static parsing of the source Sequoia GLB found a valid glTF 2 binary with
  22 nodes, 8 meshes, 11 materials, and 23 embedded PNG images. Every embedded
  image is 1024x1024, and the mesh primitives contain POSITION, NORMAL,
  TEXCOORD_0, and TEXCOORD_1 attributes.
- The application registers an `image/png` texture provider, matching the
  embedded image MIME type. This does not prove successful runtime upload, but
  it weakens the hypothesis that the source file is structurally empty or uses
  an unsupported image type.
- The active worktree remains canonical and the diagnostic evidence is locally
  committed through `aa7e924`; unrelated pre-existing evidence files remain
  un-staged.
- Docker Desktop's Docker socket is still stale/unresponsive, and the required
  `fluorite-yocto-devtool:22.04` image/container cannot currently be inspected.

### Inferences

- The strongest unverified boundary is now runtime resource/material readiness
  or Filament draw-list execution after the secondary instance is added, not
  source GLB structure or empty AABB.
- A Devtool-generated diagnostic is still required before a production fix can
  be selected; no source or generated patch was changed in this iteration.

### UNKNOWN

- Runtime primitive counts, material instance names, and resource readiness for
  the 14 renderables reported by the active Scene.
- Delayed offscreen readback pixels after the secondary instance and active
  camera are ready.

### Act

Restore Docker Desktop's engine, reuse the persistent container and its named
volumes, then implement the pending diagnostic in the Devtool source workspace.

## Latest validation — production Sequoia pixels and route boundary (2026-09-08)

The fixed Mini PC artifact was launched through the existing one-QEMU contract,
with the app started as `agl-driver`. The current QMP-only capture
`../latest-mac/flr0049-002f86e/model-stage-sequoia.png` visibly contains the
production `sequoia_ngp.glb` vehicle. Its PPM SHA-256 is
`99d0b78f90b8e49ece4afd18624799729b6c757de88eff146c2bb9d3e0e88690`; the
white-background analysis region `[300,80,620,360]` changed `86983/223200`
pixels with bounding box `[336,96,544,304]`. The companion runtime log is
`../latest-mac/flr0049-002f86e/runtime-4.log`.

The same QMP method on a QEMU profile with USB tablet/keyboard opened the
Scenes menu, and the QMP image
`../latest-mac/flr0049-002f86e/route7-scenes-menu-correct.png` lists all five
scene names. Clicking the visible Radar row produced
`../latest-mac/flr0049-002f86e/route7-radar-10s.png`, which is all white in
the candidate region and has no route-specific camera marker in the matching
runtime log. Scenes-menu input is PASS; Radar route activation and Radar 3D
pixels remain UNKNOWN.

This changes the earliest proven boundary: the common production GLB path can
produce screen pixels, so no new GLB/material patch is justified from the
Radar white frame alone. The remaining work is to capture the route-specific
camera/scene transition and compare its model placement with the visible
Sequoia run. The QEMU run must be ended through QMP after that capture.

## Iteration 10 — readbackなしproduction A/B (2026-09-08)

### Facts

- The existing fixed Mini PC rootfs, build directory, TMPDIR, USB input
  devices, QMP-only display capture, and single QEMU run directory were reused.
  No source or image patch was changed for this A/B.
- The app was launched as `agl-driver` with
  `FLR0026_NATIVE_MODEL_MATCH=sequoia`, `FLR0026_NATIVE_MODEL_LIMIT=2`,
  skybox/indirect-light/shapes/lights diagnostic skips, and
  `FLR0026_NATIVE_READBACK_PROBE` **unset**.
- The runtime reached `MODEL_STAGE_SCENE_ADD_DONE` for
  `assets/models/sequoia_ngp.glb`, then repeatedly reported
  `scene=true entities=25 renderables=14`, `FRAME_BEGIN ... started=true`,
  and successful Vulkan queue submit/present markers through approximately
  60 seconds.
- QMP-only `no-readback-35s.png` and `no-readback-60s.png` visibly contain the
  production Sequoia vehicle and red light pixels. Their PPM SHA-256 is
  `61d1c910b7bdc39893b00812ce94b25c917f603d139773aae71c935c1e04e9a2`;
  candidate region `[200,100,400,250]` changed `65299/100000` pixels. The two
  captures are bit-for-bit identical.
- The matching runtime and serial evidence contain no page fault/Oops/SIGSEGV
  marker. QMP teardown returned `reason=host-qmp-quit`, and exact post-checks
  found no QEMU, flutter-auto, or QMP socket residual.

### Inferences

- The common production GLB/Filament path is capable of producing visible 3D
  pixels in the current image. The prior all-white/black interpretations were
  condition-dependent and cannot be used as a blanket GLB failure verdict.
- The page fault observed in `serial-19.log` is correlated with the opt-in
  readback diagnostic path, not reproduced by this no-readback display run.
  This is evidence of correlation, not yet proof of the exact fence lifetime
  root cause.
- The current native surface masks the Flutter HUD in this profile. The 2D
  overlay baseline remains valid separately, but combined 2D-over-3D
  composition is not yet accepted.

### UNKNOWN

- Whether the readback page fault is caused by the extra Filament Fence,
  asynchronous buffer ownership, or another Vulkan readback lifetime race.
- Whether Radar/Planetarium route-specific camera and scene transitions also
  produce visible pixels.
- Whether the product composition should show the 2D HUD above the native
  surface or intentionally hide it while the 3D route is active.

### Decision / Act

- Mark common production Sequoia 3D pixel output **PASS under readback-disabled
  runtime conditions**.
- Keep FLR-0049 In Progress. Next scope is separate: reproduce and fix the
  readback diagnostic crash through the persistent Mac Devtool, then validate
  route-specific 3D and the intended 2D/native composition. Do not patch the
  GLB loader or production render path based on the previous white frame.

## Iteration 11 — transparent-alpha build and QMP video (2026-09-08)

### Facts

- The Mac Devtool-generated patch
  `0170-filament-vulkan-transparent-alpha-devtool.patch` was registered after
  the existing Filament baseline patch. Its SHA-256 is
  `59b35281bfd31c2fbb572ef35826cc894911df50905e4d1bd53d5e93df6cc17c`.
- The fixed Mini PC receiver accepted feature tip
  `ffab6585d80e8adb304558b3e546a1e8ff8787c8`; the existing build directory
  and TMPDIR were reused. `agl-ivi-image-flutter` completed with 11748/11748
  tasks successful, 22 warnings, and no `ERROR:` marker.
- The resulting rootfs SHA-256 is
  `496bbc58f6c9a334976b8315b5d483ca90b8724eea61a9585ab7f196176811ea`.
- One direct QMP-only QEMU instance was launched on the Mini PC with
  `-usb -device usb-tablet -device usb-kbd -device virtio-vga -display none`.
  The app ran as `agl-driver` with Sequoia model selection and the existing
  diagnostic shape/light/skybox controls.
- The runtime emitted
  `FLR0026_VK_COMPOSITE_ALPHA transparent=true supported=0x3 selected=0x2`,
  reached `MODEL_STAGE_SCENE_ADD_DONE`, `scene=true entities=25
  renderables=14`, and repeated successful Vulkan present results.
- The QMP-only representative image is
  `work/latest-mac/flr0049-002f86e/alpha-build-ffab658/qmp-alpha-runtime-representative.png`.
  The raw PPM SHA-256 is
  `99d0b78f90b8e49ece4afd18624799729b6c757de88eff146c2bb9d3e0e88690`.
  Against white, candidate region `[200,100,400,250]` changed `40257/100000`
  pixels with bounding box `[337,100,263,250]`.
- The QMP video is
  `work/latest-mac/flr0049-002f86e/alpha-build-ffab658/qmp-alpha-runtime.mp4`:
  1280x800, 1 fps, 39 seconds, 39 frames, SHA-256
  `35537195f38d4cfa80e54dbb3c00dd9685cffdaa273f046459a1d9925de6e209`.
  All frames were byte-identical, so this is a stable-state video, not an
  input-transition video.
- QMP teardown returned `host-qmp-quit`; no QEMU, runqemu, flutter-auto, or
  QMP socket remained.

### Inferences

- The transparent-alpha selection is active and the production Sequoia 3D
  output remains visible. The patch did not regress the native 3D path.
- The native surface still masks the Flutter 2D HUD/CPU/FPS in this profile.
  Combined 2D/native composition is therefore still UNKNOWN; the evidence
  does not justify a GLB-loader patch.

### Act

Keep FLR-0049 In Progress. Add the QMP video capture procedure to future runs,
then inspect native surface dimensions/opacity and compositor stacking before
choosing another source change. Continue with route-specific Radar and
Planetarium transitions after the composition boundary is isolated.

## Iteration 12 — Devtool input-region A/B and Wayland protocol evidence (2026-09-08)

### Facts

- The first `devtool finish flutter-auto` attempt did not generate a patch
  because the changed file belongs to the `ivi-homescreen-plugins` child Git
  tree. Re-registering the existing `a58af08` baseline as a component-scoped
  `fluorite-plugins` workspace and running Yocto
  `devtool finish --mode patch --no-clean` generated the patch. The generated
  patch and registered copy are byte-identical, SHA-256
  `a1a3c547a7e6cae8902ee4d56316f58a4cf3c181ac89b57fe6c91d32635b686d`.
- The source commit is `19701c7`; it adds an opt-in empty `wl_surface` input
  region. The layer registration is local project commit `ccb81ec`.
- The fixed Mini PC receiver accepted the full-tip bundle and checked out
  `ccb81ec`. `flutter-auto:do_patch`, `flutter-auto:do_compile`, and the full
  image build completed in the fixed build directory/TMPDIR. The new rootfs
  SHA-256 is `31ac4d215ba6c5f06cc85a8c00f96aabcc54eb8acbcb72666c72baf06450f812`;
  qemuboot is
  `56960be4b59b14667568e5d9f866987031755c268ab4217e2e3231d2bb9aade3`.
- With `FLR0026_WAYLAND_EMPTY_INPUT_REGION=1`, QMP showed the production
  Sequoia vehicle and red light pixels. Region `[200,100,400,250]` changed
  `40257/100000` pixels against white. The 40-frame video is
  `work/latest-mac/flr0049-ccb81ec/empty-input-20260908/qmp-flr0049-empty-input.mp4`
  (SHA-256
  `a6b55997aa47f07c15df7755e9e835a191efe4f2695538d1c76d8989ee417e2d`).
- A correct QMP Scenes-button click returned successfully, but the after-click
  PPM SHA-256 remained
  `99d0b78f90b8e49ece4afd18624799729b6c757de88eff146c2bb9d3e0e88690` and no
  Scenes/Radar/Planetarium marker appeared. The after-click video is
  `work/latest-mac/flr0049-ccb81ec/empty-input-20260908/qmp-flr0049-after-scenes-click.mp4`
  (SHA-256
  `5cad6f78c564c16e14ff9cca19f80217da3ea836c6c6493310c614e762ad68af`).
- The same image with `FLR0026_NATIVE_CLEAR_PROBE=1` restored the Flutter
  HUD/FPS/CPU/GPU/Script/graph, but did not show native green clear or 3D. Its
  runtime selected `transparent=false supported=0x3 selected=0x1`. The
  30-frame video is
  `work/latest-mac/flr0049-ccb81ec/clearprobe-20260908/qmp-flr0049-clearprobe.mp4`
  (SHA-256
  `a964a0d80a092ac25fdff9252e55be2cb5df50ef7bc893f1222cb0cae91b37cd`).
- `WAYLAND_DEBUG=client` showed parent and native child surface identifiers were redacted: `get_subsurface`, `place_above`, `set_position(0,0)`,
  `set_desync`, native `attach/damage/commit`, and repeated parent
  `attach/damage/commit`. The native swapchain was RGBA8 (`format=44`) and
  no `set_opaque_region` request was emitted. The protocol video is
  `work/latest-mac/flr0049-ccb81ec/wayland-debug-20260908/qmp-flr0049-wayland-debug.mp4`
  (SHA-256
  `83977c8982de11aee26ebfe97aa3b9368b2a40787226131c72f09ddaae81bdbb`).
- Runtime health checks found zero failed systemd units. `agl-compositor` was
  active, recognized `fluorite` as a DESKTOP app, used llvmpipe, and reported
  a black curtain because no background surface was present. `flutter-auto`
  remained alive and emitted successful Vulkan present results.

### Inferences

- The empty input region does not explain the missing HUD or route transition;
  it changes input ownership only and leaves the visible native 3D result
  unchanged.
- Flutter startup, AGL activation, scene insertion, renderable creation,
  RGBA8 swapchain creation, Wayland child commit, and Vulkan present are all
  reached. The remaining failure is at the visible alpha/composition boundary,
  not a proven GLB-load or global Vulkan failure.
- The opaque clear-probe HUD image is not a combined-render pass: the native
  clear/3D pixels are absent in that run.

### Hypotheses

1. The transparent native child contributes an opaque full-rectangle background
   after Vulkan present despite RGBA8 and the selected composite mode.
2. Vulkan premultiplied-alpha mode and the actual clear/material alpha written
   by Filament are mismatched.
3. AGL compositor policy treats this native subsurface as a full-rectangle
   visible child.

### UNKNOWN

- The alpha value of presented native pixels at the compositor boundary is
  UNKNOWN; the prior readback diagnostic is unsafe because of its correlated
  page fault.
- Whether an explicit `wl_surface_set_opaque_region(surface, NULL)` or a
  compositor-side surface-role diagnostic changes the result is UNKNOWN.
- Production Radar/Planetarium route behavior remains UNKNOWN because the
  native child masks the Flutter route controls.

### Act

Keep FLR-0049 In Progress. The next source change must be one Devtool-generated
alpha/compositor diagnostic, followed by the same fixed Mini PC build loop.
Do not claim combined 2D+3D success until a QMP frame shows both the HUD and
production 3D object, and a route transition is recorded.

## Iteration 13 — explicit empty opaque-region A/B and mandatory QMP video (2026-09-08)

### Plan / Do

The next single diagnostic was generated in the persistent Mac Devtool
component workspace. The source commit was `05f80aa` and
`devtool finish --mode patch --no-clean` generated
`0001-diag-clear-native-opaque-region-hint.patch`. The registered layer copy
is `0197-diag-clear-native-opaque-region-hint-devtool.patch`, SHA-256
`27d8547cf79f14f23b56b891bef7c967e29c58ba3374d0e64d53b35226ef2186`.
The behavior is opt-in through
`FLR0026_WAYLAND_EMPTY_OPAQUE_REGION=1`; the project registration and bundle
tip are local commit `743f5ea`. The existing Mini PC build directory and
TMPDIR were reused; no second build tree was created.

### Check — build

- `flutter-auto:do_patch` passed with the 0197 patch in effective `SRC_URI`.
- `flutter-auto:do_compile` passed.
- Full `agl-ivi-image-flutter` completed. The resulting rootfs SHA-256 is
  `d89a8e2c408742e59469165718af1b41da9ae39f9a1c077d4b684625d31f1183` and
  qemuboot SHA-256 is
  `02385295a51fb295b37e2f42281c5dc28d4ff0054ec9966b2b50230acb1b9d93`.

### Check — runtime and video

- One direct QMP-only QEMU instance was launched on the Mini PC with the
  fixed USB tablet/keyboard, virtio-vga, and `-display none` profile.
- The runtime reached `MODEL_STAGE_SCENE_ADD_DONE`,
  `scene=true entities=25 renderables=14`, GLB completion, RGBA8 swapchain
  creation, and repeated `FLR0026_VK_QUEUE_PRESENT result=0` markers.
- The QMP video is
  `work/latest-mac/flr0049-ccb81ec/opaque-region-20260908/qmp-flr0049-empty-opaque-region.mp4`:
  1280x800, 40 frames, 30 seconds, SHA-256
  `ca1c6c3c221322d4aa895f0e9dbca87d4895b58c0c1589306b8f06f25bdca5fd`.
- The final QMP PPM SHA-256 is
  `99d0b78f90b8e49ece4afd18624799729b6c757de88eff146c2bb9d3e0e88690`.
  Against white, region `[200,100,400,250]` changed `40257/100000` pixels
  with bounding box `[337,100,263,250]`, exactly matching the preceding
  empty-input-region run.
- The final QMP frame visibly contains the white background, black Sequoia
  vehicle, red pixels, and wireframe/light bounds. The Flutter HUD/CPU/FPS
  layer is absent. The runtime log SHA-256 is
  `6f8102e2ca3ca3711b5488795088d0a28315cff945057ca9d526e0231d4890dc`.
- QMP returned `host-qmp-quit`; the QMP socket and recorded QEMU process were
  absent after teardown. No QEMU/runqemu/flutter-auto residual was found on
  the Mini PC.

### Facts / Inferences / Hypotheses

- Fact: `wl_surface_set_opaque_region(surface, NULL)` did not change the
  visible pixel result in this A/B.
- Inference: the compositor's opaque-region hint is not the cause of the
  missing Flutter HUD in this profile. The native 3D path is independently
  alive, and the remaining boundary problem is not explained by input-region
  ownership or this opaque-region metadata.
- Hypothesis: the presented RGBA8 content or its premultiplied-alpha values
  still form an opaque full-rectangle native child, or the compositor's
  subsurface policy masks the Flutter surface after native present.

### UNKNOWN / Act

- The actual alpha values at the compositor boundary remain UNKNOWN; the
  prior readback diagnostic is unsafe because of its correlated page fault.
- Combined 2D HUD + production 3D and route-specific Radar/Planetarium
  transition remain UNKNOWN and are not claimed as success.
- Keep FLR-0049 In Progress. The next diagnostic should target alpha content
  or compositor policy (for example a controlled sync/async subsurface A/B or
  a safe WSI alpha trace), then repeat the same Mini PC build and mandatory
  QMP-video capture loop.

## Iteration 14 — Wayland synchronous-subsurface runtime A/B (2026-09-08)

### Plan / Do

Before adding another source patch, run the existing image with
`FLR0026_WAYLAND_SYNC=1`. This isolates subsurface synchronization policy from
the 0197 opaque-region metadata change. The same fixed rootfs, one-QEMU rule,
Mini PC build/TMPDIR, explicit `agl-driver` bundle launch, and QMP-only video
capture were used. No source or layer file was changed in this iteration.

### Check — runtime and video

- The guest app stayed alive through the capture interval and reached
  `scene=true entities=25 renderables=14`, GLB completion, RGBA8 swapchain
  creation, and repeated `FLR0026_VK_QUEUE_PRESENT result=0` markers.
- The QMP video is
  `work/latest-mac/flr0049-ccb81ec/sync-20260908/qmp-flr0049-wayland-sync.mp4`:
  1280x800, 40 frames, 30 seconds, SHA-256
  `c5f02cc47153ff2484eebe0b4bd27efa06a77148c9805cc5bdf90bc988ef47c8`.
- The final QMP PPM SHA-256 is
  `99d0b78f90b8e49ece4afd18624799729b6c757de88eff146c2bb9d3e0e88690`.
  Against white, region `[200,100,400,250]` changed `40257/100000` pixels
  with bounding box `[337,100,263,250]`.
- The QMP frame again shows the native black Sequoia vehicle and red pixels,
  with no Flutter HUD/CPU/FPS layer. The copied runtime log SHA-256 is
  `4701347befa4e1a1b2f27ce5e4f58913ceff0fbc19714b97c49af4630db339f0`.
- QMP returned `host-qmp-quit`; the QMP socket and recorded QEMU process were
  absent after teardown, with no QEMU/runqemu/flutter-auto residual.

### Facts / Inferences / Hypotheses

- Fact: enabling synchronous subsurface mode did not change the visible pixel
  result; it exactly matched the 0197 and 0196 native-3D frame hash.
- Inference: the missing HUD is not explained by this Wayland sync policy
  toggle. Native scene creation and present remain healthy, while the
  combined composition remains unproven.
- Hypothesis: the compositor receives a native buffer whose alpha content is
  effectively opaque, or the compositor's surface policy applies an opaque
  full-rectangle child independent of this sync setting.

### UNKNOWN / Act

- Actual presented alpha values remain UNKNOWN; no unsafe readback conclusion
  is being used.
- Route-specific Radar/Planetarium behavior remains UNKNOWN because the
  native child masks the Flutter controls in this profile.
- Keep FLR-0049 In Progress. The next source change should be a single
  Devtool-generated safe WSI/alpha-content diagnostic, followed by the same
  bundle, Mini PC build, and mandatory QMP-video loop.

## Iteration 15 — below-parent stacking probe and 2D/native separation (2026-09-08)

### Plan / Do

Generate and register one opt-in Devtool patch that changes only the native
subsurface stacking operation from `place_above` to `place_below` when
`FLR0026_WAYLAND_BELOW_PARENT=1`. The default `place_above` path is unchanged.
The source commit in the persistent Devtool workspace is `647921a`; official
`devtool finish --mode patch --no-clean` generated the patch. The generated
patch and registered 0198 copy are byte-identical, SHA-256
`0fbd02b84bfd9ce3b2d05728b1d70f6aa8ad1121e26be79d5ff05d30850de8a8`.
Project commit `3154aa4` was bundled and built on the fixed Mini PC
build/TMPDIR.

### Check — build

- `bitbake -e flutter-auto` showed 0198 in effective `SRC_URI`.
- `flutter-auto:do_patch` passed 104/104 and `flutter-auto:do_compile` passed.
- Full `agl-ivi-image-flutter` passed 11748/11748 with 21 warnings and no
  `ERROR:` marker.
- Rootfs SHA-256:
  `525b24b08aacbcd3d738b4a231b4d6d64da29c76f0835533eefb1c95d0b29067`.
- qemuboot SHA-256:
  `e24ecb27ab4389f4ed1bd92feb3aecc839bfe82797a45689a578d3eda741a8f1`.

### Check — runtime and video

- The app was launched as `agl-driver` with the production Sequoia selection,
  and QMP captured 40 frames at 1280x800 over 30 seconds.
- The video is
  `work/latest-mac/flr0049-ccb81ec/belowparent-20260908/qmp-flr0049-below-parent.mp4`,
  SHA-256
  `034db5c3244f14c8e26cc27203a44041d20495fa6cf070382e22a7848a9e819b`.
- Runtime logged `below_parent=true`, reached
  `scene=true entities=25 renderables=14`, GLB completion, RGBA8 swapchain
  creation, and repeated successful Vulkan presents. Runtime log SHA-256:
  `96fed542d0b1f88d2ee90f57cf5efde4fc30091552c2b8ead0ff4b4daed58d2f`.
- The QMP frame shows the Flutter HUD, CPU/FPS/GPU/Script graph, Scenes
  button, and bottom controls. Native Sequoia 3D is absent. Pixel analysis
  against white changed `99942/100000` pixels in region
  `[200,100,400,250]`, with bounding box `[200,100,400,250]`; this is the
  black Flutter surface, not native model evidence.
- QMP returned `host-qmp-quit`; the QMP socket and recorded QEMU process were
  absent after teardown, with no QEMU/runqemu/flutter-auto residual.

### Facts / Inferences / Hypotheses

- Fact: putting the native subsurface below the parent restores the Flutter
  2D HUD, proving the prior `place_above` ordering was masking it.
- Fact: the same below-parent operation removes native 3D from the visible
  QMP frame, so it is not a combined-render solution.
- Inference: the two surfaces are independently functional, but the native
  surface is effectively opaque/full-rectangle at the composition boundary.
- Hypothesis: making the native Vulkan content genuinely transparent (clear
  alpha plus compatible blend/composite semantics) while keeping it above the
  parent will produce the required combined frame.

### UNKNOWN / Act

- Actual alpha values of the presented native buffers remain UNKNOWN; the
  unsafe readback path is not reused.
- Combined HUD + production 3D and Radar/Planetarium route transition remain
  UNKNOWN and are not claimed as success.
- Keep FLR-0049 In Progress. Next, use the confirmed stacking result to make
  one safe Devtool-generated alpha-content diagnostic, then repeat bundle,
  fixed Mini PC build, and mandatory QMP-video capture.

## Iteration 16 — explicit transparent frame-clear probe (2026-09-08)

### Plan / Do

Use the confirmed above-parent masking result and add one opt-in
Devtool-generated diagnostic that calls Filament `Renderer::setClearOptions`
with `{0,0,0,0}` immediately before the native frame work. This tests whether
the per-frame clear state is being overwritten after the existing transparent
clear setup. The source commit is `5ac26bd`; official finish generated the
registered 0199 patch, byte-identical SHA-256
`87fb9087ad5021561aa406dc3a957a5302283055663ac4ffb635561553d68e06`.
Project commit `47c147a` was bundled to the fixed receiver. The existing build
directory and TMPDIR were reused.

### Check — build

- 0199 appeared in effective `SRC_URI`; `flutter-auto:do_patch` and
  `flutter-auto:do_compile` passed.
- Full `agl-ivi-image-flutter` passed 11748/11748 with 21 warnings and no
  `ERROR:` marker.
- Rootfs SHA-256:
  `46cbaea463998ee486b73e93542833ef8dde22415be170ece6a55610de61d12b`.
- qemuboot SHA-256:
  `2b67cabbe0846e0c26ff26af4302553239b53515fa64f8c35853477124866c58`.

### Check — runtime and video

- With `FLR0026_NATIVE_ALPHA_CLEAR_PROBE=1`, the runtime logged the probe,
  reached `scene=true entities=25 renderables=14`, GLB completion, RGBA8
  swapchain creation, and repeated successful Vulkan presents.
- QMP captured 40 frames at 1280x800 over 30 seconds. The video is
  `work/latest-mac/flr0049-ccb81ec/alpha-clear-20260908/qmp-flr0049-alpha-clear.mp4`,
  SHA-256
  `d9e61b4f8410e0283aeada3f836586db3188211aad0bc7ab846e776593ce26c7`.
- Final PPM SHA-256 is
  `99d0b78f90b8e49ece4afd18624799729b6c757de88eff146c2bb9d3e0e88690`.
  Against white, region `[200,100,400,250]` changed `40257/100000` pixels
  with bounding box `[337,100,263,250]`, exactly matching the prior native
  3D-only result.
- The final frame contains native Sequoia 3D and no Flutter HUD/CPU/FPS.
  Runtime log SHA-256:
  `db8a98cc750154b0f5d8ca82cb686841d85c983e01aed267fed1e9741b2e7729`.
- QMP returned `host-qmp-quit`; the QMP socket and recorded QEMU process were
  absent after teardown, with no QEMU/runqemu/flutter-auto residual.

### Facts / Inferences / Hypotheses

- Fact: the explicit per-frame transparent clear was reached but did not alter
  the visible pixel hash.
- Inference: the clear color itself is not sufficient to make the presented
  native child transparent; the loss is later in the WSI/compositor boundary
  or in the actual swapchain image alpha contents.
- Hypothesis: Filament's Vulkan WSI path or the compositor's interpretation of
  `VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR` does not match the alpha written
  by the native render target.

### UNKNOWN / Act

- Actual alpha values of the presented swapchain image remain UNKNOWN; the
  prior readback path is unsafe and remains disabled.
- Combined HUD + production 3D and Radar/Planetarium route transition remain
  UNKNOWN and are not claimed as success.
- Keep FLR-0049 In Progress. Next, inspect the standard Vulkan WSI source and
  choose one minimal Devtool-generated diagnostic for composite-alpha mode or
  image-content semantics, then repeat the same build and QMP-video loop.

## Iteration 18 — first failing fence boundary and independent composition A/B (2026-09-08)

### Plan / Do

Reuse the 0199 rootfs and fixed Mini PC build/TMPDIR. Launch the installed
Example Demo only after the guest Wayland socket exists, capture the QEMU
framebuffer through QMP, and enable existing runtime diagnostics for
FrameSkipper, Vulkan fence, command execution, and model-stage state. No
source patch or new BitBake build was made.

### Facts

- The explicit launch reached the production model path: the GLB was loaded,
  `MODEL_STAGE_SCENE_ADD_DONE` was logged, scene visibility reached
  `entities=82 renderables=58 lights=13`, and the camera was applied.
- The first two frames returned `FRAME_BEGIN started=true`. From frame 3,
  `FRAME_BEGIN started=false` repeated. `FRAME_SKIP_STATUS status=1` was
  preceded by `FRAME_FENCE_WAIT_LINKED linked=false`.
- Vulkan queue submissions returned `result=0`, but the command trace showed
  `createFenceR` being enqueued without a matching command execution or
  `FRAME_FENCE_LINK` in the bounded run. This is the first confirmed native
  draw-loop failure boundary; it is not evidence that the GLB or camera failed.
- `TREAT_UNLINKED_FENCE_READY=1` made subsequent `FRAME_BEGIN` calls return
  true and caused further queue submissions, but its QMP frame still showed
  only the Flutter HUD. This flag is diagnostic only and is not a proposed
  production fix.
- The diagnostic QMP videos were encoded on the Mac:
  `work/latest-mac/flr0049-ccb81ec/sync-boundary-r3-20260908/qmp-flr0049-sync-boundary-r3.mp4`,
  SHA-256
  `0590ee135b992f2af3731a41c9bbeb3f7bd098f791197a593803fdb1f6eb7b89`, and
  `work/latest-mac/flr0049-ccb81ec/unlinked-fence-probe-20260908/qmp-flr0049-unlinked-fence-probe.mp4`,
  SHA-256
  `a95b564a9817149a7470b5786e34d1dec04eaa54c4392df1e015533c960d0901`.
- The command-trace QMP video is
  `work/latest-mac/flr0049-ccb81ec/fence-command-trace-20260908/qmp-flr0049-fence-command-trace.mp4`,
  SHA-256
  `ec67d5adf95a40313bfb1577e01d0b3da26d54ed1098a763d20e8141a4d24071`.
- All three QEMU probes used QMP-only capture and were ended with QMP
  `quit`; the post-check found no QEMU, runqemu, flutter-auto, or QMP socket
  residual. The intermediate r2 attempt was invalid because it launched the
  app before the Wayland socket existed and is not used as evidence.

### Inferences / Hypotheses

- Inference: two independent defects must be handled separately. The
  FrameSkipper/command-stream fence boundary prevents stable native rendering;
  the above/below subsurface A/B prevents native and Flutter pixels from being
  seen together.
- Hypothesis A: the plugin's rendering work is being queued from a lifecycle
  or ECS strand pattern that leaves `createFenceR` behind a command backlog;
  the repeated off-thread system warning makes thread/flush ordering the
  highest-priority source investigation.
- Hypothesis B: after the frame loop is made stable, the native Wayland child
  still needs a verified alpha-compatible composition path. The existing A/B
  remains: above-parent shows native 3D and hides Flutter HUD; below-parent
  shows Flutter HUD and hides native 3D.

### UNKNOWN / Act

- Exact reason `createFenceR` is not executed within the bounded command stream
  remains UNKNOWN; the next diagnostic must identify the command-stream owner,
  flush boundary, and thread affinity before changing behavior.
- Exact alpha values of the presented Vulkan image remain UNKNOWN. Combined
  HUD + production 3D and Radar/Planetarium transition remain unproven.
- Keep FLR-0049 In Progress. Do not turn the diagnostic ready override into a
  production patch. First produce one minimal Devtool-generated observation
  or fix for the command-stream/thread boundary, then rebuild and repeat the
  QMP pixel loop before changing WSI composition.

## Iteration 19 — remove diagnostic-loop confounder and test flushAndWait (2026-09-08)

### Plan / Do

Repeat the explicit launch without `NATIVE_ALPHA_CLEAR_PROBE`, which creates a
separate software frame loop, to test the normal Wayland frame-callback path.
Then use the existing `NATIVE_SYNC_PRESENT` diagnostic as a bounded causal
test for forcing the engine flush after `endFrame`. No source patch or new
BitBake build was made.

### Facts

- Without the alpha-clear probe, the same production path reached
  `MODEL_STAGE_SCENE_ADD_DONE`, `entities=82 renderables=58`, and camera
  application. The first two frames were true; frame 3 onward was false with
  `FRAME_FENCE_WAIT_LINKED linked=false`. The alpha-clear software loop was
  therefore not the sole cause.
- `NATIVE_SYNC_PRESENT=1` did not provide a usable fix: the first frame logged
  `NATIVE_PRESENT_WAIT_BEGIN`, while no matching `WAIT_DONE` appeared during
  the bounded run. The driver thread continued queue submissions, but the
  app-side flush wait did not complete.
- The normal-path QMP video is
  `work/latest-mac/flr0049-ccb81ec/clean-frame-loop-20260908/qmp-flr0049-clean-frame-loop.mp4`,
  SHA-256
  `bdfbe8a7f7a3bd10fe2ad1b0fe20e4c08b760688f2640e964e466867629fe375`.
- The flush-wait diagnostic QMP video is
  `work/latest-mac/flr0049-ccb81ec/native-sync-present-20260908/qmp-flr0049-native-sync-present.mp4`,
  SHA-256
  `0c2e1b89e1db9b1d0a0f2d4bcb6a5bf091967f34e59b4f9b624af4b3e0e8dbaa`.
- Both runs used QMP-only capture and completed QMP teardown with no residual
  QEMU, runqemu, flutter-auto, or QMP socket.

### Inferences / Hypotheses

- Inference: the confirmed frame-stop boundary is not caused solely by the
  alpha-clear diagnostic loop. The command-stream backlog or driver-thread
  execution boundary remains the leading cause.
- Inference: forcing a synchronous flush from the plugin is unsafe because it
  can block before the queued frame commands complete.
- Hypothesis: the plugin's repeated frame scheduling and Filament's
  asynchronous command stream are not honoring the expected ownership/flush
  boundary; the next diagnostic should trace the driver thread's command
  buffer handoff rather than bypass FrameSkipper.

### UNKNOWN / Act

- The exact reason enqueued `createFenceR` commands are not executed in time
  remains UNKNOWN. Do not apply `TREAT_UNLINKED_FENCE_READY` or
  `NATIVE_SYNC_PRESENT` as a production fix.
- The independent above/below composition failure remains: above-parent shows
  native 3D and hides Flutter HUD; below-parent shows Flutter HUD and hides
  native 3D. Combined HUD + production 3D and route transition remain UNKNOWN.
- Keep FLR-0049 In Progress. Inspect command-buffer handoff and thread
  ownership in the existing Filament/AGL implementation, then choose one
  minimal Devtool-generated diagnostic or fix.

## Iteration 18 — ARGB composition probe prepared (2026-09-08)

### Facts

- The current A/B result is a surface-composition failure: above-parent shows
  native Sequoia 3D while hiding the Flutter HUD; below-parent shows the HUD,
  FPS/CPU/GPU metrics, and controls while hiding native 3D.
- The persistent Mac Devtool source was edited through the Mac-side staging
  workflow and committed as `7f64bba` (`diag: probe ARGB Wayland composition`).
- The Yocto official `oe.patch.GitApplyTree.extractPatches` path, using the
  existing 0199 baseline `5ac26bd`, generated the new patch. The generated
  file and the layer copy have identical SHA-256
  `053e2060b685a9e93e5495d7141c8b58a749c6a3c1c449748f13fe891cca6291`.
- The new diagnostic adds a fully transparent ARGB8888 SHM child with a
  bounded opaque red rectangle. It can be placed above the parent, so the
  compositor's alpha behavior can be observed in QMP pixels without changing
  the production renderer.
- The patch is registered as
  `0200-diag-probe-ARGB-wayland-composition-devtool.patch` after 0199 with
  `patchdir=ivi-homescreen-plugins`.

### Inferences / Hypotheses

- If Flutter HUD pixels are visible outside the red rectangle while the red
  rectangle remains visible, the compositor can alpha-composite child content
  and the remaining failure is likely in the Vulkan native surface contract.
- If the ARGB child also masks the entire parent, the compositor or its
  surface-format path is not honoring alpha; the fix boundary then moves below
  Filament/Flutter.

### UNKNOWN / Act

- The ARGB probe has not yet been built or run on the Mini PC; QMP pixel proof
  is still UNKNOWN.
- Do not treat the probe as a production fix. First commit this layer change,
  send a Git bundle to the fixed receiver, run the focused patch/compile gates,
  then capture one QMP-only run and inspect both the final pixels and runtime
  markers.

## Iteration 17 — explicit guest launch and Mini PC runqemu audit (2026-09-08)

### Plan / Do

Audit the launch contract before judging the renderer. Reuse the latest 0199
rootfs, run one QEMU at a time on the Mini PC, launch Fluorite explicitly as
`agl-driver`, and capture observable cases through QMP. No source patch or new
build was made in this iteration.

### Facts

- Static rootfs inspection found `applaunchd.service`,
  `agl-compositor.service`, `a generated image path (redacted)`, the Fluorite bundle,
  and `/etc/default/flutter`. Active `applaunchd` and compositor do not create
  a `fluorite` app unit automatically.
- The corrected contract is explicit guest launch as `agl-driver` with
  `XDG_RUNTIME_DIR=/run/user/1001`, `WAYLAND_DISPLAY=wayland-0`, and the
  installed Example Demo release bundle. Earlier black/login videos are
  boot-only evidence, not renderer evidence.
- Explicit `Present Mode=immediate` produced a QMP-visible Flutter HUD,
  FPS/CPU/GPU/System delay, Scenes button, and controls. Runtime logged
  `requested=immediate selected=0 supported=true` and transparent swapchain,
  but no model-stage marker during the bounded capture. Video:
  `work/latest-mac/flr0049-ccb81ec/mac-qemu-present-immediate-20260908/qmp-flr0049-present-immediate-explicit-launch.mp4`.
- Explicit default FIFO produced the 2D HUD, logged
  `requested=fifo selected=2 supported=true` and
  `supportedCompositeAlpha=0x3 selected=0x2`, then reproduced the known
  `FEngine::loop` page fault/Oops. Video:
  `work/latest-mac/flr0049-ccb81ec/fifo-explicit-20260908/qmp-flr0049-fifo-explicit.mp4`.
- The Sequoia-controlled case reached Vulkan initialization, transparent
  swapchain creation, model selection, shape creation, camera application,
  and repeated `started=false` frame processing. It did not reach
  `MODEL_STAGE_SCENE_ADD_DONE` or `SCENE_VISIBILITY` before teardown. Video:
  `work/latest-mac/flr0049-ccb81ec/sequoia-controlled-20260908/qmp-flr0049-sequoia-controlled.mp4`.
- Every case was ended through QMP with `host-qmp-quit`; post-checks found no
  QEMU, runqemu, flutter-auto, or QMP socket residual. QMP frames were
  1280x800.

### Inferences / Hypotheses

- Fact: 2D Flutter rendering is reproducible after explicit guest launch.
- Inference: boot health is not the current 3D failure boundary; explicit app
  launch is required before interpreting pixels.
- Hypothesis A: the production scene path can stall before model-scene
  insertion and later hit the known llvmpipe/LLVM failure; this is supported
  but not proven as the sole cause.
- Hypothesis B: the above-parent native Wayland child and Vulkan alpha boundary
  still determine whether native pixels mask or reveal the Flutter parent.

### UNKNOWN / Act

- Combined HUD plus production 3D remains UNKNOWN. The latest valid native-3D
  result remains:
  `work/latest-mac/flr0049-ccb81ec/alpha-clear-20260908/qmp-flr0049-alpha-clear.mp4`.
- Radar/Planetarium route transition remains UNKNOWN.
- Do not add another speculative clear or stacking patch yet. Next, collect
  the first failing process/thread boundary from guest journal, coredump, and
  Vulkan/Wayland markers in a bounded explicit-launch run before selecting the
  next Devtool-generated patch.

## Iteration 19 — ARGB QMP A/B result (2026-09-08)

### Facts

- Project commit `be1a271` was delivered by Git bundle to the fixed Mini PC
  receiver. The existing build directory and fixed TMPDIR were reused.
- The 0200 registration was present in `bitbake -e`. `flutter-auto:do_patch`
  passed 104/104 tasks, `do_compile` passed 2686/2686 tasks, and the full
  image passed 11748/11748 tasks with 21 warnings and no errors.
- The new rootfs artifact SHA-256 is
  `6171d00d4c10b392e3d6d09fd6bca53827a9be765f67403ce2fb480573101ca5`.
- QMP-only capture produced 40 frames at 1280x800. The parent A/B final PNG
  is `work/latest-mac/flr0049-ccb81ec/argb-composition-20260908/qmp-flr0049-argb-composition-final.png`.
  It visibly contains the Flutter HUD and a red opaque rectangle; the area
  around that rectangle remains the Flutter parent.
- The ARGB-above-native A/B final PNG is
  `work/latest-mac/flr0049-ccb81ec/argb-above-native-20260908/qmp-flr0049-argb-above-native-final.png`.
  It contains HUD/CPU/GPU metrics and the red rectangle but no Sequoia 3D.
  Runtime reached ARGB probe creation, GLB request, transparent RGBA8
  swapchain creation, and queue submit; after frame 3 it repeatedly logged
  `started=false` and did not reach `MODEL_STAGE_SCENE_ADD_DONE`.
- Both runs ended with QMP `quit`; no QEMU, runqemu, flutter-auto, or QMP
  socket remained.

### Inferences / Hypotheses

- The ARGB SHM child transparently reveals the Flutter parent outside its red
  rectangle. The compositor therefore supports this alpha path.
- Native Vulkan buffer alpha remains unproven in this A/B because native 3D
  did not reach a stable rendered frame. The earlier above/below-parent A/B
  remains the evidence that the current native and Flutter surfaces are
  mutually hidden when each is visible.

### UNKNOWN / Act

- Native Vulkan buffer alpha contents at the compositor boundary are UNKNOWN.
- Do not make a compositor or native-alpha production fix from this probe.
  Use it as a control while resolving the independent command-buffer/fence
  frame-stop boundary, then repeat composition validation after stable native
  Sequoia pixels return.

## Iteration 20 — transparent Vulkan fixture boundary (2026-09-08)

### Plan / Do

The ARGB SHM control already showed that the compositor can preserve
transparency for a child surface. To distinguish a Vulkan/Wayland WSI alpha
problem from a production Filament output-alpha problem, the persistent Mac
Devtool source now supports an opt-in transparent View for the existing native
minimal cube fixture. The source change was committed in the Devtool Git as
`15b6aca` (`diag: render minimal geometry with transparent view`).

Yocto's official `oe.patch.GitApplyTree.extractPatches` path generated the
corresponding patch from the existing `7f64bba` baseline. It was copied
unchanged into the layer as
`0201-diag-render-minimal-geometry-transparent-view-devtool.patch`; the
generated patch and layer copy have SHA-256
`ec9cc7d92847e7f05e212cb8779763ebae5920a2fce89a19fdc01d58389a25c3`.

### Hypotheses / prediction

- If the transparent Vulkan fixture shows its cube while Flutter HUD pixels
  remain visible outside it, the WSI/compositor alpha path works and the next
  boundary is the production Filament output.
- If the transparent Vulkan fixture also hides the entire Flutter parent, the
  native Vulkan surface is effectively opaque at the compositor boundary.

### UNKNOWN / Act

- The Mini PC build and QMP pixel result for the transparent Vulkan fixture are
  UNKNOWN. Run the focused Yocto gates, then capture QMP-only frames with
  `FLR0026_NATIVE_MINIMAL_GEOMETRY=1` and
  `FLR0026_NATIVE_MINIMAL_GEOMETRY_TRANSPARENT=1`. Do not promote this
  diagnostic to a production fix.

## Iteration 21 — parent-alpha probe launch boundary (2026-09-08)

### Facts

- Mac Devtool source commit `ddb0f2a` generated layer patch
  `0202-diag-probe-ARGB-wayland-below-parent-devtool.patch`; project commit
  `02b1349` was bundled and delivered to the fixed Mini PC receiver.
- The reused Mini PC build produced rootfs SHA-256
  `fba8df9e2f190703515e20ba4eb47b3b3b3e6110aaee2662074de29d96cc64a6`.
- The normal `fluorite` launch failed before Flutter/Filament initialization
  with `agl_shell extension already in use by other shell client` while the
  `agl-shell-grpc-server` child was active. Stopping that child caused the
  compositor to core-dump; it was restarted. This is a launch interaction,
  not alpha evidence.
- A diagnostic XDG-only launch using `--xdg-shell-app-id homescreen` reached
  model selection, Wayland surface creation, transparent Vulkan swapchain
  selection (`supported=0x3`, `selected=0x2`), and frame processing.
- The QMP-only final frame is
  `work/latest-mac/flr0049-ccb81ec/parent-alpha-20260908-qmp-r3-final.png`;
  its PPM SHA-256 is
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  It is all black. The QMP video is
  `work/latest-mac/flr0049-ccb81ec/parent-alpha-20260908-qmp-r3.mp4`.
- This all-black frame is not a valid composition verdict because the
  `homescreen` surface was not proven compositor-visible. QMP quit completed;
  no QEMU, runqemu, or QMP socket remained.

### Inferences / Hypotheses

- The strongest existing composition evidence remains the valid native
  above/below-parent A/B: native above hides the Flutter HUD; native below is
  hidden by the Flutter HUD. This is consistent with the Flutter 2D parent
  painting opaque pixels over the lower child, but does not identify whether
  the opacity comes from Flutter pixels, Vulkan contents, or stacking policy.
- The ARGB SHM control showed transparent child pixels revealing Flutter, so
  generic Wayland ARGB composition is not the leading issue.

### UNKNOWN / Act

- Flutter parent buffer alpha at the compositor boundary remains UNKNOWN;
  `Scaffold` alpha alone is not proof of buffer alpha.
- Valid `fluorite` launch while the grpc shell client is active remains UNKNOWN.
- Do not promote patch 0202 or the `homescreen` launch to a product fix. The
  next valid test must use a compositor-visible launch contract and a stable
  native/ARGB comparison.

## Iteration 22 — compositor-visible AGL owner and 2D-parent masking result (2026-09-08)

### Facts

- Mac Devtool source commit `57308d9c` generated layer patch
  `0203-diag-allow-XDG-fluorite-launch-without-AGL-bind-devtool.patch`.
  The unchanged patch was registered in the project and delivered as bundle
  `xdg-launch-4693bd0.bundle`; its SHA-256 is
  `45a8ac29a7189eb05c7739b016cb1835c86c372319f099ad1161aea9c838bf1e`.
- The fixed Mini PC receiver reused the existing build and TMPDIR. Focused
  patch/compile gates and the full image build passed. Rootfs SHA-256:
  `0a74582321c4deebab2dc20863d1c264f35b0857aba1ef677868436dd53d7e7a`.
- With `agl-shell-grpc-server` active, normal `fluorite` launch failed at the
  AGL-shell ownership boundary with `agl_shell extension already in use by
  other shell client`.
- For a snapshot-only A/B, the live guest Weston configuration removed the
  grpc shell-client entry and `agl-compositor.service` was restarted. No
  rootfs or layer file was changed by this runtime-only operation.
- Under that compositor-visible AGL-owner condition, explicit `fluorite`
  showed the Flutter HUD, FPS, CPU/GPU metrics, graph, Scenes button, and
  bottom controls in a QMP-only 1280x800 capture. Final PNG:
  `work/latest-mac/flr0049-ccb81ec/fluorite-production-qmp-final.png`.
- The same condition with the self-made native cube below the Flutter parent
  showed the HUD but no cube or red ARGB probe pixels. With the cube above the
  parent, the cube and HUD were both visible. Above-parent final PNG:
  `work/latest-mac/flr0049-ccb81ec/fluorite-mock-above-qmp-final.png`.
- Production selected Vulkan transparent composite alpha
  (`transparent=true`, `supported=0x3`, `selected=0x2`), but its bounded log
  did not reach `MODEL_STAGE_SCENE_ADD_DONE`; the QMP frame therefore showed
  the Flutter HUD over an otherwise black content area and no vehicle.
- The guest application and QEMU were stopped with exact PID/QMP targeting.
  Post-checks found no `qemu-system-x86_64`, `runqemu`, or QMP socket.

### Inferences / Hypotheses

- The leading composition hypothesis is that the Flutter 2D parent paints an
  opaque black buffer over a native surface placed below it. This explains the
  valid below/above A/B and visible HUD, but is not yet direct alpha-channel
  measurement.
- `transparent=true` and `blend_opaque=false` describe requested native
  rendering/compositor state; they do not prove that Flutter's parent buffer
  contains transparent pixels.
- Generic Wayland ARGB composition is not the leading fault because the
  transparent ARGB child revealed the Flutter parent around its opaque
  rectangle.
- The missing production vehicle is an additional boundary: the latest run
  stopped before model scene-add completion. It cannot yet be attributed to
  parent opacity.

### UNKNOWN / Act

- UNKNOWN: actual alpha values of Flutter's submitted parent buffer in the
  black content area. `Scaffold(backgroundColor: Colors.black.withAlpha(0))`
  is source intent, not compositor-boundary evidence.
- UNKNOWN: whether production model pixels appear after restoring a stable
  scene-add/frame loop under the same compositor-visible launch.
- Next: collect direct parent-buffer alpha evidence and separately restore the
  production model/frame loop. Keep grpc removal snapshot-only until the AGL
  shell ownership contract is selected; do not promote 0203 as a product fix.

## Iteration 23 — production model-only QMP proof and execution-loop corrections (2026-09-08)

### Facts

- The existing Mini PC QEMU was reused as the only QEMU instance; no second
  temporary build directory was created.
- The production run reached
  `FLR0026_MODEL_STAGE_SCENE_ADD_DONE asset=assets/models/sequoia_ngp.glb
  guid=14 mode=secondary`.
- The run selected Vulkan transparent composite alpha:
  `transparent=true supported=0x3 selected=0x2`.
- QMP-only evidence contains actual production Sequoia 3D pixels and red
  lamps:
  `work/latest-mac/flr0049-ccb81ec/model-only-20260908/qmp-final.png`.
  The video is
  `work/latest-mac/flr0049-ccb81ec/model-only-20260908/qmp-model-only.mp4`.
  This isolation used native-above-parent stacking, so the Flutter HUD was not
  visible in the same frame.
- PPM, PNG, video, runtime-log, and serial-log SHA-256 values are recorded in
  the corresponding Iteration 23 entry in the working log.
- The runtime continued to emit Vulkan submit/present markers, but
  `FLR0026_FRAME_BEGIN` reached `seq=630 started=false`; stable continuous
  rendering is not proven.
- The guest Flutter process was stopped by its exact PID, QMP `quit` was sent
  to the exact run socket, and no QEMU process or QMP socket remained.

### Inferences / Hypotheses

- This is direct evidence that the production asset-loading, scene insertion,
  native Filament rendering, and QMP-visible pixel path can work. It is not
  evidence that Flutter 2D and native 3D can be composited together.
- The leading composition hypothesis remains an opaque Flutter 2D parent
  covering a native child placed below it. The parent alpha itself is still not
  directly measured.
- The `started=false` boundary is an independent runtime issue and must not be
  attributed to the alpha hypothesis without an A/B test.

### Execution corrections

- Guest runtime inspection must use Mac -> Mini PC -> forwarded QEMU guest SSH;
  host-side `/tmp` is not the guest runtime log.
- QEMU startup must include `-usb -device usb-tablet` before the first boot.
- Log marker queries must preserve shell quoting; the raw copied runtime log is
  authoritative when a filtered query is malformed.
- Keep one reusable QEMU and one reusable build/TMPDIR. Store both failed and
  successful artifacts under the same run directory, and stop the exact guest
  app before sending QMP `quit`.

### UNKNOWN / Next

- UNKNOWN: actual alpha values in the Flutter parent buffer at the compositor
  boundary.
- UNKNOWN: combined below-parent production 3D visibility after the frame loop
  is restored.
- Next: instrument or otherwise directly measure the Flutter parent buffer
  alpha, separately restore continuous frame starts, then run the combined
  QMP-only scene and route-transition validation.
