# FLR-0292 — A/B swapchain configuration before beginFrame

- Status: Waiting
- Priority: High
- Owner: Filament swapchain configuration / Vulkan acquire lifecycle
- Created: 2026-09-25
- Predecessor: [FLR-0291](FLR-0291-isolate-begin-frame-failure-after-native-attach.md)
- Working log: `work/logs/2026-09-25-flr0292.md`

## Objective

Test the existing `FLUORITE_NATIVE_OPAQUE_SWAPCHAIN=1` control as one isolated
variable against the FLR-0291 transparent-swapchain failure. Determine whether
swapchain alpha configuration changes the `beginFrame` result after the native
Wayland surface is attached.

This is a diagnostic A/B, not a product fix. The final acceptance target still
requires a single frame containing both the Flutter HUD and colored Sequoia
3D/light pixels.

## Acceptance gate

One sequential QEMU run using the fixed FLR-0289 image must record:

1. the opaque-swapchain launch marker;
2. bounded `beginFrame=true/false` counts and the existing probe state;
3. one QMP-only frame and bounded video with native/HUD ROI analysis;
4. comparison against FLR-0291's transparent control;
5. QMP teardown with zero residual QEMU, `flutter-auto`, and QMP targets.

## Facts

- FLR-0291's transparent configuration produced 4 `beginFrame=true`, 9,113
  `beginFrame=false`, a uniform `(224,224,224)` QMP frame, and no observable
  HUD or vehicle.
- `view_target.cc` already supports the opt-in opaque configuration at native
  swapchain creation; no source edit is required for this A/B.
- FLR-0286 proves the same image can render a self-made LIT fixture with an
  explicit light and the HUD, so this A/B must not be promoted to a generic
  Filament-light conclusion.

## Ranked hypotheses

1. **Transparent swapchain is rejected or not forward-progressing.** If true,
   opaque mode will materially increase `beginFrame=true` and produce a stable
   native frame, although it may cover the HUD.
2. **The rejection is independent of alpha configuration.** If true, opaque
   mode will retain the same false-heavy lifecycle and uniform QMP output.
3. **The diagnostic scene setup is the first divergence.** If both swapchain
   modes behave differently only after scene setup, the next ticket must isolate
   scene setup timing rather than add a light patch.

## Verification plan

- Reuse the fixed Mini receiver, build, TMPDIR, rootfs, and one-QEMU harness.
- Run only the opaque-swapchain variant; FLR-0291 is the transparent control.
- Save the bounded guest log before teardown, capture QMP frame/video, analyze
  native ROI `(440,220,400,360)` and HUD ROI `(1120,0,160,80)`, and record
  hashes.
- Do not change source, recipe, patch stack, camera, light count, or Wayland
  stacking in this ticket.

## UNKNOWN

- Whether the existing opaque control is compatible with the diagnostic
  translucent view and HUD composition.
- The exact Vulkan result hidden behind Filament's boolean `beginFrame` API.

## Visual evidence

Evidence is retained under the fixed Mini `$EVIDENCE_ROOT/flr0292-0001` role
path. Raw QMP frames remain outside Git; this ticket will record their hashes
and bounded ROI summaries.

## 2026-09-25 runtime result

The fixed FLR-0289 image was run once with only
`FLUORITE_NATIVE_OPAQUE_SWAPCHAIN=1` added to the FLR-0291 launch. The image
logged `FLUORITE_NATIVE_OPAQUE_SWAPCHAIN enabled=true`, but the lifecycle did
not change: `beginFrame=true=4`, `beginFrame=false=8036`, and the begin-frame
probe still reported all objects present with `wayland_error=0`.

The opaque QMP frame SHA-256 was
`3a5f5b2e7c9a934083620faaf14bfd52f5ed67c76f964e595c509edd7b67d374`, exactly
matching FLR-0291. Native and HUD ROI summaries also matched FLR-0291: nearly
uniform `(224,224,224)` with two small blue pixels in native and no observable
HUD pixels. QMP teardown passed with zero residual targets.

### Decision

Swapchain alpha configuration is falsified as the first cause. FLR-0292 is
Waiting; FLR-0293 owns a bounded GDB inspection of the actual
`filament::Renderer::beginFrame` return path.
