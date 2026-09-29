# FLR-0190 — align MaterialParameter COLOR wire format with current native API

- Status: Done (material contract boundary)
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0188](FLR-0188-compile-and-validate-clean-3d-runtime.md)
- Working log: `work/logs/2026-09-15-flr0190.md`

## Work unit

Correct the `MaterialParameter` COLOR serialization through the persistent Mac
Devtool source workspace, regenerate the canonical Yocto patch with the normal
`devtool update-recipe` flow, and prove the result on Mini before returning to
the QEMU 3D validation loop.

## Problem

The current image reaches `flutter-auto`, Wayland, Vulkan, AOT loading, camera
parsing, and native readiness, but the Example Demo aborts before its first
frame. The runtime error is:

`value must be a EncodableList (name: baseColor, type: COLOR)`

The effective Dart source currently serializes both `MaterialParameter.color`
and `.baseColor` as `Color.toHex()` strings. The effective native
`MaterialParameter::Deserialize` groups COLOR with FLOAT2/FLOAT3/FLOAT4 and
requires an `EncodableList` of four doubles.

## Success criteria

- [x] Record the current source/patch provenance and compare the two contract
  remediation paths.
- [x] Edit only the persistent Mac Devtool source workspace.
- [x] Create one source commit and generate the replacement/current patch using
  official Devtool `update-recipe`; do not hand-author a generated patch.
- [x] Retire the stale 0052 active registration and update the baseline lock
  with deterministic ordering. No replacement patch is active because the
  current upstream source already has the required list representation.
- [x] Verify the source contract and the same-container Devtool generation
  path. Canonical recipe validation is authoritative on Mini.
- [x] Commit the layer/ticket/log changes locally, with no push.
- [x] Send one Git bundle to Mini and prove clean `do_patch`; the corrected
  image build also proves the affected recipe compiles.
- [x] Rebuild the image and rerun the `.ext4` QEMU profile after the gate
  passed.
- [x] Do not call 3D successful until QMP pixels and bounded runtime markers
  prove the app survives material initialization.

## Facts

- Mini receiver `44c88ec1fe69506f561ad09330da05d788eef187` built the current
  image successfully.
- The authoritative current runtime profile is the historical direct
  `bzImage` + `.ext4` profile; WIC.xz/VMDK runs stopped at firmware and are not
  application evidence.
- Run 3 reached AGL login, guest SSH, `agl-driver` Wayland runtime, Vulkan
  llvmpipe, AOT loading, camera parsing, and native readiness.
- Run 3 aborted before the first application frame at the `baseColor` COLOR
  wire-format assertion. QEMU teardown passed with zero residual targets.
- Current effective Dart source sets both COLOR constructors to
  `color.toHex()`.
- Current effective native source requires four-element `EncodableList` values
  for COLOR and FLOAT vector types. `HexToColorFloat4` remains in native source
  but is not used by the current deserializer path.
- The persistent Mac Devtool source branch is `devtool-flr0190-material-color`;
  source commit is `7a81fde7170be147dfd9ea685e98e1e67aeb1ec1`.
- Official Devtool generated a candidate reverse patch with SHA-256
  `c8c70ec00ea7ee627571076561239486759e19cac3f25294774545de31d9755b`.
  It was intentionally not retained because it cannot apply to the original
  source once the stale 0052 patch is removed.
- Mini full-image validation proved that the original source already uses the
  required list representation: adding candidate 0064 after removing 0052
  failed at do_patch because both hunks had no matching string baseline.
- The correct active recipe state is therefore removal of 0052 only. The
  historical 0052 file remains unmodified for provenance and no replacement
  patch is registered.
- Corrected Mini receiver tip is `2ddab094cea058be5dfcb784063acb19fb1aab0d`;
  bundle SHA-256 is
  `b004e7e1a8514592b12b241e0c7e0774ec1f194e895d389c5c16a7054e44b82f`.
- Corrected Mini clean gate is PASS: `workdir-reset=PASS` and `do_patch=PASS`.
- Corrected full image build is PASS: 11,758 tasks attempted and all
  succeeded. The authoritative `.ext4` SHA-256 is
  `d1f0f1d4726cee1bb5b1dc99e34ab845a01319a2d548bffef0625acfe2926b66`.
- The second `.ext4` QEMU run kept `flutter-auto` alive. The bounded runtime
  log is retained on Mini at `evidence/FLR-0191/qemu/runtime.log`; SHA-256 is
  `dc6477056ff565537a2a60a3c00a2f87968006a94f1c31a879e96c7bcff6d665`.
- The log contains `FLR0026_SHAPE_READY` for entities 17–37 and repeated
  `Native is not ready`; there is no `baseColor` exception.
- QMP screenshot `evidence/FLR-0191/qemu/frame-native-not-ready.ppm` has
  SHA-256 `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
  Full-screen analysis found 7,431 non-black HUD pixels; the fixed 3D region
  was 248,000/248,000 black pixels with zero edges and zero chroma.
- QEMU teardown passed with zero residual targets and no QMP socket.

## Inferences

- This is a deterministic Dart/native API contract mismatch before rendering,
  not yet a Wayland composition, camera projection, light, or shader-output
  failure.
- The old 0052 patch was correct for its historical native string contract but
  is stale against the current native list contract after later source changes.

## Hypotheses / alternatives

| Path | Change | Risk | Decision |
| --- | --- | --- | --- |
| A | Remove stale 0052 so the current Dart source keeps its native-compatible RGBA list representation | Smallest canonical change; the base source already has the required contract | Selected |
| B | Add a reverse patch after removing 0052 | Cannot apply because the base source has no string baseline; adds noise | Rejected by Mini do_patch |
| C | Teach native COLOR deserialization to accept both strings and lists | Broader compatibility, but retains a stale contract and expands native risk | Rejected for this unit |

## 4W1H (Why excluded)

| Dimension | Record |
| --- | --- |
| What | Restore the Dart/native COLOR wire contract before 3D rendering |
| Where | `filament_scene/lib/material/material.dart` and the app recipe patch stack |
| When | After FLR-0188 reached the first real app runtime boundary |
| Who | Mac Devtool source role, layer integration role, Mini build/runtime role |
| How | inspect → edit Devtool source → source commit → official patch generation → Mac gate → bundle → Mini gate → QEMU |

## PDCA

### Plan

1. Freeze the existing QEMU evidence and source/patch provenance.
2. Edit the persistent Mac Devtool source to restore the current native list
   contract and create one source commit.
3. Generate the canonical patch using standard Devtool update-recipe, replace
   the stale active registration deterministically, and validate Mac.
4. Bundle the local commit to Mini, run clean recipe gates, rebuild the image,
   and repeat the bounded `.ext4` QEMU launch.

### Do

- Opened after FLR-0188 reached the valid guest/application boundary and
  reproduced the pre-frame material abort.
- Reconnected the existing app source with `modify --no-extract`, created the
  ticket branch `devtool-flr0190-material-color`, edited only
  `packages/filament_scene/lib/material/material.dart`, and committed it
  through the bounded source-Git helper.
- Ran official Devtool `update-recipe --mode patch --append --no-remove
  --force-patch-refresh`; the candidate patch was inspected and rejected as
  inapplicable after the Mini baseline comparison. No generated patch body was
  hand-edited.
- Retired only the stale 0052 active registration and removed the invalid
  candidate from the canonical layer. Refreshed
  `manifests/baseline-sources.lock`.
- The first Mini full-image attempt failed deterministically at do_patch on the
  invalid candidate 0064; its task log is retained outside Git under the
  FLR-0190 evidence directory.

### Check

- Source contract comparison: PASS.
- Source commit and official Devtool candidate generation: PASS.
- Baseline comparison and rejection of the inapplicable candidate: PASS.
- Stale 0052 retirement and baseline refresh: PASS.
- Canonical Mini do_patch after the correction: PASS.
- Corrected image build and QMP runtime: PASS for this material-contract unit;
  the 3D/readiness boundary is split to FLR-0191.

### Act

- Mark this ticket Done as the material-contract unit. The app survives
  material initialization and shows the 2D HUD; FLR-0191 owns the independent
  native-readiness/3D draw boundary.

## UNKNOWN

- Whether the native readiness handshake reaches a positive state.
- Whether the later 3D draw/present path produces pixels.
- Whether light/material and composition remain black after readiness is fixed.
