# FLR-0228 — isolate Flutter-parent repaint composition

- Status: Done
- Priority: High
- Owner: Flutter embedder and Wayland parent-surface composition roles
- Created: 2026-09-20
- Predecessor: FLR-0227

## Objective

Identify the first boundary that turns the transparent Flutter parent/HUD area
into a uniform white frame when the pointer enters the Scenes coordinate, while
preserving the already-visible diagnostic 3D cube and 2D HUD.

## Facts

- FLR-0226 made `MaterialApp`, `ThemeData`, and the normal `Scaffold`
  transparent. The Mini build and QMP runtime reproduced the white transition.
- FLR-0227 removed `MenuAnchor` and all popup menu children while retaining a
  same-position `FilledButton`. The Mini patch, compile, image, QMP, and
  teardown gates passed, but the same white transition occurred.
- In both runs, the initial QMP native ROI had `chromatic_pixels=24178` and the
  parent/HUD ROI became uniform luma 255 with no chromatic or edge pixels after
  the vertical pointer move.
- Focused runtime markers show Vulkan present result 0 and continued parent
  surface attach/damage/frame/commit traffic. The native ROI does not change.
- A runtime-only parent-alpha probe was launched on the FLR-0227 image with
  `FLR0026_PARENT_ALPHA_CLEAR=1`; no source or image rebuild was involved.
- With the probe command, the initial QMP frame kept the diagnostic 3D ROI
  visible (`chromatic_pixels=24178`) while the parent/HUD ROI was uniformly
  black (`luma_range=[0,0]`, `changed_pixels=0`).
- After the same vertical pointer move used by the control run, the diagnostic
  3D ROI remained identical (`chromatic_pixels=24178`) while the parent/HUD
  ROI became uniformly white (`luma_range=[255,255]`, `changed_pixels=12800`).
- The selected log records `FLR0026_VK_COMPOSITE_ALPHA transparent=true
  supported=0x3 selected=0x2`, Vulkan queue-present `result=0`, and repeated
  parent `attach/damage/frame/commit` operations. QMP quit and residual
  process cleanup both passed.
- Static inspection narrowed the parent repaint trigger to the Wayland output
  enter path: `handle_base_surface_enter` applies the buffer scale and calls
  `Engine::SetPixelRatio`, which sends a full `FlutterWindowMetricsEvent`.

## Hypotheses

| Rank | Hypothesis | Prediction | Discriminator |
| --- | --- | --- | --- |
| 1 | Flutter embedder loses the transparent parent clear/alpha contract during pointer-triggered repaint | a minimal embedder-side or parent-surface alpha A/B changes the QMP parent ROI without changing widget source | focused flutter-auto/Wayland damage and buffer evidence plus QMP ROI |
| 2 | Compositor imports the parent buffer as opaque only after input damage | parent buffer metadata or compositor selection changes at the first white frame | bounded compositor journal/protocol evidence correlated to the QMP frame |
| 3 | Native child-surface ordering changes on input | native attach/commit/ROI changes at the same transition | native ROI and Wayland child markers; currently low probability |

## Inferences

- The parent-alpha clear probe does not prevent the input-triggered white
  transition. The first useful boundary remains after the native 3D producer
  (which is unchanged) and at or after the Flutter parent repaint/import path.
- The unchanged native ROI and the absence of a native child reattach in the
  selected transition log make native geometry or child ordering unlikely as
  the immediate cause.

## UNKNOWN

- The probe environment variable was present in the serial launch command, but
  the dedicated `FLR0026_PARENT_ALPHA_CLEAR` branch marker was absent from the
  bounded selected log. Whether that branch executed is therefore UNKNOWN;
  this run is a discriminator, not a fix.

## Decision

FLR-0228 is closed as a boundary-classification unit. The native 3D producer
and child-surface ordering are not the immediate cause of the white frame. The
next independent discriminator is FLR-0229: hold the pointer path constant and
test whether the output-enter `SetPixelRatio` metrics resend is the repaint
trigger.

## Plan / Do / Check / Act

### Plan

1. Reuse the fixed source/build/image flow; do not edit the Flutter widget or
   native 3D/light/material code for the first discriminator.
2. Compare the existing successful initial frame with the first white frame
   using only selected parent-surface, buffer, and compositor markers.
3. Select the smallest embedder/compositor correction, generate it through the
   official Devtool source baseline → commit → `update-recipe` flow, and run
   one Mini image plus one QMP runtime.
4. Split route activation and Planetarium production-scene validation into
   separate tickets after the parent frame remains stable.

### Check

| Gate | Expected | Result |
| --- | --- | --- |
| Runtime boundary | first white transition classified without raw-log sprawl | PASS: alpha probe did not prevent white parent after input; compositor/import boundary remains |
| Source history | complete Devtool baseline before any edit | NOT APPLICABLE: no source edit was made |
| Mini build | do_patch, do_compile, image build pass | NOT CHECKED |
| QMP runtime | native ROI preserved and parent/HUD ROI stable | PASS for native ROI preservation; FAIL for parent/HUD stability, as expected for diagnosis |
| Teardown | no residual QEMU, flutter-auto, or QMP socket | PASS: `residual_targets=0`, `residual_qmp=0` |

## Scope boundary

Do not combine menu route selection, Planetarium lighting, camera, production
GLB, or native Vulkan changes with this unit. Split every independent boundary
into a new Markdown ticket.

## Evidence

- Predecessor: [FLR-0227](FLR-0227-isolate-menuanchor-hover-composition.md)
- Evidence root: `$EVIDENCE_ROOT/FLR-0228/qemu-parent-alpha-probe/`
- Working log: [2026-09-20-flr0228.md](../logs/2026-09-20-flr0228.md)
- Next ticket: [FLR-0229](FLR-0229-isolate-output-enter-pixel-ratio-repaint.md)
