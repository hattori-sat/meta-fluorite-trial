# FLR-0074 — isolate explicit-light render-target boundary

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan roles
- Created: 2026-09-11
- Depends on: [FLR-0067](FLR-0067-reintroduce-production-scene-stages.md), [FLR-0073](FLR-0073-compare-pre-0206-image-stack.md)
- Working log: `work/logs/2026-09-11-flr0074.md`

## Work unit

Using the restored current image, compare the already-proven visible
model-only control with the one-explicit-light black condition. Add only the
existing opt-in operation, pipeline, model-stage, and target traces at runtime
to locate the first marker divergence after light setup. This is a runtime-only
ticket: no source edit or new patch is justified until the marker comparison
shows an unobserved boundary.

## Success criteria

- Reuse the fixed Mini receiver, build, TMPDIR, current rootfs, one compositor
  owner, one QEMU, and the QMP-only evidence root.
- Hold Sequoia selection, camera, `DEFAULT` indirect light, skybox skip/clear,
  backend, and launch order constant. Vary only explicit-light participation
  and the already-existing opt-in traces.
- Compare QMP 3D/HUD pixels, selected runtime markers, final frame/runtime
  hashes, and teardown for the visible control and black condition.
- Identify the first differing operation among light registration, material or
  pipeline creation, draw/target selection, submit/present, and composition;
  otherwise record UNKNOWN and the missing evidence.
- If source instrumentation is required, edit the Mac Devtool source and
  generate the official patch there. Mini remains authoritative for
  `do_patch`, BitBake, image creation, QEMU, and QMP validation.
- Do not delete QMP evidence or patches as a response to similar names or
  equal frame hashes. Remove only exact, validated runtime residue outside
  the fixed state and evidence roots.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0066 and FLR-0070 prove that the current image can display the 2D HUD
  together with native 3D under a controlled/model-only or diagnostic path.
- FLR-0067 p6 found the first isolated zero boundary when explicit production
  lights were enabled under fixed `DEFAULT` indirect light and no skybox:
  lights skipped produced `4905/223200`, while lights enabled produced
  `0/223200`.
- FLR-0073 proved that removing 0206 does not restore the black production
  target. The 0206 timing diagnostic is not the cause of that result.
- The current image already contains opt-in markers for native light state,
  model stages, graphics pipeline creation, draw/target execution, and
  submit/present. Their runtime side effects must be separated from the
  no-trace control.

### Ranked hypotheses

1. Explicit light participation changes a material/pipeline or software
   Vulkan/LLVM operation before the production draw reaches a nonzero target.
2. Light participation leaves draw/submit positive but selects or masks a
   different target or attachment.
3. An existing trace changes timing or output; a trace-enabled result alone
   is not causal without a trace-disabled control.

### UNKNOWN

- The first exact operation that turns the production target zero.
- Whether the issue is light data, aggregate resource state, shader/pipeline,
  target attachment, or surface composition.
- Whether the old visible p9 condition can be recovered from complete image and
  launch identity.

## Plan / Do / Check / Act

### Plan

- Confirm the restored Mini rootfs and no residual QEMU before starting.
- Run a bounded sequential matrix: light-skipped control and one-light
  production condition, each once without traces and once with the existing
  trace set.
- Preserve QMP frames, selected markers, hashes, and official teardown before
  selecting the next source or patch ticket.

### Do

- Pending.

### Check

- Pending. Pixel and marker evidence must agree before a causal statement.

### Act

- The first valid discriminator was found before the explicit-light runtime
  operation: the p6 image and the current image do not have the same effective
  production scene source. Open FLR-0075 for a source-generated restoration of
  the DEFAULT indirect-light state. Mini remains authoritative for `do_patch`,
  BitBake, image, QEMU, and QMP validation.

## Result — forced matrix and source-stack correction (2026-09-11)

### Facts

- The corrected four-condition matrix used one QEMU, one fixed current rootfs,
  one compositor owner, `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`, and official
  QMP teardown. All four conditions produced `0/223200` in the 3D candidate
  region. The HUD region was nonzero for p2, p3, and p4, so this was not a
  guest-wide display failure.
- QMP cleanup passed with `residual_targets=0`, `residual_qmp=0`, and the
  socket absent. No QEMU, runqemu, or flutter-auto process remains.
- The matrix condition files requested
  `FLR0026_INDIRECT_LIGHT_TYPE=DEFAULT`, but the runtime logs for p1–p4 all
  emitted `FLR0026_INDIRECT_LIGHT_TYPE=HDR`. The variable is an observation
  path for the deserialized native scene; recording the requested value alone
  did not prove the effective scene type. This matrix is therefore not a
  valid direct reproduction of p6, and is retained as a precondition-miss
  artifact rather than deleted.
- Historical p6 used rootfs SHA-256
  `c8ee1fc3e4e0a467ed642a939120788040fd1dc96bd71f6cc72ebc92d60f37d1`, built
  from `e066ba0`, and logged `INDIRECT_LIGHT_TYPE=DEFAULT` with
  `4905/223200` 3D pixels. The current rootfs uses SHA-256
  `d401ed8ab0e3522e1828ae5688966763284e65aa6a4246e4da3b83879f10d66a` and
  logged `INDIRECT_LIGHT_TYPE=HDR` with `0/223200` pixels.
- The relevant layer-stack difference between `e066ba0` and `a94f877` is the
  deletion of `0001-fix-use-default-indirect-light-for-production-scene.patch`
  and its removal from the demo recipe `SRC_URI`. Patch `0050` changes the
  final `poGetScene()` indirect light from DEFAULT back to HDR; the deleted
  `0001` was the later patch that restored DEFAULT. The current Mini do_patch
  source consequently contains `indirectLight: HdrIndirectLight.asset(...)`.
- This explains the apparent disagreement between p6 and the later current
  image. It is a real image-stack regression candidate, not evidence that
  0206 caused the black result. FLR-0073 already falsified 0206 as the cause.

### Inferences

- The prior visible 2D+3D p6 state was lost by the production indirect-light
  source-stack change, before the explicit-light material/target boundary can
  be compared fairly.
- The next efficient one-variable action is to restore the exact source
  behavior through Mac Devtool and rerun Mini `do_patch`, image build, and QMP.
  A new light/material patch is not justified until that baseline is restored.

### Hypotheses / UNKNOWN

- H1: restoring production DEFAULT indirect light reproduces the p6 visible
  model pixels and may allow the subsequent explicit-light boundary to be
  re-evaluated. This is the leading hypothesis.
- H2: DEFAULT restoration removes the black result but exposes a second
  downstream light/material/target issue. This remains plausible.
- UNKNOWN: whether the p6 result is fully deterministic once the source stack
  and launch identity are matched.

### Check / Act

- **PASS:** runtime logs exposed the requested/effective-condition mismatch;
  source and recipe history identified the exact removed change; QMP evidence
  and teardown are complete.
- **FAIL corrected:** the first p1–p4 matrix omitted the historical force-render
  precondition; the rerun included it but still used HDR because the image
  source stack was not matched. Both process misses are retained in the log.
- **Act:** FLR-0075 owns Mac Devtool source restoration and the authoritative
  Mini validation. Do not delete the existing patches or QMP evidence.
