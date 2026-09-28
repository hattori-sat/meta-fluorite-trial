# FLR-0199 — isolate Wayland/native surface composition

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Mini authoritative build + QEMU runtime roles
- Created: 2026-09-16
- Predecessor: [FLR-0198](FLR-0198-trace-vulkan-readback-payload.md)
- Working log: `work/logs/2026-09-16-flr0199.md`

## Work unit

Explain why the QMP frame shows the 2D HUD but a uniformly black 3D candidate
after the Vulkan driver-completion readback contains non-zero bytes. Keep the
first pass diagnostic-only: do not change production scene, lighting, camera,
or rendering behavior until the visible-pixel owner is identified.

## Facts inherited

- FLR-0198's official Filament patch, Mac/Mini gates, image, QMP capture, and
  teardown all passed.
- Driver completion reports a non-zero total buffer:
  `bytes=4096000 nonzero_bytes=478864 checksum=1693330037`.
- QMP 3D candidate `[300,250,620,400]` is uniformly black, while the HUD is
  visible.
- The current driver statistic is total-buffer only; it does not prove that
  the 3D candidate ROI contains non-zero pixels.
- `ViewTarget` creates a `CONFIG_TRANSPARENT` swapchain, while
  `FLUORITE_NATIVE_FORCE_OPAQUE` changes only the Filament View blend mode.
  Runtime logs select pre-multiplied composite alpha. This is a candidate
  alpha-contract mismatch, not yet a root-cause finding.

## Hypotheses

1. **H1 — native surface composition:** the child surface is committed but its
   geometry, mapping, scale, alpha, opaque region, or stacking places it
   outside or behind the visible parent content.
2. **H2 — ROI mismatch:** the non-zero driver payload is outside the 3D
   candidate, so the native draw/content boundary is still unresolved.
3. **H3 — capture path:** QMP captures the Flutter parent surface but not the
   native child surface's compositor path.

## Success criteria

- [x] Collect a direct driver readback statistic for the exact 3D candidate
  ROI, without changing rendering behavior.
- [x] Correlate one runtime sample with native child-surface creation/commit,
  viewport, alpha contract, and present evidence; record unavailable geometry
  and compositor-layer fields as UNKNOWN.
- [x] Run one paired QMP capture after the first frame is ready; distinguish
  timing errors from rendering evidence.
- [x] Identify the first missing boundary, record UNKNOWN items explicitly, and
  tear QEMU down through QMP with zero residual targets.

## Plan / Do / Check / Act

### Plan

1. Inspect only the bounded Wayland/native-surface source and the selected
   runtime marker chain from FLR-0198.
2. Add the smallest diagnostic needed for ROI and surface metadata through the
   existing Mac Devtool source → official patch → bundle → Mini gate flow.
3. Run one QMP-only session after guest-ready and first-frame readiness, then
   compare ROI, surface metadata, and the screenshot.

### Do

Bounded source/log analysis found the child surface lifecycle and the
transparent/pre-multiplied swapchain boundary. The next source change is a
diagnostic-only RGBA/ROI statistic in the existing `filament-vk` Devtool
workspace. It must not change swapchain, blend, or compositor behavior.

The corrected source commit is `4c3a4f2` on baseline `608c1c4`. Yocto standard
`modify --no-extract` was performed at the baseline, then the committed source
was checked out and `update-recipe --mode patch --append --no-remove
--force-patch-refresh` generated the official patch. The canonical patch SHA256
is `bd722d3ab66ec9af4e7b1cc8c5ba71acda2bd93a6b17fac530e885ae9cfff692` and
Mac `filament-vk:do_patch` passed all 104 tasks. The first Mini compile exposed
and the corrected source removed a clang tautological comparison warning. No
source behavior other than diagnostic logging changed.

### Check

Pending Mini do_patch/do_compile/image and one QMP run with the ROI and alpha
statistics. The initial post-edit modify attempt produced zero patches because
it recorded the new HEAD as `initial_rev`; this was corrected by registering
the baseline before checking out the source commit. No canonical patch was
copied from the failed attempt.

### Act

If ROI is non-zero and QMP is black, patch or correct the native
surface/compositor boundary in a new ticket. If ROI is zero, return ownership
to the native render/content path. If QMP excludes the child surface, change
the evidence method before changing rendering code.

## Result

The corrected official Devtool patch, Mini `do_patch`, `do_compile`, full image
build, one fixed-harness QEMU run, QMP capture, and QMP teardown all passed.
The driver-completion ROI contained non-zero RGBA data (`nonzero_rgb=111758`,
`nonzero_alpha=111758`), while the paired QMP ROI was uniformly black and the
HUD ROI was visible. Exactly one `flutter-auto` process ran. This moves the
first missing boundary past Filament/Vulkan draw and into the native
surface/compositor or QMP capture path; it does not yet prove which of those
two owners is responsible.

The 74 restored paths were pre-existing zero-byte tracked HEAD files. They were
restored exactly from HEAD and are not part of the diagnostic patch. The source
commit and generated patch remain deterministic and contain only the intended
`VulkanDriver.cpp` diagnostic change.

See [FLR-0200](FLR-0200-isolate-native-surface-compositor-visibility.md) for
the next bounded unit.
