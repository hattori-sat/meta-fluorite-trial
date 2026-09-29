# FLR-0215 — trace native surface compositor visibility and selection

- Status: Done
- Priority: High
- Owner: Wayland surface-role / compositor-selection role
- Created: 2026-09-20
- Predecessor: [FLR-0214](FLR-0214-trace-wayland-wsi-buffer-transfer.md)

## Work unit

Identify why the RGB-positive native surface does not appear in the final QMP
frame after the app and compositor share the same non-zero WSI buffer. Trace
surface role, parent/child relation, geometry, visibility, stacking, and final
compositor selection. Do not patch until one source-side owner is evidenced.

## Success criteria

- Reuse the fixed Podman/Devtool state, Mini receiver/build/TMPDIR, and one
  QEMU/QMP instance.
- Preserve one QMP frame plus bounded compositor/protocol evidence that names
  the native surface and its final visibility/selection state.
- Compare the native surface with the known-good visible SHM control surface.
- Decide whether the owner is Flutter/Filament surface setup or compositor
  policy; mark UNKNOWN if evidence cannot distinguish them.
- If a source owner is proven, create the smallest official Devtool patch in a
  later implementation unit, then verify Mac bundle → Mini `do_patch` → build →
  QMP. Otherwise split the next diagnostic unit.

## Facts inherited from FLR-0214

- Native WSI shared-buffer bytes are RGB-positive in both producer and
  compositor mappings.
- Native-only QMP is black in the candidate ROI while 2D HUD is visible.
- A/Bs for alpha, flush, stacking direction, clipping, and layout have not
  restored native QMP pixels.
- The bounded runtime log records `scene_native=true`,
  `parent_surface=true`, `surface=true`, and `subsurface=true` for the native
  ViewTarget contract.
- The same run records `wl_surface@37.attach → damage → frame → commit` for
  the native WSI buffer and `vkQueuePresentKHR result=0`.

## Inferences

- Native surface creation, parent attachment, role setup, buffer attach, and
  commit all occur. The missing boundary is after native surface commit and
  before final QMP composition.
- The source-side owner for the remaining diagnostic is
  `fluorite-plugins/plugins/filament_view/core/scene/view_target.cc`, not the
  Filament Vulkan platform source alone.

## Hypotheses

1. Native surface role or parent/child relationship prevents final selection.
2. Native surface geometry/visibility differs from the visible SHM control.
3. Compositor policy suppresses the imported surface despite valid content.

## Plan / Do / Check / Act

### Plan

Inspect bounded compositor surface state and the corresponding Wayland object
creation/role path, then compare against the visible SHM control.

### Do

- Compared the FLR-0214 runtime markers with the current `ViewTarget` source.
- Confirmed the native surface is created as a child of the Flutter base
  surface, positioned, made desynchronized, and presented through Filament's
  native swapchain.
- Confirmed the native WSI buffer has RGB-positive bytes in the compositor
  mapping while the final QMP native ROI remains black.

### Check

- PASS: native surface role and parent relationship are established.
- PASS: native buffer attach/damage/frame/commit and present result are
  observed.
- PASS: native buffer RGB is present in both producer and compositor mappings.
- PASS: QMP still shows 2D HUD but no native pixels.
- PASS: the first owner class is native-surface final composition, not buffer
  content transfer.

### Act

Close this evidence unit and open FLR-0216 for a bounded readback-to-visible-
SHM diagnostic bridge. Do not treat that bridge as the native WSI fix.

## UNKNOWN

- Exact compositor surface identifier and role for the native WSI surface at
  the point of final composition.
- Whether the fix belongs in Flutter/Filament surface setup or in compositor
  policy/configuration. FLR-0216 will isolate this by putting the same
  readback bytes through the already-proven visible SHM path.
