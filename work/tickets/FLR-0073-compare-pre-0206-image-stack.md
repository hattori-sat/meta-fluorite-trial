# FLR-0073 — compare pre-0206 image stack

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Yocto build roles
- Created: 2026-09-11
- Depends on: [FLR-0072](FLR-0072-reproduce-p9-trace-visible-condition.md)
- Working log: `work/logs/2026-09-11-flr0073.md`

## Work unit

Determine whether the diagnostic patch introduced in 0206 changes the
full-shaded black result through compile/layout/timing effects even when its
environment variable is absent. Compare the 0206-free layer commit `a0ddaf3`
with the current `a94f877` using the same Mini build/TMPDIR, artifact checks,
guest launch, and QMP trace profile. This is an image-stack comparison; no
source edit or product fix is allowed until the comparison is complete.

## Success criteria

- Reuse the fixed Mini receiver, build directory, TMPDIR, Podman state, and
  QEMU evidence root. Do not create duplicate machines, containers, volumes,
  build trees, or TMPDIRs.
- Transfer the selected layer revision as a Git bundle and record the exact
  receiver revision. Mini remains authoritative for `do_patch`, compile,
  image, and runtime.
- Produce artifact identity for the 0206-free image and run the same explicit
  one-light native-trace profile used by FLR-0071 p3/p4.
- Compare QMP-only 3D/HUD pixels, runtime markers, hashes, and clean teardown
  against FLR-0071's current `a94f877` result.
- Restore the receiver to the current development tip after the comparison;
  record each checkout and build state in the working log.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0071's current `a94f877` image is black in trace-disabled,
  delay-only, and native-state-trace conditions.
- FLR-0072 p4 repeated the native-state trace condition and remained black.
- 0206 is opt-in at runtime, but it changes compiled source around the light
  operation; a default-neutral source flag does not prove binary/timing
  neutrality.

### Hypotheses

1. The 0206-free image is also black; the diagnostic patch is not the source
   of the current failure.
2. The 0206-free image reproduces visible 3D; the diagnostic patch changed
   timing or code generation and is a regression candidate.
3. Both images vary or remain inconclusive; a lower-level production draw or
   target handoff discriminator is required.

### UNKNOWN

- Exact p9 old rootfs contents and whether it corresponds exactly to `a0ddaf3`.
- Whether `a0ddaf3` is sufficient to remove every difference between p9 and
  the current image.

## Plan / Do / Check / Act

### Plan

- Confirm receiver history contains `a0ddaf3` and that only 0206 is removed
  relative to `a94f877` for the layer input.
- Bundle/check out the pre-0206 revision, run progressive Mini gates, build
  one artifact, and execute the fixed QMP profile.
- Restore `a94f877` after the A/B and record the state.

### Do

- Bundled layer revision `a0ddaf39f0bb591f24d0cf23cd4c53a94ceda2a6`
  (0206-free) and checked it out in the fixed Mini receiver. The bundle
  SHA-256 was
  `c0f3f8d0b8e59be6916f5f974b91428a9d60d3c2faf5f1ca3f9b76a365243758`.
- Mini `flutter-auto:do_patch` passed with 104 tasks, `do_compile` passed with
  2686 tasks, and the full `agl-ivi-image-flutter` image passed with 11748
  tasks. The 0206-free rootfs was
  `/mnt/yocto/flr0023-tmp-835a04e-selfinstall/deploy/images/qemux86-64/agl-ivi-image-flutter-qemux86-64.rootfs-20260910222501.ext4`
  with SHA-256
  `92058e6c09455ec4a059377c0aaf6069f46e6a6f4bca15e0779b72f3c03a7077`.
- Ran the fixed one-owner QMP profile against the 0206-free image, restored
  the receiver to `a94f8770c37b8a2fbc0150bd1a14352429e5af24`, and reran the
  same progressive gates. The restored current rootfs was
  `/mnt/yocto/flr0023-tmp-835a04e-selfinstall/deploy/images/qemux86-64/agl-ivi-image-flutter-qemux86-64.rootfs-20260910223553.ext4`
  with SHA-256
  `d401ed8ab0e3522e1828ae5688966763284e65aa6a4246e4da3b83879f10d66a`.
- Used five QMP-only 1280x800 frames for each image with the same
  `FLR0026_NATIVE_LIGHT_OPERATION_TRACE=1` one-light profile. Both image
  runs reached the application, model/light markers, and Vulkan submit/present
  markers, then were closed through the official QMP teardown.

### Check

- The 0206-free final frame was
  `5f30be78bb90b070c39e9cb2eb2bb64507be5501325de11a8fdefd361106bb93` and
  its runtime log was
  `01319e4c90a394ec5d956a02cc884aeda97b498b8afd5b7c9536524773c0e544`.
  The 3D candidate region `[300,80,620,360]` was `0/223200`; the repeated
  region hash was
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- The restored current final frame was
  `0f19754d8bc4841e9f0f8dcc031a39caa03aa44e2dee5e388ec06ef8bd451c89` and
  its runtime log was
  `6f8e8f7622132abb2ea495a9a0af549bb19f3b01d82dd63b23a6db61d0dd6046`.
  Its 3D candidate region was also `0/223200` with the same repeated region
  hash. The 2D HUD changed in both representative frames, so the guest had
  not simply failed to display any surface.
- QMP evidence is retained under
  `/mnt/yocto/flourite-qemux86-64/qemu-evidence/flr0073/pre-0206/qemu-trace`
  and `/mnt/yocto/flourite-qemux86-64/qemu-evidence/flr0073/current-qemu`.
  Both runs recorded accepted QMP `quit`, an absent socket, and zero residual
  `qemu-system`, `runqemu`, and `flutter-auto` processes.

### Act

- H1 is falsified: removing 0206 did not restore the production 3D pixels.
  The observed black output is not a regression introduced by the 0206 timing
  diagnostic.
- The earlier 2D+3D state remains a valid controlled/model-only result from
  FLR-0066 and FLR-0070, but p9's exact old rootfs and complete launch identity
  are unavailable. It cannot be used as a deterministic A/B baseline.
- Close this image-stack comparison without deleting diagnostic patches or
  QMP evidence. Open the next one-variable runtime ticket at the already
  isolated explicit-light/material/render-target boundary; source changes, if
  justified, continue to be edited and patched on Mac Devtool, while Mini is
  authoritative for `do_patch`, BitBake, image, QEMU, and QMP.

## Result

- **Classification:** no 0206-induced regression proven; full production shaded
  output remains unresolved.
- **Known working path:** the same current image can show the 2D HUD together
  with native 3D under the controlled/model-only path.
- **Next boundary:** explicit production-light participation under fixed
  `DEFAULT` indirect light and skybox-skipped conditions, as recorded by
  FLR-0067/FLR-0068. The likely candidates are light/material/resource or
  target handoff operations, not generic Flutter surface visibility.
