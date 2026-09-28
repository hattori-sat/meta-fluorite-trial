# FLR-0290 — observe diagnostic native-surface alpha and Wayland stacking

- Status: Waiting
- Priority: High
- Owner: native surface alpha / compositor ownership
- Created: 2026-09-25
- Predecessor: [FLR-0289](FLR-0289-add-opt-in-translucent-diagnostic-surface.md)
- Working log: `work/logs/2026-09-25-flr0290.md`

## Objective

Determine why the opt-in translucent diagnostic scene produces a full-white
QMP frame instead of composing with the Flutter HUD. Observe Wayland attach,
damage, commit, buffer alpha, and native-surface stacking without changing
production or adding another render patch.

## Acceptance gate

The evidence must identify the first boundary among:

1. Filament clear/alpha content;
2. Wayland native child-surface attach/commit/import;
3. compositor stacking above the Flutter parent;
4. QMP framebuffer visibility.

Capture a QMP-only frame, bounded Wayland client markers, runtime markers, and
clean teardown. A patch is not justified until one boundary is proven.

## Facts

- FLR-0287 default production scene has HUD plus completely black native ROI.
- FLR-0288 diagnostic scene attached 13 production lights but forced opaque
  blend and made the whole QMP frame black.
- FLR-0289 diagnostic scene reports translucent blend and still produces a
  full-white frame with only two chromatic native pixels.
- Filament renderer clear color is explicitly `(0,0,0,0)` in
  `filament_system.cc`.

## Hypotheses

1. The diagnostic native surface is composited above the Flutter parent even
   when the Filament View reports translucent blend.
2. Native Wayland buffer alpha is lost or imported as an opaque white/gray
   buffer.
3. QMP is observing a compositor frame that differs from the Filament target.

## Verification plan

- Reuse the fixed FLR-0289 image and one-QEMU harness.
- Launch the same diagnostic translucent light control with bounded
  `WAYLAND_DEBUG=client` only.
- Save selected attach/damage/frame/commit/release lines and runtime blend
  markers before teardown; retain QMP frame/video and ROI analysis.
- Do not use opaque, place-below, SHM-cube, or source changes in this ticket.
- If the first boundary is proven, create a separate minimal implementation
  ticket for that boundary.

## Unknowns

- Whether the native child surface is above or below the Flutter HUD at the
  time of the full-white frame.
- Whether the submitted native buffer contains transparent alpha or an opaque
  clear.

## 2026-09-25 runtime result

One run reused the FLR-0289 image and enabled only `WAYLAND_DEBUG=client` in
the translucent diagnostic light control. The Wayland trace recorded
`wl_subsurface@40.place_above(wl_surface@14)` followed by native
`wl_surface@14` attach, damage, commit, and buffer release cycles. No Wayland
protocol error was observed.

The QMP-only frame is retained at
`/mnt/yocto/evidence/flr0290-0001/wayland-diagnostic.ppm`, SHA-256
`d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
The bounded video is under
`/mnt/yocto/evidence/flr0290-0001/wayland-diagnostic-video/`. Both native and
HUD ROIs were completely black in the captured frame.

The full Wayland/runtime log SHA-256 is
`d499023691d1d3cee884ddb859fcda4cf626b679055232e97a70867aa89bf76c` and the
selected bounded slice SHA-256 is
`01406ab396bcf85831ab4eb48c98285c34b222f4e8fcb060721db241ef8d86bc`.
Counts from the saved log are:

- `wl_subsurface`: 4;
- `wl_surface@`: 1574;
- `wl_buffer@`: 788;
- `wl_shm`: 220;
- protocol errors: 0;
- `FLUORITE_VIEWTARGET_BEGIN_FRAME_FALSE`: 26534;
- `FLUORITE_VIEWTARGET_BEGIN_FRAME_TRUE`: 4.

The begin-frame probe reports renderer, swapchain, native display, native
surface, parent surface, and subsurface all present, with `wayland_error=0`,
yet `frame_started=false`. QMP teardown passed with zero residual targets.

### Decision

Wayland attach/commit/release is not failing at the protocol boundary. The
first actionable divergence is Filament `beginFrame` failure after the native
surface is attached and placed above the Flutter parent. FLR-0290 is Waiting;
FLR-0291 owns the renderer/swapchain lifecycle correlation. No surface patch is
justified yet.
