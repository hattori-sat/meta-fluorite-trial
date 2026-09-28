# FLR-0071 — separate trace timing side effect

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan roles
- Created: 2026-09-11
- Depends on: [FLR-0070](FLR-0070-trace-explicit-light-operation.md)
- Working log: `work/logs/2026-09-11-flr0071.md`

## Work unit

Determine whether p9's visible 3D result is caused by a timing/synchronization
side effect of the native-state trace or by the native-state reads themselves.
Add one opt-in diagnostic control in the existing Mac Devtool source workspace:
a bounded delay at the same post-`BuildLightAndAddToScene` boundary, without
calling native state getters and without changing the default path. Generate
the layer patch through the documented Yocto Devtool lifecycle, then let the
Mini PC apply and validate it.

## Success criteria

- Use the existing Mac Podman/Devtool source workspace and one active
  operation; do not create a new container, machine, volume, source tree,
  build directory, or TMPDIR.
- Edit source only in the Devtool-managed source workspace. Create the patch
  with the official Devtool command; do not hand-edit a generated patch.
- Register the untouched generated patch under `meta-fluorite-trial`, commit
  the layer change locally, and transfer that exact commit as a Git bundle to
  the fixed Mini receiver.
- On Mini, pass the progressive `do_patch`, component compile, and image gates
  before QEMU. Mini is authoritative for those gates.
- Compare three runtime conditions on the same image/profile where possible:
  trace disabled, timing-only diagnostic enabled, and native-state trace
  enabled. Use one QEMU owner and QMP-only screenshots.
- Record 3D/HUD pixel counts, bounding boxes, frame/runtime hashes, selected
  markers, image identity, and clean QMP teardown for every condition.
- The default path remains unchanged when the new environment variable is
  absent.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0070 p9 reported valid native light state and visible QMP 3D pixels only
  when `FLR0026_NATIVE_LIGHT_OPERATION_TRACE` was enabled.
- FLR-0069 p8 used the same one-light profile without the trace and remained
  black in the 3D candidate region.
- The existing trace performs native state reads after
  `BuildLightAndAddToScene`; it is diagnostic and is not a product fix.
- The fixed Podman wrapper reported the Devtool source clean before editing.
- The source commit `6b3597d` contains only the opt-in delay control in
  `light_system.cc`; its default path is unchanged.
- A first official `update-recipe` attempt with `--initial-rev 32ddefc`
  returned exit 0 but produced no patch. This was treated as an inconclusive
  Devtool baseline error, not as a successful handoff.
- Source history showed the correct imported effective-source baseline was
  `32f4fab`, followed by the existing `32ddefc` diagnostic commit and the new
  `6b3597d` commit.
- The standard official `update-recipe --mode patch --append --no-remove`
  generated an existing 0205-equivalent patch and new patch
  `0002-diag-isolate-post-light-operation-timing.patch`. The existing output
  was byte-identical to layer patch 0205 and was not copied as a duplicate.
- The new generated patch was copied unchanged to
  `0206-diag-isolate-post-light-operation-timing-devtool.patch` and registered
  after 0205 in the `flutter-auto` append. Its SHA-256 is
  `1f5a91a9003ab0c855c91bbe449bf6e3c4663c200781bed3fef2a117accb08ad`.

### Ranked hypotheses

1. H1 — timing/order is the cause. Prediction: a delay-only control can make
   the model visible without any native-state query.
2. H2 — one of the native-state reads has a synchronization or lazy-init side
   effect. Prediction: delay-only stays black while the existing trace remains
   visible.
3. H3 — p8/p9 differ in an unobserved runtime condition. Prediction: repeated
   no-trace and trace runs under the same image will not preserve the p8/p9
   separation.

### UNKNOWN

- The correct delay location and safe bounded duration must be confirmed from
  the Devtool source, not guessed from the generated patch.
- The downstream operation affected by the trace is not yet identified.
- A diagnostic delay that restores pixels would establish a timing boundary,
  not a production fix.

## Plan / Do / Check / Act

### Plan

- Inspect the existing Devtool source, recipe patch order, and Yocto Devtool
  command availability before editing.
- Add only the opt-in delay control in the Mac Devtool source and generate the
  official patch.
- Bundle the layer commit to Mini and validate progressively.

### Do

- Added the bounded source-Git status, diff-check, and file-scoped commit
  operations to the fixed Podman wrapper because host Git cannot resolve the
  container-path alternates safely.
- Edited the existing Mac Devtool source workspace only. The delay is enabled
  only by `FLR0026_NATIVE_LIGHT_OPERATION_DELAY_US`, uses a bounded range of
  1..1,000,000 microseconds, and is placed after `AddLightToScene` without
  native state reads.
- Ran wrapper diff-check and committed the source as `6b3597d diag: isolate
  post-light operation timing`.
- Corrected the Devtool baseline after the no-output attempt and reran the
  official standard `update-recipe` flow.
- Copied the untouched generated patch into `meta-fluorite-trial` and
  registered it in recipe order.

### Check

- Mac source diff-check and source commit completed in the fixed wrapper.
- Existing 0205 output and layer file have identical SHA-256; no duplicate was
  added. New 0206 output and layer file have identical SHA-256.
- Mini authoritative `do_patch`, component compile, full image, and artifact
  identity all passed for receiver revision
  `a94f8770c37b8a2fbc0150bd1a14352429e5af24`.
- The new rootfs is
  `/mnt/yocto/flr0023-tmp-835a04e-selfinstall/deploy/images/qemux86-64/agl-ivi-image-flutter-qemux86-64.rootfs-20260910213934.ext4`
  with SHA-256
  `0d8df09ac176eaf4c301fb6761ee2a50843f4d27ae49c602eed63dababb08a4f`.
- Three sequential QMP-only runs used the same rootfs, fixed runqemu profile,
  guest bundle, and `agl-driver` launch. Each reached `Application Id`, model
  scene/light markers, and successful Vulkan submit/present. The 3D candidate
  region was `[300,80,620,360]`; all 5 frames in all three conditions had
  `0/223200` changed pixels and region SHA-256
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- p1 trace-disabled final frame SHA-256 is
  `b9e77d697d3c167df3f93078c73355800509ba616bc80eb9648857d154a2ffad` and
  runtime log SHA-256 is
  `88763ece330c1f0d726e55e2f43617ac40d81465d515cde66d35106b87f2aa9c`.
  HUD changed `585/100000` pixels in the representative final frame.
- p2 delay-only (`FLR0026_NATIVE_LIGHT_OPERATION_DELAY_US=10000`) final frame
  SHA-256 is
  `6323b6b477d984d8c9267170eb3ab392ae24ea8bf26f907179d2b16cc9675d90` and
  runtime log SHA-256 is
  `06879270abdc89a218de7c374084e2cb1f056398bdc4efd4c897dd55fd1f27b9`.
  The log contains matching delay begin/done markers; HUD changed
  `845/100000` pixels.
- p3 native-state trace final frame SHA-256 is
  `72ff078c18fe475f076b2862f69fb33e8254e7749fe8a5ddf172f9cd0a27a410` and
  runtime log SHA-256 is
  `168c75f7246cc3d876aba071df0f34fa040b3d77acf4cd4601f5f987e48b11ca`.
  The log contains
  `native_entity=5 light_component=true instance_valid=true
  scene_has_entity=true scene_light_count=1`; HUD changed `760/100000`
  pixels.
- p1/p2/p3 evidence directories are respectively
  `/mnt/yocto/flourite-qemux86-64/qemu-evidence/flr0071/p1`, `p2`, and `p3`.
  Each run ended with official QMP `quit`, absent QMP socket, and zero
  residual `qemu-system`, `runqemu`, and `flutter-auto` processes.

### Act

- Next action is to commit the layer registration and wrapper improvement,
  send the exact tip as a bundle to Mini, and run the progressive Mini gates.
- If delay-only reproduces visibility, split the next ticket at the first
  timing/order boundary and remove or replace the diagnostic delay before any
  product fix.
- If only the native trace reproduces visibility, split the next ticket at the
  specific getter/lazy-state boundary; do not ship the trace as a fix.
- If the A/B separation disappears, reopen reproducibility analysis in a new
  ticket with the exact image and runtime identities.

### Result

- H1 is not supported: the 10ms delay-only condition stayed black.
- H2 is not established: the native-state trace also stayed black on the new
  image, although it again proved valid native registration state.
- H3 is supported: p9's earlier visible result was not reproduced under this
  exact image/profile/launch sequence. The p9 effect remains an
  unobserved-condition or nondeterministic-runtime observation, not a product
  fix. The reproducibility work is split into FLR-0072.

## Visual evidence

- QMP-only frame series and runtime logs are retained outside Git under the
  three evidence directories named above. Representative analyses are
  `analysis-3d-series.txt` and `analysis-hud.txt` in each run.
- This ticket does not claim a 3D success. It proves a clean three-condition
  negative comparison on the new image and keeps the earlier p9 positive as
  non-reproduced evidence.
