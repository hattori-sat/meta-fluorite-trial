# FLR-0245 — isolate Builder from platform-view composition

- Status: Done
- Priority: High
- Owner: Flutter Builder and native platform-view/Wayland composition boundary
- Created: 2026-09-21
- Predecessor: FLR-0244

## Objective

Remove the `ValueListenableBuilder` from the tested scene subtree while
retaining the same native fixture, parent `Stack`, 2D HUD, QMP input
coordinates, and pixel ROIs. Determine whether the Builder itself is required
for the post-input white HUD or whether the failure remains below it at the
Flutter platform-view/Wayland composition boundary.

## Facts

- FLR-0235 proves simultaneous 2D HUD and self-made native 3D pixels.
- FLR-0243 proves a plain child replacement whitens the HUD while native 3D
  remains chromatic.
- FLR-0244 proves a notifier-driven Builder rebuild that returns the same
  `const SizedBox.shrink()` child also whitens the HUD.
- The FLR-0244 native ROI remained `100800` chromatic pixels through button-up.
- FLR-0245 directly mounted the same stable `const SizedBox.shrink()` without
  `ValueListenableBuilder`; the HUD stayed chromatic through button-up.
- Initial, move-x, move-y, down, and up frames each had `2883` chromatic HUD
  pixels and `100800` chromatic native-ROI pixels.
- Native readiness, shape creation, render, readback, and QMP pointer button
  markers were present. Cleanup found no QEMU, QMP, or flutter-auto residue.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | `ValueListenableBuilder` rebuild/compositing boundary | Directly mounting the same stable child preserves the HUD | The parent Stack or platform view may still repaint independently |
| 2 | Flutter/native platform-view or Wayland composition below Builder | Direct mount also whites the HUD while native ROI remains chromatic | Requires a lower-level surface/compositor discriminator |
| 3 | QMP input or button release artifact | A no-input/direct-mount control does not white the HUD | Existing FLR-0231/0233 evidence makes this lower probability |

## Scope and invariants

- Change only the scene-subtree wrapper needed to remove the Builder.
- Do not change Filament engine, camera, light, material, native fixture,
  parent `Stack`, window size, QMP coordinates, or ROI thresholds.
- Use the fixed Mac Devtool source baseline and official generated patch flow.
- Use the existing Mini build/TMPDIR and one QEMU run; save QMP evidence before
  teardown.

## Success criteria

- [x] Static source inspection identifies the minimal Builder-removal A/B.
- [x] Mac Devtool source commit and generated patch are recorded; no hand-authored
  patch is accepted.
- [x] Exact bundle passes Mini `do_patch`, compile, and full image gates.
- [x] QMP initial and button-up frames are analyzed for HUD and native ROIs.
- [x] Bounded runtime markers/logs are saved before QMP quit, and all residual
  QEMU/QMP/flutter-auto processes are zero.
- [x] The result selects the Builder boundary for the next ticket.

## Evidence

- Predecessor: [FLR-0244](FLR-0244-isolate-builder-rebuild-from-child-identity.md)
- Working log: [2026-09-21-flr0245.md](../logs/2026-09-21-flr0245.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0245/`
- Source commit: `8c11c515252841e3d18b606b728bc53f76f26cd8`.
- Official generated patch:
  `0077-flr0245-isolate-builder-from-platform-view-composition-devtool.patch`.
- Patch SHA-256: `e2a17fcaef233a6f06589328cfffacebbcdb285c7741dd16233a937adf625d84`.
- Canonical layer commit: `5ca03b58a6e128648c6077ca2fffbc4554a8b467`.
- Bundle SHA-256: `da7401b704bfdef2c0a1445af050982ec57c627506223ea8b86ce2bbf5f5493f`.
- Mini rootfs SHA-256: `77d801f21ff26b4c7168486620f010b90275a350aa21c3ea083ff450c195d003`.
- Mini qemuboot SHA-256: `dd01d6a0028a2e8de09a3d247fc9a895299ab32fb5b7fe1df6bc3aeedf15a22f`.
- Mini kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP initial/up SHA-256: `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.
- Pixel analysis SHA-256: `511c206fefdc4e5b4866cb175fa5bf9de5838e98a459d73091f841a4851765d0`.
- Bounded app-log SHA-256: `ab329776bdb01a9a487c1e3c1a97d869e8a73d47481fdd6e3f587ebde1e7fce3`.
- Cleanup: `qmp_residual=0 qemu_residual=0 app_residual=0`.

## UNKNOWN

- Whether mounting `PlanetariumSceneView` directly, without a Builder, keeps
  the HUD stable while preserving its lifecycle.
- Whether the production Planetarium geometry is visible independently of the
  self-made native fixture.
