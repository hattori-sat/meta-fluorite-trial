# FLR-0283 — restore production lighting for the attached model

- Status: Done
- Priority: High
- Owner: production lighting and material visibility
- Depends on: [FLR-0282](FLR-0282-attach-primary-production-model-to-scene.md)
- Working log: `work/logs/2026-09-24-flr0283.md`

## Problem

FLR-0282 proves that the production Sequoia asset is loaded, attached to the
Filament scene, populated with 12 renderables and real `base_lit_*` materials,
and sent through draw/present. QMP is still black because that run skipped the
indirect light and diagnostic lights.

## Hypotheses

1. The black production region is expected from unlit `base_lit_*` materials;
   restoring the existing production indirect light makes QMP chromatic.
2. The production lighting setup is itself broken or faults; restoring it will
   remain black or produce a bounded runtime error.
3. Lighting is not the cause; a camera/transform or target-composition issue
   remains after scene attachment.

## Scope and success criteria

- Reuse the FLR-0282 image and one 4096 MiB QEMU.
- Change only the lighting skip controls in the runtime command; do not create
  another source patch before this A/B is complete.
- Capture bounded lighting/material/draw logs and ten QMP frames.
- Require a clean QMP teardown. If chromatic production pixels appear, record
  visible production 3D as proven for the model-only path; otherwise preserve
  the first lighting boundary and open the next ticket.

## Verification plan

1. Keep `FLR0026_NATIVE_MODEL_LIMIT=1`, frame-event skip, and the primary scene
   attachment patch unchanged.
2. Run one baseline with indirect light restored and diagnostic lights still
   skipped.
3. Compare scene, light, draw/present, and QMP pixel evidence against FLR-0282.

## Result

- Reused the FLR-0282 image and one 4096 MiB QEMU. Preflight and guest-ready
  passed, and teardown ended with no residual targets or QMP socket.
- Restored the production indirect light only. The runtime explicitly reported
  `FLR0026_INDIRECT_LIGHT_TYPE=DEFAULT`; diagnostic lights remained skipped
  (`FLR0027_NATIVE_SKIP_LIGHTS enabled=true lights=13`).
- Primary Sequoia still reached scene attachment with 12 renderables and real
  materials, and Vulkan queue present returned 0.
- QMP-only frame `production-indirect-light-video/frame-00009.ppm` retained
  SHA-256 `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`,
  changed=0, chromatic=0, max_chroma=0. The 3D region remained black.
- Guest memory was `MemTotal=4087260 kB`, `MemFree=2986472 kB`, and
  `MemAvailable=3356008 kB`; no OOM or killed-process marker appeared.

## Conclusion

Restoring the default indirect light alone did not change the black QMP result.
The indirect-light-only hypothesis is falsified for this image. Direct
production lights remain skipped, so FLR-0284 owns the direct-light A/B before
camera or target-composition changes.
