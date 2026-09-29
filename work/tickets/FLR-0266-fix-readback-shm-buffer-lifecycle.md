# FLR-0266 — fix readback SHM buffer lifecycle

- Status: Done
- Priority: High
- Owner: readback callback / Wayland SHM buffer lifecycle
- Created: 2026-09-24
- Predecessor: [FLR-0264](FLR-0264-reconcile-readback-shm-runtime-patch.md)

## Objective

Make the actual native readback pixels visible through the already-proven
Wayland SHM child surface, without changing the production scene or hiding the
native WSI failure. The result must be proven in QMP while the app is alive.

## Facts

- Native readback contains nonzero, chromatic pixels.
- The readback path emits a valid Wayland child-surface position, stacking
  order, attach, damage, commit, and flush.
- The same image's SHM-only control displays the self-made cube in QMP.
- The readback path's target ROI remains black in ten live QMP frames.
- Official diagnostic patch `0280` passed Mini `do_patch`, `do_compile`, and
  the full `agl-ivi-image-flutter` build.
- In the new image, setup, readback callback, and publish all reported the
  same thread ID. The callback and publish occurred twice with the same SHM
  surface and buffer addresses; both publications reported `100800/100800`
  nonzero and chromatic pixels.
- The paired QMP video in `0285-thread-trace` reproduced the failure in all
  ten frames: 2D remained visible while ROI `(460,260,360,280)` stayed
  `0/100800` changed and chromatic 0. Full-frame SHA-256 was
  `2149fccddf4ce9a725333e416f6b4ba1e0f2bf83976ac4d9daa82361c8d02046`.

## Hypotheses

1. The bridge reuses `shm_buffer_` without a verified `wl_buffer.release`, so
   the compositor does not import the updated contents as a new frame.
2. The readback callback runs on a different thread from the Wayland client
   owner, making the proxy/mmap update path unsafe despite a successful flush.
3. The readback byte/alpha contract is not accepted by the compositor, even
   though source-side counters see chromatic input.

## Check

- Official patch/build gates: PASS.
- setup/callback/publish thread identity: same thread; hypothesis 2 is
  falsified for this run.
- Source-side payload counters: PASS, but they do not prove compositor import.
- QMP live-frame acceptance: FAIL, reproduced with the new diagnostic image.
- Buffer lifecycle: UNKNOWN at the protocol-event level; the observed
  behavior is consistent with reusing the same SHM buffer without a verified
  `wl_buffer.release`, and this is now the leading hypothesis.

## Act

Close this diagnostic unit. FLR-0267 owns the minimal source change: add
explicit release/fresh-buffer ownership for the opt-in readback bridge and
re-run the SHM control and QMP acceptance gate. Keep the native-only path
unchanged.

## Visual evidence

- QMP-only evidence: `$EVIDENCE_ROOT/FLR-0266/0285-thread-trace/qmp-frames/`.
- The evidence shows the 2D surface and a black readback ROI in all ten
  frames; no host-window screenshot was used.

## Options

- First add bounded release/callback-thread evidence to the existing bridge.
- If lifecycle is confirmed, use the smallest opt-in implementation that owns
  a released/fresh SHM buffer for each publication; keep native-only and SHM
  control A/Bs unchanged.
- If lifecycle is falsified, test the pixel/alpha contract in isolation before
  touching the native WSI path.

## Success criteria

- The first failing readback-to-QMP boundary is identified with runtime
  evidence, not inferred from the source counters.
- Any source change is made in the persistent Mac Devtool source repository,
  committed before official `devtool update-recipe`, and materialized as an
  untouched generated patch in `meta-fluorite-trial`.
- Mini `do_patch`, the smallest required build gate, and QMP live-frame
  evidence pass.
- The self-made SHM control and native-only negative control remain recorded.

## Scope boundary

Do not change production scene setup, model/light/camera code, or native WSI
selection until this SHM publication unit is closed.
