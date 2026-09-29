# FLR-0125 — trace the Example Demo ViewTarget entry path

- Status: Done
- Priority: High
- Owner: Mac Devtool source + canonical layer + Mini runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0124](FLR-0124-restore-native-control-through-devtool.md)
- Working log: `work/logs/2026-09-13-flr0125.md`
- Plan: `docs/superpowers/plans/2026-09-13-flr0125-trace-viewtarget-entry-path.md`

## Work unit

Identify the first missing runtime boundary between the Flutter Example Demo
PlatformView registration and the native `ViewTarget` initialization. Restore
only that entry boundary if source evidence proves it is missing, then prove
the native-control setup marker is reached. This ticket does not claim 3D
pixels, production Sequoia rendering, or a Dart scene fix.

## Problem

FLR-0124 delivered a native-control implementation into the image and the
binary contains its marker strings. In the one valid `agl-driver` QEMU run,
scene deserialization reached `FLUORITE_NATIVE_PURE_FIXTURE`, but no
`ViewTargetCreateRequest`, `InitializeFilamentInternals`, `setupView`, or
`FLUORITE_NATIVE_MINIMAL_GEOMETRY_*` runtime marker appeared. The fixed QMP
3D region remained uniform black.

## Success measure

- Static call chain and runtime markers distinguish PlatformView registration,
  ECS message dispatch, ViewTarget creation, and ViewTarget initialization.
- One minimal Devtool-generated source patch is used only if the missing
  boundary is a source-controlled defect.
- Mac patch gate, canonical commit, bundle handoff, Mini compile/image, and one
  QMP-only control run are recorded.
- The control run observes the native geometry setup marker. Nonzero 3D pixels
  are a follow-up criterion, not silently inferred from setup.
- No second QEMU runs concurrently and no new build/TMPDIR/receiver is made.

## Facts

- FLR-0124 source and deployed binary contain `FLUORITE_NATIVE_MINIMAL_GEOMETRY`
  strings, while the runtime log contains none of its setup or failure markers.
- The same runtime log contains `FLUORITE_NATIVE_PURE_FIXTURE` and
  `FLUORITE_NATIVE_PURE_FIXTURE_SETUP_DONE`.
- The QEMU process count was one `agl-driver` flutter-auto, with no coredump.
- QMP early/late captures were uniform black in `[300,250,620,400]`.
- The canonical and Mini build gates for FLR-0124 passed.
- `RunOnceCheckAndInitializeECSystems()` posts system creation and
  `vInitSystems()` asynchronously on the ECS strand.
- `FilamentViewPlugin::RegisterWithRegistrar()` routes
  `ViewTargetCreateRequest` immediately after posting that initialization.
- The current `ECSManager::vRouteMessage()` only iterates the systems currently
  in `_systems`; it has no pending-message queue or replay path.
- `vInitSystems()` changes the run state to `Initialized` only after all system
  handlers have been registered, while the C API starts the main loop only when
  it observes that state. This is a second startup-order race.
- `DeserializeDataAndSetupMessageChannels()` waits for system objects but does
  not replay a ViewTarget request that was routed before system registration.
- The Devtool source change was committed as `efd2b7b33cc166db0ea2c1d283e12499eb9d40ca`
  on `devtool-flr0125-entry-fix`.
- Official Devtool `update-recipe --mode patch` generated
  `0236-fix-defer-viewtarget-request-until-ecs-init-devtool.patch`; its
  unchanged SHA-256 is
  `f99c8b053696b36da6df26121d663ab8521765b5b2e5fd5e4753713fce253c1c`.
- Mac fixed-container `flutter-auto:do_patch` passed: 104 tasks attempted,
  100 reused, all succeeded.
- The Mini authoritative `do_patch`, `do_compile`, and full image gates passed
  from canonical commit `f0406dae15cbf0572f0fd8b925026de41e06fc99`.
- The fixed QEMU run reached `FLUORITE_VIEWTARGET_CREATE_REQUEST_ROUTED`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_READY vertices=8 indices=36`, and the
  native present/commit sequence without a coredump.
- QMP early and late captures were 1280x800 and both showed the fixed region
  `[300,250,620,400]` with `111758` changed/chromatic pixels, bounding box
  `[467,250,346,323]`, and region SHA-256
  `aba96a8548fe822f3ba5c5b0acafd7aa86ca63c5e7eec9d9b4a46d2ddbf98c2d`.
  The full-frame SHA-256 values were
  `b470396f59ad726dd62f742b446cfe1c0b0cae23efc81fa62448ab9a235d90a4` and
  `6eb0d5f874dcfc41829588949a418cbd7039f106e1563c9ebc831cd8f2800704`.
- Eight QMP video frames were captured; repeated frame hashes show that the
  blue fixture remained visible across the sample window. The QEMU run ended
  through negotiated QMP `quit` with zero residual targets and sockets.

## Inferences

- The native geometry function was not entered in the accepted run; a black
  region alone cannot distinguish entry failure from present failure, but the
  absent setup marker narrows the current boundary before geometry creation.
- The most efficient next observation is the registration-to-ECS-to-ViewTarget
  call chain, not another QMP retry with unchanged binaries.
- The source call order provides a concrete loss mechanism: the first
  ViewTarget request can be routed while `_systems` is empty, so the request is
  discarded before `ViewTargetSystem::vOnInitSystem()` can receive it.
- The likely source-controlled correction is to make the request delivery
  occur after the strand has completed system initialization and to make ECS
  loop startup independent of the caller's state-race observation. Runtime
  markers are still required before claiming this is proven.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Test | Result |
| --- | --- | --- | --- |
| H1: PlatformView registration is not invoked by the Example Demo | no registration/request marker | add bounded entry markers or inspect callback route | REJECTED; native request marker observed |
| H2: registration runs but ECS creation request is lost before system registration | request is routed while `_systems` is empty; ViewTarget creation marker is absent | source order plus one runtime marker run | CONFIRMED; fixed by strand ordering |
| H3: ViewTarget initializes but native setup marker is suppressed | initialization marker exists, setup marker absent | compare exact source path and log level | REJECTED; setup marker observed after fix |
| H4: setup occurs in another process or before log capture | binary marker exists but process log misses it | process/user and startup window evidence | REJECTED for accepted run; one process and captured marker |

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | native setup marker is absent after pure fixture setup | bounded runtime log |
| Where | Flutter PlatformView callback, ECS queue, ViewTargetSystem, ViewTarget | source call chain and markers |
| When | after app start and before first native submit | monotonic log order |
| Who | Flutter plugin registration and ECS/ViewTarget runtime roles | process/thread/user |
| How | registration → message route → target creation → init → setup | source and runtime sequence |

## PDCA

### Plan

1. Read and record the current effective source call sites before editing.
2. Align the persistent Mac Devtool source with the current Mini-effective
   entry files, then use Devtool to make the smallest ordered-delivery fix and
   bounded info-level markers.
3. Generate the patch through official Devtool, register it in the canonical
   layer, run Mac `do_patch`, commit, bundle, and hand off to the fixed Mini.
4. Run Mini target gates, then one QMP-only run with the same native-control
   environment and classify request delivery, ViewTarget initialization, and
   the resulting pixels.

### Do

- Created as a separate work unit after FLR-0124 failed at native-control
  runtime entry.
- Read the Mini-effective `filament_view_plugin.cc`, `ecs.cc`, `ecs.h`,
  `ecsystem.cc`, and `view_target_system.cc` call sites.
- Confirmed the static sequence: asynchronous system creation → immediate
  `vRouteMessage(ViewTargetCreateRequest)` → no pending queue → later system
  initialization. The same ordering applies to the start-rendering message.
- Confirmed the deployed binary contains the native-control strings, so this
  is not a missing-patch or missing-binary explanation.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Static chain | registration-to-init path is mapped | async route-before-init loss mechanism identified | PASS |
| Runtime boundary | first missing marker is identified | request route, ECS init, and native setup markers observed in order | PASS |
| Source patch | only if evidence requires it | Devtool source commit and official patch generated | PASS |
| Mac patch gate | registered patch applies to existing recipe stack | 104 attempted, 100 reused, all succeeded | PASS |
| QMP control | setup marker observed | setup marker and nonzero fixed-region pixels observed | PASS |
| QMP pixel control | fixed region contains visible native geometry | 111758 changed/chromatic pixels in early/late captures | PASS |
| Teardown | negotiated QMP quit leaves no target/socket | zero residual targets/sockets | PASS |

### Act

- The source edit and official patch generation are complete. The canonical
  commit was handed off as a bundle, Mini gates passed, and one QMP-only
  runtime control reached visible native pixels.
- If H3/H4 is confirmed, split logging/process-capture correction from
  rendering diagnosis before changing geometry or present code.
- Native setup and visible fixture pixels are reached. Continue with a separate
  Dart Example Demo ticket; do not infer Dart or production-scene success from
  this native control.

## Evidence locations

- `$EVIDENCE_ROOT/flr0113-authoritative/flr0124-native-control/qemu`
- `$EVIDENCE_ROOT/flr0113-authoritative/flr0125-viewtarget-entry`
- Working log: `work/logs/2026-09-13-flr0125.md`

## PDCA checker

- Status: PASS
- Checked by: bounded Devtool → Mini → QMP control loop
- Findings: the source-order defect was fixed through the official Devtool
  patch path; native fixture setup, present, visible pixels, and clean QMP
  teardown all passed. Dart and production-scene behavior remain separate.
