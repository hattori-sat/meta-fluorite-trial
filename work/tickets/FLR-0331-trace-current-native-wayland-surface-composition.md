# FLR-0331 — trace current native Wayland surface composition

- Status: Done
- Priority: High
- Owner: native Wayland surface attach/commit/import and QMP composition
- Created: 2026-09-25
- Predecessor: [FLR-0330](FLR-0330-replay-production-without-readback-diagnostic.md)
- Working log: `work/logs/2026-09-25-flr0331.md`

## Objective

Observe the current production control's native Wayland surface lifecycle
after Filament draw submission, using one bounded `WAYLAND_DEBUG=client` run.
The purpose is to distinguish “surface never commits” from “surface commits
but QMP composition omits its content.” Do not change source, Light, camera,
material, Scene ownership, or route behavior.

## Success criteria

- Reuse the fixed rootfs/build/TMPDIR and the no-readback production control.
- Add only `WAYLAND_DEBUG=client` to the launch environment.
- Capture one QMP full frame before ROI analysis.
- Retain only bounded Wayland lifecycle lines, selected draw/frame markers,
  app liveness, fixed ROIs, and hashes.
- QMP teardown leaves zero target processes and zero QMP sockets.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0330 reaches Scene add, `beginFrame=true`, and draw submit while QMP's
  native ROI remains uniformly black and HUD pixels remain visible.
- Historical FLR-0205/0219 prove that a native surface can attach, damage,
  request a frame callback, and commit in this project, but that evidence is
  not automatically current-image evidence.

### Hypotheses

1. Current native surface attach/damage/commit is present, so the missing
   boundary is after client commit and before QMP composition.
2. Current production does not commit the intended native surface or commits
   a zero/black buffer, so the missing boundary is before compositor import.
3. The parent Flutter surface is visible while the native child is hidden by
   stacking/placement, despite a valid client lifecycle.

### UNKNOWN

- Current surface IDs, buffer attach/release, and commit sequence for this
  exact production control.
- Whether the committed native buffer contains visible 3D pixels.

## Result

- One fixed-image QMP run reused the FLR-0330 no-readback production control
  and added only `WAYLAND_DEBUG=client`.
- The parent Flutter surface `wl_surface@14` attached buffers, damaged,
  requested frame callbacks, and committed repeatedly.
- The native surface `wl_surface@39` was created and registered as
  `wl_subsurface@40` under `wl_surface@14`, with `place_above` and position
  `(0,0)`, but no `wl_surface@39.attach`, `damage`, or `commit` appeared in
  the bounded slice.
- Filament reached `beginFrame=true`, fixed-color replacement, Scene add, and
  draw submit. QMP full-frame PPM:
  `/mnt/yocto/evidence/flr0331-0001/qemu/qmp-0331-wayland-full.ppm`,
  SHA-256
  `99954a888b65a9e1b79ff9e35cb48fdba1491fc676aaf14fe414352312196c54`.
- Native ROI `(440,220,400,360)` is uniform black (`0/144000` chromatic),
  while HUD ROI remains positive (`2845` chromatic).
- Bounded Wayland serial output:
  `/mnt/yocto/evidence/flr0331-0001/qemu/serial-0331-wayland.output`,
  SHA-256
  `33a8a2925d9d41d8992a0e6c3279b27502ded590cda69be9fdc2ff10076dff9e`.
- QMP teardown passed with `residual_targets=0` and `residual_qmp=0`.

The first missing current-image event is native buffer publication after
surface creation/subsurface registration and before native `wl_surface@39`
attach. FLR-0332 owns the source/runtime trigger for that publish step.

## Plan / PDCA

1. Commit and bundle the one-line `WAYLAND_DEBUG=client` launch/slice.
2. Run one QEMU pass, save QMP full frame first, then extract the bounded
   surface lifecycle and fixed ROIs.
3. Choose the next source or runtime boundary only from the observed first
   missing event.

## Stop conditions

- Do not call attach/commit success proof of visible 3D pixels.
- Do not change stacking, alpha, camera, or Light in this ticket.
