# FLR-0120 — register Filament camera API before fixture initialization

- Status: Waiting
- Priority: High
- Owner: Mac persistent Devtool native source + Mini authoritative runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0119](FLR-0119-fix-ecs-platform-channel-init-race.md)
- Working log: `work/logs/2026-09-13-flr0120.md`

## Work unit

Make the self-made blue-cube fixture deliver its initial camera state through
the Filament Pigeon API before the first native scene frame. This ticket owns
the camera API registration/readiness boundary only. It does not claim that
the production shaded scene, light, material, or compositor alpha path is
fixed.

## Problem

FLR-0119 stopped the native ECS null dereference and reached shape creation and
Vulkan submit, but QMP showed only the 2D HUD and buttons. The runtime log
contains `PlatformException(channel-error)` for
`FilamentViewApi.setCameraDolly` and `setCameraTarget`. Static native source
shows that `RegisterWithRegistrar` calls scene deserialization before it
constructs `FilamentViewPlugin` and calls the generated
`FilamentViewApi::SetUp`, so the camera's initial dolly/target messages can
arrive before their handlers are registered.

## Success criteria

- [x] This is the sole `In Progress` ticket; no QEMU/build process is running
  before source work begins.
- [x] Effective native and Dart source confirm the message registration and
  camera initialization order, with ownership/thread risks recorded.
- [x] At least two remedies are compared: native API registration before
  deserialization, and a Dart-side readiness gate/replay of camera state.
- [x] The selected source change is made in the persistent Mac Devtool source
  and converted to a patch by official Yocto Devtool; no generated patch body
  is hand-edited.
- [x] The unchanged patch is registered in `meta-fluorite-trial`, passes the
  Mac recipe gate, and is committed locally.
- [x] The exact commit reaches the fixed Mini receiver by complete-history
  bundle; `do_patch`, targeted compile, and full image pass using the existing
  build/TMPDIR.
- [ ] One fresh QEMU launches exactly one source-selected fixture with no
  camera `channel-error`; logs show camera target/dolly delivery and frame/
  present markers, while coredump remains empty. **FAIL:** the process stayed
  alive and submitted Vulkan work, but the two camera calls still returned
  `channel-error`.
- [ ] QMP-only capture shows nonzero geometry in `[300,250,620,400]`, and the
  run is stopped by negotiated QMP quit with zero residual targets/sockets.
  **Capture/teardown PASS; geometry FAIL:** the region remained
  `0/248000` and uniform black.

## Facts

- FLR-0119 evidence is under
  `$EVIDENCE_ROOT/flr0113-authoritative/flr0119-bbdcd60/qemu`.
- The FLR-0119 fixture QMP frame showed 2D HUD/button pixels but
  `[300,250,620,400]` was uniform black (`0/248000` changed, no edges, no
  chromatic pixels).
- The FLR-0119 fixture log recorded successful ECS initialization,
  `SHAPE_READY`, native readiness, event-channel creation, and Vulkan submit,
  but `setCameraDolly` and `setCameraTarget` first returned Pigeon
  `channel-error`.
- The effective native order is `RunOnce` → view-target request → async scene
  deserialization/channel setup → `FilamentViewPlugin` construction →
  `FilamentViewApi::SetUp` → event-channel setup. The generated Pigeon API
  handler registration is therefore later than the Dart camera initialization
  messages under this timing.
- The final Dart fixture camera requests orbit distance 5, dolly offset
  `(5,0,0)`, orbit angle `1.5707963267948966`, and target `(0,0,0)`.
- The final Dart generated API contains `setCameraOrbit`, `setCameraTarget`,
  `setActiveCamera`, and `setCameraDolly` channels. The effective native
  `messages.g.h/.cc` contains no handlers for those names; it contains the
  older `changeCameraMode`, `changeCameraOrbitHomePosition`,
  `changeCameraTargetPosition`, `changeCameraFlightStartPosition`, and
  `setCameraRotation` channels instead.
- The effective `SceneView` sends `widget.cameras` as a root-level
  `cameras` creation parameter and initializes each Dart camera in
  `_onPlatformViewCreated`. The effective native deserializer handles only
  root `models`, `scene`, and `shapes`; it creates its native camera only
  from `scene.camera`. Therefore the current root camera payload is ignored
  and the Dart initialization calls an API generation the native side does
  not implement.
- The persistent Devtool source commit is `3d2582901653497a8e62349b3ab4813752d7def2`.
  It moves only the existing plugin/API registration block before scene
  deserialization.
- Official Yocto Devtool generated
  `0001-fix-register-filament-camera-API-before-scene-load.patch` from the
  post-FLR-0119 baseline `c3087dfef4469d58ac71d3759e02468122cb5268`.
  The canonical 0232 copy is byte-identical and has SHA-256
  `8f576e01c10d402209b9c0fe4d04a818cb49da0d7cbfe8b99d7383c11789fe63`.
- The Mac fixed-container `flutter-auto:do_patch` gate passed: 104 tasks were
  attempted and all succeeded, including the registered 0232 patch.
- The first post-registration canonical verification failed only because the
  authorized layer file count was still 295 while the actual count was 296.
  After updating the lock to measured repository and normalized hashes,
  `make verify` passed with 85 Python tests and all repository/QEMU gates.

## Inferences

- The camera message loss is a stronger next boundary than light/material
  analysis because it is directly evidenced by the runtime error and source
  order, while the shape and submit path already succeed.
- The native registration reorder was smaller than a new Dart replay protocol,
  but the runtime falsified it: registration order cannot create handlers that
  are absent from the native generated API.
- The plugin constructor only registers the platform-view listener and does not
  consume the asynchronously deserialized scene. The generated API setup uses
  the registrar messenger and plugin instance, while `registrar->AddPlugin`
  retains ownership. This supports testing the native reorder before the
  scene-deserialization call.
- The first attempt used a pre-FLR-0119 `b12886d` baseline and produced no
  usable update because the installed Devtool's `--initial-rev` override skips
  the recipe's top-level initial revision in this workspace. It was not
  registered. Recreating the temporary component recipe at the exact
  post-FLR-0119 baseline produced the expected one-commit patch.

## Hypotheses / UNKNOWN

1. **Native reorder is safe and sufficient.** **Falsified:** the generated
   native API has no `setCameraDolly` or `setCameraTarget` handlers, and the
   same two channel errors remained after 0232.
2. **Dart readiness/replay can solve the current failure.** **Not sufficient
   by itself:** delaying calls cannot reach handlers that do not exist in the
   native generated API.
3. **Dart/native camera contract is from different API generations.** This is
   the leading next boundary, supported by the source-set comparison and the
   post-0232 runtime. FLR-0121 owns the compatible scene-payload experiment.
4. **UNKNOWN:** after the camera contract is corrected, whether the central
   black region is caused by camera visibility or a separate
   light/material/surface-composition issue.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | Pigeon camera dolly/target calls return `channel-error` | fixture log and generated API registration |
| Where | `RegisterWithRegistrar` order in `filament_view_plugin.cc` | Mini effective source |
| When | Initial camera setup before `FilamentViewApi::SetUp` | timestamped fixture log |
| Who | native plugin registration and Dart camera initialization roles | source call chain |
| How | scene deserialize is entered before generated method handlers exist | source diff and controlled runtime |

## PDCA

### Plan

1. Preserve FLR-0119's QMP/coredump result and ensure no QEMU remains.
2. Inspect native plugin construction, generated Pigeon API setup, Dart camera
   state sends, and plugin lifetime/thread ownership.
3. Compare native registration reorder with Dart readiness/replay; choose one
   minimal falsifiable change.
4. Edit persistent Mac Devtool source, generate official patch, register and
   gate it, then bundle/build and run one QMP fixture.

### Do

- Ticket created after FLR-0119 proved the ECS crash boundary was repaired but
  camera state was lost before the first visible 3D frame.
- Confirmed the fixed Podman machine/container and persistent source Git path
  are available; the Mac gate is rootful and bind-mounted.
- Confirmed the Mini role has no residual QEMU, Flutter, compositor, or BitBake
  process before source work.
- Read the effective native source and generated Pigeon setup. The native
  reorder was selected as the minimal countermeasure, then rejected by the
  runtime because the native generated API lacks the Dart camera methods.
- Edited the persistent source, committed it through the source-Git wrapper,
  generated the official patch from the exact post-FLR-0119 baseline, and
  copied it unchanged to the canonical 0232 path.
- Saved the execution plan at
  `docs/superpowers/plans/2026-09-13-flr0120-camera-api-registration.md`.
- Registered 0232 after 0231 and passed the Mac recipe gate. The canonical
  layer checkpoint commit `81caadcd6f32910a80de0d0bffce671ca2e50386` was
  bundled to the fixed Mini receiver; all progressive and full-image gates
  passed.
- One fresh QEMU run reached `SHAPE_READY`, successful Vulkan submit, and no
  coredump, but still emitted `setCameraDolly` and `setCameraTarget`
  `channel-error` messages. QMP early/late frames were byte-identical; the
  central region was uniform black.
- The video wrapper attempt failed because its public operation accepts only
  `capture|analyze`, not `video`. The underlying QMP captures and negotiated
  quit were still completed and preserved; this harness-interface failure is
  not a runtime success or failure.

### Check

- Ticket/dashboard split: **PASS**; FLR-0119 is Waiting and FLR-0120 is the
  sole active work unit.
- Source order, plugin lifetime review, and two-remedy comparison: **PASS**.
- Pre-change fixture QMP/runtime evidence: **PASS as inherited red control**;
  camera calls fail with `channel-error` and the central region is black.
- FLR-0120 source edit and official patch generation: **PASS**.
- Canonical registration, lock refresh, and Mac recipe gate: **PASS**.
- Canonical layer commit: **PASS**, `81caadcd6f32910a80de0d0bffce671ca2e50386`.
- Mini bundle/receiver/build gates: **PASS**; receiver tip is
  `81caadcd6f32910a80de0d0bffce671ca2e50386`.
- FLR-0120 runtime test: **PASS as a bounded falsification run**; no coredump,
  submit succeeded, but camera channels and 3D pixel acceptance failed.
- Native reorder hypothesis: **FAIL**.
- QMP capture and QMP teardown: **PASS**; geometry acceptance: **FAIL**.

### Act

- Do not add another registration-order variant to FLR-0120. Create FLR-0121
  for the Dart/native camera API-generation mismatch and restore the native
  v2 scene-camera payload contract there.
