# FLR-0153 — align native fixture MaterialInstance parameter API

- Status: Done
- Priority: High
- Owner: Native fixture material + Filament MaterialInstance runtime roles
- Created: 2026-09-14
- Updated: 2026-09-14
- Depends on: [FLR-0152](FLR-0152-trace-vulkan-pipeline-state-contract.md), [FLR-0149](FLR-0149-trace-filament-draw-to-target-contract.md)
- Working log: `work/logs/2026-09-14-flr0153.md`

## Work unit

Align the native diagnostic fixture's declared material parameter with the
MaterialInstance actually bound to its Renderable. Change only the color-value
assignment; keep the scene, camera, geometry, ViewTarget, swapchain, present,
Wayland, and QEMU profile unchanged.

## Problem

The native fixture declares `color` in `MaterialBuilder` and uses
`materialParams.color` in the material script. It then calls
`native_diagnostic_material_->setDefaultParameter("color", ...)`, which the
Filament API documents as writing `Material::getDefaultInstance()`. The code
subsequently creates `native_diagnostic_material_instance_` with
`createInstance()` and binds that separate instance to the Renderable. The
active instance therefore has no explicit color assignment. FLR-0152 proved
that viewport, scissor, color-write mask, program handles, vertex input,
indexed draw, present, and Wayland commit are valid while the native 3D QMP
region remains black.

## Success criteria

- [x] Edit only the persistent Mac Devtool-managed Filament ViewTarget source.
- [x] Generate the official Yocto Devtool patch and copy it unchanged into
  `meta-fluorite-trial` under the existing patch directory.
- [x] Pass Mac `do_patch`, Mini `do_patch`, `do_compile`, and the fixed full
  `agl-ivi-image-flutter` build using the existing build/TMPDIR/container.
- [x] Run one QEMU with root serial synchronization, QMP-only screenshot, and
  six-frame video; prove the fixed 3D candidate region becomes nonzero and
  chromatic, or retain the unchanged black result as a falsified API
  discriminator.
- [x] Confirm the 2D HUD remains present and QMP teardown leaves zero target
  processes and no QMP socket.
- [x] If the region remains black, retain the result and split the next
  source owner into a new ticket; do not silently broaden this unit.

## Facts

- FLR-0139 is the historical positive control: the self-made Dart Cube became
  visible after the packaged textured unlit material bound `baseMap`.
- FLR-0152 is the native fixture control: the Renderable has one primitive,
  eight vertices, 36 indices, a valid full-target Vulkan state, and successful
  present, but the 3D candidate region is zero in both swapchain readback and
  QMP.
- `Material::setDefaultParameter()` writes the Material's default instance.
  Filament's checked `FMaterial::createInstance()` implementation duplicates
  that default instance when it exists, including its uniform buffer, before
  returning the Renderable-bound instance. The initial API-mismatch hypothesis
  was therefore incorrect.

- The Mac Devtool source branch is `devtool-flr0153-material-instance-api`;
  source commit `6879a84` changes only `view_target.cc`.
- Official `devtool finish --force-patch-refresh` generated the patch copied
  unchanged as `0248-fix-native-fixture-color-on-active-material-instance-devtool.patch`.
  Generated and canonical SHA-256 are both
  `9c7d158b04421d565bd2be961f86d566b2b487cae305a018785f1dade86b7b69`.
- After finish moved the component out of the Devtool workspace,
  `devtool-status` reported no registered recipes and Mac
  `flutter-auto:do_patch` passed all 104 tasks using the canonical recipe.

## Inferences

- The explicit active-instance assignment is behavior-equivalent to the
  original default-instance assignment for this MaterialBuilder path.
- Because the QMP candidate stayed black with unchanged draw/present state, the
  next useful discriminator must bypass the dynamic material uniform while
  keeping geometry, camera, target, and compositor unchanged.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: the active MaterialInstance has no explicit color value | setting `color` on the created instance produces nonzero blue 3D pixels | **Falsified:** candidate remained black with the same state |
| H2: dynamic material output is black for another shader/attachment reason | explicit instance assignment does not change the QMP candidate | **Selected for FLR-0154:** hardcoded shader output remains black |

UNKNOWN: whether explicit instance assignment alone is sufficient to produce
fragments; FLR-0152 did not trace the uniform contents or fragment output.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | active MaterialInstance color parameter |
| Where | native fixture `setupNativeMinimalGeometry()` before Renderable binding |
| When | after `createInstance()`, before the first native draw |
| Who | Mac Devtool/source, Mini BitBake/image, QEMU/QMP runtime roles |
| How | one official Devtool patch, fixed build/TMPDIR, one QEMU A/B |

## PDCA

### Plan

1. Reconfirm the Material default-instance versus created-instance API from the
   checked-in Filament headers.
2. Add the smallest source change that assigns the existing blue value to the
   Renderable-bound MaterialInstance.
3. Generate the official Devtool patch on Mac, register it unchanged in the
   canonical layer, run Mac and Mini progressive/full-image gates, and run
   one QMP-first QEMU loop.
4. Compare the fixed 3D region and unchanged state markers; close this unit or
   split the next owner.

### Do

The persistent Mac Devtool source was switched to
`devtool-flr0153-material-instance-api`. The source edit replaces the
Material default-instance call with `createInstance()` followed by
`MaterialInstance::setParameter("color", RgbType::LINEAR, ...)`. The official
finish patch was copied byte-for-byte into the canonical Toyota recipe patch
directory and registered after the existing ViewTarget patch stack. The Mac
recipe gate passed after confirming that no Devtool externalsrc registration
remained.

### Check

The Mini progressive and full-image builds passed on the fixed build/TMPDIR,
and the accepted QEMU run retained the 2D HUD but showed zero chromatic and
zero changed pixels in the fixed native 3D candidate region. The six video
frames matched that result. Runtime markers still showed valid render area,
viewport/scissor, color-write mask, shader/layout handles, vertex input,
indexed draw, queue present, and Wayland child commits. Filament source
inspection then showed that `createInstance()` duplicates the default instance
uniform buffer, so the proposed API mismatch is falsified.

### Act

Close this unit as a negative API discriminator. Any additional camera, scene,
shader, attachment, or compositor change requires a new ticket; FLR-0154 owns
the next hardcoded shader-output test.

## Evidence

- FLR-0152 state/API evidence: `work/tickets/FLR-0152-trace-vulkan-pipeline-state-contract.md`.
- Raw runtime evidence will be retained under `$RECEIVER/evidence/flr0153/qemu/`
  and summarized here after the accepted run.
