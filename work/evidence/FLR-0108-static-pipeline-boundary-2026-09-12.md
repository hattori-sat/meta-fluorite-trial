# FLR-0108 evidence — static production pipeline boundary (2026-09-12)

## Outcome

The authoritative Mini build metadata and the Mesa 24.0.7 source boundary are
resolved. The next runtime observation can be limited to the production
graphics-pipeline path; no source-semantic change was made.

## Fixed build identity

- Receiver revision: `06bb8bb77fa4c000c8ecb29e69f89d6970675d2f`.
- Machine: `qemux86-64`.
- Distro: `poky-agl`.
- Build role: `$BUILD_DIR`.
- TMPDIR role: `$BUILD_TMPDIR`.
- `flutter-auto`: PV `2.0`, `SRCREV=INVALID` (release/source recipe).
- `filament-vk`: PV `1.65.4`, SRCREV
  `2a86c0c60ecce9443fc34631570e924721b20b40`.
- `mesa`: PV `24.0.7`, `SRCREV=INVALID` (release tarball recipe).

## Effective recipe evidence

Read-only `bitbake-layers show-appends` resolved the project append for
`filament-vk_1.54.3.bb` and both the generic and versioned project appends for
`flutter-auto_2.0.bb`. The relevant effective project patch order is:

1. `filament-vk`: `0163-filament-vulkan-pipeline-creation-trace-devtool.patch`
2. `filament-vk`: `0186-diag-trace-effective-Vulkan-pipeline-inputs-devtool.patch`
3. `filament-vk`: `0187-diag-trace-render-pass-execute-seam-devtool.patch`

The `flutter-auto` append contains the neutral fixture controls and the
production-stage diagnostics, including `0180`–`0187`, `0209`, and `0210`.
The target also resolves `backend-wayland-vulkan` and `filament-view`.

The effective Mesa configuration includes `gallium`, `vulkan`, `wayland`, and
`gallium-llvm`; its dependencies include `llvm`, `llvm-native`,
`vulkan-loader`, and Wayland. This matches the runtime's observed llvmpipe /
lavapipe path.

## Static source boundary

The official Mesa 24.0.7 source tarball in `$DL_DIR` was read without modifying
the source or build tree. The relevant path is:

```text
lvp_CreateGraphicsPipelines
  -> lvp_graphics_pipeline_create
    -> lvp_graphics_pipeline_init
      -> lvp_pipeline_shaders_compile
        -> lvp_shader_compile
          -> lvp_shader_compile_stage
            -> pipe_context->create_{vs,fs,...}_state
              -> Gallium / llvmpipe shader compilation
                -> gallivm_compile_module
```

The source lines establish that `lvp_graphics_pipeline_create()` calls
`lvp_graphics_pipeline_init()` and returns only after
`lvp_pipeline_shaders_compile()` completes for a non-library pipeline. The
shader stage function passes NIR to the Gallium context's stage-specific
`create_*_state` callback. `gallivm_compile_module()` then runs the two LLVM
new-pass-manager sequences: `default<O0>` and the optimized
`sroa,...,instcombine<no-verify-fixpoint>` sequence.

This proves the ownership boundary, not a cause. It does not prove which
production shader, resource, or operation differs from the fixture.

## Facts, inferences, and hypotheses

### Facts

- The pipeline input marker is emitted immediately before Filament calls
  `vkCreateGraphicsPipelines`; its result marker is emitted after the call.
- The RenderPass marker surrounds Filament command execution, not the Mesa
  shader compiler itself.
- The fixture has prior positive evidence with nonzero native pixels and a
  queue-present return; production has prior evidence of native-black output
  and a missing queue-present return in the bounded observation.

### Inferences

- A bounded debugger observation at the production `vkCreateGraphicsPipelines`
  path, followed by the existing render-pass and present markers, can classify
  the first divergence without another LLVM device-initialization breakpoint.

### Hypotheses

1. Production-specific shader/resource inputs block or diverge inside pipeline
   creation before command execution.
2. Pipeline creation returns for production and fixture, and the first
   divergence is later command execution or present ownership.
3. Production rendering completes but composition/occlusion keeps the native
   region black.

## UNKNOWN

- Which pipeline input is production-specific.
- Whether the existing pipeline result marker is reached for the final
  production pipeline in the current image.
- Whether the prior OOPS is causally related to the pipeline path.

## Next observation

Use one QEMU and the fixed image identity. Capture one bounded production
pipeline entry/return with process/thread identity, correlate it with the
existing fixture positive-control markers, capture QMP-only pixels, and stop
through negotiated QMP `quit` followed by residual checks.
