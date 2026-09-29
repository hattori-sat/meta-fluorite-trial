# FLR-0102 — instrument the production scene draw seam

- Status: Done
- Priority: High
- Owner: Fluorite production scene/resource boundary
- Created: 2026-09-12
- Depends on: [FLR-0101](FLR-0101-isolate-libllvm-fault-trigger.md), [FLR-0100](FLR-0100-vk-present-return-boundary.md)
- Working log: `work/logs/2026-09-12-flr0102.md`
- Evidence: `work/evidence/FLR-0102-production-scene-draw-seam-2026-09-12.md`

## Work unit

Use the persistent Mac Devtool source and the project-owned
`meta-fluorite-trial` layer to add the smallest neutral, opt-in diagnostic at
the production scene draw/command-recording seam. The purpose is to identify
the last successful operation before the current userspace fault, while
leaving present, fence, semaphore, compositor, scene, and resource semantics
unchanged.

## Success criteria

- Static source mapping identifies the exact scene draw/command-recording seam
  and its caller before any edit.
- The source change is made in the persistent Mac Devtool workspace and
  finished through the official Devtool patch flow.
- The generated patch is registered under `layers/meta-fluorite-trial`, then
  committed locally and transferred to the fixed Mini receiver as a bundle.
- Mini `do_patch`, `do_compile`, and the full image gate pass on the existing
  build/TMPDIR without creating a second container, volume, receiver, or QEMU
  run directory.
- One control and one production run use QMP-only evidence, record marker
  order, native/HUD pixels, hashes, and clean QMP teardown.
- New controls and markers use the neutral `FLUORITE_*` namespace. No new
  `FLR0026` directory, marker, environment variable, or evidence path is
  created.

## Facts

- FLR-0099's fixture returns from queue present and produces native pixels.
- FLR-0100 and FLR-0101 show the recovered production path entering present
  without a retained return marker, while effective model/environment
  reductions do not move that boundary.
- Existing target/present markers begin too late to identify the last successful
  scene command-recording operation.
- Static mapping identifies `RendererUtils` as the caller of
  `RenderPass::Executor::execute`; its backend draw calls reach
  `VulkanDriver::draw2`, and frame completion reaches
  `VulkanSwapChain::present` and `VulkanPlatformSurfaceSwapChain::present`.

## Inferences

- A source seam probe is now more informative than another runtime selector or
  synchronization workaround.
- The probe should be opt-in and observational so the control remains
  semantically comparable with the current production image.

## Hypotheses

1. A production scene draw or command-recording operation leaves an invalid
   state before present. Prediction: the new marker pair stops inside that
   operation in the failing production case while the fixture records both
   sides.
2. The scene draw completes and the fault is introduced by a later common
   operation. Prediction: all scene markers close, moving the next boundary to
   the already-known present/LLVM transition.

## UNKNOWN

- The exact source function and operation that produces the invalid state.
- Whether the eventual fix belongs to the application/Filament path or the
  image's LLVM/Mesa runtime.

## Plan / Do / Check / Act

### Plan

1. Verify canonical repository and current ticket state.
2. Inspect the active persistent Mac Devtool source and map the production
   draw/command-recording call path.
3. Add only bounded `FLUORITE_*` entry/exit markers at the selected seam,
   generate the patch with official Devtool, and register it in the layer.
4. Commit, bundle, transfer, and apply/build on the Mini using the fixed
   receiver/build/TMPDIR.
5. Run one control and one production QMP evidence case, then classify the
   first missing marker.

### Do

1. Verified the canonical repository, one active ticket, existing Podman
   machine/container, fixed bind state, and clean Devtool source baseline.
2. Mapped the production call chain from `RendererUtils` through
   `RenderPass::Executor::execute` to `VulkanDriver::draw2` and the present
   functions.
3. Edited only `filament/src/RenderPass.cpp` in the persistent Mac Devtool
   source. The diagnostic adds opt-in
   `FLUORITE_SCENE_PASS_EXECUTE_BEGIN/END` markers and does not alter draw,
   command, synchronization, or presentation behavior.
4. Created source commit `80b80ad89` through the bounded source-Git wrapper.
5. The first direct official `devtool finish` attempt was retained as a
   failure: the current recipe shape tried to move the workspace recipe to
   the read-only original AGL layer. A second attempt with an initial-revision
   override exposed an unsupported behavior in this fixed Yocto version.
6. Added one repository-owned fixed finish-layer template and reran the
   official `devtool finish --mode patch`. It succeeded. The generated patch
   corresponding to the new source commit is registered as
   `0187-diag-trace-render-pass-execute-seam-devtool.patch`; the generated
   earlier 0186 patch matched the existing layer patch byte-for-byte and was
   not duplicated.

### Check

Mac-side checks passed: Podman status, wrapper syntax, and the existing
Podman mount/reuse contract. The untouched generated patch has SHA-256
`55bd172990f42d2fbd0d10d52af75f5c2a56f9b447775367d56682c09f22d09f`; it is
byte-identical to the fixed finish-layer output. Source status is clean after
finish. The layer commit was bundled to the fixed Mini receiver. Mini
`do_patch`, `do_compile`, and the full image all passed. The fixture produced
`41750/223200` native pixels with bbox `[501,278,278,162]`; production scene
execution emitted BEGIN/END markers but the native region remained `0/223200`
and the guest reproduced the `FEngine::loop` page fault at the queue-present
boundary. QMP-only evidence, marker extraction, and QMP teardown all passed.

### Act

Close FLR-0102 as a diagnostic evidence unit. Do not treat the 0187 marker as
a production fix or claim production 3D success. Continue the goal in a new
ticket for the common post-scene Vulkan/LLVM present boundary.
