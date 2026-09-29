# FLR-0127 — isolate the Dart fixture black region after the ViewTarget fix

- Status: Waiting
- Priority: High
- Owner: Mac source and Mini runtime/QMP evidence roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0126](FLR-0126-validate-dart-example-demo-after-viewtarget-fix.md), [FLR-0125](FLR-0125-trace-viewtarget-entry-path.md)
- Working log: `work/logs/2026-09-13-flr0127.md`
- Plan: `docs/superpowers/plans/2026-09-13-flr0127-isolate-dart-fixture-black-region.md`

## Work unit

Identify the first Dart-specific boundary after the proven Shape/Camera/
submit/present markers and before visible QMP pixels. This unit compares the
Dart fixture's material/resource and normal translucent ViewTarget conditions
with the positive native control. It does not claim production Sequoia,
scene-transition, or touch success.

## Success criteria

- Reuse the fixed Devtool/container state, Mini receiver, build/TMPDIR, image
  baseline, and one-QEMU/QMP evidence contract.
- Collect only bounded material, asset, camera, blend/surface, and render-list
  evidence needed to rank the first missing boundary.
- Use at least two falsifiable hypotheses and change one condition at a time.
- If a source change is justified, edit the Devtool source on Mac and generate
  the official untouched patch before the canonical layer commit and Mini
  bundle/build.
- Capture a QMP-only image for every visual A/B and prove negotiated teardown.

## Facts

- FLR-0125's native control produced visible blue geometry, but it enabled the
  diagnostic native scene, an unlit material, and opaque View blend mode.
- FLR-0126's normal Dart path uses a Dart-created Cube with `lit.filamat`, a
  deserialized camera, a default light/indirect light, a transparent swapchain,
  and translucent View blend mode.
- FLR-0126 reached `FLR0026_SHAPE_READY`, Camera enable, Vulkan submit return,
  and present entry, while its QMP 3D region remained uniformly black.
- The fixed image contains `lit.filamat` (SHA-256
  `46f4ec14987cb17fd92238d30b2698b042e8b259f740ab9643e0d05add5ad307`),
  `unlitUV.filamat` (SHA-256
  `21f094083bdc71cd32ca9d4ab591d097ce6549db3cb87b62a91cc2cbc7e1ea12`),
  and `textured_pbr.filamat` (SHA-256
  `8f42dc83947f9ffe196c05f711ca35be7b229183a724783e55103a3383fb759e`).
- The active Dart fixture calls `poGetLitMaterial` for one rotated Cube and
  supplies one default point light plus the default indirect light. The
  existing `poGetUnlitMaterial` helper already points at the packaged
  `unlitUV.filamat` asset.
- The normal native path creates a transparent swapchain and sets the View
  blend mode to `TRANSLUCENT`; only the native diagnostic branch replaces the
  scene and sets the View blend mode to `OPAQUE`.
- The release logger defines `SPDLOG_ACTIVE_LEVEL` as `SPDLOG_LEVEL_OFF` under
  `NDEBUG`, and the inspected source has no runtime log-level setter or
  environment switch. A no-source-change verbose probe is therefore
  unavailable in this image; this is a tooling limitation, not evidence of a
  material failure.
- The first standard `devtool modify` attempt for the Example Demo recipe
  failed during its recipe `do_patch:append`: the function tried to copy
  `${WORKDIR}/pubspec.lock` from a Devtool temporary work directory and
  received `FileNotFoundError`. No Example Demo source workspace was
  registered and no canonical layer file was changed by that attempt.

## Inferences

- The problem is later than ViewTarget request delivery and earlier than
  observable target pixels.
- The missing-file explanation for `lit.filamat` is falsified by the image
  asset hashes, but material load/instance/parameter success is still UNKNOWN
  because the release log path suppresses the detailed status messages.
- The translucent surface contract is the leading candidate because it is the
  condition that differs between the negative Dart run and the positive native
  control; this remains a hypothesis until a one-variable runtime A/B changes
  QMP pixels.
- Camera placement remains a lower-ranked candidate: the Dart fixture camera
  serializes an eye at `(5,0,0)` toward the origin, and the native control
  reused the same deserialized camera contract, but a transform-specific
  runtime observation is still absent.
- The Devtool failure is a separate preparation boundary, not evidence for any
  of the three runtime rendering hypotheses. The documented recovery is to
  import the already patched effective source into the fixed Devtool source
  workspace, commit that as a baseline, and register it with `modify
  --no-extract`.

## Hypotheses

| Hypothesis | Falsifiable prediction | Probe |
| --- | --- | --- |
| H1: Dart lit material/resource path produces no color output | a Dart unlit-only A/B becomes pixel-positive while the surface and camera remain fixed | one source-controlled unlit-material A/B |
| H2: normal translucent ViewTarget hides the Dart buffer | forcing the same Dart scene through an opaque diagnostic condition changes QMP pixels while material markers remain valid | one surface/blend A/B; no compositor rewrite |
| H3: Dart camera/transform places the cube outside the frustum | camera/transform evidence shows an invalid or unexpected eye/target/model transform; correcting only that condition changes the QMP region | bounded camera/transform trace |

## PDCA

### Plan

1. Inspect the exact do-patch source, package assets, and logger controls.
2. If the release logger exposes no runtime level switch, record that
   limitation and do not repeat an identical no-source-change QEMU run.
3. Select one leading hypothesis from the evidence and create a minimal A/B.
4. If the A/B identifies a source boundary, perform the Mac Devtool patch →
   canonical layer commit → Mini bundle/build → QMP loop.

### Do

- Ticket opened after FLR-0126's negative visual gate. No source edit or new
  build has started for FLR-0127.
- Static inspection completed on the fixed Mini build source and staged app
  assets. The assets are present, the Dart fixture's lit/unlit alternatives
  are identified, and the normal-versus-diagnostic View blend difference is
  confirmed.
- The planned no-source-change verbose probe was not run: the release logger
  has no runtime level switch, so it could not distinguish the candidates.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Static boundary map | material, surface, camera candidates | assets, call paths, and blend-mode difference recorded | PASS |
| Verbose Dart probe | first resource/surface divergence | unavailable without a source instrumentation change; limitation recorded | UNKNOWN |
| Example Demo Devtool registration | baseline source workspace available | standard `modify` failed at recipe `do_patch:append` while copying missing `pubspec.lock` | FAIL |
| A/B visual evidence | one-variable QMP comparison | pending | OPEN |
| Teardown | negotiated quit, zero residuals | pending | OPEN |

### Act

- Keep this ticket diagnostic until one Dart-specific boundary is identified.
- The next probe is the unlit-only Dart A/B, with camera, shape, ViewTarget,
  image baseline, and runtime command held constant.
- Recover the source preparation through the fixed workspace and
  `modify --no-extract`; do not alter the generated patch or the recipe task
  merely to hide this failure.
- Split a source fix or a production-scene transition into a new ticket after
  this gate is judged.

## Visual evidence

- Pending. Raw QMP artifacts remain outside Git under the fixed evidence root;
  this ticket will record the run ID, visible result, and checksums.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings:

## Post-run result (2026-09-13)

### Facts

- The current-source Mac Devtool A/B generated official patch
  `0055-diag-compare-Dart-fixture-with-unlit-material-devtool.patch` with
  SHA-256 `85bf6bd689c8d034bb89d4cf8da5d8bcb3c7ba7809d662204b389e8ef5aa6e88`.
  The canonical layer commit is `4d64c50`; the verified Mini receiver used
  for this run was at layer tip `116bbfa`.
- Mini `do_patch`, `do_compile`, and the full `agl-ivi-image-flutter` image
  build all succeeded. The image was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260913012934.ext4`; its SHA-256
  is `b892de4e1054a062af8b52496341bd6f248f3bb07727c2026bc5913ac0431056`.
  The matching kernel SHA-256 is
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  qemuboot SHA-256 is
  `c086efe060503e24ecb816608a90fce9d8c8efe9d59c4a9ff7a08efa9ddec9d7`.
- The one-QEMU run passed preflight, start, and guest-ready. The normal Dart
  launch had one `agl-driver` `flutter-auto` process, no coredump, and reached
  `FLR0026_SHAPE_READY`, Camera enable, Vulkan submit return `0`, and present
  return `0`.
- The QMP-before frame was uniformly black in the fixed region
  `[300,250,620,400]`: `0/248000` changed, edge, and chromatic pixels, with
  region SHA-256 `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25`.
- After replacing only the Dart material with `poGetUnlitMaterial`, both
  early and late QMP frames were uniformly white in the same region:
  `248000/248000` changed pixels, edge `0`, chromatic `0`, luma `[255,255]`,
  and region SHA-256
  `717d9278825ac7a430f917a83eaac27d725b558dcc9992782eca409e46cec1dd`.
  The complete 8-frame QMP sample had one identical PPM SHA-256,
  `2097d8f3aa89cb4083d5414e2636bbd9cf88d6a261844a2d8b9a947554376311`.
- The QMP visual result was a full white frame with no detectable cube,
  edge, chroma, or HUD. This is not accepted as visible 3D geometry.
- One video-capture invocation initially used an unsupported wrapper
  subcommand and failed before capture; the corrected direct QMP capture
  completed. QMP negotiated `quit` was accepted and cleanup reported zero
  residual target processes and zero QMP sockets.

### Inferences

- The unlit A/B falsifies the narrow expectation that changing the material
  alone would reveal a visible cube. It does show a full-frame state change
  from black to white, so the material/resource and surface-composition
  boundaries cannot yet be separated from this result.
- Because the unlit frame is uniform and hides the previously visible 2D HUD,
  the next highest-value one-variable test is the ViewTarget blend mode with
  the Dart fixture returned to its original lit material.

### Check / Act

- Source edit and official patch generation: **PASS**.
- Mini patch/compile/full-image gates: **PASS**.
- QMP A/B collection: **PASS** for boundary evidence; **FAIL** for 3D visual
  acceptance because no geometry indicators were present.
- Teardown: **PASS**; negotiated quit and zero residuals.
- This ticket is now `Waiting`. FLR-0129 owns the next independent test: lit
  Dart material plus a current-source Devtool-generated opaque ViewTarget
  probe.
