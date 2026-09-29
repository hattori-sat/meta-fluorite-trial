# FLR-0277 — isolate production `CallEvent` SIGSEGV after bounded model load

- Status: Done
- Priority: High
- Owner: production frame-event lifecycle / render-thread safety
- Depends on: [FLR-0276](FLR-0276-restore-bounded-production-model-control.md)
- Working log: `work/logs/2026-09-24-flr0277.md`

## Problem

With QEMU memory increased to 4096 MiB and the production payload bounded to
one model, the stale-control/OOM ambiguity is gone, but `flutter-auto` still
terminates with `SIGSEGV`. The bounded stack first enters
`plugin_filament_view::FilamentViewPlugin::CallEvent(...)` from
`ViewTarget::DrawFrame(unsigned int)`. The same QEMU and image run the pure
native fixture with colored QMP pixels, so a generic QEMU or capture failure
is not sufficient to explain the production result.

## Facts

- Production selected one model and reached draw/present markers before the
  core was recorded.
- The core has a first application frame in `CallEvent`; llvmpipe/LLVM work
  and a Wayland present callback are active on other threads.
- The pure fixture remains alive and produces chromatic QMP geometry under the
  same 4096 MiB QEMU.
- Existing source has a static `eventBus` initialized null and initialized by
  `setupMessageChannels()`; the lifetime/concurrency state at the crash is
  UNKNOWN.
- A current-source diagnostic patch was generated through the persistent Mac
  Devtool component workflow as canonical patch `0284`; it adds only the
  `FLR0026_SKIP_FRAME_EVENT` runtime gate around the existing pre-render
  `CallEvent()` wait.
- The authoritative Mini patch, compile, and full image gates passed. In one
  4096 MiB QEMU, both normal production and frame-event-skip production stayed
  alive without a coredump; neither produced late chromatic pixels, while the
  same-image pure fixture produced chromatic QMP geometry.

## Competing hypotheses

1. `CallEvent` dereferences an invalid or concurrently changed `eventBus` or
   callback map during the production frame path. Prediction: a bounded
   diagnostic around event-bus state, or a frame-event-skip A/B, changes the
   crash boundary without changing the fixture.
2. The production model/material workload triggers an asynchronous render
   race that only becomes visible while llvmpipe/LLVM is active. Prediction:
   the crash changes when the production model is narrowed further or when
   the frame-event path is held constant, while event-bus state remains valid.

## Success criteria

- Reproduce production `MODEL_LIMIT=1` with 4096 MiB and capture a bounded
  coredump/backtrace plus the exact source line or object state at the first
  application frame.
- Run the pure fixture as the no-crash control in the same runtime session.
- Decide between the two hypotheses using evidence; do not infer the root
  cause from the black QMP frame alone.
- If a source change is justified, make it through the persistent Mac Podman
  Devtool workspace and official Yocto `update-recipe` flow, then transfer
  only the committed canonical layer delta as a bundle to the fixed Mini
  receiver.
- Keep route/input and full production visual acceptance out of this ticket.

## Verification plan

1. Inspect the current `CallEvent`, `eventBus`, callback-map, and
   `DrawFrame` ownership/lifetime paths; compare with the existing historical
   frame-event controls without copying stale names.
2. Re-run one bounded production case with the smallest diagnostic needed for
   core classification; retain the QMP screenshot only as supporting evidence.
3. Compare with the pure fixture control and the bounded stack.
4. Only then decide whether a minimal diagnostic or safety patch is needed.

## Current implementation checkpoint

- Source commit: `e8a37b6cfb2b60ef90dd0dd09323211745f8f3c5`
- Canonical patch: `0284-flr0277-diag-skip-frame-event-devtool.patch`
- Patch SHA-256:
  `06593b8f82545065f3682500a0a3f650d125272ad8f044799d3356bdc6e9b2e6`
- Mac Devtool rebase gate: PASS
- Mini patch/compile/image/runtime gates: PASS; production visual gate remains
  negative and is owned by FLR-0278.

## Result

Done as a diagnostic discriminator. The normal-versus-skip A/B did not change
the production chromatic-pixel result and did not reproduce the earlier
SIGSEGV. Therefore the frame-event path is not established as the direct cause
of the current production 3D failure. The static event-bus/map race remains an
open risk, but the next productive boundary is production scene
content/material/lighting, owned by FLR-0278.

## Visual evidence

The QMP evidence and hashes for the production control, skip case, and positive
fixture are recorded in `work/logs/2026-09-24-flr0277.md`.

## Visual evidence

Production QMP is UNKNOWN/invalid until the process survives without a core.
The fixture positive evidence is recorded in
`work/logs/2026-09-24-flr0276.md` under the FLR-0276 run directory.
