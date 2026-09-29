# FLR-0236 — activate Planetarium scene from the Scenes control

- Status: Done
- Priority: High
- Owner: Flutter scene-selection and native scene-activation roles
- Created: 2026-09-20
- Predecessor: FLR-0235

## Objective

Prove one real scene transition: QMP tap on the existing Scenes control must
activate the existing Planetarium scene, keep the 2D HUD visible, and produce
an observable post-transition 3D frame. This ticket does not redesign the
scene menu or validate every scene.

## Facts

- FLR-0235 proved that the current image can show the 2D HUD and a native
  3D fixture cube together through pointer motion.
- The current Devtool source contains `_setScene(0..4)`, including
  `PlanetariumSceneView` at scene id `3`.
- The current Scenes control is a static `GestureDetector` whose `onTap` is
  an empty callback; it does not call `_setScene`.
- The initial native creation payload already contains Planetarium shapes and
  cameras, while `poGetScenesShapes()` also appends the diagnostic fixture.
- The current QMP evidence proves the fixture cube, but does not prove a
  Planetarium transition or a production-scene frame.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Reconnect the existing static control to `_setScene(3)` | QMP tap causes a route-state change and Planetarium frame while HUD remains visible | direct validation path is intentionally narrow |
| 2 | Restore the full `MenuAnchor` scene menu | selecting Planetarium reaches the same scene | reintroduces the widget hover/composition boundary |
| 3 | Native creation already selects Planetarium but its geometry is off-camera or hidden | adding the route callback does not change the native ROI; logs/pixels isolate camera/composition | requires a follow-up scene-shape ticket |

Candidate 1 is selected because it changes only the missing application-level
activation edge and preserves the FLR-0235 static surface that already passed
the white-frame gate.

## Plan / Do / Check / Act

### Plan

1. Register the current FLR-0235 source HEAD in the fixed Devtool workspace.
2. Change only the Scenes tap callback to activate scene id `3`.
3. Generate the patch through the official Devtool finish flow, bundle the
   layer commit to Mini, rebuild the image, and run one QMP tap/evidence gate.

### Success criteria

- The patch contains no camera, light, material, native renderer, or fixture
  changes.
- QMP initial frame retains the FLR-0235 2D HUD and native 3D baseline.
- QMP tap at the measured Scenes control bounds produces a distinct
  post-transition frame and an application scene-activation marker.
- The post-transition frame retains a non-white HUD and has a documented
  native 3D ROI result; whether that ROI is Planetarium geometry or an
  off-camera/unchanged fixture is recorded explicitly.
- QMP quit, process cleanup, and residual socket checks pass.

## Evidence

- Predecessor: [FLR-0235](FLR-0235-replace-material-hover-button.md)
- Working log: [2026-09-20-flr0236.md](../logs/2026-09-20-flr0236.md)
- QMP screenshot/video and hashes are required before closing this ticket.

### Completed evidence

- Mini patch gate: `PASS`; compile gate: `1674/1674` tasks succeeded; image
  gate: `11758/11758` tasks succeeded.
- The validated rootfs was identified by the matching qemuboot configuration
  and SHA-256 recorded in the working log.
- QMP initial frame retained the FLR-0235 baseline: HUD chromatic pixels
  `2845`, native ROI chromatic pixels `24178`.
- The QMP tap delivered the expected Wayland pointer sequence and the runtime
  emitted `FLR0236_SCENE_ACTIVATION id=3 name=Planetarium`.
- After the tap, the native ROI remained `24178`, but the HUD region became
  uniform white (`0` chromatic pixels). Therefore the callback edge is proven;
  a visible Planetarium frame is not proven.
- QMP quit was accepted and residual QEMU, compositor, and Flutter targets
  were zero. Evidence is retained under `$EVIDENCE_ROOT/FLR-0236/`.

### Verdict

The application-level Scenes-to-Planetarium callback is fixed and verified.
The visible scene transition remains blocked at the Flutter/native composition
boundary: the post-tap frame loses the HUD while retaining the diagnostic
native ROI, and no Planetarium-specific pixels were demonstrated. FLR-0237
owns that next boundary investigation.

## UNKNOWN

- Whether the current Planetarium shape payload is visible in the target
  camera after activation remains UNKNOWN and is explicitly scoped to
  FLR-0237.
