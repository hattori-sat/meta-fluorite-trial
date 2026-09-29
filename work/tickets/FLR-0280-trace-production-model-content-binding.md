# FLR-0280 — trace production model content binding

- Status: Done
- Priority: High
- Owner: production model transform/material binding and default-scene content
- Depends on: [FLR-0279](FLR-0279-isolate-production-opaque-surface-composition.md)
- Working log: `work/logs/2026-09-24-flr0280.md`

## Problem

The production model path reaches asset load, Scene insertion, draw, render
return, and Present, but QMP remains black or grayscale. The native fixture is
chromatic in the same image and the opaque View discriminator was falsified.
The next comparison must inspect whether production renderables have valid
material instances, transforms, bounds, and camera visibility in the default
Filament scene.

## Facts

- Production loads `assets/models/sequoia_ngp.glb` and reports 12 renderable
  entities for the selected asset.
- Production uses Filament gltfio's Ubershader provider, while the fixture uses
  a self-created unlit material with an explicit blue color.
- The production View is on the default Filament scene and reaches the camera
  position `(5,0,-5)` after model load.
- QEMU memory and View blend mode are not the current leading causes.

## Result

The first production-vs-fixture difference is earlier than material binding:
the bounded run selected only `sequoia_ngp.glb` model ordinal 0, and the
runtime dispatch marker reports `mode=primary`. The current source explicitly
does not add a primary model to the Filament scene. Therefore
`setupRenderable`, primitive/material inspection, and scene-add markers do not
appear, and the QMP ROI remains uniformly black. `FLR0028_MODEL_CONTENT_TRACE`
was present in the deployed binary and the environment reached flutter-auto;
the absent renderable trace is explained by this primary-model branch, not by a
missing patch.

## Competing hypotheses

1. The production asset's renderable entities do not have the expected material
   instances or primitive binding. Prediction: bounded per-renderable material
   and primitive inspection finds an invalid or zero-content binding.
2. The production model is valid but its transform/bounds/camera contract puts
   it outside the visible frustum. Prediction: bounded transform/AABB/camera
   evidence differs from the fixture and a minimal diagnostic transform changes
   QMP pixels.

## Success criteria

- Identify the first concrete production-vs-fixture difference in material,
  primitive, transform, bounds, or camera visibility.
- Keep logs bounded; no full runtime log dump.
- Do not patch until a specific boundary is supported by runtime or static
  evidence.

## Verification plan

1. Inspect the existing `ModelSystem::setupRenderable` and gltfio asset path.
2. Add only the smallest diagnostic needed through the official Mac Devtool
   flow if static evidence cannot answer the first boundary.
3. Build on Mini only if a source patch is required; otherwise reuse the
   authoritative image and QMP harness.
4. Require nonzero chromatic QMP pixels before claiming production 3D.

The next independent unit is
[FLR-0281](FLR-0281-validate-secondary-production-model-instance.md), which
keeps the same image and raises only the model selection limit to include the
secondary instance.
