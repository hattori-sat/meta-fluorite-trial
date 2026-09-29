# FLR-0201 — reproduce the known-good native fixture after the current patch stack

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Mini authoritative build + QEMU runtime roles
- Created: 2026-09-16
- Predecessor: [FLR-0200](FLR-0200-isolate-native-surface-compositor-visibility.md)
- Working log: `work/logs/2026-09-16-flr0201.md`

## Work unit

Explain the regression between the known-good FLR-0042 native Filament cube
and the current image. Reproduce the same fixture and QMP evidence from the
current effective source, then compare the patch/source boundary before making
a composition or rendering change.

## Facts

- FLR-0042 recorded a visible self-made Filament cube through QMP at 1280x800:
  candidate change `5608/100000`, bounding box `[501,285,99,65]`, with the
  QMP-only evidence retained at `work/evidence/flr0042/native-fixture-15s.png`.
- FLR-0042 independently showed a Wayland SHM child surface in QMP, so QMP
  and child-surface composition are not globally incapable of showing native
  pixels.
- The current image's QMP frame is black in the 3D candidate while the driver
  ROI is non-zero.
- The current `flutter-auto_2.0.bbappend` registers only `0181`, `0183`, and
  `0184` among the scene-deserializer diagnostic patches; `0177`, `0209`, and
  `0235` are not in the effective recipe registration.
- The current Mini unpacked source's `RunPostSetupLoad()` has no
  `FLUORITE_NATIVE_PURE_FIXTURE` or `FLR0026_NATIVE_PURE_FIXTURE` branch.
  Passing that environment variable therefore does not prove that the
  production scene/resource setup was bypassed.

## Inferences

- The QMP omission hypothesis is not sufficient as a global explanation,
  because FLR-0042 displayed the Filament cube through the same evidence type.
- The current effective patch/source stack is a leading regression boundary,
  but the exact patch or runtime operation is UNKNOWN.

## Hypotheses

1. A later current-source patch changed the native fixture/WSI or frame path
   after FLR-0042 and removed the visible-pixel condition.
2. The current QEMU profile or surface extent differs in a way that changes
   visibility, even though both evidence frames are 1280x800.
3. The current run is not a pure fixture because the deserializer control is
   absent; production resource setup may alter the frame loop or child surface.

## Success criteria

- [ ] Record a source/patch-stack identity for FLR-0042 and the current image.
- [ ] Reproduce the known-good fixture and current fixture with the same
  bounded QMP harness and compare pixel statistics and runtime markers.
- [ ] Identify the first differing source/patch/runtime boundary, or record
  UNKNOWN with a concrete next probe.
- [ ] If a source fix is required, generate it through Mac Devtool, commit the
  layer, bundle it to the fixed Mini receiver, and pass the authoritative
  gates before claiming visible 3D.

## Plan / Do / Check / Act

### Plan

1. Freeze the current effective `SRC_URI`, unpacked source markers, image
   hashes, and QMP profile.
2. Reconstruct the FLR-0042 source/image identity from its recorded evidence.
3. Compare only the first differing fixture, frame, WSI, or compositor
   operation; do not combine a patch with an unproven runtime workaround.

### Do

Initial static comparison is recorded in `work/logs/2026-09-16-flr0201.md`.
No source or runtime behavior has been changed for this ticket.

### Check

The current image was built and run through the fixed Mini QEMU harness. The
correct escaped service instance was first checked, then the diagnostic fixture
was launched explicitly with `--xdg-shell-app-id fluorite`. This separated an
initial app-id/service-template failure from the remaining rendering boundary.

The QMP-only frame `pure-fixture-fluorite-id.ppm` is 1280x800 and has visible
2D HUD content (`changed_pixels=7431`, `chromatic=2801`, bounding box
`[4,7,1252,193]`). Its central 3D candidate ROI `[300,250,620,400]` is
uniformly black (`changed_pixels=0`, `edge=0`, `chromatic=0`). The same run's
native driver readback is non-zero in the corresponding candidate area:
`nonzero_rgb=111758`, `nonzero_alpha=111758`, `nonzero_rgb_zero_alpha=0`,
`alpha_min=0`, `alpha_max=255`.

The QMP evidence was retained at the receiver under
`evidence/FLR-0201/qemu-pure-fixture-20260919/pure-fixture-fluorite-id.ppm`.
Its SHA-256 is
`b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
The Mac-side temporary display copy was not treated as repository evidence.

An A/B run with `FLUORITE_NATIVE_FORCE_OPAQUE=1` changed only the View blend
mode. It produced the same full-frame SHA and the same all-black 3D ROI. This
falsifies “View blend mode alone fixes composition”; the active 0223 patch still
creates the Filament swapchain with `CONFIG_TRANSPARENT`.

QEMU cleanup was completed through QMP with `residual_targets=0` and
`residual_qmp=0`.

### Act

The first actionable missing boundary is now after non-zero native driver
pixels and before final QMP parent-frame visibility. The View-only opacity A/B
did not change it. FLR-0202 owns the next single-variable source probe: an
environment-gated opaque native swapchain generated through the fixed Mac
Devtool flow and validated on the same Mini/QMP harness.

## UNKNOWN

- The exact FLR-0042 rootfs/source tip is not yet correlated with the current
  fixed receiver's retained artifacts.
- It remains UNKNOWN whether the transparent swapchain's Vulkan/Wayland
  composite-alpha contract or child-surface metadata is the first owner of the
  missing QMP pixels. The next opaque-swapchain A/B is the discriminator.

## 2026-09-19 checkpoint

- The current pure-fixture control was added in the fixed Mac Devtool source,
  committed as `98f2b3e6b25420977c1eb4074b7254464d60fb9c`, and generated through
  official `devtool update-recipe`.
- The unchanged generated output is registered as
  `0263-diag-add-current-pure-native-fixture-control-devtool.patch`; its
  SHA-256 is
  `badd790e14b5c0361b3cabc5a3bba3b40e00acd722b9264a2c109ce1352effea`.
- The source/helper handoff gates passed. Mini build and runtime gates remain
  pending; no 3D success claim is made.

## Completion decision

This ticket is complete as a boundary-classification unit: 2D is visible,
native driver pixels are non-zero, and the QMP 3D ROI is black. The remaining
source-controlled discriminator is intentionally split into FLR-0202 so that
this ticket remains one independently reproducible unit.
