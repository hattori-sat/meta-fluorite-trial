# FLR-0077 — isolate full production shaded boundary

- Status: Done (default indirect-light attachment falsified as sole cause)
- Priority: High
- Owner: Mini QEMU runtime + source diagnosis roles
- Created: 2026-09-11
- Depends on: [FLR-0076](FLR-0076-isolate-surface-extent-composition.md), [FLR-0067](FLR-0067-reintroduce-production-scene-stages.md)
- Working log: `work/logs/2026-09-11-flr0077.md`

## Work unit

Identify the first production-scene operation that changes the current image
from a visible native 3D control to a black full-scene target. Keep the exact
current rootfs and fixed Mini runtime infrastructure. Start with static source
and existing opt-in runtime controls; do not create a product patch until one
source boundary has a falsifiable prediction.

## Success criteria

- Reuse the fixed receiver, build directory, TMPDIR, shared caches, QEMU
  evidence root, and one QMP-owned QEMU at a time.
- Retain the current-image self-made cube plus 2D HUD as the general render/
  composition positive control and the Sequoia model-only result as the
  production geometry positive control.
- Compare full production stages one variable at a time, prioritising
  material/resource, explicit-light, environment, and output-target boundaries.
- For each control, retain launch identity, selected runtime markers, QMP-only
  frame evidence, candidate-region analysis, runtime-log hash, and QMP teardown.
- If a source change is justified, edit only the existing Mac Devtool source
  workspace and materialise the official layer patch there. Mini remains
  authoritative for `do_patch`, compile, image creation, QEMU, and QMP.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- The exact current rootfs used for the FLR-0077 A/B is
  `$BUILD_TMPDIR/deploy/images/qemux86-64/agl-ivi-image-flutter-qemux86-64.rootfs-20260911015230.ext4`
  with SHA-256
  `87043b0e099eca442a39f4d7b104d4bcfbc79e7f8a54851df78bb5dd93697ed7`.
- Matching qemuboot SHA-256 is
  `353c574ff1ed32a225c6a03ce8ea97e947e9aeaac7471e85426bda1876147dba`;
  matching kernel SHA-256 is
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- The self-made native fixture produced a bright 3D cube and the Fluorite 2D
  HUD in the same final QMP frame. The 3D candidate region changed
  `41750/223200` pixels, and the HUD region changed `6291/100000` pixels.
- The production Sequoia model-only run produced a visible car model in the
  native 3D surface. Its candidate region changed `140034/223200` pixels.
  The native surface masked the parent HUD in this model-only frame, so this is
  a 3D-only positive, not combined composition acceptance.
- Full production scene runs after restoring DEFAULT indirect light still
  reached model/camera/frame/submit/present markers but retained a black
  production candidate region.
- Static source inspection of the current Mac Devtool workspace found that
  `setIndirectLight(DefaultIndirectLight*)` builds a Filament IBL but does not
  register the result with the Scene; the HDR loader in the same component
  does register its IBL.
- The existing Mac Devtool source was changed only for an opt-in diagnostic,
  committed as source commit `e2d2444`, and materialised by official
  `devtool update-recipe --mode patch --append --no-remove` as patch
  `0207-diag-optionally-attach-default-indirect-light-devtool.patch`.
- The registered patch is byte-identical to the official generated output with
  SHA-256
  `3b4d329eb6ccb45d172dfddc99a7e6c463f0b8d3c85a97c2d4cc45405843a123`.
- The existing Podman machine initially stopped immediately after a normal
  start. Keeping its start parent alive allowed the same machine and the same
  Devtool container to run the official update-recipe operation; no duplicate
  machine, container, volume, source tree, build directory, or TMPDIR was
  created.
- Historical FLR-0070 p9 showed one QMP-visible combined condition with the
  native light operation trace, but FLR-0071 and FLR-0072 did not reproduce it
  under the later exact-image/profile runs. It is not a stable product
  baseline.
- The historical p9 evidence is retained at
  `$EVIDENCE_ROOT/flr0070/p9/light-skip126-limit1-optrace/frames/frame-00004.ppm`;
  its final candidate region was `5510/223200` and its HUD region was
  `3961/100000`. The frame SHA-256 is recorded in FLR-0070.
- The reproducible outline-like HUD+Sequoia diagnostic is recorded in
  FLR-0066's `combined-current` evidence. It selected two Sequoia models and
  intentionally suppressed environment/skybox, indirect light, shapes, and
  lights; twelve QMP frames remained at `3290/223200` candidate pixels and
  `3158/100000` HUD pixels. Its final frame SHA-256 was
  `7c9f6c73b9360fa37795d71fe68fc6fd75ae09ebf7e6a4393dd93accedd5479e`.
  This proves a controlled 2D+diagnostic-3D path, not the full shaded scene.
- With the current image, p1 (attach disabled) and p2-corrected (attach
  enabled) both reached the same valid guest launch and QMP capture boundary.
  p1 was `0/223200` in the 3D candidate and `1248/100000` in the HUD; p2 was
  `0/223200` and `1264/100000`, respectively. p2 logged
  `FLR0026_NATIVE_ATTACH_DEFAULT_INDIRECT_LIGHT enabled=true scene=true`,
  model selection, renderable shapes, frame events, Vulkan submit, swapchain,
  and present-boundary markers while the app remained alive.
- The first p2 attempt used an incorrect bundle path and is retained under
  the runtime evidence root as an invalid-launch execution failure. It is not
  used as evidence that attach-enabled rendering stayed black.
- The Mac Podman wrapper was run twice consecutively after the runtime test;
  both runs passed mount/FIFO/xattr checks and reused one machine and one
  persistent container. No second machine, container, volume, build tree, or
  TMPDIR was created.
- Mini currently has one Podman/Devtool-related build workflow and no active
  QEMU, Flutter, or BitBake owner after cleanup. The seven old inactive
  `flr0026-tmp*` work directories were removed; the fixed TMPDIR, caches,
  receiver, and QMP evidence were preserved.

### Inferences

- The general QEMU, Wayland, Vulkan/llvmpipe, native frame/present, QMP
  capture, and at least one composition path are operational in the current
  image.
- The `1280x800` native surface versus `1280x720` Flutter view is an observed
  extent mismatch, but it is not sufficient to explain the black result: the
  current image still renders both the cube/HUD control and model-only car.
- The remaining high-value boundary is downstream of production model loading
  and upstream or at the first full shaded resource/light/output operation.

### Ranked hypotheses

1. A full production material/resource or renderable combination triggers the
   zero-output path. Prediction: model-only remains visible while adding the
   smallest shaded resource stage makes the candidate region zero.
2. An explicit-light operation interacts with the production material/resource
   path under the software Vulkan renderer. Prediction: model plus environment
   remains visible when explicit lights are skipped, while the first selected
   light makes the target zero; a source trace must identify the operation
   before any fix is proposed.
3. Environment/skybox or output-target setup changes the target after geometry
   is valid. Prediction: adding only that stage reproduces black pixels without
   changing model selection or native entity validity.
4. A hidden runtime timing or owner condition remains. Prediction: repeated
   exact-profile controls diverge despite identical image and launch identity;
   this must be demonstrated before treating timing as causal.

### UNKNOWN

- The exact first operation that changes visible production model-only output to
  black full-scene output.
- Whether the current model-only car's dark regions are intended material
  appearance or evidence of incomplete lighting; only the stable visible
  geometry criterion is established.
- Whether a full production 2D+3D state can be reproduced without a diagnostic
  side effect.

## Plan / Do / Check / Act

### Plan

- Inspect the existing Mac Devtool source and recipe patch order around model,
  material/resource, light, environment, and target setup.
- Select the smallest existing runtime-only stage controls and run them on the
  exact current rootfs, one QEMU at a time.
- If static evidence identifies a source operation, make one opt-in diagnostic
  change through Mac Devtool, generate the official patch, then send the exact
  layer commit as a bundle to Mini for authoritative `do_patch` and build gates.

### Do

- Reused the persistent Mac Devtool source workspace and inspected the model,
  environment, light, and indirect-light setup order before editing.
- Added only the opt-in `FLR0026_NATIVE_ATTACH_DEFAULT_INDIRECT_LIGHT`
  diagnostic. When enabled, it attaches the built default IBL to the Scene and
  logs the attachment; when absent, the product path is unchanged.
- Committed the source through the fixed Devtool container as `e2d2444` and
  generated the official split-component patch. Existing generated duplicate
  patches were compared against layer hashes and were not added again.
- Registered only the new patch after 0206 in the existing
  `flutter-auto_2.0.bbappend` patch order and preserved the generated patch
  body unchanged.
- Recorded the machine-start failure and recovery path in the working log;
  the fixed machine/container was then reused successfully.

### Check

- Mac source diff-check passed and the official generated patch matches the
  registered layer copy byte-for-byte.
- Repository verification, Mini `do_patch`, component compile, full image,
  artifact identity, QMP A/B, and teardown all passed. The visual result is a
  negative diagnostic result, not a 3D success claim.
- The opt-in attachment marker and downstream present markers were positive,
  but the required recognizable full-production 3D object remained absent.

### Act

- Keep the current image and patch 0207 as the recorded positive/negative
  baseline. The exact layer commit was bundled to the fixed Mini receiver and
  the runtime evidence was committed.
- Close this ticket and continue in FLR-0078 rather than adding another source
  change here.

### Runtime A/B result

- H1 is falsified as the sole cause. Registering the built default IBL with the
  Filament Scene did not change the full-production 3D candidate from zero,
  despite valid downstream frame/present markers and a live app process.
- The result moves the next boundary to explicit-light/material/resource or
  output-target interaction. The diagnostic patch remains opt-in and is not
  promoted to a product-default behavior by this ticket.

FLR-0077 is complete. The explicit-light Scene attachment/resource boundary is
split to [FLR-0078](FLR-0078-isolate-light-scene-attachment-boundary.md).

## Visual evidence

- Self-made cube plus 2D HUD: `$EVIDENCE_ROOT/flr0076/qmp-control/pure-fixture/frames/frame-00005.ppm`.
  Frame SHA-256:
  `759c6c1c9d6551c010e6f8a80c20a884c78a85a0c591712164f89a9ca85e07e`.
- Production Sequoia model-only: `$EVIDENCE_ROOT/flr0076/model-only/frames/frame-00007.ppm`.
  Frame SHA-256:
  `99d0b78f90b8e49ece4afd18624799729b6c757de88eff146c2bb9d3e0e88690`.
- Selected runtime evidence hashes are recorded in the FLR-0076 log. Both
  runs ended with accepted QMP `quit`, zero QMP sockets, and no runtime owner.
- FLR-0077 p1/p2-corrected QMP evidence is retained outside Git under
  `$QEMU_EVIDENCE_ROOT/flr0077/p1` and
  `$QEMU_EVIDENCE_ROOT/flr0077/p2-corrected`. The p2-corrected selected frame
  SHA-256 is
  `d68b558ac4fc6d4a3b737d883d4a588c4da810f8a0b05cb2da881adfa0e1b64f`.
