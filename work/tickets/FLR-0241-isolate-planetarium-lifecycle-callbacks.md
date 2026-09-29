# FLR-0241 — isolate Planetarium lifecycle callbacks

- Status: Done
- Priority: High
- Owner: Planetarium widget lifecycle and native command roles
- Created: 2026-09-20
- Predecessor: FLR-0240

## Objective

Separate mounting the `PlanetariumSceneView` widget from the native commands
issued by its lifecycle callbacks. Keep the FLR-0240 child-only parent boundary
and QMP contract unchanged, but temporarily make the Planetarium lifecycle
callbacks inert. Determine whether `onCreate`/`onUpdateFrame` or widget mount
alone causes the white HUD.

## Facts

- FLR-0239 proves parent `setState` is sufficient to whiten the HUD.
- FLR-0240 replaces parent rebuild with `ValueNotifier`/
  `ValueListenableBuilder`, then mounts `PlanetariumSceneView` on tap.
- FLR-0240 still produces HUD `0`/uniform white after activation while native
  ROI stays `24178`.
- The current Planetarium `onCreate` calls `camera.setActive`, queues fog and
  visibility commands, and `onUpdateFrame` queues orbit transforms.
- The existing FLR-0237 A/B already makes `build()` return `SizedBox.shrink()`;
  the remaining active behavior is lifecycle/native callbacks.
- A provisional edit made before `devtool modify --no-extract` was rejected:
  Devtool treated that edited tree as its baseline and emitted no patch. Its
  commit remains only as an unaccepted history branch.
- The corrected sequence established the FLR-0240 effective source commit
  `ea824e41a4cb83afdcc2cf9189221b4a5d90df3c` as the Devtool baseline, then
  committed the edit as `7eda35d03d607ac44d1d60c2c12fb149a3f0b26b`.
- Official `update-recipe --mode patch --append --no-remove
  --force-patch-refresh` generated the patch and official finish copied it
  byte-for-byte into the canonical layer.
- The inert-callback image still changed the HUD from `2845` chromatic pixels
  to uniform white after the tap, while the native fixture stayed at `24178`
  chromatic pixels.
- The bounded runtime slice contained the FLR-0240 scene activation marker and
  Wayland attach, but no observed `FLR0241_PLANETARIUM_LIFECYCLE_INERT` marker;
  callback invocation timing is therefore not yet proven.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Planetarium lifecycle/native commands trigger the white composition | inert callbacks keep HUD chromatic; active callbacks reproduce white | the scene will not be functionally activated in the control |
| 2 | Mounting the StatefulSceneView itself triggers white | inert callbacks still whiten HUD | points below widget lifecycle into Flutter/Wayland child mount |
| 3 | `ValueListenableBuilder` child replacement is sufficient | a no-op child replacement also whitens HUD | composition boundary is independent of Planetarium code |

The first A/B disables only the Planetarium callback bodies; it does not alter
camera, light, material, fixture, or parent Stack code.

## Success criteria

- The source change is generated through the official Mac Devtool flow from
  the FLR-0240 effective source commit.
- Mini `do_patch`, compile, and full image gates pass for the exact bundle tip.
- QMP initial/post-tap frames and bounded runtime marker distinguish inert
  versus active lifecycle behavior.
- Guest logs, artifact hashes, and clean QEMU teardown are retained.
- If callbacks are causal, open a separate ticket for the smallest safe native
  scene activation command; do not mix the diagnostic no-op into production.

## Evidence

- Predecessor: [FLR-0240](FLR-0240-mount-scene-subtree-without-parent-repaint.md)
- Working log: [2026-09-20-flr0241.md](../logs/2026-09-20-flr0241.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0241/`
- Canonical patch:
  `layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/0073-flr0241-isolate-planetarium-lifecycle-callbacks-devtool.patch`.
- Patch SHA-256:
  `74ef148ee2871f40bac3a3bb647a13a93d8592315989b9bb21172120610f4eba`.

## Result

Disabling both Planetarium native lifecycle bodies did not change the failure:
the HUD still became uniform white after the child was mounted, while the
self-made native 3D fixture remained visible. The callback commands are not a
sufficient cause. The next discriminator is the widget/stateful-view mount
boundary, owned by FLR-0242.

## Verification

- Canonical commit: `537433fd29743d122120a92acaaa12963d60fd77`.
- Bundle SHA-256: `b83ffb32b69bb031fe712dbf57f8e1265f4aa5d72856f9b688f2021af93039e1`.
- Mini receiver preflight and recipe `do_patch`: PASS.
- Mini compile: `COMPILE_RC=0`, 1,674/1,674 tasks succeeded.
- Mini image: `IMAGE_RC=0`, 11,758/11,758 tasks succeeded.
- Rootfs: `agl-ivi-image-flutter-qemux86-64.rootfs-20260920152750.ext4`.
- Rootfs SHA-256: `bd72a619b35fae7e36c510f4c99c04bd17e2a7d248be729bd1ccaad6dd7029a0`.
- Qemuboot SHA-256: `e45a719d7892fbd0a2ca804db4a16d6e7ff99f03ea3a4554cba1622b8c61f954`.
- Kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP evidence: `$EVIDENCE_ROOT/FLR-0241/qmp-lifecycle/`.
- Pixel analysis: `$EVIDENCE_ROOT/FLR-0241/pixel-analysis.jsonl`.
- Initial/move/down: HUD `2845`, native ROI `24178`.
- Up after tap: HUD `0`/uniform white, native ROI `24178`.
- Runtime marker slice: `$EVIDENCE_ROOT/FLR-0241/scene-marker.output`.
- Runtime marker evidence SHA-256: `7f89e6e388999d19df9f233a2283c0201c33479`.
- Pixel analysis SHA-256: `a44951fd78014597c56b99d1f4ac495d0b6f30d5a1dab0459234ace9fcd0795e`.
- Cleanup: `residual_targets=0`, `residual_qmp=0`.

## UNKNOWN

- Whether a generic inert `StatefulSceneView` mount also whitens the HUD.
- Whether `PlanetariumSceneView`-specific state or callback registration is
  required for the white frame.
- Whether a production-safe scene activation can avoid the faulty boundary.
