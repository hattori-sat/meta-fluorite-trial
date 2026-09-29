# FLR-0310 — isolate production light registration versus renderer present

- Status: Done
- Priority: High
- Owner: production light entity / Scene ownership / renderer queue-present roles
- Created: 2026-09-25
- Predecessor: [FLR-0309](FLR-0309-probe-zero-intensity-production-light.md)
- Working log: `work/logs/2026-09-25-flr0310.md`

## Objective

Identify the first differing operation between the production Sequoia path that
faults after a SUN is registered and the known-good self-made LIT fixture that
shows colored 3D plus HUD. Keep camera, model limit, QEMU memory, compositor,
and QMP capture fixed.

## Facts

- FLR-0308 normal-intensity SUN and FLR-0309 zero-intensity SUN both reach
  queue/present markers and reproduce the FEngine/libLLVM page-fault boundary.
- FLR-0308 no-light avoids the fault but stalls before present, so it is not a
  positive rendering control.
- FLR-0251 and FLR-0286 prove a self-made native/LIT fixture can show colored
  3D and HUD together in the same QMP frame.
- FLR-0309 native ROI is `0/144000`; its eight-frame QMP video is byte-stable.
- The persistent Mac Devtool source now has an opt-in order probe committed as
  `a0170a6450bcf22c8fd3f2198f318230d39274e6`, based on source baseline
  `81060181b637280612c675152fa872fd83b04abe`.
- The official Devtool patch was generated and registered as
  `0310-flr0310-probe-production-light-order-devtool.patch`; its SHA-256 is
  `5645ef461f1037f3b3de069199b5bc11598cecf1d0a163a5689c326170479b73`.
- The opt-in variable is
  `FLR0310_PRODUCTION_SCENE_LIGHT_BEFORE_ECS_UPDATE`; the default order is
  unchanged.
- The canonical layer commit is `ffcde606848e9ac38940ef632dce927b718282de`.
- Bundle handoff passed with SHA-256
  `99b945313e2e4bebe0318a952213a4ac5f46e1c6c578fedf15cadc46881fd8ba`.
- Mini `do_patch`, `flutter-auto do_compile` (2686 tasks), and full image
  build (11758 tasks) all passed.
- The order-before-ECS QEMU used rootfs SHA
  `37cc077042d9c1f9e921f65e957bfe681aec16db4aca49a5d7942c3cc5e78d9c` and
  qemuboot SHA `e909f37647238eb88205e0f82bfe5c0d4c2ac2f9b52123e822bbb65db4102aae`.
- QEMU preflight/start/guest-ready/serial-exec/QMP capture/video/quit and
  residual cleanup all passed.
- The order marker and zero-intensity setup marker were observed. The guest
  again reached queue/present markers and then recorded the same
  `FEngine::loop`/`#PF` fault. The parent process remained alive and no
  coredumpctl entry was present.
- QMP still and all eight QMP video frames share SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`;
  native ROI remained `0/144000` and HUD ROI remained uniform white.

## Hypotheses

1. Production light entity registration or Scene ownership reaches an invalid
   renderer state that the self-made fixture does not use.
2. The first queue/present operation is common, but production asset/material
   work before it corrupts the engine; the light is only correlated.
3. The production and fixture light/material call order differs in a way that
   can be tested without changing final camera/composition.

## Plan / PDCA

### Plan

Read the effective source/API call order for production light creation, model
attachment, material setup, and the fixture's known-good light path. Select one
runtime discriminator only after that comparison.

### Do

The source/API comparison found that production light registration is called
after `ecs->update()` in `DrawFrame`, while the known-good fixture registers
its SUN during direct fixture scene initialization. An opt-in order-only
probe was generated through the standard Devtool flow. The authoritative Mini
patch/build/runtime gates were then completed.

The order-before-ECS probe reached its order marker and reproduced the same
FEngine/libLLVM fault and byte-identical QMP output as FLR-0309. Registration
timing is not the distinguishing variable.

### Check

The order marker is positive, but the first differing result is unchanged:
FEngine/libLLVM fault with native ROI `0/144000` and byte-identical QMP video.
The order hypothesis is falsified.

### Act

Close this ticket and hand the production GLTF/material/asset boundary to
FLR-0311. Preserve the known-good fixture and historical HUD+Sequoia evidence
as acceptance references.

## UNKNOWN

- Exact owner of the FEngine/libLLVM fault: light entity, Scene ownership,
  material/asset work, or queue/present lifecycle. Light intensity and
  registration timing are now falsified as the distinguishing variables.
- Whether production Sequoia geometry is rendered but hidden, or never reaches
  a visible draw before the fault.
