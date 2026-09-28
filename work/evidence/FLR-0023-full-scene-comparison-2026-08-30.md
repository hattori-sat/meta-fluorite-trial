# FLR-0023 — full-scene comparison boundary

## Scope

This record compares the existing probe-free full-scene clean-branch runtime
with the new self-made minimal-fixture runtime. The comparison is intentionally
stage-based: successful startup or Filament initialization is not treated as
proof of visible 3D content.

## Full-scene clean-branch reference

- Repository-safe reference: `work/evidence/FLR-0023-full-scene-reference-2026-08-23.md`
- QEMU profile: qemux86-64, q35, 2048 MiB, 12 vCPU, TCG, virtio-vga,
  snapshot disk
- Rootfs SHA-256:
  `e218933d1c666566596094375ed6996a3d23b4e871137fa3bb57b296bd055cfc`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`

Observed in the full-scene reference:

- AGL boot, compositor, Wayland session, Vulkan, llvmpipe, Filament
  initialization, and swapchain creation: PASS.
- Dynamic 2D overlay values changed, and the Scenes menu showed Playground,
  Radar, Settings, Planetarium, and Trainset: PASS.
- The 3D region remained black at startup. After selecting Playground, the
  runtime entered a long processing state, later returned with `FPS: 0`, and
  ultimately became all white while QEMU remained alive: 3D scene acceptance
  FAIL.

## Minimal-fixture r12/r13 reference

- Source evidence: `work/evidence/FLR-0023-qemu-r12-runtime-2026-08-30.md`
- The built AOT payload contains `flr0023_fixture_cube` and
  `poGetMinimal3dFixtureScene`: fixture inclusion PASS.
- AGL boot, Vulkan/Wayland initialization, llvmpipe selection, Filament
  initialization, and `lit.filamat` loading: observed.
- `flutter-auto` then exits with status 139 before native
  entity/renderable/frame-completion evidence and before a visible 3D frame.
  The QEMU window remains black: runtime display FAIL for this session.
- The final r13 revision was rebuilt and rerun after the QEMU-only quality
  scope correction. It reproduced the same post-`lit.filamat` status-139
  boundary, so the comparison is not dependent on the pre-review revision.

## Boundary comparison

| Boundary | Full-scene clean reference | Minimal fixture r12 | Interpretation |
| --- | --- | --- | --- |
| Image/package inclusion | PASS | PASS | The fixture is present in the AOT payload. |
| Boot and graphical session | PASS | PASS | Not the differentiating failure. |
| Vulkan/Wayland and Filament init | PASS | observed | Both reach the renderer setup boundary. |
| Recurring 2D frame path | PASS at startup | UNKNOWN after crash | r12 terminates before this can be accepted. |
| Native entity/renderable/frame completion | UNKNOWN | UNKNOWN | Neither runtime proves this ordered boundary. |
| Child Wayland attach/commit | UNKNOWN | UNKNOWN | No child-surface protocol evidence is available. |
| Visible 3D pixel change | FAIL | FAIL | The self-made fixture did not isolate a passing display path. |

## Conclusion

The released/full-scene path is not proven to display 3D even when its startup
2D and scene-menu path is alive. The self-made fixture is included and reaches
the material-loading boundary, but its runtime crash prevents the intended
native-renderable and child-surface experiment. Therefore the current evidence
separates package inclusion from runtime display, but does not yet identify the
first native crash frame or prove a WSI/compositor-only defect.

## Next smallest diagnostic

Run the same r12 image with a symbolized crash/backtrace or bounded diagnostic
markers immediately around material load, entity creation, and renderable
creation. Keep the 12-vCPU QEMU profile and do not broaden the fixture or
full-scene scope until that boundary is observed.
