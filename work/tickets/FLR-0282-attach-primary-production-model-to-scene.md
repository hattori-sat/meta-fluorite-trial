# FLR-0282 — attach the primary production model to the scene

- Status: Done
- Priority: High
- Owner: primary production model scene attachment
- Depends on: [FLR-0281](FLR-0281-validate-secondary-production-model-instance.md)
- Working log: `work/logs/2026-09-24-flr0282.md`

## Problem

The current production selection can load a unique GLB as `primary`, but the
current `ModelSystem` primary branch deliberately does not call
`addModelToScene`; `addModelToScene` also returns early for primary. A scene
containing only unique assets can therefore load valid renderables while
displaying no production object.

## Facts

- FLR-0281 loaded both Sequoia and Fox, and both dispatched as `primary`.
- The source creates and stores the primary `FilamentInstance`, so the primary
  has the instance data required by the existing scene-add path.
- The existing secondary and non-instanced paths already call
  `addModelToScene`.

## Hypotheses

1. Minimal product fix: dispatch `primary` through `addModelToScene` and remove
   its defensive early return. Prediction: a unique production GLB reaches
   scene-add, renderable/material traces, and nonzero chromatic QMP pixels.
2. The primary instance is not safe for the shared scene-add path. Prediction:
   the call fails or produces a runtime fault; then retain the diagnosis and
   split asset-instance ownership from scene attachment into a separate ticket.

## Scope and success criteria

- Edit only `model_system.cc` through the fixed Mac Devtool source workspace.
- Generate the patch with official Devtool `git add`, `git commit`, and
  `devtool update-recipe`; do not hand-author the patch.
- Mini `do_patch`, component compile, and full image must pass.
- One 4096 MiB QEMU must show primary scene-add/material markers and a QMP
  frame with nonzero chromatic production pixels, or produce a bounded failure
  with the first failing boundary recorded.
- Record exact image/QMP hashes and controlled teardown.

## Verification plan

1. Reuse the fixed Podman Devtool container and canonical layer.
2. Apply the smallest primary-dispatch change on the source branch, then use
   the official rebase helper to register one canonical patch.
3. Bundle the committed canonical repository to the fixed Mini receiver.
4. Run the clean recipe gate, component compile, image build, and one QMP-only
   runtime with bounded logs.

## Result

- The official patch was generated from source commit
  `d138e54436a86e6885d52dfb12781ca6ffef8082` and registered as
  `0286-flr0282-attach-primary-production-model-devtool.patch`.
- Mini `do_patch`, `flutter-auto do_compile`, and full image all passed. The
  image completed 11758 tasks with all tasks successful.
- The runtime selected Sequoia as `primary`, loaded 12 renderable entities, and
  reached `SCENE_ADD_DONE model=2 root_entity=59 renderable_entities=12` and
  `ADD_COMPLETE ... in_scene=true child_entities=17`.
- Material tracing reached real production materials including `PaintColor`,
  `Chrome`, `HeadLightGlass`, and `MetalEngine`; color/depth writes were
  enabled on the opaque materials.
- QMP-only frame `primary-model-video/frame-00009.ppm` is 1280x800 with SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
  Against the initial frame it had changed=0, chromatic=0, and max_chroma=0.
  Visual inspection shows the 2D HUD and Scenes button with a black 3D area.
- Draw/present was reached (`BEGIN_FRAME_TRUE=3`, `RENDER_RETURN=3`,
  `END_FRAME=3`, `FLR0026_VK_QUEUE_PRESENT=3`, result=0).
- With the explicit 4096 MiB QEMU allocation, guest memory was
  `MemTotal=4087256 kB`, `MemFree=2993240 kB`, and `MemAvailable=3362328 kB`.
  No OOM-killer, cgroup-memory, or killed-process marker was present.
- QMP teardown passed with `residual_targets=0 residual_qmp=0`.

## Conclusion

The source fix proves and repairs the primary scene-attachment boundary, but it
does not yet prove visible production 3D. The remaining black frame is after
scene attachment and draw/present. This run intentionally skipped skybox,
indirect light, and diagnostic lights; the production materials are
`base_lit_*`, so lighting is now the leading runtime hypothesis. FLR-0283 owns
the minimal lighting-restoration A/B.
