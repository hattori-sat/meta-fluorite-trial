# FLR-0285 — trace the production draw-command boundary

- Status: Waiting
- Priority: High
- Owner: production render queue and target draw boundary
- Depends on: [FLR-0284](FLR-0284-restore-production-direct-lights-ab.md)
- Working log: `work/logs/2026-09-24-flr0285.md`

## Problem

The production model is attached with valid renderables and materials, and
Vulkan present succeeds, but QMP remains black under both indirect-only and
direct-light conditions. The direct-light run reports one scene-pass command,
whereas the primary attachment run reports 36 commands.

## Hypotheses

1. The draw-command count is the real visibility boundary: the production
   renderables are not submitted to the visible target in the late frame.
2. The command count is a diagnostic timing difference; the model is submitted
   but camera/target composition still hides it.
3. The 36-command path contains stale or fixture commands and the 1-command
   path is the correct production path; QMP black is a later surface import
   issue.

## Scope and success criteria

- Reuse the existing image and one 4096 MiB baseline QEMU; a single 6144 MiB
  memory A/B is allowed only to falsify guest-memory pressure.
- Do not change source before collecting bounded command, renderable, camera,
  and present evidence.
- Identify the first difference between model attachment, Filament render
  queue, scene pass execution, and QMP pixels.
- Preserve exact QMP hashes and clean teardown; open a source patch ticket only
  after the missing boundary is identified.

## Current discriminator

Static inspection narrowed the next bounded A/B to camera framing. The normal
camera is reapplied every frame from the ECS camera at `(5,0,-5)` looking at
the origin, while the primary Sequoia renderable bounds extend mainly toward
negative Z. A diagnostic wide camera will be applied only when
`FLR0285_NATIVE_PRODUCTION_CAMERA=wide` is present; no memory or surface
condition will change. The next discriminator is now the common `beginFrame`
loop, because the no-model control fails at the same boundary.

## Runtime evidence — 0006 beginFrame control and composition A/B

- The same 4096 MiB QEMU was reused for all bounded cases and was cleanly
  stopped. The Mini host showed no residual `qemu-system`, `runqemu`, or
  `flutter-auto` process, and the QMP socket was removed.
- The production historical model case reached `beginFrame=true` only three
  times and then reported `beginFrame=false` repeatedly after the asynchronous
  model was attached. This made the late model-add timing a strong hypothesis,
  but it was not sufficient to claim a root cause.
- The no-model control set `FLR0026_NATIVE_MODEL_LIMIT=0` and otherwise used
  the same runtime. It also reported `begin_true=3`, `begin_false=2715`,
  `scene_add=0`, and `queue_present=3`. Its QMP capture was uniformly black
  with SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- Therefore the persistent `beginFrame=false` state is not caused by model
  loading, model attachment, or model memory pressure. It is a common
  production frame-loop/surface state failure. Increasing QEMU RAM is not
  justified by this evidence.
- The earlier `FLUORITE_NATIVE_WAYLAND_PLACE_BELOW=1` case showed the 2D HUD
  and Scenes control but no vehicle pixels. This confirms that the parent 2D
  surface is opaque over the below-placed native surface; changing placement
  alone cannot solve production visibility.

### Updated hypotheses

| ID | Prediction | Status |
| --- | --- | --- |
| H1 | The late production model is absent from the render queue | Rejected as sole cause: no-model control has the same frame failure |
| H2 | Render queue is valid and camera/target hides the model | Open, but blocked by common `beginFrame=false` state |
| H3 | QMP omits a valid target draw | Open for production; fixture disproves a generic QMP omission |
| H4 | Production frame scheduling/surface state stops successful frames after startup | Strongest current hypothesis; common no-model control supports it |

## Runtime evidence — 0006 frame-event control

- A second no-model control set `FLR0026_SKIP_FRAME_EVENT=1`, removing the
  pre-render event wait while retaining the same 4096 MiB QEMU and production
  binary.
- The bounded summary reported `begin_true=3`, `begin_false=47602`,
  `scene_add=0`, `queue_present=3`, and `frame_event_skipped=47604`.
- Disabling the frame event did not restore successful `beginFrame` calls.
  The event wait is therefore not the primary cause of the common frame-loop
  failure.
- One attempted start used a mistyped rootfs SHA. The fixed harness rejected
  it before starting QEMU; the corrected invocation passed preflight, guest
  readiness, the control run, and clean QMP teardown. This operator error is
  retained as evidence that the preflight gate is working.

## Source diagnostic — beginFrame failure state

- A no-model control with the fixture's surface conditions
  (`FLUORITE_NATIVE_FORCE_OPAQUE=1`,
  `FLUORITE_NATIVE_OPAQUE_SWAPCHAIN=1`, and
  `FLUORITE_NATIVE_WAYLAND_COMMIT=1`) still reported
  `begin_true=3`, `begin_false=45681`, and `queue_present=3`.
- The opaque swapchain and explicit Wayland commit therefore do not restore
  the production frame loop. This weakens the surface-composition-only
  hypothesis, while retaining native swapchain state as the boundary to
  inspect.
- A one-shot diagnostic was edited in the persistent Mac Podman Devtool source
  and committed as source revision
  `6c635c57d2667ade671643132cb2da4f9d5178b0`, based on baseline
  `b61ce701b46b2b1e29675a9b44088d145363ecad`.
- The official Devtool patch was generated and registered as
  `0291-flr0285-probe-beginframe-failure-state-devtool.patch`, SHA-256
  `93a823271e82fe8520a0cccf4144251103f959162d4a4b6b8cf4bab278752792`.
  The probe is opt-in under `FLR0285_BEGIN_FRAME_PROBE` and samples only the
  first eight failures, logging swapchain/native-window pointers, Wayland
  error, and native dimensions. No render behavior is changed.

## Verification plan

1. Compare FLR-0282/0283/0284 logs using marker counts, not full-log dumps.
2. Add only a bounded runtime probe if existing markers cannot distinguish
   renderable submission from target draw.
3. Run the smallest discriminating A/B and record whether the 3D pixels change.

## First A/B result

The first camera-profile placement was compiled and present in the guest
binary, but produced zero runtime profile markers because the selected
`updateCameraSettings()` path was not reached before the frame. QMP remained
black with `changed_pixels=0` and `chromatic_pixels=0`. This does not falsify
the camera hypothesis; it falsifies only that insertion point.

The next bounded patch moves the profile to `DrawFrame()` after ECS update and
before `renderer->beginFrame()`. It is still opt-in and does not alter the
default camera or surface contract.

## Evidence update — 2026-09-24

- The camera profile was proven active after the launch command was changed to
  individual `export` statements. The app PID contained the variable and
  emitted 44845 profile markers, but QMP stayed black except for grayscale
  geometry indicators. Camera framing is not sufficient.
- The existing native readback-to-SHM diagnostic displayed a colored cube with
  the 2D HUD, proving the compositor can show a colored subsurface. It did not
  produce an asynchronous readback result in the bounded log.
- The existing self-made Filament minimal-geometry fixture displayed a blue
  3D polygon with the 2D HUD, but it was clipped at the left edge. The fixture
  contract and viewport were valid; the effective camera was unexpectedly
  `(5,0,-5)`, proving the ECS camera update overwrote the fixture-local camera.
- Patch 0289 preserves the fixture-local camera only under the three explicit
  fixture environment controls. It is diagnostic-only and leaves the
  production path unchanged.

## Remaining success criteria

- [x] Build and validate patch 0289 on Mini using the fixed receiver/build.
- [x] Re-run the native fixture and prove the blue geometry is centered.
- [ ] Re-run production camera/model and determine whether vehicle pixels become
  visible after the camera ownership boundary is corrected.
- [x] Retain QMP frame/video evidence and cleanly stop the exact QEMU process.

## Mini validation update — 2026-09-24

- 0289 passed fixed-receiver do_patch, `flutter-auto do_compile`, and full
  image build. The new QEMU run used 4096 MiB and had no OOM evidence.
- The corrected fixture camera contract was visible in logs, but full-frame
  QMP still showed only the HUD and a black center ROI. The opaque-swapchain
  A/B was unchanged, so transparent swapchain alone is not the cause.
- 0290 reapplies the fixture camera immediately after ECS update. It was
  generated through the official Devtool flow, passed Mini `do_patch`,
  `do_compile`, and full-image gates, and produced the validated rootfs used
  by the next runtime loop.

## Runtime evidence update — 2026-09-24

- The first post-build fixture capture was taken before the runtime had settled
  and was black. A second bounded capture with scene-pass/present tracing
  settled correctly: all ten QMP frames shared SHA-256
  `f4d5eb2a32c6ef3a97ba13b3cef1a694f836f49656abc717bfc9c604dc0dffa1`, and
  the center ROI contained `92352` chromatic pixels with bbox
  `[484,220,312,296]`. The 2D HUD remained visible in the same QMP frame.
- Fixture scene-pass execution and queue present both succeeded repeatedly;
  the fixture contract had 8 vertices, 36 indices, and a bound material.
- A production A/B in the same 4096 MiB QEMU stayed alive without OOM and
  reached asset load, scene insertion, `beginFrame`, render return, scene pass,
  and queue present. Its effective contract was
  `scene_native=false scene_default=true camera=(5,0,-5) blend=1`, and the
  QMP production ROI remained zero-chroma with stable frame hash
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- A temporary guest-disk failure was separately identified: the fixture trace
  log consumed the complete 400 MiB `/run/user/1001` tmpfs. After cleanup,
  production startup succeeded. This must be handled by bounded log capture,
  not by increasing QEMU RAM.
- QMP Scenes input was accepted and changed the HUD to the known white repaint
  state, but the current run emitted no `FLR0274_SCENE_TRANSITION` marker and
  did not show Planetarium/Sequoia pixels. Route activation remains UNKNOWN.

### Current decision

The shared QEMU/Wayland/QMP path is now a positive control: the self-made
Filament fixture produces stable 3D pixels. The production failure is narrower
than a generic surface or memory problem. The next discriminator is the
production renderable/material/active-camera contract and the route callback,
not another QEMU memory increase or an unbounded log run.

## Renderable/material and full-light update — 2026-09-24

- Fresh run `flr0285-0005` confirmed one Sequoia asset, 12 valid renderables,
  21 material-instance records, and no invalid renderable. `Seq_Body` is
  entity 78 with seven primitives and AABB center z `-108.89394`; all sampled
  materials have color writes enabled.
- A full-light A/B with indirect light and direct lights both enabled remained
  byte-identical to the black production control. QMP ROI chromatic pixels
  remained zero across ten identical frames. This excludes “all lights were
  skipped” as the sole cause.
- The production draw boundary is therefore reached with valid CPU-side
  scene/material objects, but no visible production pixels are produced. The
  next discriminator is the active camera/view visibility and material input
  values, followed by route camera activation; no production behavior patch is
  accepted yet.

## Runtime evidence — 0011 memory allocation A/B

### Facts

- The same minimal production failure condition used in the 4096 MiB controls
  was run once with the QEMU override `-m 6144`. The rootfs SHA-256 was
  `3062d6e48656fe9c9c4ff6adc2e92065d163d70ffd6b3503eda1b63c06de8763` and
  the kernel SHA-256 was
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- Guest memory at the bounded observation was `MemTotal=6145492 kB`,
  `MemAvailable=5572184 kB`, with no swap and no OOM, cgroup-kill, or
  no-space marker. `/run/user/1001` had 578 MiB available.
- The QMP-only screenshot was captured at
  `$EVIDENCE_ROOT/flr0285-0011/qmp-6g.ppm` with SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
  The center ROI `(440,220,400,360)` was uniform black: `changed_pixels=0`,
  `chromatic_pixels=0`, `luma_range=[0,0]`.
- The 6144 MiB marker summary remained `begin_true=3`,
  `begin_false=47611`, `queue_present_return=1`, and `present_done=1`.
  The second `FLR0026_VK_QUEUE_PRESENT_BEGIN` was followed by no return in
  the bounded command output, matching the 4096 MiB control.
- QMP quit returned `accepted`; the harness reported
  `residual_targets=0 residual_qmp=0`, and the post-check found no QEMU,
  runqemu, or flutter-auto process.

### Decision

The memory-allocation hypothesis is rejected for the current black-frame
failure. Increasing QEMU from 4096 to 6144 MiB did not change the framebuffer
hash, center ROI, or present/fence boundary. The current first divergence
remains the second `vkQueuePresentKHR` call not returning, after a successful
queue submit; `beginFrame=false` is the downstream delayed-fence timeout.
The historical OOM cases remain a separate bounded-asset/debugger/logging
problem and must not be conflated with this production visibility failure.

### Act

- Keep 4096 MiB as the default bounded runtime profile; use 6144 MiB only for
  an explicitly named memory-control experiment.
- Keep the next investigation at the production/default-scene Vulkan present
  boundary and compare it with the proven native fixture path.

## Runtime evidence — 0012 native diagnostic-scene model A/B

### Facts

- The source-side diagnostic was created in the persistent Mac Podman Devtool
  source tree, committed as `4ee993f1d84eb241de57746d5a0d5a8a28164334`, and
  converted by the official helper into patch 0292. The canonical layer
  commit is `b8dfbc012fcbabb375dd114f5009af2c5b12e0af`.
- The Mini image was rebuilt successfully from that layer state. The tested
  rootfs SHA-256 was
  `168a6ff9d51521886423e1d81f1ab8d2d4f59570143d6732e0a1fae077b153a6` and
  the kernel SHA-256 remained
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- Run `flr0285-0012` used bounded 4096 MiB QEMU with one selected production
  model (`sequoia_ngp.glb`), native diagnostic geometry, the diagnostic scene
  opt-in, and the wide production camera. The model was ready, one model was
  added to the diagnostic scene, and 22 model entities were attached.
- The diagnostic-scene run returned from repeated `vkQueuePresentKHR` calls;
  the summary was `model_scene_added=1`, `model_scene_active=3348`,
  `begin_true=4`, `begin_false=3387`, `queue_present_begin=2`,
  `queue_present_return=2`, and `wayland_error=0` in the bounded guest
  evidence. The QMP socket was then quit and the harness reported
  `residual_targets=0 residual_qmp=0`.
- The QMP-only screenshot was
  `$EVIDENCE_ROOT/flr0285-0012/qmp-native-model-scene.ppm` with SHA-256
  `3a5f5b2e7c9a934083620faaf14bfd52f5ed67c76f964e595c509edd7b67d374`.
  Its center ROI `(440,220,400,360)` changed across the full ROI and had
  luma `[100,255]`, but only two chromatic pixels. The image is therefore
  not accepted as proof that the vehicle is visibly rendered: it is mostly
  gray with the known blue diagnostic pixels.
- The active-scene contract reported `skybox=true indirect_light=false`.
  No source change has yet duplicated direct-light entities into the
  diagnostic scene.

### Inference

- Moving the same loaded production entities into the native diagnostic scene
  changes the present boundary: the native-scene path repeatedly returns from
  present while the production default-scene control stalls after the second
  present. This narrows the failure to scene ownership/setup or a dependent
  render contract, not QEMU RAM or a generic Wayland/QMP failure.
- The Sequoia asset can be attached to the diagnostic scene, but the current
  screenshot does not prove vehicle visibility. The missing visible content
  may still be caused by light/environment ownership, camera/frustum, or
  material input; the immediate next discriminator is UNKNOWN until those
  contracts are measured separately.

### Act

- Keep 4096 MiB as the default runtime profile. Do not use another RAM increase
  for this symptom unless a new bounded OOM marker appears.
- Inspect `LightSystem`, `IndirectLightSystem`, `SkyboxSystem`, and camera
  activation before making another source edit. The next patch, if needed,
  must be an opt-in diagnostic only and must preserve the normal production
  scene path.

## Runtime evidence — 0013 native diagnostic-scene IBL A/B

### Facts

- Run `flr0285-0013` reused the rebuilt rootfs from 0292 with 4096 MiB QEMU.
  The only runtime change from 0012 was
  `FLR0026_NATIVE_ATTACH_DEFAULT_INDIRECT_LIGHT=1`.
- The scene contract reported `scene=diagnostic skybox=true
  indirect_light=true`, and the production asset was ready with the same
  selected Sequoia model. QMP capture and teardown both passed.
- QMP-only capture SHA-256:
  `a4a33e32cd80783bb2d2c7adc79c0faf725b6be6d7234ea633e42f475d7f750e`.
  Center ROI `(440,220,400,360)` had `changed_pixels=143999`,
  `chromatic_pixels=1`, dominant color `(224,224,224)` with 143998 pixels,
  and luma `[1,255]`. This is still not vehicle-visible evidence.
- The first attempt to collect the log slice violated the harness contract
  because the command file contained multiple lines, and the first analysis
  invocation passed an unsupported output option. The QEMU run was kept
  alive, the command was corrected to one line, and the same run's log and
  QMP analysis were successfully re-collected.
- Serial stop and QMP quit both passed; the post-check found no QEMU,
  runqemu, or flutter-auto process and no QMP socket.

### Inference

- Attaching the default indirect light to the native diagnostic scene changes
  the ownership contract but does not produce meaningful vehicle pixels.
  Missing IBL attachment is therefore not sufficient to explain the current
  production visibility failure.
- Direct lights are still owned by the default Filament scene in the current
  implementation. Whether the native diagnostic scene needs the same light
  entities is the next isolated question; camera, memory, and generic QMP
  causes remain rejected for this symptom.

### Act

- Keep the IBL option as an explicit diagnostic variable, not a production
  behavior change.
- Add only an opt-in diagnostic that duplicates already-built direct-light
  entities into the native diagnostic scene, then compare QMP pixels. If the
  result remains gray, inspect material/camera visibility next.

## Source diagnostic — 0293 direct-light scene ownership

### Facts

- The persistent Mac Podman Devtool source commit is
  `c9dc2aae7fd5f91672effe7062b05431612b814e`, based on source baseline
  `4ee993f1d84eb241de57746d5a0d5a8a28164334`. Its author metadata uses the
  project-approved anonymous identity `Fluorite Devtool
  <fluorite-devtool@localhost>`.
- The official helper generated and registered
  `0293-flr0285-probe-direct-lights-in-diagnostic-scene-devtool.patch` with
  SHA-256
  `af9f8f95b0a5df7bc0b8d3fd83326a72daaeca4549b10fcc978bda65a5ee9306`.
  The previous copy differed only in Git patch metadata and was replaced by
  the helper's explicit `--replace-canonical` path.
- An earlier helper attempt stalled because the persistent container retained
  update-recipe/BitBake processes; exact recorded PIDs were stopped. A manual
  sequence then proved the required ordering:
  baseline branch → component-add → source commit branch → update-recipe.
  When component-add was done at source HEAD, Devtool correctly emitted
  “No patches or local source files needed updating”; this was an operator
  ordering error, not a patch conflict.
- The Mac recipe gate was first run against the externalsrc component recipe
  and correctly rejected `do_patch` because that task is not defined there.
  The outer `flutter-auto` target has the same task absence in this setup, so
  Mac do_patch is not treated as an acceptance gate. Authoritative Mini
  `do_patch` remains the required layer verification.

### Decision

- The source change is diagnostic-only: normal default-scene ownership is
  unchanged, and direct lights are copied into the native diagnostic scene
  only when the existing `FLR0285_NATIVE_MODEL_SCENE=diagnostic` path is
  active.
- Privacy metadata is now compliant; no personal address is recorded in the
  new patch. The next step is Mini do_patch, component compile, image build,
  and one bounded QMP A/B.

## Runtime evidence — 0014 native diagnostic-scene direct-light A/B

### Facts

- Run `flr0285-0014` used the 0293 image at rootfs SHA-256
  `90143ccf8fae16dd7eac05bcd712cdb75cb87e611192c0edfdb929bf1003c293`, the
  unchanged kernel SHA-256
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  4096 MiB QEMU.
- The runtime log reported `FLR0285_NATIVE_LIGHT_SCENE_ADD lights=13
  scene=diagnostic`, `scene=diagnostic skybox=true indirect_light=true`, and
  the expected wide camera and native diagnostic scene contract. The
  direct-light diagnostic therefore reached its intended code path.
- QMP-only capture SHA-256:
  `3a5f5b2e7c9a934083620faaf14bfd52f5ed67c76f964e595c509edd7b67d374`.
  Center ROI `(440,220,400,360)` had 144000 changed pixels,
  `chromatic_pixels=2`, dominant `(224,224,224)` with 143998 pixels, and
  luma `[100,255]`. The hash is identical to the 0012 native-model-scene
  capture and is not vehicle-visible evidence.
- Serial stop, QMP quit, and residual cleanup all passed. No OOM or Wayland
  error marker was observed in the bounded selected output.

### Inference

- Adding all 13 already-built direct-light entities to the native diagnostic
  scene does not change the framebuffer. Direct-light scene ownership is
  therefore falsified as the sufficient cause of missing vehicle pixels.
- The stable gray output with only two blue diagnostic pixels points next to
  material input/visibility or model coordinate/projection state. Memory,
  IBL-only, direct-light-only, and generic QMP/Wayland causes are now
  rejected for this exact reproducer.

### Act

- Keep 0293 as a diagnostic patch only; do not promote it as a product fix.
- Inspect and measure the selected model's renderable AABB, world transform,
  camera frustum/depth range, material instance parameters, and culling state
  in the same native diagnostic scene before changing source again.

## Source diagnostic — 0294 production culling A/B

### Facts

- Static inspection found that production model renderables do not explicitly
  set culling in `ModelSystem::setupRenderable`, while the self-made fixture
  explicitly disables culling. The diagnostic source change adds an opt-in
  `FLR0285_NATIVE_DISABLE_CULLING` branch that disables culling only for
  renderables copied into the native diagnostic scene.
- The persistent Devtool source commit is
  `e716e620f127ef81cb3ce88ed5d5d0ac97590cee`, based on
  `c9dc2aae7fd5f91672effe7062b05431612b814e`, with the approved anonymous
  identity. Official patch 0294 was generated and registered with SHA-256
  `e99bd2a280ec1c3b7f11b011154b502846bf23536f6dee2ca14d8f8625471a8f`.
- The first helper attempt used an incorrect source SHA and stopped at
  `source-branch`; canonical layer state was unchanged. Reflog resolved the
  exact 40-character SHA and the retry passed the official component-rebase
  contract.

### Act

- Commit the official 0294 registration and evidence, hand it to Mini, then
  run the smallest authoritative build and one QMP A/B. Do not alter the
  normal production culling path.

## Runtime evidence — 0015/0016 culling probe status

### Facts

- Both runs reused the 0294 rootfs and the existing Mini build/TMPDIR with
  4096 MiB QEMU. They passed start, guest-ready, QMP-only capture, and exact
  cleanup; no target process or QMP socket remained.
- Both QMP captures had SHA-256
  `3a5f5b2e7c9a934083620faaf14bfd52f5ed67c76f964e595c509edd7b67d374` and
  the same gray ROI with only two chromatic pixels. No vehicle was visible.
- 0015 and the 30-second 0016 bounded logs reached the diagnostic scene and
  direct-light duplication, but did not emit model-selection/load-plan or
  `FLR0285_NATIVE_MODEL_SCENE_ADDED` markers. Consequently the new
  `culling_disabled` count was not observed.
- No OOM or cgroup/no-space evidence was present.

### Inference

- QEMU memory is not the active cause for this frame result. The culling
  experiment is `UNKNOWN`, because the production model-add gate was not
  reached in these runs; it must not be reported as a successful or failed
  culling A/B.

### Act

- Treat the next diagnostic boundary as model selection/load completion and
  the call into `addLoadedModelsToScene`. Keep the default memory at 4096 MiB,
  avoid another image build until that gate is explained, and retain the
  QMP-only evidence requirement.

## Runtime evidence — 0017/0018 normal production scene

### Facts

- 0017 and 0018 reused the same current rootfs, existing Mini build/TMPDIR,
  and 4096 MiB QEMU. Both were cleaned up through the fixed QMP harness.
- With `FLR0026_SKIP_FRAME_EVENT=1` in 0017, Sequoia was selected and loaded,
  but `ASSET_READY` observed `queued_models=0`; no scene dispatch or scene-add
  marker followed. The QMP frame was effectively non-geometric.
- Removing only that skip in 0018 produced `queued_models=2`, primary and
  secondary dispatch, and two `SCENE_ADD_DONE` markers. QMP SHA-256 was
  `3c2769cbcff1eb225e9115968663da97433e1d8026c6065be34bdb6edbbebede`;
  the vehicle silhouette is visible in
  [the QMP evidence image](../evidence/flr0285-0018/qmp-production-sequoia-current.png).
  The ROI changed 216303/223200 pixels. Color was intentionally not judged in
  this run because lights, IBL, skybox, and shapes were skipped.
- No OOM, cgroup/no-space, SIGSEGV, or residual process evidence was present.

### Inference

- The 0017 failure is a deterministic-looking asynchronous queue-order race
  induced by the frame-event skip, not QEMU memory pressure. The no-skip
  control proves current production Sequoia geometry reaches QMP pixels.
- Culling remains a lower-priority `UNKNOWN` for the diagnostic-scene branch;
  the normal production path now has a stronger, direct pixel proof.

### Act

- Keep frame-event skip disabled for acceptance runs and use it only for the
  labeled race probe.
- Next run the no-skip production scene with normal lights/IBL and capture the
  2D HUD plus native 3D composition, then test route transition separately.

## Runtime evidence — 0019 normal-light composition A/B

### Facts

- 0019 kept the no-skip model-loading order and restored production lights,
  IBL, skybox, and shapes. The runtime added both Sequoia instances and the
  QMP harness cleaned up successfully.
- QMP SHA-256 was
  `c333c513caaa4b30a82082cceb562115e678e33d492b38116f268411a8f2a097`.
  [The QMP image](../evidence/flr0285-0019-qmp-production-sequoia-normal.png)
  visibly shows the 2D HUD, CPU/FPS metrics, and Scenes button, but not the
  vehicle. The ROI had 190 changed pixels and 72 chromatic pixels.
- No OOM, cgroup/no-space, SIGSEGV, or residual process evidence was found.

### Inference

- Against 0018, normal production composition preserves Flutter 2D while the
  vehicle disappears; the model-load gate is no longer the suspect. The next
  discriminator is the native target's alpha/composite/stack and draw content
  contract.

### Act

- Compare the effective alpha/stack settings with the previously proven
  simultaneous self-made 2D+3D fixture. Keep frame-event skip disabled and
  avoid a model-loader patch until that comparison identifies a product-owned
  difference.

## Runtime evidence — 0020 opaque View A/B

### Facts

- The same production Sequoia run was repeated at 4096 MiB with only
  `FLUORITE_NATIVE_FORCE_OPAQUE=1` added. The effective contract reported
  `blend=0`, and the model asset was loaded.
- QMP SHA-256 was
  `fa6990e92d241ba7cb17555ea718b57f388e650d344322f1b344c80c35d98d0d`.
  [The QMP image](../evidence/flr0285-0020-qmp-production-sequoia-opaque-view.png)
  contains a black native polygon with 30,385 changed grayscale pixels and
  no chromatic pixels; Flutter HUD pixels are covered.
- Teardown passed and no OOM/cgroup/no-space/SIGSEGV marker was observed.

### Inference

- Opaque View is not sufficient to make the vehicle visible and has the
  expected 2D-composition regression. Keep it as a rejected diagnostic
  condition, not a production fix.

## Runtime evidence — 0021 wide-camera attempt

- The existing wide-camera command produced no app, camera, model, scene-add,
  frame, or present markers; its QMP frame was uniformly black. This is an
  invalid stimulus, not a camera falsification.
- Retry through guest SSH and require an app PID plus the camera marker before
  accepting the QMP image. The camera hypothesis remains open because 0018's
  vehicle is visibly clipped at the left edge.

## Runtime evidence — 0024/0026 SSH-controlled camera and light A/B

### Facts

- 0024 recovered the 2D HUD through QMP, but serial-login did not obtain a
  guest shell. It is HUD evidence, not proof of an environment-controlled app
  launch.
- 0026 used guest SSH, one QEMU, one `flutter-auto` PID at a time, the existing
  rootfs/build/TMPDIR, and 4096 MiB. Sequoia selection, asset load, and
  scene-add all passed.
- The production-light 0026b frame reached `beginFrame=true=2` and one
  queue-present marker, but QMP SHA-256 was
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e` and
  showed only the Flutter HUD. The chromatic pixels belonged to the Scenes
  button, not the vehicle.
- The exact 0018-style 0026f condition enabled frame events and disabled only
  diagnostic skybox, indirect light, direct lights, and shapes. It reached
  `beginFrame=true=22` and `queue-present=41`; QMP SHA-256 was
  `22f855bb6aff888aa6fcdc064cdfa6a770ce38af0f28c076fe257a732e513bd6`.
  The QMP image
  `work/evidence/flr0285-0026-qmp-production-sequoia-default-camera-no-lights.png`
  visibly contains the black Sequoia silhouette, strongly clipped at the left
  edge. No OOM, SIGSEGV, cgroup/no-space, or residual process was observed.
- Historical FLR-0049 evidence is separate but valid: both
  `work/latest-mac/flr0049-002f86e/no-readback-35s.png` and
  `alpha-build-ffab658/qmp-alpha-runtime-representative.png` visibly contain
  the Sequoia and red tail-lamp pixels. That run proved 3D plus light, but not
  simultaneous Flutter 2D HUD composition.

### Inference

- The current black production-light frame is not explained by a black car
  alone: the same current image draws the vehicle silhouette when diagnostic
  lighting and shapes are disabled, while the production-light case leaves
  only the HUD.
- Camera/framing is a real independent defect. The default camera places much
  of the current vehicle outside the viewport; the wide-camera experiment is
  not yet accepted as a product camera because it did not show a complete
  vehicle.
- Current light-enabled 2D/3D composition remains unresolved. Model-load and
  QEMU-memory hypotheses are rejected for this A/B. UNKNOWN: whether the
  production light/material path hides the renderable through native target
  content, alpha/stack composition, or a later camera update.

### Act

- Keep guest SSH as the runtime control path and require one PID,
  model/scene/frame/present markers, QMP capture, and residual cleanup before
  accepting a run.
- Keep QEMU at 4096 MiB and do not promote diagnostic skip controls to a
  product fix. Next isolate the production light/material/composite boundary
  with measured vehicle bounds.
