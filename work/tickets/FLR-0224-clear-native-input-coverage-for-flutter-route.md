# FLR-0224 — clear native input coverage for Flutter route

- Status: Done
- Priority: High
- Owner: Native Wayland surface input region and QEMU input evidence role
- Created: 2026-09-20
- Predecessor: FLR-0223

## Objective

Prove whether the native Fluorite surface is intercepting QEMU pointer input
before the Flutter HUD can activate the `Scenes` route. Use the official
Mac-Podman Devtool workflow, starting from the source baseline that includes
all registered `meta-fluorite-trial` patches, and deliver the resulting patch
through the Mini PC bundle/build loop.

## Success criteria

- Devtool source status proves the existing recipe patch stack is applied
  before the new source edit.
- The source change is committed in the Devtool source Git before
  `update-recipe`/`finish` generates a patch.
- Mini PC `do_patch` applies the bundle without manual patch editing.
- One QEMU run proves whether a scaled QMP click reaches the Flutter parent
  and activates `Scenes`, with QMP-only screenshots and hashes.
- QEMU teardown is clean and the result is recorded in the working log.

## Scope boundary

- This ticket does not claim native WSI 3D restoration; FLR-0222 owns that.
- This ticket does not hand-edit a generated patch.
- The first source change is a minimal, gated native-surface input-region
  control. If it restores routing, a follow-up decides whether the default
  should change; if it does not, the next input boundary is split separately.

## Plan / Do / Check / Act

### Plan

1. Run canonical-repository and ticket gates; confirm FLR-0223 is Done and this
   is the only In Progress ticket.
2. Inspect the fixed Podman Devtool status, active recipe, source revision,
   source log, and existing recipe patch registration.
3. Edit only the Devtool source workspace, commit the source change, then run
   the official bounded patch-generation helper.
4. Commit the generated patch and recipe registration in
   `meta-fluorite-trial`, create a Git bundle, and send it to the fixed Mini
   receiver.
5. Run Mini `do_patch`, component compile, image build, and one QEMU input A/B.

### Do

- The source change was committed in the fixed Devtool component Git as
  `848e15983ed0380fb251c000f04bf6194e5b5001`.
- Official split-component `update-recipe` generated patch 0272 with SHA-256
  `58e630178fe9a79012d9cbac8323fa68c26433240ef0129de5474d32caa0715c`.
- Layer commit `98e7546f6af2fdcd495557208e9b853d37965060` was transferred by
  Git bundle to the fixed Mini receiver. Bundle SHA-256:
  `333af09cf4d1ed41c3929dd5598ad82ada712ac8fe305b02e2352d1b7ba5edd4`.
- Mini `do_patch`, `do_compile`, and full image build passed.
- One QEMU run used the exact built image and enabled
  `FLUORITE_NATIVE_EMPTY_INPUT_REGION=1`. Initial and post-click frames were
  captured through QMP only.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Existing Devtool baseline | all registered patches applied | `1da4a54...` baseline; source commit before generation | PASS |
| Source commit before patch generation | clean source commit | `848e159...` | PASS |
| Mini do_patch | PASS without hand edits | PASS; `$EVIDENCE_ROOT/FLR-0224/patch-gate-flutter-auto.summary` | PASS |
| QMP input target | Flutter parent receives click and route result is observable | pointer entered the Flutter parent; no Scenes marker; HUD became uniform white | PARTIAL; boundary decided |
| QMP-only visual evidence | initial and post-click frames with hashes | `830fd73a...` and `83b474a...` | PASS |
| Teardown | no residual QEMU/QMP | QMP quit and residual check PASS | PASS |

### Act

The input-coverage boundary is decided and this ticket is closed. The empty
input region changes the pointer destination, but it does not prove or restore
the Scenes route and it leaves a uniform-white HUD surface. FLR-0225 owns the
next post-input composition/route investigation. Do not broaden this ticket's
patch or mix production-scene camera/material changes into it.

## Facts

- FLR-0223 showed the scaled pointer leaving the Flutter parent and entering
  the native surface at the `Scenes` click coordinate.
- FLR-0223 post-click QMP lost the HUD and did not emit a route-transition
  marker.
- The official Devtool workflow requires existing recipe patches to be applied
  by `devtool modify`/component registration before source editing, followed by
  source Git commit and only then `devtool update-recipe`/`finish`.
- The authoritative Mini rootfs SHA-256 is
  `9176823a494b9f866ad28249bde8a9faf23520cdc93203a62072fc3270900064`.
- The initial QMP frame SHA-256 is
  `830fd73a5eb8ca51798dc037add59fcb37c9e3b5c3082f4d515c487fa0ab0cf4`.
  Native diagnostic ROI `chromatic_pixels=24178`; HUD ROI
  `chromatic_pixels=2801`.
- The QMP click was accepted at absolute tablet coordinate `(30463, 1638)`.
  The post-click frame SHA-256 is
  `83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`.
- Focused runtime evidence records
  `FLUORITE_NATIVE_EMPTY_INPUT_REGION enabled=true` and pointer enter to
  the Flutter parent surface. The post-click HUD ROI is uniform white
  (`chromatic_pixels=0`, `luma_range=[255,255]`), while the diagnostic native
  ROI remains chromatic.
- QMP teardown passed with zero residual QEMU/app targets and zero QMP socket.

## Decision

The native-surface input-coverage hypothesis is supported: clearing the native
surface input region changes the QMP pointer destination to the Flutter parent.
It is not sufficient for route activation or final 2D/3D composition. The
first remaining divergence is post-input surface content/route composition,
not the QMP input transport itself.

## Hypotheses

1. The native surface has input coverage and an empty input region will restore
   Flutter routing.
2. The input event is delivered to the native surface for another reason, so
   clearing the input region will not change the route.

## UNKNOWN

- Whether the uniform-white parent surface is a route-rendering failure, a
  surface-stack replacement, or an application state transition without a
  marker.
- Whether the production scene will become visible after route input is fixed.

## Evidence

- Evidence root: `$EVIDENCE_ROOT/FLR-0224/`
- QMP run: `$EVIDENCE_ROOT/FLR-0224/qemu-input-region/`
