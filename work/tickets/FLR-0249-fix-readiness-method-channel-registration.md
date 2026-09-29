# FLR-0249 — fix readiness MethodChannel registration boundary

- Status: Done
- Priority: High
- Owner: Native readiness channel registration
- Created: 2026-09-21
- Predecessor: [FLR-0248](FLR-0248-trace-readiness-method-channel-boundary.md)

## Objective

Make the existing readiness MethodChannel registration explicit and stable so
the Dart `isReady` poll reaches the native handler in the effective Mini image.
Keep the proven 2D HUD and self-made native 3D fixture unchanged while proving
the smallest boundary correction.

## Facts

- FLR-0248's exact Mini source worktrees contain the Dart and native markers.
- The runtime produced two `MissingPluginException` results, then 345 bounded
  Dart timeouts, with zero native handler receive/respond markers.
- The Dart channel is `plugin.filament_view.readiness_checker` and the method
  is `isReady` on both sides.
- The native channel is constructed inside plugin setup and its handler is
  currently owned by a local `MethodChannel` object.
- The source correction is committed as
  `88324284058b89b1bfce230636e8329ac4eab246`.
- Official Devtool finish generated and the canonical recipe registers
  `0081-flr0249-start-readiness-after-platform-view-devtool.patch` with SHA256
  `c2b3af70705b7c2132eb6f4691897803b9e408c56c846bc9d5dba1974d4a4b75`.

## Hypotheses

1. The handler is registered after the first Dart poll or is not active on the
   messenger used by the running Flutter view.
2. The local channel lifetime/registration path is not stable across plugin
   setup and engine activation.
3. The channel name or messenger identity differs at runtime despite matching
   source literals. This is lower probability but remains falsifiable.

## Scope

- Inspect the native plugin registration order, messenger, channel lifetime,
  and Flutter embedding contract.
- Apply one minimal native registration/lifetime correction.
- Generate the patch through the fixed Mac Devtool workflow, register only the
  official generated patch in this layer, and validate Mini `do_patch`,
  `do_compile`, image build, QMP pixels, markers, and teardown.
- Do not change camera, light, material, scene geometry, or the proven fixture
  in this ticket.

## Success criteria

- [ ] Static evidence identifies the smallest registration/lifetime change.
- [ ] Official Devtool source commit and generated patch are recorded.
- [ ] Mini `do_patch`, `do_compile`, and full image pass.
- [ ] Runtime records native receive/respond and Dart return markers.
- [ ] 2D HUD and self-made native 3D remain chromatic in QMP evidence.
- [ ] Cleanup proves zero residual QEMU/QMP/flutter-auto processes.
- [ ] Production Planetarium geometry is only claimed after its own pixels are
  visible; otherwise the next missing boundary is ticketed separately.

## Resumed execution

FLR-0250 repaired the Mac Devtool control path. The focused recipe profile uses
the existing AGL mount, parses 20 recipes, and keeps the single fixed
`/workspace/tmp`. Official `devtool modify --no-extract` and `finish-source`
completed, and only the source-HEAD FLR-0249 patch was registered. Mini build
and runtime validation are now the remaining gates.

## Unknowns

- Exact Flutter engine registration timing and messenger identity in the
  effective image.
- Whether an explicit persistent channel owner alone is sufficient.

## Evidence

- Working log: [2026-09-21-flr0249.md](../logs/2026-09-21-flr0249.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0249/`

## Result

The official `0081` patch is applied in the authoritative Mini image. The
runtime reaches `FLR0249_READINESS_START_AFTER_PLATFORM_VIEW`,
`FLR0247_READINESS_READY`, and `FLR0247_READINESS_CALLBACK_DISPATCHED`.
The display criterion does not pass: the production QMP frame is uniform
white, and the fixture comparison shows HUD only. Simultaneous 2D+3D
restoration is split to [FLR-0251](FLR-0251-restore-known-good-2d-3d-display.md).
