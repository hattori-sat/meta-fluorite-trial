# FLR-0311 — compare production GLTF/material fault with the known-good LIT fixture

- Status: Done
- Priority: High
- Owner: production GLTF asset/material/shader path versus direct Filament fixture
- Created: 2026-09-25
- Predecessor: [FLR-0310](FLR-0310-isolate-production-light-registration-present-boundary.md)
- Working log: `work/logs/2026-09-25-flr0311.md`

## Objective

Find the first production GLTF/material operation that differs from the
known-good self-made LIT fixture and causes the FEngine/libLLVM fault before
visible Sequoia pixels. Keep the accepted target as one QMP frame containing
HUD plus colored 3D; do not replace that target with a process-survival claim.

## Facts

- FLR-0308 and FLR-0309 show that normal versus zero SUN intensity does not
  change the fault boundary.
- FLR-0310 shows that moving production light registration before ECS update
  also does not change the fault or QMP frame.
- FLR-0251/FLR-0286 show a self-made direct Filament LIT material, geometry,
  and SUN can produce colored 3D plus HUD in one QMP frame.
- The production path loads `sequoia_ngp.glb` asynchronously through
  `ModelSystem`; the fixture builds a simple material instance and vertex/index
  buffers directly.
- The persistent Mac Devtool source has a bounded opt-in marker around
  `assetLoader_->createAsset()` and `resourceLoader_->asyncBeginLoad()`:
  source commit `a8740abcc3aabb29f9898f055d413e3c968fc7ea`.
- The official generated patch is
  `0311-flr0311-trace-production-asset-boundary-devtool.patch` with SHA-256
  `3d35ad7b27b9b6ca25393ed65f9ee5a77f45289301061e04ae7312867bed28d3`.

## Hypotheses

1. Production GLTF material/shader generation reaches an LLVM/llvmpipe path
   that the simple fixture does not exercise.
2. Production asset-instance ownership or scene attachment corrupts the engine
   before the material marker, while light is only correlated.
3. Production and fixture render-target contracts are different; the known-good
   fixture can be used as a direct control for material/scene state.

## Plan / PDCA

### Plan

Compare the effective production asset/material creation path with the fixture
material path and existing bounded markers. Select one opt-in material or asset
discriminator only after identifying the first operation not shared by the
fixture.

### Do

Opened after FLR-0310 falsified light intensity and registration order. The
smallest diagnostic patch now traces the first GLTF asset creation and async
resource-load calls without changing their behavior.

### Check

Require source/API evidence plus a bounded runtime marker and QMP still/video
result. Keep the historical Sequoia/HUD and self-made LIT/HUD frames as two
separate acceptance references.

### Act

Create one new Devtool patch ticket for the smallest source-backed control.
Do not hand-edit generated patches or combine camera, composition, and
material changes in one experiment.

## UNKNOWN

- Exact first production GLTF/material operation before the LLVM fault.
- Whether production Sequoia has been rendered but hidden, or never reaches a
  visible material/draw path.

## 2026-09-25 runtime result — asset boundary reached, vehicle ROI still black

### Facts

- Mini bundle, `do_patch`, `do_compile`, and the full image build passed before
  this runtime. The run used one QEMU with 4096 MiB and QMP-only capture.
- The guest selected the intended production asset:
  `FLR0026_MODEL_SELECTED ordinal=0 asset=assets/models/sequoia_ngp.glb`.
- The new trace markers were reached in order:
  `FLR0311_PRODUCTION_ASSET_CREATE_BEGIN` → `CREATE_DONE` with
  `asset_present=true renderable_entities=12` →
  `ASYNC_BEGIN_LOAD_BEGIN` → `ASYNC_BEGIN_LOAD_DONE`.
- The runtime reached Vulkan queue submit and present markers, then the same
  FEngine/libLLVM page fault occurred in `FEngine::loop`. This is not an OOM
  result.
- QMP screenshot SHA-256:
  `0fbb14682df6eba06ef686a8c2c9ea73096dc23affc3a5260672b965f89bdc05`.
  The eight QMP video frames had this identical SHA-256.
- Native ROI `(440,220,400,360)` was uniform black: `0/144000` changed,
  `0` chromatic, luma range `[0,0]`.
- HUD ROI `(1120,0,160,80)` was present and colored: `2990` changed and
  `2845` chromatic pixels. The QMP screenshot shows the CPU/FPS/system-delay
  HUD and the purple `Scenes` button, but no vehicle.
- This run intentionally set
  `FLR0309_PRODUCTION_SCENE_LIGHT_ZERO_INTENSITY=1`; therefore it cannot
  decide whether normal light produces vehicle color. It does establish that
  the production asset boundary is reached before the fault and that the
  current black ROI is not caused by failure to select or begin loading the
  GLTF asset.
- QMP quit and residual-process cleanup passed: zero QEMU, `runqemu`,
  `flutter-auto`, and QMP socket residuals.

### Inference

- The earlier positive baseline must remain the acceptance target: FLR-0070
  recorded simultaneous HUD plus production Sequoia/color pixels, while
  FLR-0286 recorded simultaneous HUD plus a self-made lit Filament fixture.
- The current experiment narrows the boundary past GLTF asset creation and
  async-begin-load, but does not yet distinguish camera/framing, async
  resource completion, material-instance setup, scene attachment, or the
  zero-intensity control itself.

### Act

- Do not close FLR-0311 as a 3D success. Preserve this run as a boundary
  result and use a normal-intensity A/B with the same asset trace before
  changing source again. The next experiment must retain the same QMP ROI and
  capture the bounded runtime log before teardown.

## 2026-09-25 normal-intensity A/B result

### Facts

- The same rootfs, kernel, camera, model selector, asset-boundary trace,
  QMP ROI, and 4096 MiB QEMU profile were reused. The only relevant change
  was removing `FLR0309_PRODUCTION_SCENE_LIGHT_ZERO_INTENSITY`.
- The production light marker reported
  `FLR0305_PRODUCTION_SCENE_LIGHT_SETUP_DONE ... intensity=110000 mode=normal`.
- The same asset markers were reached in the same order through
  `FLR0311_PRODUCTION_ASYNC_BEGIN_LOAD_DONE`, followed by Vulkan submit and
  present.
- The normal-light QMP screenshot and all eight video frames had SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
- Native ROI `(440,220,400,360)` remained absent: `0/144000` changed,
  chromatic pixels `0`, luma range `[1,6]`.
- HUD ROI was a uniform white surface in this capture (`12800/12800`
  changed, chromatic pixels `0`).
- The same FEngine/libLLVM page fault occurred in the guest kernel journal;
  `coredumpctl` contained no entry and no OOM marker was observed.
- QMP quit and residual cleanup passed with zero QEMU/flutter-auto targets and
  zero QMP sockets.

### Inference

- Zero versus normal SUN intensity does not distinguish the black production
  vehicle ROI. The light contribution is not the first proven boundary.
- FLR-0311 closes the asset-create/async-begin-load observation unit. The
  remaining boundary is after asynchronous resource completion: Scene add,
  renderable/material setup, camera/target visibility, or the renderer fault.

### Act

- Keep the historical FLR-0070 HUD+Sequoia/color frame and FLR-0286
  self-made-LIT/HUD frame as acceptance references.
- Hand off the next independent marker-only runtime check to FLR-0312. No
  product patch is justified by the light A/B alone.
