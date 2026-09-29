# FLR-0191 — isolate native readiness and 3D draw boundary

- Status: Done
- Priority: High
- Owner: Mini QEMU runtime + native ViewTarget evidence role
- Created: 2026-09-15
- Predecessor: [FLR-0190](FLR-0190-align-material-color-wire-format.md)
- Working log: `work/logs/2026-09-15-flr0191.md`

## Work unit

Determine why the corrected Example Demo remains 3D-black while its 2D HUD is
visible and its Filament shapes are ready. Separate the native readiness
handshake from the later draw/present/composition path using one bounded QEMU
runtime session at a time.

## Problem

After retiring stale active patch 0052, `flutter-auto` no longer aborts during
`MaterialParameter` deserialization. The app remains alive, loads `lit.filamat`
and `unlitUV.filamat`, and emits `FLR0026_SHAPE_READY` for entities 17–37.
However, the runtime repeatedly reports `Native is not ready`, while the QMP
frame shows the 2D HUD in the upper region and a uniformly black fixed 3D
region.

## Success criteria

- [ ] Preserve the current corrected image, runtime log, QMP screenshot, and
  teardown evidence.
- [ ] Identify the exact readiness sender/receiver and the first negative
  condition using bounded logs and source/API inspection.
- [ ] Compare at least two explanations: readiness handshake gating versus
  draw/present/composition producing black pixels after readiness.
- [ ] Use existing diagnostics first; add a minimal Devtool patch only if the
  evidence identifies a concrete source-owned condition.
- [ ] If a patch is needed, generate it through the persistent Mac Devtool,
  commit the canonical layer locally, bundle once to Mini, and rerun the
  minimal build/runtime gate.
- [ ] Capture QMP-only screenshot evidence for every runtime conclusion and
  tear down all QEMU/app processes.
- [ ] Do not claim 3D success until the fixed 3D region contains non-black
  geometry pixels.

## Facts

- Corrected image receiver: `2ddab094cea058be5dfcb784063acb19fb1aab0d`.
- Corrected `.ext4` SHA-256:
  `d1f0f1d4726cee1bb5b1dc99e34ab845a01319a2d548bffef0625acfe2926b66`.
- Runtime log: `evidence/FLR-0191/qemu/runtime.log` on the Mini evidence
  receiver; SHA-256 `dc6477056ff565537a2a60a3c00a2f87968006a94f1c31a879e96c7bcff6d665`.
- The app process remained alive after startup and material loading.
- The log shows `FLR0026_SHAPE_READY` for entities 17–37 and repeated
  `Native is not ready` messages through the bounded observation window.
- QMP screenshot: `evidence/FLR-0191/qemu/frame-native-not-ready.ppm`;
  SHA-256 `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- Full-screen QMP analysis found 7,431 non-black HUD pixels. The fixed 3D
  candidate `[300,250,620,400]` was uniformly black: 248,000 pixels, zero
  edges, zero chroma, luma `[0,0]`.
- QEMU teardown passed with zero residual targets and no QMP socket.

## Inferences

- The MaterialParameter startup crash is fixed and is not the current 3D
  boundary.
- The 2D Flutter surface is presenting independently of the missing 3D
  candidate; this is not yet proof of a generic QMP or guest-display failure.
- Mini's effective source has `StartMainLoop()` commented in the C API, but
  restoring it is insufficient because its current loop body does not call
  `ECSManager::update()`.
- Active 0013 starts the QEMU software loop through `OnFrame(nullptr, ...)`.
  The base `OnFrame` path can store `framePromise` and then be re-entered by
  `setInitialized` while the same ECS queue is being drained.
- The persistent Mac Devtool source change is commit
  `f71683efadb0365886e607c8a9ff942e345fca3d`; its baseline imports the
  Mini-effective 0252-predecessor source as commit
  `6d290b322ec0e717b96bc3850ee905bf275cc01f`. Official `update-recipe`
  regenerated canonical patch 0252 with SHA-256
  `c96e5e9f88bb245e99b12dde46939112c2ef93382b301e045795a009885c5529`.
- The first Mini gate rejected the previous 0252 because Yocto detected patch
  fuzz (`hunk #1 succeeded at 49 with fuzz 2`); the task log was
  `/mnt/yocto/flr0023-tmp-835a04e-selfinstall/work/corei7-64-agl-linux/flutter-auto/2.0/temp/log.do_patch.3354470`.
- Rebase procedure: extract the `.pc/0252-.../view_target.cc` backup from the
  Mini quilt work directory, import only that effective file into the fixed
  Mac Devtool baseline branch, commit the baseline, apply the intended change,
  commit it, then run official `update-recipe`. No generated patch was edited.
- The bounded 0252 runtime recheck still showed `FLR0026_SHAPE_READY` for
  entities 17–37 and Vulkan begin/submit/end-frame markers, but zero
  `FLUORITE_VIEWTARGET_*` and zero `FLR0026_TARGET_DRAW*` markers. The Dart
  side reported `Native is not ready` through attempts 1–30. The QMP frame
  kept the HUD visible while the fixed 3D region `[300,250,620,400]` was
  uniformly black; frame SHA-256 was
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- Current source inspection found that `RegisterWithRegistrar()` queues the
  ViewTarget bootstrap messages and starts the rendering loops, but does not
  drain `ViewTargetSystem::ProcessMessages()` after registration. The existing
  `ecs->initialize()` wait is separate from this bootstrap queue.
- The persistent Mac Devtool source commit for the minimal drain is
  `9b4f1f717a13be074aa98e3cccd2a32271eab123`. Official `update-recipe`
  generated canonical patch 0253 at
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0253-fix-drain-initial-viewtarget-messages-devtool.patch`;
  its SHA-256 is
  `d5da045c1a9078daf1b4cd9f749e534034ec48a6387c8677e2c68626fa07b19b`.
- Mac Podman initially stopped BitBake because its fixed `/workspace/tmp`
  tmpfs had only about 0.9 GB free. After confirming no active BitBake or
  Devtool task, only the old `filament-vk` work directory (about 1.4 GB) was
  removed; source, downloads, sstate, evidence, and the `flutter-auto` work
  directory were retained. The same gate then advanced past the capacity
  check and failed at existing patch 0220 in the Mac-side unpacked source:
  `wayland_vulkan.cc` and `wayland/window.cc` hunks did not match. This is a
  separate Mac source-stack boundary, not evidence that 0253 is malformed.

## Hypotheses / alternatives

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: readiness handshake is gating native scene activation | The sender or receiver never observes the expected ready state; draw admission remains gated | readiness becomes positive while 3D remains black |
| H2: native scene is ready enough to draw, but draw/present produces black pixels | runtime markers show draw/present after shape readiness while readiness is only a stale Dart flag | no draw/present markers occur before the black frame |
| H3: 2D/3D composition hides a valid native surface | native readback or alternate QMP region contains geometry while the fixed composite region is black | native target/readback is also zero |
| H4: QEMU software-frame promise deadlocks before `DrawFrame` | separating `callback == nullptr` from the Wayland promise path lets frame markers and non-black pixels appear | frame markers remain absent after 0252 |
| H5: ViewTarget bootstrap messages remain queued after registration | one strand-safe initial `ProcessMessages()` drain produces ViewTarget/DrawFrame markers and then native pixels | active C API already has the drain and 0253 runtime still has zero ViewTarget markers |

## 4W1H (Why excluded)

| Dimension | Record |
| --- | --- |
| What | Separate readiness gating from 3D pixel generation/composition |
| Where | Flutter scene readiness bridge, native ViewTarget/Filament frame path, QMP |
| When | After FLR-0190 removed the pre-frame material abort |
| Who | Mini runtime/evidence role and Mac Devtool source role if a patch is required |
| How | bounded log slice → source/API trace → one hypothesis test → QMP screenshot → teardown |

## PDCA

### Plan

1. Read only the persisted FLR-0191 runtime log and QMP analysis first.
2. Locate the readiness sender/receiver and existing diagnostics; avoid broad
   journal/system-log collection until the first owner is known.
3. Select the smallest discriminator, then run one QEMU session and capture
   QMP plus the bounded runtime slice.

### Do

- Opened after FLR-0190 corrected the material contract and the first valid
  runtime showed 2D HUD plus a black 3D candidate.
- Read the bounded Mini markers and current Mac/Mini source boundaries before
  editing. Generated 0252 through the persistent Devtool source commit and
  official finish path; the generated patch body was not edited.
- Rechecked the 0252 runtime with QMP-only capture and bounded log filters.
  Then made the smallest source-owned H5 change through the persistent Mac
  Devtool, committed the source change, and regenerated 0253 with official
  `update-recipe`. The generated patch was copied byte-for-byte into the
  canonical layer; its body was not edited.
- Recovered the Mac Podman temporary capacity using a process guard and a
  targeted removal of the stale `filament-vk` work directory. A second
  `flutter-auto:do_patch` run reached the pre-existing 0220 mismatch, proving
  the capacity stop was cleared but leaving the Mac stack gate separate from
  the Mini authority gate.

### Check

- 0252 runtime: 2D HUD PASS, shape readiness PASS, Vulkan submit/end-frame
  PASS, ViewTarget/DrawFrame markers FAIL, fixed 3D pixels FAIL.
- 0253 Devtool source commit and official patch generation: PASS.
- Mac capacity recovery: PASS. Mac recipe gate: FAIL at existing 0220 source
  context after capacity recovery; this does not validate or reject 0253.
- Mini 0253 `do_patch`, `do_compile`, and full image: PASS. QMP 3D pixels:
  FAIL; HUD pixels: PASS. QEMU teardown: PASS.

### Act

- Keep FLR-0190 closed and do not reintroduce a material patch. Split any
  concrete source fix into its own ticket after the owner is identified.
- Commit and transfer the canonical 0254 diagnostic layer and this evidence as
  one bundle update. Run Mini `do_patch` first, then compile/image/QEMU only
  after that gate passes. If Mini rejects 0220, open a separate
  patch-provenance ticket and do not alter 0253 while diagnosing it.

## UNKNOWN

- The exact readiness condition and its sender/receiver are UNKNOWN.
- Whether native draw/present markers occur after shape readiness is now
  narrowed: Vulkan submit/end-frame occurs, but ViewTarget/DrawFrame markers
  are absent in the bounded 0252 slice.
- Whether a valid native surface is later hidden by composition is UNKNOWN.
- 0253 did not remove the missing ViewTarget/DrawFrame markers or produce
  visible 3D pixels in the bounded Mini QEMU run.
- Whether the canonical 0253 plus the active historical stack passes the
  authoritative Mini `do_patch` gate is UNKNOWN until the bundle is
  transferred.

## 2026-09-15 0253 Mini runtime result and 0254 diagnostic boundary

### Facts

- Bundle handoff of canonical commit `32c76bd6ab12a431c765a03451fb23fac296e8be`
  passed. The fixed Mini receiver, build, and TMPDIR were reused.
- Mini `flutter-auto:do_patch`, `flutter-auto:do_compile`, and
  `agl-ivi-image-flutter` all passed. The generated rootfs was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260915101400.ext4`, SHA-256
  `98be988892d98f73826a42a379a02a8b39fa289896b9eb156af8019b133b56a2`.
- One new QEMU session ran the fixture. Shape-ready and Vulkan submit/end-frame
  markers appeared, but ViewTarget/DrawFrame markers did not. QMP-only frame
  SHA-256 stayed `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`:
  HUD region present, fixed 3D region uniformly black. QEMU teardown passed
  with zero residual targets.
- The active C API already posts `ViewTargetSystem::ProcessMessages()` after
  registration. The 0253 plugin-side drain did not change the runtime result;
  the only observed ViewTarget-related warning was the existing C API
  off-thread `getSystem` warning.
- The next source change is diagnostic-only 0254. Devtool source commit:
  `83599021b1db090ede5e827abfcefd3d6251c35a`. Official finish generated
  patch SHA-256:
  `ea769c44020435f52bcdeabde6e3d0929452f7c143818eeef437c1e19850d7ac`.

### Inference

- H5, stated as “no bootstrap drain exists anywhere in the active path”, is
  falsified by source inspection. The first unresolved boundary is now whether
  the C API drain runs its ViewTarget handlers, not whether any drain exists.
- The 3D failure remains before `ViewTarget::DrawFrame()` or at the platform
  registration path; composition cannot yet be blamed because no native draw
  marker exists.

### Check

- 0253 patch/compile/image: PASS.
- 0253 QMP 3D pixels: FAIL; 2D HUD: PASS.
- 0253 QEMU teardown: PASS.
- 0254 Devtool source commit and official patch generation: PASS.
- 0254 Mini patch/compile/image/QMP: UNKNOWN.

### Act

- Commit and transfer 0254 as one bundle update. Run Mini `do_patch` first,
  then compile/image/QEMU only after that gate passes. Read only the new
  boundary markers to select the next owner.

## 2026-09-15 0254 diagnostic result and 0255 handler boundary

### Facts

- Mini 0254 `do_patch`, `flutter-auto:do_compile`, and full image all passed.
  The diagnostic rootfs was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260915104004.ext4`, SHA-256
  `c344f76ba2e9007b191cbc4329fa1be08c4ecd4c0486932895bedddfbb57057a`.
- QEMU 0254 emitted `FLUORITE_VIEWTARGET_CAPI_REGISTER_ENTER`, then
  `...REGISTER_RETURN state=1`, `...CAPI_DRAIN_BEGIN`, and
  `...CAPI_DRAIN_END`. It still emitted no ViewTarget/DrawFrame marker, and
  the fixed QMP 3D region remained uniformly black while the HUD was visible.
- The next source boundary was narrowed to `ViewTargetSystem::onSystemInit`,
  the create/start handlers, and `KickOffFrameRenderingLoops()`.
- The first 0255 `update-recipe` attempt correctly failed closed because the
  official 0254 finish had removed the split component recipe from the active
  Devtool workspace. Recovery used the documented order: checkout baseline
  `6d290b3`, run `component-add fluorite-plugins`, checkout source commit
  `89bfac7`, then run `update-recipe`. No patch body was edited.
- Official finish generated 0255 from Devtool source commit
  `89bfac7902c13960b32bdde802f4a4901d72dee4`; canonical patch SHA-256:
  `fd57a7db60228dd4db1037f671d416dcfeac1ca0609953146d6a59c00f66bd13`.

### Inference

- The C API registration and its existing drain are proven to execute. The
  remaining unknown is whether the ViewTargetSystem handlers are registered
  and invoked by that drain.
- The 3D failure is still upstream of `ViewTarget::DrawFrame()`; there is no
  evidence for a composition-only failure yet.

### Check

- 0254 C API registration/drain markers: PASS.
- 0254 ViewTarget/DrawFrame markers: FAIL.
- 0254 QMP 3D pixels: FAIL; HUD pixels: PASS.
- 0254 QEMU teardown: PASS.
- 0255 Devtool re-registration, source commit, and official patch generation:
  PASS.
- 0255 Mini patch/compile/image/QMP: UNKNOWN.

### Act

- Commit and transfer 0255 as one bundle update. Run the Mini patch gate,
  compile, image, and one QEMU marker/QMP loop. Use handler marker presence to
  choose the next source owner; do not add another broad trace patch before
  this result.

## 2026-09-15 0255 handler result and 0256 registration boundary

### Facts

- Mini 0255 `do_patch`, `flutter-auto:do_compile`, and full image all passed.
  The rootfs was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260915112723.ext4`, SHA-256
  `3ea41e40c3a1b6b6ce390ed587f912807d575f6fd1fc8ff87a6caae8bf959ba3`.
- QEMU 0255 reached `FLUORITE_VIEWTARGET_SYSTEM_INIT_BEGIN` and
  `...SYSTEM_INIT_END`. The start handler ran with `count=0`, and
  `FLUORITE_VIEWTARGET_KICKOFF_FRAME_LOOPS` also reported `count=0`.
  No create handler marker appeared. This proves the frame loop is starting
  with no ViewTarget object, before `DrawFrame` or Wayland composition.
- The next diagnostic source change traces plugin registration entry,
  `_hasLoadedOnce` early return, and create/start message enqueue points.
- After 0255 official finish, the split component was again absent from the
  active Devtool workspace. The documented baseline checkout → component-add
  → source checkout sequence was used again before `update-recipe`.
- Official finish generated 0256 from source commit
  `d841f9b9edea69992fa2e72f3290919198eb83ac`; canonical patch SHA-256:
  `a159fd0d5cbd380b970f0b3d7862d45abe24d6dcb91389abec4b3d41f73fa6ac`.

### Inference

- The immediate cause is now narrowed to the ViewTarget creation request path:
  the system exists and processes the start message, but its ViewTarget list is
  empty. The remaining alternatives are plugin registration early return or
  create-message enqueue/routing loss.
- This is not currently a light/camera/composition problem; no ViewTarget
  exists to own those operations.

### Check

- 0255 handler initialization: PASS.
- 0255 start handler: PASS with `count=0`.
- 0255 create handler: FAIL/not observed.
- 0255 QMP 3D pixels: not yet captured for this marker boundary; prior fixed
  region remains black until a ViewTarget is created.
- 0255 QEMU teardown: PASS.
- 0256 Devtool source commit and official patch generation: PASS.
- 0256 Mini patch/compile/image/QMP: UNKNOWN.

### Act

- Commit and transfer 0256, run the progressive Mini gates, then use one
  QEMU fixture run to compare registration entry/early-return/create-enqueue
  markers with the handler count. Select the smallest source-owned fix from
  that result.

## 2026-09-15 0256 deterministic rebase and patch gate

### Facts

- The earlier "capacity" message was two different conditions: the execution
  service reported model capacity, while Mac Podman `/workspace/tmp` had real
  temporary-space pressure. The latter was reduced by removing only the stale
  `filament-vk` work product; source, downloads, sstate, evidence, and the
  fixed container were retained. Mini `/mnt/yocto` remained within its safe
  capacity margin. Neither condition was a Yocto patch-application failure.
- The previous 0256 patch applied with offset/fuzz because the Mac Devtool
  source was not the same effective source as the Mini receiver. The Mini
  `filament_view_plugin.cc` had a different initialization and registration
  ordering. This was a source-baseline error, not a patch-body error.
- The Mini effective pre-0256 file was imported as the comparison authority.
  Devtool source commit `adbebb3855995fd0cf6d4237061a0d3d1bfa62d4` records
  that baseline alignment, and `fdca97aded748bd60f20711ef82ae8a198111ea6`
  records only the eight intended registration markers.
- Official Devtool `update-recipe` regenerated 0256 from those commits. The
  canonical patch is byte-identical to the generated patch and has SHA-256
  `de4e162eda5e45c2388d1be098767dc62f753aafd46c6aac545d65318131939b`.
- Canonical repo commit `b85068fe2b09b29e68042e363d7370d1e1dc11c7` contains
  the regenerated patch and refreshed baseline lock. The bundle was transferred
  to the fixed Mini receiver with SHA-256
  `c570695c9ab1db00e64463333d9340343c213d9ccceced2806611ebc78825084`.

### Inference

- The deterministic Devtool path is now: align against the Mini effective
  source, commit the baseline, commit the intended source change, re-register
  the component, run `update-recipe`, and copy only the generated patch.
- The earlier fuzz was caused by using a source commit whose parent was not the
  receiver's effective source. Repeating `update-recipe` without that baseline
  alignment would reproduce the failure.

### Check

- Canonical repository check: PASS.
- Generated/canonical patch comparison: PASS.
- Bundle transfer, remote hash, and fixed receiver exact tip: PASS.
- Mini `flutter-auto` do_patch: PASS; no fuzz QA failure.
- Compile, image, and QEMU runtime for the regenerated patch: UNKNOWN.

### Act

- Continue with the existing progressive gate: compile, image, then one QEMU
  registration-marker/QMP run. Do not start another patch until the first
  missing marker boundary is identified.

## 2026-09-15 0256 runtime result

### Facts

- Mini `flutter-auto:do_compile`: PASS. Evidence is recorded under
  `$RECEIVER/evidence/FLR-0191/compile-flutter-auto.output`; task log was
  `log.do_compile.3490022`.
- Full `agl-ivi-image-flutter`: PASS. Rootfs SHA-256 is
  `3fe299d3476da96b6e7561fcef93a90042a2842bfc66fb3e40ffe1ed8e1832e` and
  kernel SHA-256 is
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- The first QEMU capture was pre-launch black: the image starts `applaunchd`
  but does not auto-start the Example Demo. The stale 3.32.5 bundle path was
  also corrected to the installed 3.38.3 release path. These are launch
  contract findings, not 3D rendering findings.
- After explicit `agl-driver` launch, runtime markers showed
  `REGISTER_ENTER loaded=false state=0`, `CREATE_ENQUEUED`,
  `START_ENQUEUED`, ViewTargetSystem init begin/end, shape-ready entities,
  `START_HANDLER_BEGIN count=0`, kickoff count `0`, C API register return, and
  C API drain begin/end. Vulkan submit/end-frame markers were present.
- QMP-only frame `frame-fixture-0256-after-launch.ppm` is 1280x800 with SHA-256
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
  HUD region `[200,100,400,250]` had 116 changed pixels; fixed 3D region
  `[300,250,620,400]` had 0/248000 changed pixels and was uniformly black.
- QMP quit, guest `flutter-auto` termination, QEMU teardown, and residual
  target/socket checks all passed with zero residual targets.

### Inference

- The 2D surface and Vulkan frame submission are alive. The 3D failure is
  upstream of light, camera, model shading, and surface composition.
- Registration enqueues the ViewTarget create message, but the first observed
  start handler runs with an empty ViewTarget list and the create handler is
  absent. This is a message initialization/order or queue ownership problem,
  not a black-light or camera-color problem.
- The next source boundary is the ordering of `RouteMessage`, system
  initialization/handler registration, automatic frame-loop processing, and the
  explicit C API drain.

### Check

- do_patch, do_compile, full image: PASS.
- Explicit Example Demo launch: PASS after using the installed 3.38.3 bundle.
- 2D QMP pixels: PASS.
- 3D QMP pixels: FAIL; uniformly black.
- Registration/create/start marker correlation: PASS; first missing boundary
  is the ViewTarget create handler.
- QEMU teardown and evidence capture: PASS.

### Act

- Create a follow-up ticket for ViewTarget message ordering. First inspect
  `RouteMessage`, handler registration, and `ProcessMessages` ownership on the
  Mini effective source. Compare the pre-init queue-loss hypothesis with the
  cross-thread/queue-routing hypothesis before making the smallest Devtool
  source change.
