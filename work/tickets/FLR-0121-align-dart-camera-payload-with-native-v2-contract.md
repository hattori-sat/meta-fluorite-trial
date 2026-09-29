# FLR-0121 — align Dart camera payload with native v2 contract

- Status: Waiting
- Priority: High
- Owner: Mac persistent Devtool app source + Mini authoritative runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0120](FLR-0120-register-filament-camera-api-before-fixture-init.md), [FLR-0119](FLR-0119-fix-ecs-platform-channel-init-race.md)
- Working log: `work/logs/2026-09-13-flr0121.md`

## Work unit

Make the self-made blue-cube fixture use the native v2 camera contract that
the effective `flutter-auto` plugin actually implements. This ticket owns the
Dart creation-parameter placement and the removal of unsupported Dart camera
method calls. It does not implement a new native Pigeon API, change lighting,
or claim production-scene success.

## Problem

FLR-0120 moved native `FilamentViewApi::SetUp` before scene deserialization,
but the runtime still returned `channel-error` for
`setCameraDolly` and `setCameraTarget`. Static evidence shows that the Dart
generated API is newer than the native generated API: Dart sends
`setCameraOrbit`, `setCameraTarget`, `setActiveCamera`, and `setCameraDolly`,
while native has only legacy `changeCamera...` and `setCameraRotation`
handlers. The Dart `SceneView` also sends a root-level `cameras` list that the
native root deserializer ignores; native creates its ViewTarget camera from
`scene.camera`.

## Success criteria

- [x] This is the sole `In Progress` ticket; FLR-0120 is Waiting and no
  QEMU/build process is running before source work begins.
- [x] Effective Dart/native generated APIs and native deserializer are
  compared, and at least two remedy paths are recorded.
- [x] The selected Dart adapter is edited only in the persistent Mac Devtool
  source; no `tmp/work` file or generated patch body is edited.
- [x] Official Yocto Devtool generates the patch, which is copied unchanged
  into `meta-fluorite-trial` and passes the Mac recipe gate.
- [x] The canonical layer change is committed locally and delivered by one
  complete-history bundle to the fixed Mini receiver.
- [x] Mini `do_patch`, targeted compile, and full image pass using the existing
  build directory/TMPDIR without duplicate storage trees.
- [x] One fresh QEMU starts exactly one source-selected fixture. The camera
  channel errors disappear, the native camera path reaches `Camera 8 enabled`,
  and no coredump occurs.
- [ ] QMP-only evidence shows nonzero geometry in `[300,250,620,400]`; the
  run ends through negotiated QMP `quit` with zero residual targets/sockets.
  **Capture/teardown PASS; geometry FAIL:** both captures are `0/248000`
  changed and uniform black.

## Facts

- FLR-0120 evidence is under
  `$EVIDENCE_ROOT/flr0113-authoritative/flr0120-81caadc/qemu`.
- FLR-0120's post-0232 runtime reached shape readiness and Vulkan submit with
  no coredump, but `setCameraDolly` and `setCameraTarget` still returned
  `channel-error` and the central QMP region was `0/248000` uniform black.
- Native `SceneTextDeserializer::vDeserializeRootLevel` handles root
  `models`, `scene`, and `shapes`; `scene.camera` is deserialized into the
  native `ViewTarget` camera. It has no root `cameras` branch.
- Dart `ModelViewerState._setupCreationParams` currently creates
  `scene = widget.scene.toJson()`, sends it as `creationParams["scene"]`, and
  separately sends `creationParams["cameras"]`. Its
  `_onPlatformViewCreated` currently calls `camera.initialize`, which sends
  the unsupported new Pigeon methods.
- Existing project patches 0007 and 0008 describe the native v2 adapter:
  inject the selected camera as `scene.camera`, omit root cameras, and do not
  initialize the camera as an ECS entity after platform-view creation.
- Historical QMP evidence proves that a native fixture can render visible
  geometry, but current FLR-0120 does not prove that the present payload and
  current camera contract do so.
- Commit `36d976a7d488c14667e829d60ed18f21d299c334` contains the canonical
  layer patch. The unchanged Devtool patch and registered layer patch have
  SHA-256 `cd21aa363ab56a4175ffadc24608bea603d8cf849a4249761fb83a92e194d70d`.
- The Mac Devtool `do_patch` gate passed. The Mini authoritative receiver then
  passed app `do_patch` (104 tasks), targeted `do_compile` (2590 tasks), and
  full `agl-ivi-image-flutter` image build (11898 tasks) using the fixed build
  directory and TMPDIR.
- The fresh Mini QEMU run used the built Example Demo release and exactly one
  `flutter-auto` fixture process. `SHAPE_READY` reported `renderable=true`,
  Vulkan queue submit returned `result=0`, and no coredump was found. The
  QMP-only early and late captures were 1280x800; the central region remained
  uniform black with changed count `0/248000`, no edges, no chromatic pixels,
  and luma range `[0,0]`. The central-region SHA-256 was
  `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25` for
  both captures.
- QMP teardown negotiated `quit`, removed the QMP socket, and reported zero
  residual targets. The failed first build setup (wrong AGL role path) and the
  failed `set -u` setup (`BBSERVER` unset during OE initialization) are
  recorded in the working log; the corrected run used `set -eo pipefail` and
  passed.

## Inferences

- The selected fix is a Dart-side contract restoration, not a readiness delay:
  a delay cannot reach handlers that do not exist in the native generated API.
- Reusing the native deserializer's established `scene.camera` path is smaller
  and lower risk than adding three new native Pigeon methods and mapping them
  into camera-manager operations that do not currently exist.
- If camera errors disappear but QMP remains black, the first camera boundary
  will be cleared and the next ticket must isolate geometry/material or
  surface composition separately.
- This run clears the API-generation boundary but does not prove that the
  native rendered buffer reaches the visible QMP region. Because the native
  shape and queue-submit markers succeed while pixels remain unchanged, the
  next diagnostic priority is the frame-to-present/Wayland surface boundary.

## Hypotheses / UNKNOWN

1. **Selected:** restoring `scene.camera`, omitting root `cameras`, and
   removing post-create camera initialization eliminates the channel errors
   and applies the camera before the first native frame. **Result:** the
   channel-error messages disappeared and the native log reached
   `Camera 8 enabled`, but the central QMP region remained black.
2. **Alternative:** native Pigeon regeneration plus new camera-manager methods
   is required. Prediction: Dart calls work only after a broader native API
   implementation; this is deferred unless the selected adapter fails.
3. **Next leading boundary:** the render result or its native child surface is
   not reaching the QMP-visible region after successful shape setup and queue
   submit. This is not yet a confirmed root cause; FLR-0122 owns the bounded
   present/surface comparison.
4. **UNKNOWN:** whether the remaining failure is command/render output,
   Vulkan present/WSI, Wayland buffer attach/commit, compositor stacking, or
   the QMP region being behind another surface.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | Dart sends new camera channels that native does not expose | generated API comparison |
| Where | `SceneView` root payload and `_onPlatformViewCreated` | effective Dart source |
| When | initial platform-view creation before the first visible 3D frame | fixture log and QMP |
| Who | Dart package/native plugin integration roles | recipe and source provenance |
| How | root `cameras` is ignored; camera methods are unhandled | deserializer switch and runtime errors |

## PDCA

### Plan

1. Record the FLR-0120 falsification and preserve its QMP evidence.
2. Edit the persistent Mac Devtool app source to inject the selected camera
   into `scene.camera`, remove root `cameras`, and skip camera.initialize.
3. Generate the official patch, register it unchanged, run the Mac recipe
   gate, commit the canonical layer, and send one bundle to Mini.
4. Run progressive BitBake gates and one QMP fixture with camera-error,
   native-camera, coredump, and central-pixel checks.

### Do

- Ticket created after static comparison falsified the FLR-0120 order-only
  hypothesis.
- Edited the persistent Mac Devtool source and committed the source change as
  `63e116879125fafc252f32981b267e92d54eae68`. Official Devtool generated the
  adapter patch; the patch was copied unchanged into the canonical layer.
- Passed the Mac recipe gate, refreshed the authorized baseline lock, ran the
  repository verification suite, and committed the layer as
  `36d976a7d488c14667e829d60ed18f21d299c334`.
- Delivered one complete-history bundle to the fixed Mini receiver and passed
  Mini progressive and full-image BitBake gates.
- Ran one official QEMU fixture, captured QMP-only early/late PPM evidence,
  analyzed the central region, and stopped the run through negotiated QMP
  `quit` with zero residual targets and sockets.

### Check

- API mismatch diagnosis: **PASS**.
- Selected source patch and unchanged Devtool generation: **PASS**.
- Canonical commit, bundle handoff, Mini `do_patch`, targeted compile, and
  full-image build: **PASS**.
- Runtime camera boundary: **PASS as a bounded error-removal result**; no
  camera `channel-error`, shape readiness and queue submit succeeded, and no
  coredump was found.
- QMP geometry acceptance: **FAIL**; both captures remained uniform black in
  `[300,250,620,400]`.
- QMP capture and teardown: **PASS**.

### Act

- Do not add another camera-registration variant to this ticket. FLR-0122
  owns the next bounded present/surface diagnosis.
- Keep FLR-0120 evidence immutable and use a new evidence directory for this
  ticket.

## Evidence locations

- Prior FLR-0120 evidence: `$EVIDENCE_ROOT/flr0113-authoritative/flr0120-81caadc/qemu`
- This ticket's Mini evidence: `$EVIDENCE_ROOT/flr0121-*`
- Working log: `work/logs/2026-09-13-flr0121.md`
