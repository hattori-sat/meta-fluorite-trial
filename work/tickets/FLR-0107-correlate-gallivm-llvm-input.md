# FLR-0107 — correlate Gallivm input with the LLVM fault boundary

- Status: Done
- Priority: High
- Owner: Mesa/llvmpipe + LLVM runtime diagnosis + target-validation roles
- Created: 2026-09-12
- Depends on: [FLR-0106](FLR-0106-capture-llvm-outer-producer.md), [FLR-0104](FLR-0104-runtime-debug-tools.md)
- Working log: `work/logs/2026-09-12-flr0107.md`

## Work unit

Use the proven outer boundary at Mesa's `gallivm_compile_module()` to identify
the expected Gallivm operation, the LLVM input/return contract, and whether
the later `isOrdered+1` OOPS belongs to that operation. This is an evidence
unit only. Do not change renderer semantics or add a workaround until the
invalid input or violated contract is directly demonstrated.

## Success criteria

- Inspect the pinned Mesa 24.0.7 source and symbols around
  `lp_bld_init.c:620` before changing files.
- Use a bounded observation at the Gallivm/LLVM boundary, recording only the
  relevant arguments, return path, thread identity, and marker order.
- Compare at least two explanations: invalid LLVM input/state reaching
  llvmpipe versus an unrelated userspace control-flow/memory fault.
- Preserve QMP-only visual evidence and one-QEMU teardown if a runtime run is
  required.
- Explicitly classify the result as proven, disproven, or UNKNOWN; open a
  separate source-fix ticket if and only if a contract violation is proven.

## Hypotheses

1. Production Sequoia rendering reaches llvmpipe Gallivm with invalid or
   unexpected compiler input. Prediction: the bounded boundary observation
   identifies an input/state difference before `LLVMRunPasses` or a failed
   return that correlates with the OOPS.
2. The `isOrdered+1` OOPS is an unrelated control-flow or memory fault.
   Prediction: the normal Gallivm call has a valid, repeatable entry/return
   contract and the fault has a different thread or state with no direct
   correlation.

## Plan / Do / Check / Act

### Plan

1. Read the pinned Mesa source, recipe/debug-symbol provenance, and the
   existing FLR-0103–0106 logs.
2. Select the smallest static and bounded runtime observations that separate
   the two hypotheses.
3. Capture only those observations, then correlate with the QMP native/HUD
   pixel result.

### Do

- Read the fixed Mini metadata for Mesa 24.0.7, `gallium-llvm`, Vulkan, and
  the fixed DL_DIR. Because `rm_work` removed the expanded source, read the
  exact Mesa 24.0.7 tarball and recipe without changing the build tree.
- Confirmed `gallivm_compile_module()`'s two `LLVMRunPasses` calls and their
  pass strings from the pinned source.
- Reused one fixed image and one QEMU. Captured one Gallivm entry, both
  `LLVMRunPasses` entries, the second call's return path, focused OOPS/process/
  memory evidence, and one QMP frame.

### Check

- PASS: the dynamic stack identifies `lvp_CreateDevice` →
  `llvmpipe_create_texture_handle` → `gallivm_compile_module`, a shared device
  initialization path.
- PASS: `default<O0>` and the expected LLVM 18 optimization pass string were
  observed with the same module/target/options pointers; the second call
  reached the caller's post-call instruction and returned normally.
- PASS: QMP screenshot and pixel analysis are retained. Native region is
  `0/223200`; focused HUD region is `1264/100000`.
- PASS: QMP quit and residual checks reported zero targets and zero sockets.
- UNKNOWN: exact normal-call LWP and whether the later `isOrdered+1` OOPS is
  causally related.
- FAIL: production native 3D remains black; no source fix is justified.

## Visual evidence

- QMP-only PPM: `$RECEIVER/evidence/flr0107-r4/gallivm-boundary-late.ppm`
- SHA-256: `fa62faded438fafc8ef8825ee10e957c6e87a3f7e9594eaffaf2bc357d4f81f8`
- Resolution: `1280x800`; native region `[300,80,620,360]` is
  `0/223200`; focused HUD region is `1264/100000`.
- The HUD is visible, but the central native 3D area is black. The QMP quit
  and residual evidence is in `$RECEIVER/evidence/flr0107-r4/qmp-quit.log`.

### Act

- Closed this Gallivm/LLVM evidence unit without a source or image patch.
- Opened FLR-0108 to isolate the production-specific graphics-pipeline
  boundary.

## UNKNOWN

- Whether the observed module belongs only to shared device initialization or
  is also reused by production scene rendering.
- Whether the later OOPS is caused by the compiler path or is independent.

See `work/evidence/FLR-0107-gallivm-input-correlation-2026-09-12.md` for the
complete static, GDB, runtime, and QMP evidence.
