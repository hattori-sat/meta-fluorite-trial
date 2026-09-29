# FLR-0281 — validate secondary production model instance

- Status: Done
- Priority: High
- Owner: production model selection and secondary scene attachment
- Depends on: [FLR-0280](FLR-0280-trace-production-model-content-binding.md)
- Working log: `work/logs/2026-09-24-flr0281.md`

## Problem

The first selected production model is `mode=primary`, and the current source
deliberately does not add primary models to the Filament scene. The prior
one-model control therefore could not prove production rendering. This ticket
tested whether raising the selection limit would provide a secondary instance
without changing source, lighting, camera, or compositor behavior.

## Hypothesis

The secondary production model instance is the renderable vehicle content. If
the selection limit is raised from one to two, scene attachment and material
markers should appear and QMP should gain nonzero chromatic pixels.

## Success criteria

- Reuse the same newly built image and one 4096 MiB QEMU.
- Change only `FLR0026_NATIVE_MODEL_LIMIT` from `1` to `2`.
- Capture bounded model dispatch/material logs and ten QMP frames.
- Require live-process and clean QMP teardown.
- If chromatic pixels appear, record production 3D as proven for this path; if
  not, identify whether the secondary path was actually reached before opening
  a new ticket.

## Verification plan

1. Launch with frame-event skip, one selected asset family, and the existing
   no-light/no-environment controls.
2. Compare primary and secondary dispatch, scene-add, renderable, primitive,
   material, AABB, and QMP evidence.
3. Only create a source patch after the secondary path is proven insufficient.

## Result

The test is complete, but it did not reach a secondary instance.

- The authoritative image was reused with one QEMU and the explicit 4096 MiB
  override. The launch, ten-frame QMP capture, and QMP teardown all passed.
- `FLR0026_NATIVE_MODEL_LIMIT=2` selected two different assets:
  `assets/models/sequoia_ngp.glb` and `assets/models/Fox.glb`.
- Both assets were loaded successfully. The bounded runtime log reported
  `renderable_entities=12` for Sequoia and `renderable_entities=1` for Fox.
- Both dispatch records were `mode=primary`; neither was `secondary`.
  Therefore no `SCENE_ADD_DONE` or material trace was expected from this run.
- QMP frame `secondary-model-video/frame-00009.ppm` was 1280x800 with SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
  It had 116 changed pixels, 294 edge pixels, 0 chromatic pixels, and
  `max_chroma=0`. This is not production 3D proof.
- `flutter-auto` remained alive during the targeted log read, and QMP cleanup
  ended with `residual_targets=0 residual_qmp=0`.

## Conclusion

The hypothesis is not proven because the test selected two unique assets, not a
primary plus a secondary instance. The first concrete boundary remains the
primary branch: the current source logs “primary ... not adding to scene”.
FLR-0282 owns the minimal primary-scene-attachment test.
