# FLR-0278 — isolate production grayscale render content after frame-event A/B

- Status: Done
- Priority: High
- Owner: production model/material/lighting and target-content state
- Depends on: [FLR-0277](FLR-0277-isolate-production-call-event-segv.md)
- Working log: `work/logs/2026-09-24-flr0278.md`

## Problem

The current authoritative image renders the self-made native fixture as
colored QMP geometry, but the production scene with one selected model remains
black/grayscale. Increasing QEMU memory and skipping the pre-render frame event
do not restore production chromatic pixels. The next discriminator must compare
production scene content and render state against the known-good fixture in the
same QEMU without changing the compositor or capture path.

## Facts

- The fixture is positive in the same image/QEMU: late ROI has 3,562
  chromatic pixels and maximum chroma 242.
- Production normal and frame-event-skip cases both survive without a core but
  have zero late chromatic pixels.
- Production reaches model selection, shape readiness, draw submit/end, and
  Vulkan present.
- Current production controls suppress skybox, indirect light, and lights;
  this makes the remaining material/target contract a deliberate variable.
- The authoritative run used 4096 MiB and the guest had 3,560 MiB available;
  no kernel OOM record exists.
- A lights-on A/B did not sustain chromatic pixels and later produced a
  `SIGSEGV`. A shapes-skipped/model-only A/B remained uniform gray and later
  produced the same `CallEvent -> DrawFrame -> OnFrame` class of `SIGSEGV`.

## Result

This diagnostic unit is complete. The 4096 MiB allocation is not the limiting
factor, shape setup is not sufficient to explain the production gray frame,
and enabling production lights does not produce sustained chromatic pixels.
The remaining discriminator is the production translucent/opaque target and
surface-composition boundary, with the frame-event callback disabled so its
known delayed `CallEvent` fault cannot obscure the result.

## Competing hypotheses

1. Production model/material data reaches renderables but produces grayscale or
   zero-color output under the current material/light contract. Prediction:
   production shape/material or a minimal production asset A/B changes QMP
   chroma while the fixture remains positive. **Partially supported:** the
   lights-on and shapes-skipped controls did not produce sustained chroma.
2. Production scene/view target content is attached to a different or invalid
   render target/camera state despite successful draw/present markers.
   Prediction: a bounded target/scene identity or active-camera comparison
   differs from the fixture and a minimal target correction changes QMP pixels.
3. The production frame-event callback fault is independent of QEMU memory and
   can obscure later content observations. **Supported:** 4096 MiB is healthy,
   no OOM record exists, and the coredump stack enters `CallEvent` from
   `DrawFrame`; use the existing skip control during the next content A/B.

## Success criteria

- Reproduce the production and fixture cases in one 4096 MiB QEMU with
  QMP-only screenshots and bounded logs.
- Identify the first production-vs-fixture difference in model, material,
  light, scene, camera, renderable, or target state.
- Do not call grayscale geometry successful 3D; require nonzero chromatic ROI
  pixels in a live process.
- If a source change is needed, create it in the persistent Mac Devtool source,
  use the official component rebase/update-recipe flow, transfer the committed
  canonical layer bundle, and rebuild on Mini before runtime validation.
- Keep route/input validation out of scope until production chromatic pixels
  are proven.

## Verification plan

1. Inspect the current production shape/material/light and fixture setup paths.
2. Select one minimal diagnostic that compares the effective scene, camera,
   renderable/material, and target contract without broad logging.
3. Run the A/B on Mini, capture QMP ROI and only the corresponding log slice.
4. Patch only the first proven boundary, then repeat the authoritative build
   and QMP gate.

## Visual evidence

QMP evidence is present under Mini evidence run `flr0278-0001`. The production
lights-on late frame is `lights-video/frame-00009.ppm` (SHA-256
`f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`); the
model-only late frame is `model-only-video/frame-00009.ppm` (SHA-256
`a4ffc7bb0f07ccbc213989a8874f2a80755d84d808f3b85e39fdc10c68056bbb`). Both
QEMU cases were terminated through the serial stop command and QMP quit.
Visual inspection matches the metrics: the lights-on frame has only the 2D
HUD over a black 3D region, while the model-only late frame has a large
uniform white/gray upper surface and no visible production model content.

The next independent unit is
[FLR-0279](FLR-0279-isolate-production-opaque-surface-composition.md).
