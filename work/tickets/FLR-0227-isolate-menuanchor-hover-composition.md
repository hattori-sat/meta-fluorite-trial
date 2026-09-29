# FLR-0227 — isolate MenuAnchor hover composition

- Status: Done (hypothesis falsified; follow-up FLR-0228)
- Priority: High
- Owner: Flutter menu-layer and Wayland composition roles
- Created: 2026-09-20
- Predecessor: FLR-0226

## Objective

Identify and correct the smallest Flutter menu/hover layer that turns the
parent/HUD region into a uniform white frame after pointer entry, while keeping
the already-visible native diagnostic cube and 2D HUD intact.

## Facts

- FLR-0226 generated and applied the official Devtool patch that explicitly
  made `MaterialApp`, `ThemeData`, and the normal `Scaffold` transparent.
- Mini `do_patch`, `do_compile`, and full image build all passed for that
  patch.
- The FLR-0226 initial QMP frame had a visible native cube and 2D HUD. The
  native ROI remained unchanged after pointer movement, but the HUD/parent ROI
  became uniform luma 255 with no chromatic or edge pixels.
- Static source inspection shows the Scenes control is a `MenuAnchor` whose
  builder creates a `FilledButton`; its menu items select scenes in
  `onPressed` callbacks. Hover alone is not the route callback.
- Focused runtime markers show Vulkan present succeeds and the parent surface
  continues to receive damage/frame/commit traffic during the white transition.
- The fixed Mac Devtool source was officially registered at the FLR-0226 source
  HEAD before editing. The A/B source commit is
  `4ce54f88a9587f5aa6b267a548c0d4d293baf9d4`.
- Official `devtool update-recipe` generated one FLR-0227 patch. The canonical
  patch is byte-identical and has SHA-256
  `a4ec792e8b4edb381e63fa87da937a2e2cb11bec10722e4148eec2515fb1326b`.

## Hypotheses

| Rank | Hypothesis | Prediction | Discriminator |
| --- | --- | --- | --- |
| 1 | `MenuAnchor`/`FilledButton` or its popup theme creates an opaque intermediate layer | removing or constraining only the menu layer prevents uniform white while native ROI remains unchanged | source-level A/B with identical QMP pointer sequence |
| 2 | Flutter embedder loses parent alpha on the hover-triggered repaint | a minimal embedder/compositor A/B changes the parent ROI without changing app widget source | bounded parent-surface commit/damage evidence and QMP ROI |
| 3 | Native child-surface ordering is reselected on input | native surface attach/commit or ROI changes at the same transition | focused Wayland marker comparison; currently lower probability |

## Plan / Do / Check / Act

### Plan

1. Reuse the fixed Mac Devtool source baseline and inspect the exact
   `MenuAnchor`/`FilledButton` theme and popup surface contract.
2. Choose one minimal source A/B; do not change camera, light, material, or
   native WSI code.
3. Generate the patch only through the official baseline-registration,
   source-commit, `devtool update-recipe`, and finish flow.
4. Send the canonical bundle to the existing Mini receiver, run the bounded
   recipe/image gates, and use exactly one QMP runtime.
5. Only after the white transition is removed, test Scenes menu selection and
   Planetarium as a separate ticket.

### Check

| Gate | Expected | Result |
| --- | --- | --- |
| Source history | complete Devtool baseline before edit | registered at `fed6ebc`, then source commit `4ce54f8` | PASS |
| Patch identity | one official patch from baseline to source commit | one official patch; canonical byte-identical; SHA recorded above | PASS |
| Mini build | do_patch, do_compile, image build pass | do_patch PASS, do_compile PASS, image PASS; rootfs SHA `377e434a...` | PASS |
| QMP A/B | native ROI preserved and parent/HUD ROI does not become uniform | native ROI stayed at `chromatic_pixels=24178`, but parent/HUD became uniform luma 255 even with MenuAnchor removed | FAIL for hypothesis 1 |
| Teardown | no residual QEMU, flutter-auto, or QMP socket | serial stop, QMP quit, cleanup, and residual target count 0 | PASS |

## Scope boundary

Do not combine menu route selection, Planetarium lighting, camera, production
GLB, or native Vulkan changes with this unit. Split each next independent
boundary into a new Markdown ticket.

## Act

Removing the `MenuAnchor` popup did not change the white-frame transition, so
the widget-layer hypothesis is falsified. Continue with FLR-0228 for the
Flutter embedder/Wayland parent repaint boundary. Route activation remains a
separate later ticket.

## Evidence

- Predecessor: [FLR-0226](FLR-0226-fix-flutter-parent-hover-composition.md)
- Evidence root: `$EVIDENCE_ROOT/FLR-0227/`
- Working log: [2026-09-20-flr0227](../logs/2026-09-20-flr0227.md)
- Follow-up: [FLR-0228](FLR-0228-isolate-flutter-parent-repaint-composition.md)
