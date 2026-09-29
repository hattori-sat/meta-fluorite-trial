# FLR-0316 — inspect PaintColor parameters and self-made light/emissive control

- Status: Done
- Priority: High
- Owner: Filament material contract / self-made control / production comparison roles
- Created: 2026-09-25
- Predecessor: [FLR-0315](FLR-0315-target-production-body-emissive-control.md)
- Working log: `work/logs/2026-09-25-flr0316.md`

## Objective

Recover the known-good reasoning boundary without forgetting the historical
positive result. FLR-0066/0070 show combined Sequoia/HUD frames, while
FLR-0251/0286 show self-made chromatic/lit native geometry with HUD. The
current production frame is HUD-only, so first enumerate the actual Filament
parameters exposed by `PaintColor`, then compare a self-made material/light
control in the same target and composition.

## Success criteria

- Actual `PaintColor` parameter names and values are captured without guessing.
- A self-made emissive or explicitly lit Filament control is visible in the
  same QMP target while HUD remains visible.
- The result distinguishes material parameter absence, light contribution,
  camera/framing, and target composition.
- Any source change uses persistent Mac Devtool, an official generated patch,
  the fixed Mini bundle/build flow, and one QMP-only runtime.
- One QMP screenshot, bounded runtime log, hashes, and cleanup are recorded.

## Facts / hypotheses / UNKNOWN

### Facts

- Production Sequoia reaches Scene add with 12 renderables and 21 materials.
- Body entity 336 primitive 0 is `PaintColor`, `base_lit_opaque`, with color and
  depth writes enabled.
- FLR-0315's emissive predicate did not fire because the material did not
  expose `emissiveFactor` in the observed runtime path.
- The existing runtime parameter trace shows `PaintColor` uses
  `emissiveIndex` (sampler), `baseColorIndex`, `baseColorFactor`, and the
  metallic/roughness/normal/occlusion parameter family.
- Historical combined HUD+Sequoia and self-made lit controls are positive
  baselines and must not be discarded.

### Hypotheses

1. `PaintColor` uses a non-emissive parameter contract; its base-color or
   texture path is the next material boundary.
2. A self-made emissive or explicit-light material can still render in the
   current image; if it does, the production problem is material/asset-specific.
3. If the self-made control also becomes black, the current regression is in
   target/composition or a later runtime change.

### UNKNOWN

- The complete parameter list and values of the runtime `PaintColor` instance.
- Whether a bright `baseColorFactor` override produces visible vehicle pixels
  when the GLB texture/sampler path is bypassed.
- Whether the production GLB texture bindings are valid in the current
  Vulkan/llvmpipe path.
- Whether the historical Sequoia/HUD frame used a different camera, image, or
  source revision than the current production profile.

## Plan / PDCA

### Plan

1. Read the effective source and Filament APIs needed to enumerate material
   parameters; do not add a second diagnostic patch before this boundary is
   known.
2. Add one minimal opt-in trace or self-made control through Mac Devtool only
   if static evidence shows the smallest useful seam.
3. Reuse the fixed Mini receiver/build/TMPDIR and one QMP-only run.

### Do

- Reused the FLR-0315 image and fixed Mini runtime for a second single-QEMU
  trace; no new image or TMPDIR was created.
- Recovered the existing `FLR0306_MODEL_PARAMETER` trace for body entity 336.
  Primitive 0 includes `baseColorIndex`, `baseColorFactor`,
  `metallicFactor`, `roughnessFactor`, `normalIndex`, `aoIndex`, and
  `emissiveIndex`; it does not include `emissiveFactor`.
- Parameter trace SHA-256:
  `af4be81a530e433831dd5f4a240fdf4aafb4d849ce98693d51914e4c2d6eda68`.
- The second QMP teardown also passed with zero residual targets.
- Added the opt-in FLR-0316 `baseColorFactor` diagnostic through the persistent
  Mac Devtool source, generated the official recipe patch, bundled the
  canonical layer, and verified Mini `do_patch`, `do_compile`, and the full
  image build all passed.
- The FLR-0316 QMP run used one QEMU with 4096 MiB and the fixed receiver,
  build, and TMPDIR. QMP screenshot and 12-frame capture completed, followed
  by negotiated QMP quit and zero residual targets.

### Check

The runtime evidence is retained under `$BUILD_RECEIVER/evidence/FLR-0316`.
The QMP frame has SHA-256
`44a2d8ce7711800269beee8b27d60b2f52ea43149156ecf32ce22471b4c706d7`.
The production ROI `(440,220,400,360)` is `0/144000` changed, chromatic, and
edge pixels, with luma `[0,0]`. The HUD ROI `(1120,0,160,80)` contains 2990
changed pixels and 2845 chromatic pixels. The Mac-rendered evidence hashes are
PNG `cdf9ed93408878f92f872242dfd5c9436c565d53fc0a4dc95927540619af7721` and
MP4 `d6e153c2c7e3e2f261cd35c2d4d3870dd2f7d5e1b01f2bd98db8b6b5233d1bd5`.

Runtime classification:

- `FLR0305_PRODUCTION_SCENE_LIGHT_SETUP_DONE=1`.
- Asset load/add completed; 12 renderables and 21 materials were enumerated.
- `FLR0026_SCENE_STAGE_DRAW_SUBMIT=19` and
  `FLUORITE_VIEWTARGET_BEGIN_FRAME_TRUE=19`.
- `FLR0316_PRODUCTION_BASE_COLOR_OVERRIDE_DONE=0`, while the environment
  variable was present in the child process and the binary contained the
  diagnostic string.
- No `ERROR`, `segfault`, `SIGSEGV`, or OOM marker appeared in the bounded
  runtime slice.

Conclusion: the current failure is not yet proven to be HUD/Wayland
composition, camera framing, or Light registration. The known-good HUD path is
alive, while the production Sequoia has no visible pixels. The next boundary
is the exact `PaintColor` predicate/material-parameter condition, split to
FLR-0317.

### Act

The self-made production Light setup and target composition remain positive,
but the requested base-color control did not fire. Do not infer a texture or
composition root cause until FLR-0317 logs each predicate and tests the
known-present `baseColorFactor` contract.
