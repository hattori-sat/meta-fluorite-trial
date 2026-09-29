# FLR-0154 — isolate native MaterialBuilder color output

- Status: Done (runtime discriminator; branch-entry limitation recorded)
- Priority: High
- Owner: Native fixture MaterialBuilder/shader + Vulkan target-content roles
- Created: 2026-09-14
- Updated: 2026-09-14
- Depends on: [FLR-0153](FLR-0153-align-native-material-instance-api.md), [FLR-0150](FLR-0150-read-native-swapchain-pixels.md)
- Working log: `work/logs/2026-09-14-flr0154.md`

## Work unit

Run one environment-gated native fixture A/B that replaces only the dynamic
`materialParams.color` expression with a known blue shader constant. Keep the
geometry, camera, ViewTarget, Vulkan state, swapchain, Wayland surface, launch
profile, and QEMU observation window unchanged.

## Problem

The native fixture reaches a valid Renderable, full-target viewport/scissor,
color-write-enabled pipeline, indexed draw, queue present, and Wayland child
commit, but the fixed native 3D candidate remains all black in both swapchain
readback and QMP. FLR-0153 explicitly assigned the color to the active
MaterialInstance and produced the same result. Filament source inspection
shows that `createInstance()` duplicates the default instance's uniform buffer,
so the previous API-mismatch explanation is falsified. The next separable
boundary is whether a shader constant can produce fragments through this same
target path.

## Success criteria

- [x] Edit only the persistent Mac Devtool-managed Filament ViewTarget source.
- [x] Generate the official Yocto Devtool patch and copy it unchanged into
  `meta-fluorite-trial` under the existing patch directory.
- [x] Register the patch after the existing native fixture material patch and
  pass Mac `do_patch`.
- [x] Pass Mini `do_patch`, `do_compile`, and the fixed full
  `agl-ivi-image-flutter` build using the existing build/TMPDIR/container.
- [x] Run one QEMU with root serial synchronization, QMP-only screenshot, and
  six-frame video under `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR=1`.
- [x] Compare the fixed 3D candidate against FLR-0153 while confirming the 2D
  HUD remains present and QMP teardown leaves zero target processes and no
  QMP socket.
- [x] If the candidate remains black, retain the negative result and split the
  next source owner into a new ticket; do not broaden this unit.

## Facts

- FLR-0152 and FLR-0153 use the same native minimal geometry fixture and fixed
  QEMU profile. The parent 2D HUD is visible, while the native 3D candidate is
  uniformly black.
- FLR-0152 runtime markers prove the draw admission/state path through
  present; swapchain readback and paired QMP candidate pixels are zero.
- FLR-0153 changed only the native material color assignment from the Material
  default-instance call to explicit `MaterialInstance::setParameter()`. The
  Mini build and QEMU gates passed, but the pixels did not change.
- Filament's checked `FMaterial::createInstance()` implementation copies the
  default instance's uniform buffer when a default material instance exists.
- The source-side diagnostic flag is
  `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR`; it changes only the material
  script's base-color expression for the native minimal fixture.
- The Mac Devtool source branch is `devtool-flr0154-hardcoded-output-base`;
  source commit `3f7c7c9` changes only `view_target.cc`.
- Official `devtool finish --force-patch-refresh` generated
  `0001-diag-add-hardcoded-native-material-color-discriminat.patch`; it was
  copied unchanged as
  `0249-diag-hardcoded-native-material-color-devtool.patch`. Generated and
  canonical SHA-256 are both
  `d960bdb753bfad34414ba3a08cbf13684be1c691df562736c55b25fe6fcb8829`.
- Mac canonical `flutter-auto:do_patch` passed all 104 tasks after finish
  removed the temporary Devtool registration.
- The fixed Mini image was built from canonical commit
  `59f230a3c427031d6517ceb77042c59e6d2d761b`. The rootfs artifact was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260914120911.ext4` with SHA-256
  `dc15117cf43be8bf3a7c9bea042c99e21d41781da773fc0a841c450bca706511`.
- Mini `do_patch`, `do_compile`, and the full image build passed in the fixed
  build directory and existing TMPDIR. The full build completed 11898/11898
  tasks with zero failures; the eight warnings were known forced-task taint
  and `flutter-auto-dbg` build-path QA warnings.
- The QMP-only post-run screenshot is
  `$RECEIVER/evidence/flr0154/qemu/qmp-post-1.ppm`, 1280x800, SHA-256
  `47de1b0b4110ca4f02e7ea1a62f6d40ce7670dbf93763e31b15b9842451d3d09`.
  Its fixed 3D candidate `[300,250,620,400]` contained `248000/248000`
  black pixels, with `changed_pixels=0`, `edge_pixels=0`, and
  `chromatic_pixels=0`.
- The paired QMP video is under `$RECEIVER/evidence/flr0154/qemu/qmp-video-1/`.
  All six frames had the same all-black 3D candidate; the candidate-region
  SHA-256 was
  `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25`.
- The same screenshot's 2D HUD band `[0,0,1280,200]` was non-black:
  `changed_pixels=11751`, `chromatic_pixels=3373`, and `edge_pixels=21230`.
- Serial evidence is retained at
  `$RECEIVER/evidence/flr0154/qemu/serial-exec-1.txt`. It records the native
  geometry contract, effective scene/camera/viewport, color-write mask 15,
  valid shader/layout and vertex-input state, indexed draw count 36, queue
  present, and Wayland child-surface commits. The native readback nevertheless
  reported `nonzero_pixels=0`, `chromatic_pixels=0`, and `byte_sum=0`.
- QMP quit was accepted and cleanup passed with zero residual target processes
  and no QMP socket.

## Inferences

- A chromatic candidate under the hardcoded shader branch would move the first
  zero boundary to the dynamic uniform/material-input path.
- An unchanged all-black candidate with unchanged state markers would move the
  first zero boundary past dynamic material input, toward shader compilation,
  vertex/clip/fragment execution, Vulkan attachment content, or readback.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: dynamic material input or `materialParams.color` is the zero-producing boundary | hardcoded blue shader output produces nonzero chromatic 3D pixels | candidate remains black with the same state markers |
| H2: the zero boundary is after material input, such as shader execution, attachment content, or readback | hardcoded shader output remains black while draw/present/Wayland markers remain valid | candidate becomes chromatic |

UNKNOWN: whether the current launch reached the hardcoded shader-source branch;
the QEMU command set the environment flag and the binary contains the branch,
but this patch did not emit a branch-entry marker. It is also UNKNOWN whether
the current vertex/index buffers contain the expected GPU data or whether the
vertex shader places the cube inside the clip volume.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | native MaterialBuilder fragment base-color source |
| Where | `setupNativeMinimalGeometry()` material builder |
| When | package creation before the first native draw |
| Who | Mac Devtool/source, Mini BitBake/image, QEMU/QMP runtime roles |
| How | one environment-gated shader A/B with fixed image and QEMU profile |

## PDCA

### Plan

1. Reconfirm the current native material source and preserve the FLR-0153
   active-instance assignment as a controlled baseline.
2. Add an environment-gated hardcoded blue shader source, changing no target,
   geometry, camera, compositor, or runtime markers.
3. Generate the official Devtool patch on Mac, register it unchanged in the
   canonical layer, build through the existing Mini bundle/TMPDIR flow, and
   run one QMP-first QEMU loop.
4. Use the pixel result to select the next ticket owner; do not infer a fix
   from draw/present admission alone.

### Do

- The first FLR-0154 `finish` attempt produced no new patch because
  `component-add` had been run after the source commit and therefore selected
  the changed HEAD as its baseline. A retry with `update-recipe --initial-rev`
  also failed to resolve that baseline. Both failures were retained; no
  hand-written patch was accepted.
- Following the Yocto Devtool source flow, the active registration was reset
  without cleaning the source tree. The same source Git was branched at the
  exact FLR-0153 commit `6879a849a874cb741a141e5808a0d8339334e656`, registered
  with `component-add`, edited on the Mac, and committed as `3f7c7c9`.
- Official `devtool finish --force-patch-refresh` then generated the single
  FLR-0154 patch. It was copied byte-for-byte into the canonical patch
  directory and registered immediately after `0248`.

### Check

The generated/canonical patch SHA-256 is
`d960bdb753bfad34414ba3a08cbf13684be1c691df562736c55b25fe6fcb8829`, and
`cmp` passed. Mac canonical `flutter-auto:do_patch` attempted 104 tasks and
all succeeded with no patch-fuzz QA error. Mini `do_patch`, `do_compile`, and
full-image build passed. The QMP screenshot and all six QMP video frames kept
the fixed native candidate black while the HUD stayed non-black. The test
does not support a dynamic-color-only explanation, subject to the branch-entry
UNKNOWN above.

### Act

Close this unit as a recorded discriminator attempt. Do not claim that the
hardcoded shader constant executed until a branch-entry marker is observed.
Split the next source owner into FLR-0155: prove the fixture entry and trace
vertex/index upload, Vulkan buffer binding, and clip-space output before
choosing a code correction.

## Evidence

- [FLR-0153 predecessor](FLR-0153-align-native-material-instance-api.md)
- [FLR-0152 Vulkan state boundary](FLR-0152-trace-vulkan-pipeline-state-contract.md)
- Raw runtime evidence is retained under `$RECEIVER/evidence/flr0154/qemu/`.
- [FLR-0155 next boundary](FLR-0155-trace-native-vertex-upload-and-clip-contract.md)
