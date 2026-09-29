# FLR-0302 — probe production Sequoia world transform and root attachment

- Status: Waiting
- Priority: High
- Owner: production ModelSystem transform/scene boundary role
- Created: 2026-09-25
- Predecessor: [FLR-0301](FLR-0301-inspect-production-primary-model-transform.md)
- Working log: `work/logs/2026-09-25-flr0302.md`

## Objective

Observe the first missing production contract without changing rendering
behavior: whether the Sequoia renderable entities are attached to the active
scene with a valid root/child hierarchy and an in-camera world-space
transform.

## Scope

- One opt-in production-path probe only.
- Log the model root entity and a bounded sample of renderable entities.
- Log transform-instance validity, parent entity IDs, world translation/scale,
  and world-space bounds when the Filament API provides them.
- Keep camera, lights, culling, scene selection, blend mode, and draw behavior
  unchanged.
- Produce no permanent production fix in this ticket.

## Success criteria

1. The probe runs on the fixed authoritative image through the normal Mac
   Devtool → patch/bundle → Mini build flow.
2. QMP evidence retains HUD/native ROI counts and a screenshot.
3. The result classifies one of:
   - root/child transform outside the camera;
   - renderables attached to a different/invalid hierarchy;
   - valid in-camera geometry, which moves the investigation to the next
     proven boundary.
4. QEMU exits through QMP and no duplicate runtime remains.

## Current execution result

- Persistent Mac Podman/Devtool contract: PASS; the existing machine and
  container were reused.
- Devtool source commit: `b4f0760e9c54c85b9440eb64b918fbc0fecee35e`.
- Official component rebase/update: PASS.
- Registered patch:
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0297-flr0302-trace-production-world-transform-devtool.patch`
- Patch SHA-256:
  `ecf0ad33843b03cd5546c867b17ef9d5bdb3639130a7096a470fb55aefde2303`
- Mac parent-recipe `do_patch` was attempted and stopped before task execution
  because the fixed container TMPDIR disk monitor reported `0.484GB` free.
  This is not evidence of a patch hunk failure; Mini PC validation is pending.
- At ticket creation no QEMU run or 3D claim had been made; the completed run
  is recorded below.

## Runtime result

- FLR-0303 image built successfully and ran in one 4096 MiB QEMU instance.
- Production Sequoia model=2 reached scene add complete with 12 renderables.
  The root and sampled renderables had valid transform instances and parents;
  the root world translation was `(0,0,0)` and sampled renderables were near
  the expected origin.
- Materials had color/depth write enabled and layer `1`; the production view
  used default Scene and visible layers `0xff/0xff`; draw/present markers
  passed.
- QMP native ROI remained black: `0/144000` changed and `0` chromatic pixels.
- Classification: root/child transform attachment is not the first missing
  contract for this run. Effective camera/frustum and production culling are
  still unobserved. Lighting is not yet isolated.
- QMP evidence directory:
  `/mnt/yocto/evidence/flr0303-0001`.

The next observation is tracked in FLR-0304.

## Hypotheses

1. Primary mode's asset renderable list and instance-root hierarchy may not
   share the expected transform relationship.
2. The model may have a valid local AABB but an unexpected world transform or
   parent relation that places it outside the default camera.
3. If world placement is valid, the remaining issue is later in the native
   render/target path; lighting is not assumed to be the cause until geometry
   is proven visible.

## UNKNOWN

- Exact world-space transform of the current production Sequoia run.
- Exact parent relation for the renderable sample after `addModelToScene()`.
- Whether the historical FLR-0070 visible production run used the same
  primary attachment path.

## Plan / PDCA

- Plan: inspect the available Filament transform/bounds APIs and persistent
  Mac Devtool source workspace before editing.
- Do: add only the opt-in marker and run one bounded QEMU profile.
- Check: compare probe output with FLR-0300's local bounds and QMP ROI.
- Act: either open a minimal fix ticket for the proven contract divergence or
  advance to the next boundary with a clean evidence record.

## Evidence baseline

- FLR-0300 log SHA: `bfb1edc6e9e31f89c83e7a3158f27c002eb5df1c98531d1bf2d8464b49fd53ff`
- FLR-0300 frame SHA: `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`
- Historical self-made lit fixture + HUD: FLR-0286 frame SHA
  `42b731f4f71956f7d20e73e19bc72289f0a27c665ba23964e227333f70425e24`
