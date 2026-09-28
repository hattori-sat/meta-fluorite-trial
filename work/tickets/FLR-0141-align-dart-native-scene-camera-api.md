# FLR-0141 — align Dart/native scene and camera update API

- Status: Done
- Priority: High
- Owner: Flutter filament_scene API + Fluorite native plugin roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0140](FLR-0140-reconcile-2d-hud-with-recovered-dart-3d.md)
- Working log: `work/logs/2026-09-13-flr0141.md`

## Work unit

Make the Example Demo's scene selection and camera controls use one explicit,
implemented Dart/native contract. Prove the contract with a deterministic
payload transition from the self-made Cube to one selected scene fixture, then
prove the selected camera is consumed by native Fluorite and the resulting 3D
pixels reach QMP.

## Static facts opening this ticket

- Dart `SceneController.updateFilamentScene()` invokes the per-view
  `UPDATE_FILAMENT_SCENE` MethodChannel with `scene`, `models`, and `shapes`.
- Current native Fluorite source has no `UPDATE_FILAMENT_SCENE` handler. Its
  generated `FilamentViewApi` also lacks the Dart-generated
  `setActiveCamera`, `setCameraOrbit`, `setCameraTarget`, and `setCameraDolly`
  methods.
- The current Demo creates one persistent `SceneView` with the FLR0139 minimal
  Cube payload. The Scenes menu replaces only a Flutter `StatefulSceneView`
  overlay and does not update that native payload.
- The initial `scene.camera` embedded in the creation parameters is consumed by
  native deserialization; this is the camera path evidenced by
  `camera_applied=1` in FLR-0140.

## Selected contract for this work unit

Use the existing Flutter platform-view creation contract as the first gate:

- Dart supplies `scene`, `shapes`, `models`, and the first `cameras` entry.
- `SceneView` embeds that first camera as `scene.camera` because the current
  Fluorite Native deserializer consumes `scene.camera`; root-level `cameras`
  and post-create Dart camera initialization are not part of the v2 contract.
- The first payload is the shape-only Planetarium fixture. It deliberately
  excludes GLB models and the unsupported `UPDATE_FILAMENT_SCENE` channel so
  shape serialization, native deserialization, camera application, and QMP
  pixels can be evaluated independently of the known production-GLB/LLVM
  failure.

This is an initialization-path proof, not yet a menu-transition proof. A real
scene transition requires a separately implemented Native update/reload
protocol with matching Dart and Native method names and ownership.

## Implementation checkpoint

- Devtool source branch: `devtool-flr0141-planetarium-contract`
- Devtool source commit: `6498a93`
- Generated patch: `0060-test-send-planetarium-shapes-through-native-creation-devtool.patch`
- Generated/canonical patch SHA-256:
  `fe98f13ca9e88755da2f7de009b1583e97945b7aa80556f64b7e4bbf97987537`
- Mac Podman recipe `do_patch`: PASS, 104 attempted / 100 reused / 0 failed

The first finish attempt was rejected as evidence because the recipe was
reconnected only after the source edit, so Devtool treated the edited commit
as its baseline and emitted no new patch. The source commit was retained, a
new branch was created from the pre-edit `450511d`, Devtool modify was run
first, and the edit/commit/finish sequence was repeated successfully.

## Success criteria

- The chosen contract is documented in the ticket and source comments.
- Dart and native method names, arguments, return/error behavior, and payload
  ownership agree; no silent unimplemented channel remains on the exercised
  path.
- One normal-Dart QEMU run proves the selected shape-only initialization
  payload, camera application, and QMP-visible 3D pixels, while preserving the
  single-QEMU launch guard and evidence hashes.
- Any source change is generated through Mac Devtool, copied unchanged into
  `meta-fluorite-trial`, committed, bundled once, built on the fixed Mini
  receiver, and validated with QMP-only evidence.

## Hypotheses / UNKNOWN

- H1: the original Demo expected initial creation parameters to contain all
  scene entities, while the current app was reduced to the FLR0139 fixture;
  restoring that contract may be sufficient for the first scene proof.
- H2: runtime scene transitions require a native update/reload API because the
  current native deserializer is one-shot and the scene menu only changes
  Flutter controls.
- H3: camera controls require regenerating or explicitly implementing the
  current Pigeon methods; initial camera deserialization and interactive camera
  control are separate contracts.

UNKNOWN: whether the smallest safe implementation is an app-side supported
initial-payload path, a native scene-update protocol, regenerated Pigeon camera
methods, or a combination. Select one variable after FLR-0140 composition
ownership is recorded.

## Scope boundary

Do not modify FLR-0139's material patch. Do not fold Wayland surface alpha,
commit, or flush changes into this ticket; those belong to the composition
boundary ticket or its own one-variable follow-up.

## Iteration 1 result — initial Planetarium payload

### Runtime classification

- **Dart/API delivery: PASS.** The normal Example Demo reached
  `Application Id: fluorite`; Native reported 21 `SHAPE_READY` entries with
  `renderable=true`.
- **Scene/frame/present: PASS.** The bounded run recorded 354 scene-pass
  begin/end pairs and 353 successful Vulkan present returns with exactly one
  `flutter-auto` process and no coredump/page fault.
- **Visible Planetarium 3D: FAIL for this payload.** The post-launch QMP
  frame and all 12 QMP video frames were uniform `224,224,224` in the fixed
  region `[300,250,620,400]`; edge and chromatic geometry indicators were
  absent. The post-launch PPM SHA-256 is
  `2097d8f3aa89cb4083d5414e2636bbd9cf88d6a261844a2d8b9a947554376311`.
- **Transition: NOT TESTED.** `UPDATE_FILAMENT_SCENE` remains absent from
  Native, so this run intentionally tested only initial creation parameters.

### Explicit relationship found

Dart's Planetarium camera uses `orbitOriginPoint=(-720,0,680)` and an orbit
radius of `80`, but its legacy `flightStartPosition` serialization emitted
`(80,0,0)`. Native treats that field as the world-space eye in
`lookAt(flightStartPosition,targetPosition,upVector)`. The Cube trial masked
this mismatch because its target was the origin. This explains why shape
creation and present can succeed while the Planetarium geometry is outside
the intended view.

### Second implementation checkpoint

- Devtool source branch: `devtool-flr0141-camera-contract`
- Devtool source commit: `a031086`
- Generated patch: `0061-filament_scene-align-camera-world-eye-devtool.patch`
- Generated/canonical patch SHA-256:
  `5847ddadcc4d2917df826a3a316e3128d34ed67fb866d5caaca5665e9312d104`
- Mac Podman recipe `do_patch`: PASS, 104 attempted / 100 reused / 0 failed

The patch preserves the origin-centered fixture and translates only
orbit-point cameras to a target-relative world-space Native eye.

## Iteration 2 result — target-relative Native camera eye

### Facts

- Canonical commit `420c3dc2d405dd1e708cd1fca3619a57923e5071` contains the
  unchanged Devtool-generated camera patch, recipe registration, baseline
  lock, and this ticket/log evidence. Canonical verification passed before
  handoff.
- One bundle transferred the exact commit to the fixed Mini receiver.
  Metadata resolved `meta-fluorite-trial=420c3dc2`, `MACHINE=qemux86-64`, the
  fixed build/TMPDIR, and `0061` in the effective recipe `SRC_URI`.
- Mini `do_patch` passed with 104 attempted tasks, target recipe
  `do_compile` passed with 2,590 attempted tasks, and the resumed full image
  completed with 11,898/11,898 tasks successful. The existing build/TMPDIR
  and caches were reused; no clean task was run.
- The timestamp-matched rootfs was built at 2026-09-13 23:00:59 and has
  SHA-256
  `bba0d4b7d25be51ff1491b8547f3740ff1dbc1164904744d80d94c024e503093`.
- One normal-Dart QEMU run used the QMP-only evidence role
  `$EVIDENCE_ROOT/evidence/flr0141-planetarium-camera/qemu/`. QMP prelaunch
  was uniform black in `[300,250,620,400]`. Postlaunch changed
  `134,962/248,000` pixels, had edge bbox `[437,250,406,346]`, luma
  `[0,255]`, and `geometry_indicator=present`.
- The postlaunch PPM SHA-256 is
  `16472df74ab11a5cc229df1e27f6d0b6e7096481946b7a1bb5712f327b7d435e`.
  All 12 QMP video PPMs have the same SHA-256. The visual frame shows a
  centered black Planetarium shape on the pale frame: the silhouette is
  visible, but its intended color/lighting is not.
- Runtime evidence recorded exactly one `flutter-auto`, 21
  `SHAPE_READY ... renderable=true` entries, 60 paired scene-pass entries,
  58 successful queue/present returns, and zero `SIGSEGV`/page-fault matches.
  `UPDATE_FILAMENT_SCENE` and generated `setCamera*` calls remained zero by
  design; this ticket exercised the creation payload only.
- QMP negotiated quit and cleanup passed with zero residual target processes
  and zero residual QMP sockets.

### Inferences

- H1 is confirmed as the cause of the previous uniform Planetarium frame:
  Dart's orbit-point camera was serialized as a radius-like
  `flightStartPosition=(80,0,0)`, while Native consumed it as the world-space
  eye of `lookAt()`. Translating it to
  `(target.x + radius,target.y,target.z)` restores visible Planetarium
  geometry.
- The remaining black appearance is downstream of camera placement. The
  renderer, shape construction, scene pass, present, and QMP child surface
  are proven on this run.
- The result does not prove a scene transition or HUD composition fix. Those
  remain separate API/compositor work units.

### Hypotheses / UNKNOWN after this iteration

- H1 camera coordinate mismatch: **falsified as remaining cause; fixed by
  `0061`**.
- H2 child-surface opacity/stacking: **open**, but not the cause of the
  absent Planetarium silhouette in this run.
- H3 Planetarium lit material/light world-space contract: **leading for the
  black appearance; split into FLR-0143**.
- UNKNOWN: whether direct-light placement, indirect-light wire format, or
  the Native lit-material path is the first cause of the black shading.

### Decision

- Close FLR-0141 as the independent camera/API-initialization unit. Keep the
  unimplemented `UPDATE_FILAMENT_SCENE` and generated interactive camera
  methods explicit as out of scope; do not use them as silent evidence.
- Continue the overall 3D goal in the new
  [FLR-0143](FLR-0143-align-planetarium-light-material-contract.md) ticket,
  beginning with the Dart/Native light world-space relationship.
