# FLR-0322 — trace PaintColor runtime predicate

- Status: Done
- Priority: High
- Owner: persistent Devtool source Git / production PaintColor predicate / Mini runtime roles
- Created: 2026-09-25
- Predecessor: [FLR-0321](FLR-0321-trace-post-binding-vehicle-visibility.md)
- Working log: `work/logs/2026-09-25-flr0322.md`

## Objective

Run the already committed FLR-0317 predicate diagnostic against the current
production Sequoia scene. Do not create a new source change in this ticket.
Register the existing Devtool source commit through the official split-component
`update-recipe` path, build it on the Mini PC, and determine which
`PaintColor` predicate is false when the material is enumerated.

## Success criteria

- The source commit, effective baseline, generated patch, canonical registration,
  and baseline lock are attributable and byte-identical.
- Mini `do_patch`, component compile, and full image gates pass for the exact
  layer tip.
- One QEMU run uses the fixed image/profile and `FLR0317_PAINTCOLOR_PREDICATE_TRACE=1`.
- The complete QMP framebuffer is retained and inspected before ROI analysis.
- Predicate values, production ROI, HUD ROI, image hashes, and QMP teardown are
  recorded. No predicate result is treated as a production fix.

## Source identity and fixed handoff

- Persistent source: `/workspace/state/build/workspace/sources/fluorite-plugins`
- Existing source change commit: `dcd24bcb3a89fe0b7f46bcc44b13910cc6fde251`
- Effective predecessor baseline: `10acc4166a0aff06038ac5622d0bd55c1bfd73a2`
- Existing generated patch: `0317-flr0317-trace-paintcolor-override-predicate-devtool.patch`
- Canonical destination: `layers/meta-fluorite-trial/recipes-graphics/toyota/files/`
- Canonical registration: `flutter-auto_2.0.bbappend`, `patchdir=ivi-homescreen-plugins`
- Mini is the authoritative BitBake/image builder; Mac is source/Devtool/patch handoff only.

## Hypotheses

| hypothesis | prediction | falsifier |
| --- | --- | --- |
| asset path predicate is false | trace shows `asset_match=false` for PaintColor | `asset_match=true` |
| material or parameter predicate is false | trace shows `material_match=false` or `base_color_parameter=false` | all predicates true |
| predicate is true but override/pixels still fail | all predicates are true and the branch marker or ROI remains absent | branch marker and native ROI become nonzero |

## Plan / PDCA

1. Reuse the existing source commit and official `update-recipe` helper; do not
   edit the generated patch.
2. Commit only the canonical patch registration, baseline lock, ticket, and log.
3. Bundle the layer commit to the fixed Mini receiver and run progressive gates.
4. Run one bounded QMP experiment, save/display the whole frame, then inspect
   only the tagged predicate slice and fixed ROIs.
5. Close this ticket with the observed predicate boundary and create the next
   unit before any production fix.

## Do / Check / Act

- Registered the existing Devtool source commit through the official
  split-component `update-recipe` path. The generated patch and held canonical
  patch were byte-identical; the layer commit was `234af586e9bd700324613750bfbd7c5af0ad137a`.
- Mini `do_patch`, `do_compile`, and full `agl-ivi-image-flutter` all passed.
- One 4096 MiB QEMU run used the exact rootfs and the full QMP frame was saved
  before ROI analysis. The native ROI stayed uniform black and the HUD stayed
  visible.
- The runtime environment reached the guest and `FLR0280_MODEL_MATERIAL`
  enumerated `PaintColor`, but no `FLR0317_PAINTCOLOR_PREDICATE` or
  `FLR0316_PRODUCTION_BASE_COLOR_OVERRIDE_DONE` marker appeared.
- Static inspection found the 0317 diagnostic is itself nested under
  `materialInstance->getName() == "PaintColor"`; therefore the missing marker
  does not distinguish a false material predicate from an unvisited branch.
- Decision: close this diagnostic unit as inconclusive at the predicate value
  boundary. FLR-0323 will remove that observation blind spot; this ticket is
  not a production 3D success.

## Visual evidence

Required evidence is a current QMP-only full framebuffer plus its checksum.
The static Sequoia texture atlas supplied by the user is resource evidence and
must not be used as runtime visual evidence.

### 0322 evidence

- Rootfs SHA-256: `c491152d6aaeef203034892ec80468d3557194863262480c69e34114083ec469`.
- Kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP full/late SHA-256: `4fa41ce6f2106c420cdfc1eec419557799284ed74a2128d8a8e1a91eedb66814`.
- Native ROI `(440,220,400,360)`: `0/144000` chromatic, luma `[0,0]`.
- HUD ROI `(1120,0,160,80)`: `2845` chromatic; all eight video frames were
  byte-identical to the full-frame SHA.
- QMP teardown: `qmp=PASS`, `cleanup=PASS residual_targets=0 residual_qmp=0`.
