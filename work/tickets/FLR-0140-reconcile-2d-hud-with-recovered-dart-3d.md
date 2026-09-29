# FLR-0140 — reconcile 2D HUD with recovered Dart 3D

- Status: Waiting
- Priority: High
- Owner: Flutter surface/compositor + Fluorite ViewTarget roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0139](FLR-0139-bind-dart-unlit-base-map.md), [FLR-0138](FLR-0138-test-dart-cube-culling-contract.md)
- Working log: `work/logs/2026-09-13-flr0140.md`

## Work unit

Keep the FLR0139 recovered Dart Cube material, camera, culling, image, and
QEMU profile fixed. Determine why the FLR0139 QMP frame shows the recovered
3D Cube on a white frame but does not show the 2D HUD that was visible in the
FLR0138 QMP frame.

## Evidence that opened this ticket

- FLR0139 normal-Dart runtime reached a swapchain render pass and
  `FLUORITE_VK_PRESENT_CALL_RETURN result=0`.
- FLR0139 QMP fixed region `[300,250,620,400]` contained a non-uniform
  rotated Cube: `changed_pixels=217400`, edge bounding box
  `[525,302,232,202]`, and `geometry_indicator=present`.
- The same FLR0139 full QMP frame was predominantly white and did not show
  the 2D HUD metrics/buttons seen in FLR0138. This is an observed visual
  boundary, not yet proof of a single transparent-surface cause.

## Hypotheses / UNKNOWN

- H1: a Flutter platform surface or ViewTarget composition order hides the 2D
  HUD after the 3D surface becomes visible — OPEN.
- H2: the white frame is a capture/timing state after Flutter surface
  activation rather than the stable composed frame — OPEN.
- H3: the 2D HUD is emitted by a separate surface whose alpha/activation
  contract differs from the recovered 3D surface — OPEN.

UNKNOWN: which surface owns the white background and whether the HUD is still
rendering behind it.

## Static API relationship map (2026-09-13)

### Facts

- `example/lib/main.dart` keeps one persistent `SceneView`; its current
  `poGetFilamentScene()` payload is the FLR0139 minimal fixture: empty models,
  one unlit textured Cube, one fixture Camera, and no explicit Skybox.
- The `Scenes` menu only replaces the Flutter-side `StatefulSceneView` control
  widget. It does not replace the persistent `SceneView` or call
  `SceneController.updateFilamentScene`, so a menu transition is not yet a
  native scene-payload transition.
- Dart `SceneView` creates the
  `com.toyotaconnected.filament_view.channel_3d_scene` platform view. Native
  registration creates a `ViewTarget` with a separate Wayland child surface,
  places its subsurface above the Flutter parent, uses a transparent swapchain,
  and normally selects `View::BlendMode::TRANSLUCENT`.
- Native deserialization maps the Dart `scene`, `models`, and `shapes` maps
  into ECS systems before applying the deserialized camera. An absent Skybox
  selects the default transparent Skybox after initial system setup.
- The Dart package also exposes `SceneController.updateFilamentScene()` on a
  per-view `MethodChannel` named `UPDATE_FILAMENT_SCENE`, plus generated
  `setActiveCamera`, `setCameraOrbit`, `setCameraTarget`, and `setCameraDolly`
  calls. The current native `FilamentViewApi` header/implementation has no
  `UPDATE_FILAMENT_SCENE` handler and no corresponding generated camera
  methods. The initial `scene.camera` payload is therefore the only camera
  path proven to be consumed by this image.
- The `unlitUV` material declares transparent blending and requires `baseMap`.
  FLR0139's binding of the packaged opaque texture satisfied that Dart/native
  material input contract and restored Cube pixels.

### Inferences

- FLR0139's QMP Cube proves that the child Wayland surface can reach the final
  framebuffer. Its missing HUD is therefore a composition/parent-painting
  boundary, not evidence that Filament stopped producing 3D.
- The current Example Demo cannot yet prove production Scene or
  Planetarium/Playground transition behavior: the native payload remains the
  minimal fixture while only Flutter controls change.
- The API mismatch explains why the scene menu and scene-specific camera
  callbacks cannot currently be used as evidence of native scene transition;
  they are Flutter-side control changes unless a native update contract is
  added or the platform view is rebuilt with a supported initialization path.

### UNKNOWN

- Whether FLR0139's light background is the Flutter compositor background
  exposed through transparent native pixels, an opaque/incorrectly cleared
  child buffer, or a capture taken during parent-surface activation.
- Whether the HUD was painted in the parent surface but covered by the child,
  or was absent from the parent frame at capture time.
- Whether the intended fix is a native scene-update API, an app-side
  initialization/rebuild contract, or both remains an implementation decision
  for a separate ticket.

## Same-run checkpoint (2026-09-13)

- The fixed FLR0139 image was launched once with normal Dart and one QEMU.
  Early QMP showed the Flutter HUD and a uniform-black 3D region. Later QMP
  showed the rotated Cube in the same region and no HUD.
- The runtime stayed healthy across the transition:
  `application=1`, `shape_ready=1`, `camera_applied=1`,
  `begin_true=147`, `render_return=147`, `end_frame=147`,
  `target_draw2=1063`, `vk_present=588`, `errors=0`.
- QMP-only evidence is retained at
  `$LOCAL_QMP_EVIDENCE_ROOT/flr0140-reconcile-2d-hud/qmp-early.png` and
  `$LOCAL_QMP_EVIDENCE_ROOT/flr0140-reconcile-2d-hud/qmp-late.png`.
  The remote evidence role root is
  `$EVIDENCE_ROOT/evidence/flr0140-reconcile-2d-hud/qemu`.
- This closes the “3D renderer stopped” explanation for the current image and
  leaves the final-frame surface composition owner open. The first source-owned
  probe is split into [FLR-0142](FLR-0142-flush-wayland-child-surface.md). The
  Dart/native scene and camera API mismatch remains the separate
  [FLR-0141](FLR-0141-align-dart-native-scene-camera-api.md) boundary.

## Scope boundary

Do not reopen FLR0139 or change its baseMap patch. Use a new ticket and one
QMP run per composition hypothesis, with the same single-process launch guard
and evidence region.
