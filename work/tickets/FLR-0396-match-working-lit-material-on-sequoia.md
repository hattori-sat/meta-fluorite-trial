# FLR-0396 — match the known-positive LIT material interface on Sequoia

- Status: In Progress
- Priority: High
- Created: 2026-10-01
- Owner: Mac Podman Devtool / meta-fluorite-trial / Mini BitBake / guest Flutter / QMP evidence roles
- Branch: `feature-flr-0396-match-working-lit-material`
- Plan: [FLR-0396 implementation plan](../../docs/superpowers/plans/2026-10-01-flr0396-match-working-lit-material.md)
- Working log: [FLR-0396 working log](../logs/2026-10-01-flr0396.md)
- Positive runtime control: [FLR-0394 exact-image fixture + HUD](FLR-0394-capture-live-fixture-over-ssh.md)
- Previous Sequoia result: [FLR-0391](FLR-0391-apply-constant-lit-material-to-sequoia.md)
- Candidate lineage: rootfs `54da69d06c4a5d38c027453f7af4bec7e52b762fa732935766c04bebf533b690`, containing patch 0333
- Planned patch: `0334-flr0396-match-working-lit-material-interface-devtool.patch`

## Objective

Apply to every selected Sequoia primitive the same known-positive constant
LIT material definition used by the self-created fixture, then decide from a
live, full-frame QMP capture whether recognizable colored Sequoia pixels are
produced in the historical native-only visual-isolation condition. The HUD is
not part of this ticket's acceptance gate. FLR-0049's native-above-parent
condition masks the HUD by stacking; it does not prove that Flutter 2D was
disabled. This opt-in diagnostic override does not claim that Sequoia's
original PBR materials or embedded textures are fixed.

## Facts, inference, and unknowns

### Facts

- FLR-0394 on the exact FLR-0391 rootfs shows the self-created blue LIT/SUN
  fixture and CPU/GPU/FPS HUD together in a live QMP frame. Native ROI:
  `119716/144000` chromatic pixels.
- The positive fixture's constant-source branch uses
  `material.baseColor.rgb = vec3(0.05, 0.45, 1.0);`, declares
  `.parameter("color", FLOAT3)`, and sets the active instance to linear RGB
  `{0.05, 0.45, 1.0}`. The declaration/setter remain present even when the
  constant shader branch is selected.
- Patch 0333 gives Sequoia the same constant shader expression, LIT shading,
  target API, and platform, but removes the FLOAT3 declaration and instance
  setter. FLR-0391 reached READY/BOUND but its live Sequoia ROI was black in a
  run with two present begins, one return, and an FEngine Oops.
- Astra's read-only judgment recommends restoring only the fixture's FLOAT3
  declaration and linear setter while retaining the constant shader. Astra
  cautions that this is a justified controlled experiment, not a proven cause;
  parameter-layout equivalence and fault causality remain unknown.
- FLR-0049 Iteration 23 captured production Sequoia geometry and red lamps in
  QMP with the native surface above the Flutter parent; the HUD was not visible
  in that frame. This is a historical 3D-only visual reference, not a matched
  run on the current candidate image.
- The user supplied a separate 1280x800 historical frame showing the Flutter
  HUD/Scenes control and red vehicle-like pixels together. Its run/image
  identity is unavailable. The frame also shows `Shapes: On` and
  `Colliders: Off`; the large white wireframe-like lines are likely the Shape
  visualization, but their exact source is UNKNOWN.
- The existing fixed Podman machine is already running. Sandboxed localhost
  access was denied, but the fixed wrapper's escalated read-only status passed;
  no machine restart or creation is needed.

### Inference

The same shader text does not establish full material-definition equivalence.
The omitted parameter metadata/instance initialization is a concrete,
single-file difference worth testing before changing camera, texture, scene
light, or composition.

### Hypotheses

1. **Material-interface parity helps:** restoring the exact fixture FLOAT3
   declaration/setter yields visible blue Sequoia in the native-only
   visual-isolation frame.
2. **The difference is irrelevant:** the unused parameter does not alter the
   effective constant shader; Sequoia remains black and the first-fault/render
   boundary is elsewhere.
3. **A separate render fault dominates:** the same present/Oops signature
   prevents a valid visual result regardless of the material metadata.

The unused parameter's effect on generated metadata, resource layout, and
instance initialization is **UNKNOWN** until this comparison is built and run.

## 4W1H and problem point

| Dimension | Scope |
| --- | --- |
| What | Exact positive constant-blue LIT fixture material interface assigned to every selected Sequoia primitive |
| Where | `ModelSystem::setupRenderable` in the split `fluorite-plugins` source; canonical `meta-fluorite-trial`; authoritative Mini build/QEMU |
| When | One Devtool-generated patch 0334, one Mini image build, one bounded live-QMP runtime unit |
| Who | Mac Devtool source role; layer integration role; Mini BitBake role; guest `agl-driver` Flutter role; QMP evidence role |
| How | Preserve the constant shader and LIT profile; add the same FLOAT3 declaration and linear instance value used by the working fixture; keep selector, light, camera, geometry, and Flutter widget tree fixed; use only a verified, existing native-above-parent visual-isolation condition |

**Problem point:** Sequoia's override uses the proven color expression but not
the complete material interface used by the positive fixture. Whether that
difference affects output is the test, not a presumed root cause.

## Scope and exclusions

- Edit only `plugins/filament_view/core/systems/derived/model_system.cc` in the
  already-existing Devtool-managed source tree.
- Keep the Sequoia opt-in, asset predicate, constant GLSL source, LIT shading,
  target/platform, all-primitive assignment loop, destruction, SUN profile,
  camera, model transform, and Flutter widget tree unchanged. Use only the
  already documented FLR-0049 native-above-parent diagnostic presentation to
  keep HUD pixels out of this visual gate; do not describe that as disabling
  Flutter 2D. Keep Shape/Collider visualization out of the Sequoia pixel count.
- Add only the fixture's `.parameter("color", FLOAT3)` declaration and
  `setParameter("color", LINEAR, float3{0.05f,0.45f,1.0f})`. Add a narrow
  READY marker field if needed to prove the new setter path is selected.
- Generate patch 0334 only through the existing component-scoped Yocto Devtool
  `update-recipe` helper. Commit locally; push nothing.
- Transfer one verified Git bundle to the fixed Mini receiver. The Mini is the
  only authoritative full-image build host. Reuse its build/TMPDIR/caches and
  the existing Mac Podman machine/container/state.
- No Docker, extra machine/container/volume/workspace/TMPDIR, Mac image build,
  VM-image transfer, cache deletion, or `cleanall`/`cleansstate`.
- Do not change the test harness or repair FLR-0397 within this ticket.

## Success criteria

1. Devtool source is clean at exact post-0333 source commit
   `6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e`; the only source delta is the
   parameter declaration/setter (and a narrow identifying marker, if needed).
2. Official Devtool generates one nonempty patch 0334 from that baseline;
   recipe registration is unique and follows 0333. The layer commit passes
   privacy, baseline-lock, and whitespace checks.
3. The verified bundle reaches the fixed Mini receiver at the exact commit;
   Mini `do_patch`, `do_compile`, and full `agl-ivi-image-flutter` build pass.
4. Before launch, verify the exact existing native-above-parent/model-only
   presentation control against FLR-0049 and current source/configuration. Do
   not invent a new HUD-off switch or substitute a different profile silently.
   If the historical control cannot be identified on this image, record
   UNKNOWN and stop before claiming a 3D-only pass.
5. On the resulting exact image, one manual Example Demo run selects Sequoia
   and the LIT/SUN override. QMP captures a complete 1280×800 frame and short
   video while the same Flutter identity is live before and after capture.
6. This ticket passes only if the full QMP frame visibly contains recognizable
   diagnostic-blue Sequoia geometry under the verified native-only visual
   isolation condition. Record the HUD ROI as absent/occluded, plus fixed
   Sequoia ROI metrics, image hashes, present/fault state, and inspect the full
   image. This is not evidence of 2D+3D composition; FLR-0398 owns that gate.
7. Capture an attributable first userspace SIGSEGV with GDB if one occurs;
   also retain only a bounded kernel Oops/journal window for kernel faults.
   This is diagnostic evidence, not a substitute for the visual gate.
8. Stop the exact app and QEMU; independent postflight finds no residual
   QEMU/runqemu/flutter-auto process, QMP socket, or forwarded port.

If the material interface is applied but Sequoia remains black or the same
fault recurs, record a negative/UNKNOWN result and return to FLR-0395's
pre-armed GDB first-fault procedure. Do not add texture, camera, light, or
composition changes to this ticket.

## Impact

- **Build-time:** one `flutter-auto` source patch, target compile, and one
  authoritative Mini image build using the existing caches.
- **Packaging:** no package or dependency change; one opt-in source change on
  the existing `flutter-auto` patch stack.
- **Runtime:** only the diagnostic Sequoia material override is affected; the
  default path remains unchanged when the environment flag is absent. The
  native-above-parent presentation is a measurement condition, not a product
  composition fix.
- **Integration risk:** the declared FLOAT3 parameter is unused by the constant
  shader; Filament's generated metadata/instance behavior may make this a
  no-op. The visual experiment will determine whether this parity is
  sufficient, not prove that the parameter itself is causal.

## Plan / Do / Check / Act

### Plan

- Compare the exact positive material construction from `view_target.cc` with
  Sequoia's existing `model_system.cc` definition.
- Reset only the existing Devtool component registration, re-read the
  relocated attic source path, and verify clean HEAD `6946d02…` before edit.
- Add the FLOAT3 declaration/setter in the persistent source tree; commit the
  source change, then use the official Devtool component-rebase helper to
  generate patch 0334 and register it exactly once.
- Commit the layer, hand off one verified bundle to Mini, run progressive
  `do_patch`/compile/full-image gates, then one manual guest Flutter launch and
  QMP evidence capture.

### Do

- The existing Devtool component was reset without cleaning its source; the
  post-reset status was reread and the preserved source was verified clean at
  `6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e`.
- On source branch `devtool-FLR-0396-source`, only
  `plugins/filament_view/core/systems/derived/model_system.cc` changed. The
  diff adds the fixture FLOAT3 declaration, sets its linear value on the
  Sequoia instance, and identifies the parameter path in the READY marker.
  Source commit: `c9ffc87dee884af62099a18f95d7c72642997708`.
- The official component-scoped Devtool rebase/update-recipe helper passed
  with baseline `6946d02…` and source `c9ffc87…`. It generated canonical patch
  0334 byte-identically from Devtool output, SHA-256
  `73d1fb67b885a858f0cc4cca53cdee2c92a7c5e5d4041380647f516c98b7c240`,
  registered once after 0333, and refreshed the authorized project-layer
  baseline lock.
- Post-update `devtool-status` reports one `fluorite-plugins` component in the
  existing source tree.

### Check

| Gate | Result |
| --- | --- |
| Exact clean post-0333 Devtool baseline | PASS: `6946d02…` |
| Source diff scope | PASS: one C++ file; no camera/texture/light/composition changes |
| Official patch provenance | PASS: `From=c9ffc87…`; generated SHA recorded; reverse-apply check passes |
| Recipe order/uniqueness | PASS: 0334 appears once after 0333 |
| Post-update Devtool registration | PASS: one component/source pair |
| Repository verifier | NOT PASS: 147/148; one stale serial-exec fixture/invocation tracked separately in FLR-0397 |
| Mini bundle/build, live QMP, and teardown | Pending |

### Act

- Run privacy, baseline metadata, canonical, checkpoint, and whitespace gates;
  commit the generated layer patch/registration/lock and ticket records locally.
- Send one verified bundle to the fixed Mini receiver and use its existing
  BitBake build/TMPDIR. No Mac image build or VM-image copy.
- If the visual result is negative/faulted, FLR-0395 resumes; no unrelated
  changes are bundled. If it passes, FLR-0398 separately tests whether the
  Sequoia native surface and real Flutter HUD compose in one QMP frame.
