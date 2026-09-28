# FLR-0269 — trace readback Wayland protocol divergence

- Status: Done
- Priority: High
- Owner: readback SHM Wayland protocol / compositor import
- Created: 2026-09-24
- Predecessor: [FLR-0268](FLR-0268-isolate-readback-composition-regression.md)

## Objective

Identify the first Wayland protocol event that differs between the visible
SHM-only control and the readback-enabled run, using the already-built FLR-0267
image. Do not change source until the event boundary is known.

## Facts

- The SHM-only control proves 2D plus self-made 3D pixels on this image.
- Readback source pixels and `wl_buffer.release` events are present, but the
  readback-enabled QMP frame is full black.
- The previous readback serial command filtered out most Wayland protocol lines;
  this ticket retains the bounded protocol subset explicitly.

## Hypotheses

1. The enlarged pool and nonzero buffer offsets produce an invalid or harmful
   `wl_shm_pool.create_buffer`/attach contract.
2. The publish damage/commit/flush sequence changes the parent/native surface
   independently of pool allocation.
3. The readback callback's display flush interacts with the native surface
   commit ordering.

## Verification plan

- Re-run readback once with `WAYLAND_DEBUG=client` and retain only
  `wl_shm`, `wl_surface`, `wl_buffer`, `wl_display.error`, protocol-error,
  publish, release, and present markers.
- Correlate the first readback `attach/commit/flush` with the first full-frame
  black QMP capture; keep the run bounded to one QEMU.
- Compare against the SHM-only control before making a source change.

## Scope boundary

No production scene, camera, light, Flutter route, or native WSI changes belong
in this ticket.

## Runtime result

- `wl_surface@28` readback publishes completed with two buffers and matching
  release events; the parent `wl_surface@14` continued normal commits.
- No Wayland protocol error was captured.
- QMP frames 0–5 retained the 2D frame (`598250` changed pixels); frames 6–9
  became full black (`0` changed pixels). The black transition occurred during
  the live run, after readback was active.
- QMP cleanup completed after removing one stale socket only after verifying
  that the QEMU process had exited.

## Conclusion

The protocol is accepted, but readback mode causes a temporal whole-frame
blackout. The next source boundary is shared-pool/lifetime interaction, owned
by FLR-0270.
