# FLR-0301 — inspect production primary-model transform and scene ownership

- Status: Waiting
- Priority: High
- Owner: production ModelSystem transform/scene boundary role
- Created: 2026-09-25
- Predecessor: [FLR-0300](FLR-0300-ab-production-culling.md)
- Working log: `work/logs/2026-09-25-flr0301.md`

## Objective

Resolve why the production primary Sequoia path reports valid asset bounds,
materials, scene add, draw, and present but produces no native pixels. Compare
the current `addModelToScene()` root/child/transform contract with the
historical visible model-only path and determine whether a bounded runtime
probe is required for world-space transforms or scene ownership.

## Acceptance gate

Produce a source-backed classification of the first missing contract among:

1. primary model root/child attachment;
2. transform instance, parent, and world-space placement;
3. renderable layer/culling/visibility state;
4. active scene and view layer ownership;
5. draw target visibility.

The classification must cite the current source lines and existing runtime
evidence. If a runtime probe is required, define one minimal opt-in probe
before creating a patch. No production change is allowed in this ticket.

## Result

- Classification complete: the first unobserved contract is the production
  root/child world-space transform and attachment result.
- `addModelToScene()` uses `asset->getRenderableEntities()` for the primary
  renderable list (`model_system.cc:239`) but `assetInstance->getRoot()` for
  the scene root (`model_system.cc:265`). It then rebuilds child parents and
  applies the model root transform (`model_system.cc:319`).
- The production view selects the default scene and `0xff/0xff` visible
  layers (`view_target.cc:792-795`). The diagnostic scene/culling switch is a
  separate path (`view_target.cc:1468-1488`) and was not exercised by
  FLR-0300.
- FLR-0300 proves valid local bounds/materials and draw/present, but not the
  resulting world-space transform or the correspondence between the asset
  renderable list and instance-root hierarchy.
- No product source or generated patch was created.

The next bounded probe is tracked separately in FLR-0302.

## Facts to carry forward

- Current production model is `assets/models/sequoia_ngp.glb`, primary mode,
  `12` renderables, valid material instances, and valid local bounds.
- `scene_default=true`, `scene_native=false` is expected for production.
- QMP native ROI remains black while HUD is healthy and frame/draw/present pass.
- The existing culling control only affects diagnostic scene model insertion.
- Historical FLR-0285-0026f recorded a clipped model-only silhouette under an
  older/effectively different runtime profile.

## Ranked hypotheses

1. Primary model transform/parent application places the renderables outside
   the active camera or target despite valid local bounds.
2. Primary root/child attachment differs from the visible historical path;
   scene add succeeds but the active renderable instances are not the ones
   drawn by the current view.
3. Layer/culling state is valid locally but not visible in the production view;
   this requires a production-path probe, not the diagnostic-only switch.
4. Target content is discarded after draw, though the self-made fixture proves
   the generic target/composition contract.

## UNKNOWN

- Current world-space bounds after `TransformSystem::applyTransform`.
- Whether primary mode's `asset` renderables and `assetInstance` root share the
  same transform/parent hierarchy.
- Whether the historical visible run used the same primary attachment patch.

## Plan / PDCA

- Plan: inspect `ModelSystem::addModelToScene`, `setupRenderable`, transform
  application, view layer masks, and patch history 0285/0286/0294.
- Do: correlate source boundaries with FLR-0300 log bounds/materials and the
  historical model-only evidence; do not start QEMU until the missing probe is
  specified.
- Check: require a falsifiable first-divergence statement.
- Act: open a separate probe or source-fix ticket only after this classification.

## Visual evidence

The predecessor's QMP evidence is retained under
`/mnt/yocto/evidence/flr0300-0001`; no new runtime frame is required until the
source boundary is classified.
