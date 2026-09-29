# FLR-0324 — fix PaintColor string-content comparison

- Status: Done
- Priority: High
- Owner: persistent Devtool source Git / Filament material predicate / Mini runtime roles
- Created: 2026-09-25
- Predecessor: [FLR-0323](FLR-0323-trace-paintcolor-predicate-operands.md)
- Working log: `work/logs/2026-09-25-flr0324.md`

## Objective

Replace the production `MaterialInstance::getName()` pointer comparisons used
by the existing PaintColor diagnostics/overrides with string-content equality.
Keep the scope to the proven predicate: do not change camera, Light, Scene
attachment, render target, or compositor behavior.

## Success criteria

- Edit the persistent Devtool source Git and commit the source change.
- Generate the canonical patch through official `update-recipe`; do not hand-edit
  the patch.
- Mini `do_patch`, component compile, and full image pass for the exact layer tip.
- QMP full-frame evidence shows whether Sequoia native pixels return while HUD
  remains visible. The native ROI must be measured before any interpretation.
- Runtime logs show the PaintColor branch marker if the content comparison is
  effective. QMP teardown must be clean.

## Facts

- Filament declares `MaterialInstance::getName()` as `const char*`.
- The current code compares `materialInstance->getName() == "PaintColor"` in
  the FLR-0315, FLR-0316, and FLR-0317 paths.
- FLR-0323 logged `material_name=PaintColor` with `material_match=false`, while
  `asset_match=true` and `base_color_parameter=true`.
- The current QMP native ROI is uniformly black, but HUD and frame submission
  remain positive.

## Hypotheses

| hypothesis | prediction | falsifier |
| --- | --- | --- |
| pointer identity comparison is the missing branch condition | content equality makes the PaintColor branch marker and override marker appear | markers remain absent with the same material record |
| the branch is fixed but output remains black | override marker appears, but native ROI remains `0/144000` | native ROI becomes chromatic |
| another boundary is still involved | content equality and override marker pass, but QMP remains HUD-only | QMP shows Sequoia pixels |

## Plan / PDCA

1. Create a new Devtool source branch from the FLR-0323 source commit.
2. Replace only the three proven PaintColor name comparisons with content-safe
   equality, then commit the source change.
3. Generate/register one official patch, commit the canonical layer, bundle it
   to Mini, and run the progressive build gates.
4. Run one QMP-first capture with the same 4096 MiB profile and bounded log
   slice. Display the full frame before ROI analysis.
5. Close this ticket only after the runtime result is recorded; open a separate
   ticket for any remaining lighting or composition issue.

## UNKNOWN

- Whether the corrected baseColor parameter reaches the production fragment
  output and visible target. FLR-0325 owns that boundary.

## Results

- Official Devtool patch, Mini `do_patch`, component compile, and full image
  passed for the exact layer commit.
- The corrected runtime emitted
  `FLR0316_PRODUCTION_BASE_COLOR_OVERRIDE_DONE entity=335 primitive=0
  material=PaintColor value=(1,0,1,1)`.
- The corrected predicate reported `material_match=true` for the PaintColor
  records on entities 335 and 358; the asset and base-color parameter operands
  were also true.
- QMP full/late/eight-frame SHA-256 is
  `355f9d5564bd4227ef67aab62036bdd53f4099ee1dd85db3fcec4d24aa90160f`.
  The full frame shows the HUD, but not the vehicle.
- Native ROI `(440,220,400,360)` remains `0/144000` chromatic with luma
  `[0,0]`; HUD ROI remains `2845` chromatic. Scene add, beginFrame, draw
  submit, and present markers remain positive.
- QMP quit and cleanup passed with zero residual QEMU processes and sockets.

## Inference

- The pointer-identity comparison was a real defect and is fixed, but it is not
  sufficient to restore visible Sequoia pixels. The next first-divergence
  boundary is after `setParameter("baseColorFactor", ...)` and before visible
  fragment/target output. No lighting or compositor fix is claimed here.
