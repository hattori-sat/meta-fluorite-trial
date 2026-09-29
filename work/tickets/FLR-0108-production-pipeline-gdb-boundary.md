# FLR-0108 — isolate the production graphics-pipeline boundary

- Status: Done
- Priority: High
- Owner: Filament/Vulkan pipeline + Mesa/lavapipe + target-validation roles
- Created: 2026-09-12
- Depends on: [FLR-0107](FLR-0107-correlate-gallivm-llvm-input.md), [FLR-0099](FLR-0099-draw-to-native-output-boundary.md)
- Working log: `work/logs/2026-09-12-flr0108.md`

## Work unit

Trace the first production-specific graphics-pipeline operation after the
shared Vulkan device-initialization path. Compare the existing self-made
fixture positive control with the production Example Demo at
`vkCreateGraphicsPipelines`, command execution, and present ownership. Use a
bounded debugger or the existing neutral pipeline markers; do not change
renderer semantics until the first divergent operation is directly proven.

## Success criteria

- Read the resolved Flutter/Filament recipe patch order and the Mesa/lavapipe
  source boundary before changing files.
- Capture a bounded production pipeline entry/return or a precise blocked
  boundary, including the relevant thread/process and marker order.
- Correlate the result with the existing same-image fixture evidence, where
  native pixels are nonzero and queue-present returns.
- Preserve QMP-only visual evidence, fixed image identity, and one-QEMU clean
  teardown for any new runtime run.
- Classify the first divergence as pipeline creation, command execution, or
  present/WSI; create a separate source-fix ticket only after the expected
  operation and violated contract are proven.

## Hypotheses

1. Production-specific pipeline inputs or shader/resource layout stop the
   pipeline worker before the fixture's successful draw/present path.
2. Pipeline creation returns successfully for both cases, and the first
   divergence is later command execution or present ownership.
3. The native-black result is an unrelated composition/occlusion issue while
   the production pipeline completes; QMP pixels will remain black despite
   successful native submits.

## Plan / Do / Check / Act

### Plan

1. Inspect the current Flutter/Filament patch order, pipeline markers, and
   Mesa/lavapipe source symbols.
2. Choose one bounded production pipeline observation and reuse the existing
   fixture evidence as the positive comparison.
3. Capture QMP pixels and marker/process evidence, then select the next
   independent ticket.

### Do

- Static source/metadata inspection: PASS. The fixed Mini metadata resolves
  `flutter-auto` 2.0, `filament-vk` 1.65.4, and Mesa 24.0.7. Filament's
  effective order includes `0163` → `0186` → `0187`; the Flutter append
  includes the production-stage diagnostics and neutral fixture controls.
  Evidence: `work/evidence/FLR-0108-static-pipeline-boundary-2026-09-12.md`.
- Mesa's static path is resolved as
  `lvp_CreateGraphicsPipelines` → `lvp_graphics_pipeline_create` →
  `lvp_graphics_pipeline_init` → `lvp_pipeline_shaders_compile` →
  `lvp_shader_compile_stage` → Gallium `create_*_state` →
  `gallivm_compile_module`.
- Bounded production pipeline observation: PASS. `lvp_CreateGraphicsPipelines`
  was entered and returned normally in GDB. All six effective production
  pipeline-create markers returned `result=0`, and selected RenderPass
  begin/end markers were paired. The first missing operation was the
  queue-present return/WSI handoff. Evidence:
  `work/evidence/FLR-0108-production-pipeline-boundary-2026-09-12.md`.

### Check

- Static gate: PASS. The resolved patch order and the relevant Mesa/lavapipe
  source ownership are recorded before any source change.
- Runtime gate: PASS for bounded observation, QMP-only capture, and clean
  teardown. Native output remains `0/223200`; this ticket does not claim a 3D
  fix.

### Act

- Close FLR-0108 as a diagnostic unit. The pipeline-create hypothesis is
  rejected for this run; continue with a separate present/WSI owner and OOPS
  causality ticket. Do not create a source-fix patch until that contract is
  directly proven.

## UNKNOWN

- Exact production pipeline input difference from the positive fixture.
- Whether any later OOPS is causally related to pipeline creation.
- The exact owner and syscall state of the missing queue-present return.
