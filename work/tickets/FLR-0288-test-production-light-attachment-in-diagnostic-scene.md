# FLR-0288 — test production light attachment in the native diagnostic scene

- Status: Waiting
- Priority: High
- Owner: production light ownership / native diagnostic scene
- Created: 2026-09-25
- Predecessor: [FLR-0287](FLR-0287-compare-production-sequoia-light-material.md)
- Working log: `work/logs/2026-09-25-flr0288.md`

## Objective

Use the existing diagnostic-scene path to attach the selected production
Sequoia lights to the same native scene that owns the model, then compare the
QMP native ROI with FLR-0287. This isolates light scene ownership from camera,
asset loading, material creation, and HUD composition.

## Acceptance gate

One QMP-only frame must retain the HUD and show a measurable change in the
native Sequoia ROI, with a colored or recognizable vehicle result if the light
attachment is sufficient. The runtime log must contain the diagnostic-scene
light-attachment marker, model/material markers, draw/present markers, and
clean QMP teardown.

## Facts

- FLR-0287 reaches Sequoia scene-add and valid lit materials but has a fully
  black native ROI.
- The self-made LIT fixture with an explicit SUN light produces colored 3D and
  HUD in the same image.
- Existing source controls already expose
  `FLR0285_NATIVE_MODEL_SCENE=diagnostic` and
  `FLR0026_NATIVE_ATTACH_DEFAULT_INDIRECT_LIGHT=1`; previous runs record the
  diagnostic light marker without requiring a new source patch.

## Hypotheses

1. Production lights are attached to a different/default scene than the
   diagnostic model, so the renderable receives no effective illumination.
2. Explicit light attachment will change the native ROI; if it does not, the
   remaining boundary is material/resource or target draw output.

## Verification plan

- Reuse the same fixed Mini receiver, image, build/TMPDIR, and 4096 MiB QEMU.
- Run the existing native diagnostic-scene light command with one Sequoia
  model, wide camera, and indirect-light attachment only.
- Save the log after the explicit diagnostic-light marker appears, capture the
  same native/HUD ROIs and bounded video, then quit QEMU through QMP.
- Do not combine culling, SHM, opaque-surface, or compositor-owner controls.
- If the ROI changes, create a separate implementation ticket for the minimum
  production-scene ownership repair; if it does not, move to material/target
  draw analysis in a separate ticket.

## Unknowns

- Whether the diagnostic scene receives the full production light set or only
  the default indirect light.
- Whether light attachment changes pixels when the production renderables keep
  their current `base_lit_*` materials.

## 2026-09-25 diagnostic-scene runtime result

The existing diagnostic control reached the intended light path:
`FLR0285_NATIVE_LIGHT_SCENE_ADD lights=13 scene=diagnostic`, production
Sequoia model selection, scene-add, draw submit/end, and frame return all
passed. The QMP-only frame is retained at
`/mnt/yocto/evidence/flr0288-0001/native-model-scene-light.ppm`, SHA-256
`d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
The 12-frame QMP video is under
`/mnt/yocto/evidence/flr0288-0001/native-model-scene-light-video/`.

Both analyzed ROIs were black:

- native `(440,220,400,360)`: `0/144000` changed/chromatic;
- HUD `(1120,0,160,80)`: `0/12800` changed/chromatic.

The runtime log SHA-256 is
`39bccee13a9d755be30b90e361118b5c6e45111f5f59d2ad035db1e55b1149c9` and the
bounded marker slice SHA-256 is
`8c99ec10d57ee0a74c5675f4dd2f6c6d686b65fedcb0afe73b7f3d5002ca6dd0`.
The effective contract repeatedly reported `scene_native=true blend=0`.
QMP teardown passed with zero residual targets.

### Decision

This is not a valid light-only verdict: the diagnostic scene intentionally
overwrote the view blend mode to opaque, so it covered the Flutter HUD. Source
inspection confirmed the forced opaque assignment in both diagnostic setup and
the per-frame diagnostic-scene branch. FLR-0288 is Waiting; FLR-0289 owns a
minimal opt-in translucent diagnostic-surface probe. Default production and
default diagnostic behavior must remain unchanged.
