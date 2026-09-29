# Plan: FLR-0127 — isolate the Dart fixture black region

## Goal

Locate the first Dart-specific divergence after Shape/Camera/Vulkan present
and before visible QMP pixels, using the already proven native fixture as a
bounded control.

## Constraints

- Reuse the fixed Devtool/container, Mini receiver, build, TMPDIR, and caches.
- Use exactly one QEMU per run and QMP-only visual evidence.
- Keep Facts, Inferences, Hypotheses, and UNKNOWN separate.
- Do not edit generated patches; if a source change is justified, use the Mac
  Devtool lifecycle and then bundle the canonical layer commit to Mini.

## Steps

1. Inspect do-patch source, package assets, effective logger controls, and the
   camera/material/surface call chain.
2. Run a bounded verbose no-source-change probe and preserve its evidence.
3. Rank H1 material/resource, H2 translucent surface, and H3 camera/transform
   using falsifiable predictions.
4. Execute one-variable A/B only for the leading hypothesis.
5. If source-owned, generate the official Devtool patch on Mac, register the
   untouched patch in `meta-fluorite-trial`, commit locally, bundle to Mini,
   run progressive BitBake gates, and repeat QMP validation.
6. Close this gate and split the next independently verifiable scene or input
   task into a new ticket.

## Acceptance

- First Dart-specific missing boundary identified with bounded evidence.
- Any visual A/B has early/late QMP captures, pixel analysis, image identity,
  and clean negotiated teardown.
- No unsupported claim is made for production Sequoia or scene transitions.
