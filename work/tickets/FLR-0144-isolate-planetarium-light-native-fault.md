# FLR-0144 — isolate Planetarium light native fault boundary

- Status: Done
- Priority: High
- Owner: Fluorite Native Light/Material + runtime diagnosis roles
- Created: 2026-09-13
- Updated: 2026-09-14
- Depends on: [FLR-0143](FLR-0143-align-planetarium-light-material-contract.md)
- Working log: `work/logs/2026-09-13-flr0144.md`

## Work unit

Use the existing FLR-0143 image and runtime selectors to separate direct-light
entity setup from the lit material/render path. Capture the process mapping and
bounded debugger/kernel evidence before any new source patch. This ticket is a
runtime-only A/B and must not mix in camera, HUD composition, or scene
transition work.

## Problem

FLR-0141 proved the corrected camera and shape path by showing a Planetarium
silhouette. FLR-0143 moved only the shared Dart point light into that world,
but the QMP region became uniform black and the guest reported a page fault in
`FEngine::loop` before present returned. The static API path exists, so the
next question is whether creating the light, contributing the light, or
shading the lit material is the first failing operation.

## Facts

- The fixed image contains the FLR-0143 light-position patch, but runtime
  selectors already present in the Native layer can limit or skip explicit
  lights without changing Dart source.
- `SceneTextDeserializer::setUpLights()` selects and attaches parsed lights;
  `LightSystem::vBuildLight()` forwards the parsed fields to Filament's
  `LightManager::Builder`.
- FLR-0143's light-enabled run reached 21 renderable shapes and then faulted
  in `FEngine::loop`; the candidate QMP region was black.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | explicit-light setup versus lit-material/render execution |
| Where | `SceneTextDeserializer` → `LightSystem` → Filament/llvmpipe → QMP |
| When | after shape readiness and before/at first present return |
| Who | Native scene/light roles, Filament backend, runtime diagnosis role |
| How | selector-only runtime A/B, `/proc/maps`, bounded GDB/kernel/QMP evidence |

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1 zero explicit lights removes the FEngine fault and restores present | selector-only zero-light run has present returns and a stable result | zero-light run faults identically |
| H2 light entity setup is safe but direct contribution/lit material faults | zero-light and contribution-disabled runs differ from entity-enabled run | all variants share the same fault boundary |
| H3 the fault is a shared llvmpipe/LLVM path independent of light values | zero-light run still faults at the same instruction boundary | zero-light run presents stably |

## Success criteria

- Reuse the fixed FLR-0143 rootfs/build/TMPDIR and run one QEMU at a time.
- Run selector-only variants in separate tickets/runs without changing source;
  capture `/proc/<pid>/maps` before the first expected fault.
- Preserve QMP screenshot/video, runtime markers, bounded kernel/coredump/GDB
  evidence, hashes, and exact teardown for the decisive result.
- Classify the first failing owner as light entity setup, direct contribution /
  lit material, or shared backend fault. Do not claim colored 3D unless QMP
  pixels show non-black Planetarium material.

## Scope

### In scope

- Existing `FLR0026_NATIVE_LIGHT_LIMIT` / skip/contribution diagnostic
  selectors and their effective marker evidence.
- One fixed image, one QEMU per selector run, process mapping, kernel and
  debugger evidence.

### Out of scope

- New Dart/Native source patch or Devtool finish until the runtime boundary is
  identified.
- Camera contract, HUD alpha/stacking, and menu scene transitions.

## PDCA

### Plan

1. Reuse the FLR-0143 artifact and fixed Mini receiver; verify no stale target.
2. Run the smallest zero-light selector case first and collect maps before
   waiting for the known fault window.
3. Compare QMP/present/kernel evidence with FLR-0143's light-enabled result.
4. Only then decide whether a Devtool diagnostic patch is justified.

### Do

- Record every command and result in `work/logs/2026-09-13-flr0144.md`.

### Check

- Require process identity, selector markers, map-to-symbol relationship,
  QMP pixels, and teardown before deciding the owner.

### Act

- If zero-light presents stably, split direct-light/material handling into a
  new source-owned ticket. If it faults identically, split the backend/LLVM
  execution path. If evidence is incomplete, keep the result UNKNOWN.

## Iteration 1 — runtime light contribution A/B (2026-09-14)

### Facts

- The first requested zero-light attempt used `FLR0026_NATIVE_LIGHT_LIMIT=0`,
  but the deployed `flutter-auto` and plugin contained no such selector or
  marker. It was therefore a preserved no-op observation, not zero-light
  evidence.
- A first valid run was rejected before guest boot because the evidence path
  made the QMP UNIX socket name too long. No QEMU remained after this host-side
  failure. The rerun used the short, fixed evidence directory
  `$EVIDENCE_ROOT/evidence/f0144/qemu`.
- With direct contribution enabled, the QMP postlaunch SHA was
  `4df86195c21f5fbcb9973858f1c6c7c690e5382ada76e3b3aaf5f1e04a135664`;
  the candidate region `[300,250,620,400]` changed in `0/248000` pixels,
  with chroma `0` and luma `[0,0]`. The guest faulted at RIP
  `0x7f9a1761541` (run-specific address) in `PID:684 Comm:FEngine::loop`;
  the captured maps placed the instruction at relative offset `0xb1d541`
  from `libLLVM.so.18.1`.
- With `FLUORITE_NATIVE_LIGHT_DISABLE_CONTRIBUTION=1`, the same image and
  camera/shape payload produced postlaunch SHA
  `16472df74ab11a5cc229df1e27f6d0b6e7096481946b7a1bb5712f327b7d435e`.
  The candidate region changed in `134962/248000` pixels, with edge bounding
  box `[437,250,406,346]`, luma `[0,255]`, and chroma `0`; the QMP preview
  showed a centered black faceted Planetarium sphere on a white frame.
- The contribution-disabled run recorded 13 explicit light entities with
  `FLUORITE_NATIVE_LIGHT_DISABLE_CONTRIBUTION enabled=true`, reached 50 scene
  pass executions, 48 queue-present returns, and no kernel fault marker. The
  normal app process, one Application Id, 21 Shape readiness entries, and
  QMP capture all passed.
- QMP quit and cleanup passed for both valid runs; residual QEMU, runqemu,
  `flutter-auto`, and QMP socket counts were zero. The decisive QMP screenshot
  is retained outside Git at
  `$LOCAL_QMP_EVIDENCE_ROOT/flr0144-qmp-contribution/qmp-postlaunch.png`.

### Inferences

- Light entity creation and Scene attachment are not the first failing owner:
  disabling only direct contribution leaves geometry and present stable.
- Enabling direct light contribution is the first discriminating boundary for
  the current image: it correlates with the FEngine/libLLVM-family fault,
  while disabling contribution produces a stable but black lit-material result.
- Camera, shape creation, ViewTarget, Wayland child surface, QMP transport,
  and teardown are not the remaining owner for this boundary.

### Hypotheses / UNKNOWN

- H1 “zero explicit lights is sufficient” is UNKNOWN because the deployed
  `FLR0026_*` selector was a no-op and the current image creates a default
  light when the scene list is empty.
- H2 “direct contribution or the lit material path owns the fault” is leading:
  the contribution-disabled A/B is stable and geometry-positive, while the
  enabled run faults before present returns.
- H3 “the exact fault is independently a shared LLVM/llvmpipe defect” remains
  open. The relative offset matches the historical boundary, but this ticket
  does not establish a unique producer or a symbolized call chain.
- UNKNOWN: whether the earliest source-owned input is the `lit.filamat`
  shader path, its parameter values, or a direct-light state consumed by the
  backend.

### Act

- Close this runtime-only boundary ticket as classified, not as a product
  3D fix. Open FLR-0145 to replace only the Planetarium planet material with
  the existing unlit material while satisfying its declared `baseMap` input.
  Do not reuse the invalid color-only `poGetUnlitMaterial` experiment: the
  packaged `unlitUV.filamat` requires `baseMap`, and FLR-0139 already records
  that API mismatch.

## PDCA checker

- Status: PASS
- Checked by: Fluorite runtime diagnosis role
- Findings: the contribution-disabled A/B is stable and geometry-positive,
  while direct contribution correlates with the FEngine/libLLVM fault. The
  no-op selector and QMP path-length failure are explicitly excluded from the
  causal conclusion. No colored 3D product result is claimed.
