# FLR-0229 — isolate output-enter pixel-ratio repaint

- Status: Done
- Priority: High
- Owner: Wayland window metrics and Flutter parent-surface roles
- Created: 2026-09-20
- Predecessor: FLR-0228

## Objective

Determine whether the Wayland output-enter path's `SetPixelRatio` and resulting
`FlutterWindowMetricsEvent` trigger the uniform-white Flutter parent/HUD frame,
while preserving the diagnostic 3D cube and the normal pointer path.

## Facts

- FLR-0226 and FLR-0227 both reproduced the same parent/HUD white frame while
  the native diagnostic 3D ROI remained unchanged.
- FLR-0228's parent-alpha probe reproduced the white frame after input; Vulkan
  present returned 0 and the parent surface continued attach/damage/frame/commit.
- Static source inspection shows
  `WaylandWindow::handle_base_surface_enter` applying the output buffer scale
  and then calling `Engine::SetPixelRatio`.
- `Engine::SetPixelRatio` sends a complete `FlutterWindowMetricsEvent` with
  width, height, and pixel ratio.
- A clean Mac `devtool modify flutter-auto` attempt stopped at the existing
  `0220` patch stack (`hunk 3` in `wayland_vulkan.cc` and the `window.cc`
  hunk). This was a baseline mismatch before the FLR-0229 edit, not a failure
  of the new patch.
- The Mini effective source was imported into a self-contained Mac baseline
  (`4aff9bca`) and registered successfully with official
  `modify --no-extract`.
- The one-file source commit `9faf13d` was passed to official
  `update-recipe`, and official `finish-source` generated the canonical patch
  with SHA-256
  `a2c5bcaced42789307240163df1ea2edc39a160baecb367429a79368bd199058`.
- The generated diff targets `shell/wayland/window.cc` at the flutter-auto
  root. The existing finish helper initially registered it with
  `patchdir=ivi-homescreen-plugins`; that registration was corrected to root
  scope without editing the generated patch. Helper autodetection is split to
  FLR-0230.
- Mini `do_patch`, `do_compile`, and full image build passed. The QEMU rootfs
  was `agl-ivi-image-flutter-qemux86-64.rootfs-20260920071805.ext4` with
  SHA-256 `c86dce5214e19e8fb5e0e8027cb7f59070c436cbd6fc2edd6ad50c150b3824d7`.
- In the control QMP run, the initial native ROI had
  `chromatic_pixels=24178` and the HUD ROI had `chromatic_pixels=2801`.
  `move-y` changed the HUD ROI to uniform white (`luma_range=[255,255]`,
  `chromatic_pixels=0`) while native 3D remained at `24178`.
- In the metrics-skip QMP run, the explicit branch marker was emitted.
  `move-y` kept the HUD ROI chromatic (`chromatic_pixels=2799`) and native 3D
  unchanged at `24178`; the later `up` event still changed the HUD to uniform
  white. Both QEMU runs quit and cleaned up with zero residual targets.

## Hypotheses

| Rank | Hypothesis | Prediction | Discriminator |
| --- | --- | --- | --- |
| 1 | Output-enter metrics resend triggers the opaque/white parent repaint | skipping only `SetPixelRatio` on surface enter prevents white while pointer hover and native 3D remain unchanged | one official flutter-auto A/B patch plus identical QMP sequence |
| 2 | The white frame is independent of metrics resend and is caused by compositor import/damage | skipping `SetPixelRatio` does not change the white transition | same image pair and ROI comparison |
| 3 | The pointer enters a different native child surface and changes stacking | native child attach/order or native ROI changes with the pointer | selected Wayland protocol log and native ROI; currently low probability |

## Verdict

The output-enter metrics resend hypothesis is supported for the first white
transition: skipping only `SetPixelRatio` preserves the 2D HUD through
`move-y` without changing the 3D ROI. It is not a complete fix because the
button-release `up` event still produces the white HUD. That remaining path is
split to FLR-0231.

## Plan / Do / Check / Act

### Plan

1. Start from the complete current Devtool source baseline, not from a stale
   patch-only layer tree.
2. Add one environment-gated diagnostic branch around the output-enter
   `SetPixelRatio` call, preserving the default behavior when unset.
3. Commit the source change, run the official `update-recipe`/finish flow, and
   place exactly one canonical patch in `meta-fluorite-trial`.
4. Transfer the commit as a bundle, run Mini `do_patch`, `do_compile`, image,
   and one QMP-only A/B with clean teardown.

### Success criteria

- The control and A/B use the same rootfs family and QMP pointer sequence.
- The A/B log emits an explicit branch marker showing whether the metrics resend
  was skipped.
- Native diagnostic 3D ROI remains present in both frames.
- The parent/HUD ROI either remains stable (hypothesis 1 supported) or changes
  identically (hypothesis 1 falsified); no ambiguous result is accepted.
- The result is recorded with selected logs, ROI hashes, and teardown status.

## Scope boundary

Do not change Dart widgets, Filament light/material/camera code, native 3D
geometry, compositor configuration, or route activation in this ticket.

## Evidence

- Predecessor: [FLR-0228](FLR-0228-isolate-flutter-parent-repaint-composition.md)
- Working log: [to be created at execution start](../logs/2026-09-20-flr0229.md)
- Workflow follow-up: [FLR-0230](FLR-0230-fix-devtool-root-patch-registration.md)
- Remaining input follow-up: [FLR-0231](FLR-0231-isolate-button-release-repaint.md)
