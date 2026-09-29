# FLR-0320 — trace gltfio texture readiness and emissiveMap binding

- Status: Done
- Priority: High
- Owner: Filament gltfio ResourceLoader / TextureProvider / dependency graph roles
- Created: 2026-09-25
- Predecessor: [FLR-0319](FLR-0319-trace-production-material-texture-binding.md)
- Working log: `work/logs/2026-09-25-flr0320.md`

## Objective

Prove whether the embedded `HeadLights_Emission` texture reaches the
production `HeadLights` material instance before the renderable is submitted.
The accepted static path is:

`GLB image → TextureProvider → ResourceLoader/DependencyGraph →
FFilamentAsset::applyTextureBinding → emissiveMap sampler → draw`.

Do not add a new Light, force body color, or change camera/composition in this
unit. The purpose is to observe the first missing edge in the existing path.

## Success criteria

- Compare two plausible instrumentation locations and select the smallest
  source/recipe boundary that can prove the binding without logging every
  texture or frame.
- If a source change is required, make it in the persistent Mac Devtool
  workspace, commit the source first, and generate the layer patch through the
  official `devtool update-recipe <recipe> --mode patch --append ...
  --no-remove` flow. Do not use a temporary `devtool add` recipe for this
  existing layer recipe.
- Mini `do_patch`, component compile, full image, and artifact hashes are
  recorded before runtime.
- One QMP-only run records the bounded binding marker, native ROI, HUD ROI,
  and cleanup. The known red `HeadLights_Emission` resource hash remains the
  static comparison baseline.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- The deployed GLB contains `HeadLights_Emission` and source/deployed asset
  bytes match.
- Filament gltfio binds `emissiveMap` only after the texture object is ready;
  `emissiveIndex` is an integer UV selector.
- Fluorite waits for global async load progress 1.0 before Scene dispatch, but
  current application markers do not expose the internal binding callback.
- The known-good self-made lit fixture can produce QMP-visible 3D, so the
  generic QMP path is not sufficient to explain this production-only result.

### Candidate approaches

| approach | value | risk / cost |
| --- | --- | --- |
| Add one Fluorite-side marker around asset async completion and Scene dispatch | confirms ordering visible to the app | cannot prove the private gltfio `setParameter` call |
| Instrument the Filament gltfio recipe at `addTextureBinding` and `applyTextureBinding` for `emissiveMap` only | directly proves the suspected edge | requires a separate, carefully scoped recipe patch and build |

Choose the second approach only if the first cannot distinguish the boundary.

### Hypotheses

1. The texture provider creates the embedded PNG, but the dependency graph does
   not apply `emissiveMap` before the renderable is drawn. A binding marker is
   absent or late; a gated timing/order correction may restore the red pixels.
2. `emissiveMap` binding completes before draw, but the production render
   target remains black. Binding markers pass and QMP remains unchanged; the
   problem moves back to draw-to-target/output.
3. The asset is rejected or decoded with a provider error. A bounded error
   marker or provider result will identify it; no speculative color patch is
   allowed.

## Plan / PDCA

### Plan

1. Re-register the existing `filament-vk` recipe, not a temporary `devtool
   add` recipe, using the effective baseline commit.
2. Generate exactly one patch from the diagnostic source commit using official
   `devtool update-recipe`; do not hand-author or hand-edit the patch.
3. Inspect the generated patch and canonical registration before any Mini
   transfer.
4. Use the fixed Mac→bundle→Mini build→one-QEMU/QMP loop.

### Do

Static source boundary selected: `FFilamentAsset::addTextureBinding` and
`FFilamentAsset::applyTextureBinding`, filtered to `emissiveMap` only.

Complete source recovery and source-Git commits are recorded in the working
log. No rendering behavior was changed.

The first full-SHA retry exposed a wrapper defect: the installed Yocto
`devtool update-recipe` rejects the non-standard `--initial-rev <SHA>` option.
The wrapper now uses only the official two/three-argument form; the baseline
is established by `modify` and the source Git history. The workflow document
also distinguishes existing-recipe `modify --no-extract` from split-component
`component-add`. These are process guards; they do not change the runtime.

The Mac recipe gate also now normalizes the user-facing `do_patch` and
`do_configure` inputs to BitBake's `patch` and `configure` task names. The
first gate attempt failed before patch application because the previous wrapper
forwarded `do_patch` literally.

Official patch generation now passes through the corrected existing-recipe
flow. It generated exactly one patch, changing only
`libs/gltfio/src/FilamentAsset.cpp` with 11 additions. The generated patch
SHA-256 is
`053a26a150a4b63eb52f3ca6005616de3cde4db2b46cc32e69dca7dda5309b5e` and the
byte-identical copy is registered as
`layers/meta-fluorite-trial/recipes-graphics/filament/files/0272-diag-trace-gltfio-emissive-binding-devtool.patch`.

The first Mac recipe gate failed before patch application because the wrapper
forwarded `do_patch` literally. After normalization to the `patch` task, the
same gate entered parse but its BitBake control server stopped replying after
more than seven minutes; the client was interrupted once and no residual
process remained. This is a Mac gate harness failure, not a patch-application
failure.

### Check

- PASS: embedded color resource exists independently of runtime Light state.
- PASS: diagnostic source diff is limited to the intended gltfio markers.
- PASS: official Devtool generated exactly one Filament patch from the
  existing recipe baseline; the rejected temporary `filament-vk_2.0.8.bbappend`
  was not copied.
- PASS: Mini `filament-vk do_patch`, component compile, and full
  `agl-ivi-image-flutter` build completed at the exact receiver revision.
- PASS: QMP runtime recorded both gltfio binding stages: `texture_ready=false`
  queued a dependency, then `texture_ready=true` reapplied the queued binding.
  `HeadLights` material entity 358 primitive 2 was present.
- FAIL: QMP native ROI `(440,220,400,360)` remained uniform black
  (`0/144000` changed, `0` chromatic, luma `[0,0]`) while the HUD ROI remained
  visible (`2990` changed, `2845` chromatic).
- PASS: Eight QMP frames were captured and QMP quit/cleanup reported zero
  residual targets and zero QMP sockets.

### Act

Binding is proven. Do not add a Light or change the emissive resource. Continue
with a new ticket for the post-binding vehicle visibility/draw-to-surface
boundary; do not treat the Mac control-server hang as a runtime result.

## Visual evidence

QMP framebuffer: `$EVIDENCE_ROOT/FLR-0320/qemu-emissive/manual.ppm` SHA-256
`e9bf2f8e4b29a30a25d16a78c799d08dd2cd43dea5bc3667cf9c381fdb9702c9`. It shows
the HUD/CPU/GPU/Scenes control and a uniformly black native region. Eight QMP
frames are stored under `$EVIDENCE_ROOT/FLR-0320/qemu-emissive/qmp-frames/`.
