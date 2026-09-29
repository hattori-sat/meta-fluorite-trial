# FLR-0119 — fix ECS platform-channel initialization race

- Status: Waiting
- Priority: High
- Owner: Mac persistent Devtool native source + Mini authoritative runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0118](FLR-0118-devtool-fixture-3d-pixel-control.md), [FLR-0116](FLR-0116-flutter-auto-material-variant-crash.md)
- Working log: `work/logs/2026-09-13-flr0119.md`

## Work unit

Repair the native ECS initialization boundary exposed by the valid source-level
self-made 3D fixture. The current code posts system construction to the ECS
strand and immediately dereferences systems from the Flutter platform-view
message path. This ticket owns the smallest safe native synchronization or
deferred-registration repair; it does not yet claim that the production
shaded scene is fixed.

## Problem

FLR-0118 built and launched the source-selected fixture on the repaired image,
but the process crashed before present. Symbol-file GDB resolved
`ECSystem::vSetupMessageChannels(this=0x0)` at `ecsystem.cc:146` while handling
the `flutter/platform_views` create message. The effective source posts
`RunOnceCheckAndInitializeECSystems()` work asynchronously, while
`DeserializeDataAndSetupMessageChannels()` immediately calls `getSystem()` and
uses the returned pointers. The fixture reaches this race deterministically
enough to reproduce it; a production launch surviving does not prove the
ordering is safe.

## Success criteria

- [x] One ticket was the sole `In Progress` item; no QEMU or build process is
  left running before source work began.
- [x] Effective native source and history confirm the exact async-post versus
  immediate-lookup ordering and identify every dereference that can be null.
- [x] At least two safe remedies are compared: restoring a blocking wait with
  deadlock analysis, and deferring channel setup until initialization completes
  or guarding/retrying the lookup. The chosen remedy has explicit runtime and
  integration rationale.
- [x] The native source change is made in the persistent Mac Devtool-managed
  source; the generated patch comes from the official Yocto Devtool
  `update-recipe --mode patch --append --no-remove` boundary for the split
  component and is not hand-edited.
- [x] The unchanged generated patch is registered under `meta-fluorite-trial`,
  passes the Mac recipe gate, and is committed locally.
- [x] One complete-history bundle reaches the fixed Mini receiver; targeted
  patch/compile and full-image gates pass using the existing build/TMPDIR.
- [ ] One fresh QEMU run launches exactly one source-selected fixture and
  reaches the fixture's camera/frame/present path without a coredump; QMP-only
  capture shows nonzero pixels in `[300,250,620,400]`.
- [x] QMP teardown is negotiated and residual QEMU/runqemu/flutter-auto
  processes and QMP sockets are zero.

## Facts

- FLR-0118's current fixture image is layer commit `f10ba7344925d3989980f9fef0446bb60b802be9`.
- The Mini runtime has `gdb`, `coredumpctl`, and target debug symbols. The
  corrected FLR-0118 launch core is retained in the external evidence role.
- The effective `filament_view_plugin.cc` calls
  `RunOnceCheckAndInitializeECSystems()`, then
  `DeserializeDataAndSetupMessageChannels()` without an intervening wait.
- `RunOnceCheckAndInitializeECSystems()` posts `vAddSystem()` and
  `vInitSystems()` to the ECS strand. The following lookup can return null
  until that posted task runs.
- `DeserializeDataAndSetupMessageChannels()` dereferences the animation,
  view-target, and collision system results to register event channels.
- The crash is pre-present and does not establish a Vulkan, Wayland-alpha, or
  light/material rendering failure.
- The persistent Mac Devtool source baseline is `b12886d`; the bounded ECS
  lookup change is source commit `c3087dfef4469d58ac71d3759e02468122cb5268`.
- The official Devtool-generated patch is
  `0231-fix-wait-for-ecs-systems-before-channel-setup-devtool.patch` with
  SHA-256
  `4d1b290ce4510a9aa9650f16f3250dfec2f8cdb20c363282751ebe0d5e7852b8`.
  The copy under `recipes-graphics/toyota/files` is byte-identical to the
  generated append output.
- The canonical `flutter-auto_2.0.bbappend` registers the patch with
  `patchdir=ivi-homescreen-plugins`, after the existing generic plugin
  patches.
- The Mini authoritative receiver reached
  `bbdcd607a510ee4d07381ce09fdb679baa063274`. Its existing qemux86-64 build
  produced rootfs `agl-ivi-image-flutter-qemux86-64.rootfs-20260912192139.ext4`
  and the progressive gates passed: `do_patch` 104/104, `do_compile` 2686/2686,
  and full image 11898/11898.
- The rootfs SHA-256 is
  `a4a42054093a2abcefc66c379aa80f6e132cc5eb29e12a45feb258821d8a6532`; the
  kernel SHA-256 is
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`; the
  qemuboot SHA-256 is
  `81d54fc371d572cfbaa0202b69adec37c99677cc29802a587838656e1be6f254`.
- FLR-0119 QEMU evidence is
  `$EVIDENCE_ROOT/flr0113-authoritative/flr0119-bbdcd60/qemu`. One QEMU was
  started on ports 42211/42212/42213, and fixture PID 635 remained alive
  after 20 seconds with no coredump.
- The fixture log reached `All systems initialized`,
  `FLR0026_SHAPE_READY guid=4 entity=5 renderable=true`, native readiness,
  event-channel creation, and successful Vulkan submit. The initial
  `setCameraDolly` and `setCameraTarget` calls returned Pigeon
  `channel-error` before the native API registration completed.
- QMP late frame SHA-256 is
  `f8328a0e292f11342c6b8b741b77e15a640473de2ae6a0ddfffebea538f483f8`.
  The full frame contains 2D HUD/button pixels, but the HUD-excluded region
  `[300,250,620,400]` is uniform black: `changed_pixels=0`, `edge_pixels=0`,
  `chromatic_pixels=0`, luma `[0,0]`. Full-frame analysis is
  `geometry_indicator=present` because of the 2D UI, not the 3D region.
- QMP quit negotiation passed with `residual_targets=0 residual_qmp=0`.

## Inferences

- The strongest current cause is an initialization-order race exposed by the
  fixture's platform-view creation timing.
- A simple `nullptr` guard could avoid the crash but would silently omit the
  event channels and may leave the renderer without required setup; it is not
  sufficient without an explicit retry/deferred path.
- A synchronous wait might restore ordering but can recreate the deadlock that
  motivated earlier non-blocking patches, so it requires a concrete strand
  ownership analysis and bounded test.
- A deferred registration callback would preserve asynchronous progress, but
  the available registrar/messenger ownership seam is not yet proven safe from
  the ECS strand. A bounded retry at the existing Flutter-thread lookup is the
  smallest falsifiable change: it avoids an unbounded block and returns with a
  diagnostic if initialization never completes.
- The bounded retry is effective for the original null-system boundary, but it
  does not reorder `FilamentViewApi::SetUp`. The current native order calls
  `DeserializeDataAndSetupMessageChannels` before constructing the plugin and
  calling `SetUp`, so Dart camera property messages can still arrive before
  their Pigeon method handlers exist.

## Hypotheses / UNKNOWN

1. **Async ECS initialization is the direct cause.** Falsifier: a trace shows
   all required systems initialized before the lookup and the null receiver
   persists.
2. **The fixture only changes timing while production is accidentally safe.**
   Falsifier: a repaired initialization path changes the fixture but exposes a
   separate production crash; that would keep this race as real but secondary.
3. **Deferred channel setup can preserve the no-blocking design.** Falsifier:
   the registrar/messenger cannot safely be used from the ECS strand and a
   Flutter-thread callback seam is required.
4. **UNKNOWN:** which of the three channel lookups is the null receiver in the
   captured optimized frame; the bounded retry resolves the crash, but the
   camera API registration order remains a separate boundary.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | platform-channel registration dereferences a null ECSystem | GDB receiver, source call order |
| Where | `filament_view_plugin.cc` → `ecsystem.cc:146` | effective source and symbols |
| When | first platform-view create, before frame/present | coredump and launch chronology |
| Who | native plugin initialization and Flutter platform-view roles | source ownership and runtime log |
| How | async strand post races immediate `getSystem()` | thread/state trace and controlled fix |

## PDCA

### Plan

1. Preserve FLR-0118's core/QMP failure as the baseline and ensure no current
   QEMU remains.
2. Inspect current native source, patch history, and registrar/thread
   ownership. Compare a wait-based remedy with deferred/guarded setup.
3. Edit the persistent Mac Devtool native source, generate the official patch,
   register it unchanged, and run Mac gates.
4. Commit and bundle once; run progressive Mini gates, one fixture QEMU, QMP
   pixel analysis, and negotiated cleanup.

### Do

- Ticket created after FLR-0118 identified the null-system pre-present crash.
- Static source/history comparison confirmed the async-post versus immediate
  lookup ordering and the three system results used for channel setup.
- The first attempt to generate a patch through `finish flutter-auto` was
  rejected as the wrong recipe boundary: it did not materialize a patch for
  the split `fluorite-plugins` source.
- An explicit-initial-revision, force-free `update-recipe` on the existing
  `fluorite-plugins` append was also a no-op because this Devtool version skips
  the root `initial_rev` in its patchset calculation. This is recorded as a
  tool limitation, not treated as a successful patch generation.
- Created one temporary official Devtool component recipe from the baseline,
  switched the same persistent source to the bounded-retry fix, and ran
  force-free `update-recipe` on that component. It generated the unchanged
  patch recorded in Facts; no generated patch body was hand-edited.

### Check

- FLR-0118 evidence preservation: **PASS**.
- Remedy comparison and selection: **PASS**; bounded retry was selected over
  an unbounded synchronous wait and an unproven cross-thread deferred callback.
- Official Devtool patch generation and byte-identity copy: **PASS**.
- Canonical recipe registration and Mac recipe gate: **PASS**; forced
  `flutter-auto:do_patch` attempted 104 tasks and all succeeded.
- Canonical `make verify`: **PASS** after the authorized baseline-lock refresh
  to 295 layer files.
- Mini bundle, progressive build, and fixture runtime: **PASS through submit**;
  the fixture remained alive and no coredump was found.
- Fixture QMP 3D pixel criterion: **FAIL**; central region remained uniform
  black after the first camera API calls failed with `channel-error`.
- QMP teardown and residual process check: **PASS**.

### Act

- Split the camera Pigeon registration-order boundary into FLR-0120. Keep
  FLR-0119 Waiting; it is not evidence that production light/material behavior
  is fixed.

## Iteration 2 — bounded retry runtime and camera channel boundary (2026-09-13)

### Facts

- The FLR-0119 image was built from the exact receiver tip and launched in one
  fresh QEMU. The fixture process stayed alive, and `coredumpctl` reported no
  coredumps.
- The source-selected blue-cube fixture reached `All systems initialized`,
  `SHAPE_READY`, native readiness, event-channel creation, and successful
  Vulkan submit.
- Two initial Dart Pigeon calls failed before native API registration:
  `FilamentViewApi.setCameraDolly` and `FilamentViewApi.setCameraTarget`.
  The same log later shows `Native is ready`, `Creating Event Channels`, and
  `Event Channels created`.
- QMP-only screenshot inspection shows the 2D HUD and buttons, with the
  central 3D candidate uniform black. Full-frame nonzero pixels therefore do
  not establish fixture geometry.

### Inferences

- FLR-0119's bounded retry repaired the native ECS null dereference: the prior
  pre-present SIGSEGV no longer occurred under the same fixture launch.
- The next actionable boundary is the native registration order. In
  `RegisterWithRegistrar`, `DeserializeDataAndSetupMessageChannels` runs before
  `FilamentViewPlugin` is constructed and `FilamentViewApi::SetUp` is called.
  This explains why camera initialization messages can be rejected while
  system/shape work continues.

### Hypotheses / UNKNOWN

1. Moving `FilamentViewApi::SetUp` before scene deserialization will allow the
   initial dolly/target messages to reach native and make the fixture camera
   visible. Falsifier: calls succeed but the same QMP region stays black.
2. If native reorder is unsafe because plugin construction requires the current
   order, a Dart-side readiness gate that delays camera property sends until
   `onCreated`/native-ready may be safer. Falsifier: the API has no reliable
   readiness callback or delayed calls still lose their initial state.
3. **UNKNOWN:** whether the black central region after camera recovery will
   expose a separate surface-alpha/compositor stacking issue.

### Do

- Captured QMP current, late, and five-frame evidence; both current and late
  central regions were uniform black. A converted copy of the late QMP frame
  was visually inspected and showed only the 2D layer.
- Read the actual post-patch Mini Dart source and native source. The fixture
  camera has orbit distance 5, dolly offset `(5,0,0)`, orbit angle
  `1.5707963267948966`, and target `(0,0,0)`, but the native Pigeon API calls
  for dolly and target failed before `SetUp`.
- Negotiated QMP `quit` and confirmed zero residual target processes and QMP
  sockets.

### Check

- FLR-0119 bounded ECS retry: **PASS** for the original crash boundary.
- Fixture shape/Vulkan submit: **PASS**.
- Camera initial-state delivery: **FAIL** due two Pigeon `channel-error` results.
- Fixture central QMP geometry: **FAIL** (`0/248000` changed pixels; no edges
  or chromatic pixels).
- Production scene/light conclusion: **UNKNOWN / not in scope**.

### Act

- Set FLR-0119 to Waiting and create
  [FLR-0120](FLR-0120-register-filament-camera-api-before-fixture-init.md) for
  the native-vs-Dart camera API registration-order decision. Do not change the
  production-light ticket until a valid fixture camera/frame reaches QMP.
