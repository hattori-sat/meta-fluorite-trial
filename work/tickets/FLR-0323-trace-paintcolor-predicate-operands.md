# FLR-0323 — trace PaintColor predicate operands

- Status: Done
- Priority: High
- Owner: persistent Devtool source Git / production material predicate / Mini runtime roles
- Created: 2026-09-25
- Predecessor: [FLR-0322](FLR-0322-trace-paintcolor-runtime-predicate.md)
- Working log: `work/logs/2026-09-25-flr0323.md`

## Objective

Correct the existing FLR-0317 diagnostic so it reports the asset-name,
material-name, and base-color-parameter operands for every material record. The
current diagnostic hides false values by placing the trace inside the
`material_match` condition. This ticket is diagnostic-only: do not change
Light, camera, Scene attachment, fragment output, or the production material.

## Success criteria

- Edit the persistent `fluorite-plugins` Devtool source Git, commit the source
  change, and generate the layer patch through official `update-recipe`.
- Mini `do_patch`, component compile, and full image pass for the exact layer
  commit.
- One QMP-only runtime run records the complete frame before ROI analysis and
  includes at least one operand record for each Sequoia material instance.
- The result explicitly identifies which operand is true/false, or records
  UNKNOWN if the setupRenderable path is not reached.
- QMP teardown is clean; no production fix is claimed from diagnostics alone.

## Source identity

- Persistent source: `/workspace/state/build/workspace/sources/fluorite-plugins`
- Baseline source commit: `dcd24bcb3a89fe0b7f46bcc44b13910cc6fde251`
- Existing canonical trace patch: `0317-flr0317-trace-paintcolor-override-predicate-devtool.patch`
- Canonical layer: `layers/meta-fluorite-trial`
- Mini remains the authoritative BitBake/image builder.

## Hypotheses

| hypothesis | prediction | falsifier |
| --- | --- | --- |
| material name differs from the printed label | `name_match=false` for the Sequoia record | `name_match=true` |
| asset path does not contain the expected GLB name | `asset_match=false` | `asset_match=true` |
| baseColorFactor is absent | `base_color_parameter=false` | `base_color_parameter=true` |
| all operands are true and pixels still remain black | diagnostic shows all true while native ROI remains zero | nonzero native ROI |

## Plan / PDCA

1. Edit only the diagnostic condition/logging in the persistent Devtool source
   and commit it with the Devtool identity.
2. Regenerate one canonical patch, register it once, and commit the layer.
3. Bundle to the fixed Mini receiver and run progressive build gates.
4. Run the bounded QMP profile, display the full frame, then analyze only the
   fixed native/HUD ROIs and tagged operand slice.
5. Close this ticket and create the next unit before applying a production fix.

## UNKNOWN

- Whether correcting the `const char*` comparison alone restores visible
  Sequoia pixels; that is the next ticket's runtime acceptance test.

## Facts

- The Devtool source edit was committed as
  `b383404e13951f405e6a919a1970b1ea2f528efb` and converted by official
  `update-recipe` into canonical patch SHA-256
  `ea9cbc61e4aa0173e4a8b35d1ab40a8bd3a4d203d2860fdfa41fb1141562ffad`.
- Mini `do_patch`, `do_compile`, and full image passed. The tested rootfs SHA
  is `f7598e5e5336fbba4df5aaca5b93887bb34440a36a502f31fa5c1dae3c219de3`.
- QMP full, late, and all eight video frames were byte-identical with SHA-256
  `9de4a3ebba7e6ce7225684b1b7a8206b60966d04595111a19b2d126e44f2683a`.
  The full QMP frame showed the HUD/CPU/GPU/FPS/Scenes controls, while the
  native 3D candidate remained black.
- Native ROI `(440,220,400,360)` was `0/144000` chromatic with luma `[0,0]`.
  HUD ROI `(1120,0,160,80)` contained `2845` chromatic pixels.
- Runtime emitted `asset_match=true` and `base_color_parameter=true` for
  Sequoia records. For records whose printed `material_name=PaintColor`,
  `material_match=false` was still reported. Scene add, beginFrame, draw
  submit, and present markers were positive.
- The Filament API declares `MaterialInstance::getName()` as `const char*`.
  The existing source compares that pointer with the string literal using
  `materialInstance->getName() == "PaintColor"`; the runtime contradiction is
  consistent with pointer identity comparison rather than string content.
- QMP quit and cleanup passed with zero residual QEMU processes and sockets.

## Inference

- The first actionable source-level fault candidate is the PaintColor name
  comparison, not missing GLB color data, camera selection, Scene insertion,
  frame submission, or QMP/HUD composition. FLR-0324 owns the controlled
  string-content comparison fix and its runtime acceptance test.

## Visual evidence

Recorded: current QMP-only full framebuffer, fixed ROI metrics, bounded
operand log, artifact hashes, and QMP cleanup record. The static user-supplied
Sequoia texture image remains resource evidence, not runtime evidence.
