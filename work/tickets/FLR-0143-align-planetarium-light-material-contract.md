# FLR-0143 — align Planetarium light/material world-space contract

- Status: Done
- Priority: High
- Owner: Flutter filament_scene Scene/Light serializer + Fluorite Native LightManager/Material roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0141](FLR-0141-align-dart-native-scene-camera-api.md)
- Working log: `work/logs/2026-09-13-flr0143.md`

## Work unit

With the FLR-0141 camera contract fixed, identify and correct one
Planetarium light/material boundary so the QMP-visible 3D shape is not only a
black silhouette. Keep the camera, shape list, QEMU profile, and capture
region fixed while testing one lighting/material variable.

## Problem

### Facts

- FLR-0141 proves the shape-only Planetarium payload reaches Native and
  produces visible geometry after the camera eye is translated into Native's
  world-space contract.
- The Planetarium scene places its geometry around `scenePosition=(-720,0,680)`.
- `poGetSceneLightsList()` supplies a shared point light at `(0,5,1)` with
  `falloffRadius=300.1`; the Planetarium-specific `getSceneLights()` returns
  an empty list.
- Planetarium planet shapes use the lit material with colored `baseColor`
  parameters. The active scene also supplies a default indirect-light object.
- The corrected QMP frame contains a centered black polygon on a pale frame,
  not a uniform surface. This is a geometry-positive, color-negative result.

### Static Dart/Native relationship

- Dart serializes each `Light` inside `scene.lights` with `type`, `position`,
  `intensity`, `falloffRadius`, color, and cast flags.
- Native `SceneTextDeserializer` reads the `lights` list, constructs
  `Light(encodableMap)`, and `setUpLights()` passes it to
  `LightSystem::vBuildLightAndAddToScene()`.
- Native `Light::Deserialize` accepts the same `position` and
  `falloffRadius` fields. `LightSystem::vBuildLight()` forwards both to
  Filament `LightManager::Builder`. The exercised API path is therefore
  present; the value relationship is the remaining suspect.
- The current values are a shared point light at `(0,5,1)` and
  `falloffRadius=300.1`, while the Planetarium geometry is centered near
  `(-720,0,680)`. A point-light distance of roughly 990 exceeds the declared
  falloff, so black shading is expected if the values use one world-space
  frame.

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Geometry is present but lit shapes are black | FLR-0141 QMP postlaunch and 12-frame video |
| Where | Example Demo initial SceneView, Planetarium shape payload, Native lit path | FLR-0141 API map and source inspection |
| When | After the camera eye contract is corrected and during stable postlaunch frames | FLR-0141 QMP/runtime evidence |
| Who | Dart Scene/Light serializer, Native deserializer/LightManager, Filament material path | Component ownership |
| How | Shape readiness, scene pass, and present succeed; color/luma remains black in the shape | FLR-0141 runtime markers and QMP pixels |

### Problem point

The first visible gap is after successful shape creation and camera placement,
at the lighting/material contribution stage. The exact owner is UNKNOWN.

## Root-cause hypotheses

| Hypothesis | Prediction | Falsification test |
| --- | --- | --- |
| H1 direct point light is outside the Planetarium world/falloff | Moving only the light to the Planetarium world changes the shape from black to colored | One light-position patch with all other inputs fixed |
| H2 Dart lit-material or light wire format is not accepted by Native | A known-good Native-compatible material/light encoding changes color without relying on position | Compare serialized fields and one minimal material/light A/B |
| H3 Native lit shader or shadow path is independently black | A world-space light and valid base color still produce black geometry | Targeted Native runtime markers and a controlled material fallback |

UNKNOWN: the first causal variable among light placement, indirect-light
deserialization, and lit-material/shader handling.

## Success criteria

- Dart/Native light and material fields are compared explicitly before editing.
- If a source change is justified, it is made in the persistent Mac Devtool
  source after `modify`, finished with Yocto-standard Devtool, copied unchanged
  into `meta-fluorite-trial`, and locally committed.
- The exact commit is transferred once by bundle to the fixed Mini receiver;
  the same build/TMPDIR passes do_patch, do_compile, and full image.
- One QMP-only QEMU run either shows a non-black Planetarium material response
  or records a quantitative negative result and the first runtime fault, with
  a representative screenshot/video frame. Runtime logs show the app
  ownership and any crash boundary explicitly.
- QMP teardown reports zero residual QEMU/flutter-auto processes and zero QMP
  sockets.

## Scope

### In scope

- Static Dart/Native light/material relationship and one-variable correction.
- Shape-only Planetarium payload and its visible color/lighting response.

### Out of scope

- FLR-0141 camera patch and camera API redesign.
- `UPDATE_FILAMENT_SCENE` scene transitions.
- Parent Flutter HUD alpha/stacking/composition.
- Production GLB/LLVM path until shape-only lit output is understood.

## PDCA

### Plan

- Inspect Dart Light/Material JSON and Native deserialization/LightManager
  ownership, then select the first discriminating variable.
- Reuse the persistent Mac Podman machine/container and mounted Devtool source;
  do not create another volume, build directory, TMPDIR, or QEMU.
- Run Mac patch gate, canonical verification, commit, bundle handoff, Mini
  progressive build, one QMP runtime, and clean teardown.

### Do

- Record execution in `work/logs/2026-09-13-flr0143.md`.

### Check

- Compare source fields, patch identity, build gates, QMP pixels, runtime
  markers, and teardown against FLR-0141's fixed camera baseline.

### Act

- If color is restored, split HUD/composition or transition into a new ticket.
- If color remains black or a fault appears, preserve the negative result and
  create the next narrowly scoped Native material/light ticket; do not expand
  this unit.

## Visual evidence

- Baseline: `$EVIDENCE_ROOT/evidence/flr0141-planetarium-camera/qemu/qmp-postlaunch.ppm`
- Baseline visual: centered black Planetarium shape on pale frame; no HUD.
- Baseline postlaunch SHA-256:
  `16472df74ab11a5cc229df1e27f6d0b6e7096481946b7a1bb5712f327b7d435e`

## Iteration 1 — world-space light A/B (2026-09-13)

### Facts

- Canonical commit `4e7587801eff42f512941839bfb3c00c5e4dac8c` contains the
  unchanged Devtool-generated light-position patch `0062`; its SHA-256 is
  `7a38116330f2dcfc7da16b014f6c1497c6aa5b56a148126ebd8061680da01f25`.
- The bundle reached the fixed Mini receiver with SHA-256
  `a6b87fac41c0ec625ec2dbde59d04c41a7a4d0d426d9ac03fddddbeace579c3a`.
- Mini `do_patch` passed 104/104, target `do_compile` passed 2590/2590, and
  the full `agl-ivi-image-flutter` build attempted 11898 tasks with 11878
  reused and all tasks successful.
- The rootfs artifact is
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260913144014.ext4`, SHA-256
  `78145247fc698c92dfef7e5ec7a21530f37eb1b382fcce11b1a2aae1f5f83c7d`.
  The matching qemuboot SHA-256 is
  `11051d8c331ce757589182a5d266d131e84d6aac036f8afbd6ab7dba78c446a2`, and
  the kernel SHA-256 remains
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- One QEMU run used the fixed qemux86-64 `runqemu` profile and QMP-only
  capture under `$EVIDENCE_ROOT/evidence/flr0143-planetarium-light/qemu`.
  Preflight, start, guest readiness, and serial Example Demo launch passed.
- The prelaunch QMP PPM SHA-256 is
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  The postlaunch PPM SHA-256 is
  `4df86195c21f5fbcb9973858f1c6c7c690e5382ada76e3b3aaf5f1e04a135664`.
- In the fixed Planetarium candidate region `[300,250,620,400]`, the
  postlaunch image differed from prelaunch in `0/248000` pixels, with edge
  pixels `0`, chromatic pixels `0`, and luma `[0,0]`. All 12 QMP video frames
  were byte-identical to the postlaunch PPM. The full frame's non-black pixels
  were limited to the 2D HUD/Scenes area; the Mac preview is the HUD-only
  screenshot at `$LOCAL_QMP_EVIDENCE_ROOT/flr0143-qmp-light/qmp-postlaunch.png`.
- Runtime reached one `Application Id: fluorite`, 21 `SHAPE_READY` entries,
  camera deserialization/application, and three paired scene passes. One
  `flutter-auto` process remained alive, but no later present-return marker was
  recorded after the FEngine fault boundary.
- The guest kernel recorded `BUG: unable to handle page fault` at about 75.8s
  in `PID: 681 Comm: FEngine::loop`, with user RIP
  `0x7f6905cb1541`. The app process remained present while its FEngine worker
  was lost; no userspace coredump was listed in the bounded query.
- QMP capability negotiation and quit passed, with
  `residual_targets=0 residual_qmp=0`. The unrelated stale broad `grep -R`
  investigation process was then removed by exact PID; no QEMU, runqemu, or
  flutter-auto process remained.

### Inferences

- H1, “moving the direct light into the Planetarium world restores color,” is
  rejected by this A/B: the candidate region stayed uniform black and the
  change coincided with an FEngine worker page fault before present returns.
- The source/API path is not missing: Dart light position reaches Native's
  `Light::Deserialize` and `LightSystem::vBuildLight()`; the value change is
  the controlled difference. However, this run does not prove whether the
  malformed/unsupported value, the lit-material interaction, or the shared
  llvmpipe/LLVM fault path is the direct cause.
- The visual failure is no longer classified as QEMU/Wayland transport or
  shape creation. The new first runtime boundary is Native/Filament lighting
  execution, with a known-looking `FEngine::loop`/LLVM-family page-fault
  signature from historical tickets.

### Hypotheses / UNKNOWN

- H2: direct-light entity/value handling activates a Native/Filament path that
  faults for this Planetarium payload — leading, but not yet causal.
- H3: the lit material or indirect-light interaction independently reaches the
  same llvmpipe/LLVM fault — open.
- UNKNOWN: the exact shared-library mapping for this run's RIP, because a
  `/proc/<pid>/maps` snapshot was not taken before teardown; therefore the
  historical `libLLVM.so.18.1`/`isOrdered` attribution is a correlation, not a
  new symbolized proof.

### Act

- Close FLR-0143 as a completed negative light-position classification. The
  next independent ticket is FLR-0144, which uses existing runtime light
  selectors to separate “light entity setup itself faults” from “lit material
  remains black without direct lights,” before any new source patch.

## PDCA checker

- Status: PASS (one-variable light-position hypothesis classified; no product
  3D fix claimed)
- Checked by: Mac Devtool + Mac fixed-container do_patch + Mini authoritative
  BitBake + one QMP-first runtime loop
- Findings: the world-space light patch did not produce non-black Planetarium
  pixels and correlated with an `FEngine::loop` page fault; Native light setup,
  lit material, and the shared LLVM/llvmpipe path remain split to FLR-0144.
