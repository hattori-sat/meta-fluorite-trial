# FLR-0226 — fix Flutter-parent hover composition

- Status: Done (hypothesis falsified; follow-up FLR-0227)
- Priority: High
- Owner: Flutter parent composition and runtime evidence role
- Created: 2026-09-20
- Predecessor: FLR-0225

## Objective

Keep the Flutter parent surface transparent and stable when the pointer enters
the Scenes control area, while preserving the diagnostic native cube and 2D HUD.
Then prove that the Scenes menu and route callback can be exercised without the
white occluding frame.

## Success criteria

- The exact FLR-0224 image identity is recorded before source work.
- The app source is opened through the fixed Mac Devtool workspace whose Git
  history contains the complete effective source baseline.
- The change is made in source, committed in that source Git, and converted to
  a recipe patch by the official `devtool update-recipe` flow.
- Mini `do_patch`, `do_compile`, and the image build pass using the bundle from
  the canonical layer commit.
- QMP evidence shows the initial and pointer-enter frames retain the native
  cube ROI and transparent HUD/background behavior; menu open and route
  activation are tested separately.
- Exactly one QEMU instance is used and teardown leaves no target, app, or QMP
  socket.

## Scope boundary

- Do not change camera, light, material, production-scene, or native WSI code
  until the Flutter-parent hover boundary is cleared.
- Do not hand-edit a generated patch or copy a patch directly into the layer.
- Do not use a layer-only patch commit as the next Devtool source baseline.

## Hypotheses

| Rank | Hypothesis | Prediction | Discriminator |
| --- | --- | --- | --- |
| 1 | Flutter parent clear/alpha contract is not preserved during hover repaint | a minimal transparent-parent correction keeps the HUD/background from becoming white while the native ROI is unchanged | initial vs target-area pointer QMP ROI and focused parent commit log |
| 2 | `MenuAnchor` hover repaint introduces an opaque intermediate layer | parent correction alone does not prevent white, but removing or constraining the hover layer does | source-level A/B with identical input and QMP capture |
| 3 | The white frame is outside the Flutter app | neither Flutter source change affects the frame and compositor evidence identifies another surface | bounded Wayland/compositor evidence |

## Plan / Do / Check / Act

### Plan

1. Repair or recreate the fixed Mac Devtool app source workspace through the
   official Devtool lifecycle; verify its baseline and source Git history.
2. Inspect the exact parent alpha and `MenuAnchor` source contract before
   editing; choose the smallest hypothesis-driven source change.
3. Commit the source change, run official `devtool update-recipe`, and verify
   the generated patch against the source commit.
4. Commit only the canonical layer patch/recipe registration change, bundle it,
   and send the bundle to the fixed Mini receiver.
5. Run bounded Mini build gates and one QMP A/B runtime with evidence.

### Do

- Restored the Mini `do_patch` effective source into the same fixed Mac
  Devtool source path; the complete source snapshot contains 603 tracked
  files. The incomplete prior Git metadata and intermediate append files were
  moved into the fixed state attic, not deleted.
- Created the complete source baseline commit
  `8eaaa89cf8a7e34efacaf688450d0256d73d717` and registered it with the
  official `devtool modify --no-extract` flow before editing.
- Edited only `packages/filament_scene/example/lib/main.dart` to make the
  `MaterialApp`, `ThemeData`, and normal `Scaffold` surfaces explicitly
  transparent. Committed the one-file source change as
  `fed6ebc218b5a6a8d346c0f66a971caee0b273c2`.
- Ran official `devtool update-recipe` from the baseline-to-change history and
  produced exactly one patch. The generated patch SHA-256 is
  `53d052e8a849e7d0034f8cca2e8f20f524c1a180ba896a76bc26ec48c8414eaa`.
- Ran the official `finish-source` lifecycle and used the deterministic
  finish helper to register the byte-identical generated patch in the app
  recipe. The helper was extended to support app recipes whose `SRC_URI` is in
  the `.bb` file rather than a `.bbappend`.
- A first attempt registered after the edit and therefore set `initial_rev` to
  the changed commit, producing no patch. That source commit was retained,
  the branch was returned to the complete baseline, and the official sequence
  was repeated successfully. A stale Devtool marker append was moved to the
  state attic.
- Mini patch gates and image build passed from the canonical bundle:
  `do_patch=PASS`, `do_compile=PASS`, and `image-build=PASS`. The resulting
  rootfs SHA-256 is
  `1afc36864cf271239e9cc1695d3c0cdaef11aeeb86a43274c0578af429ef9654`.
- The fixed QMP runtime used exactly one QEMU instance and the reusable
  commands in `work/commands/FLR-0226-*`. Initial and `move-x` frames have
  PPM SHA `830fd73a...`; `move-y`, `down`, and `up` have PPM SHA
  `83b474a...`.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Complete Devtool source baseline | source Git has valid HEAD/index and effective history | 603-file Mini effective source; baseline `8eaaa89` | PASS |
| Source hypothesis | one minimal change with explicit prediction | root Material/Scaffold transparency change committed as `fed6ebc` | PASS |
| Official patch generation | `devtool update-recipe` succeeds from source commit | exactly one patch; SHA `53d052e8...` | PASS |
| Canonical layer registration | generated patch is byte-identical and registered once | app recipe `0064-flr0226-transparent-material-parent-devtool.patch` | PASS |
| Mini build | do_patch/do_compile/image pass | all three passed; rootfs SHA recorded above | PASS |
| QMP runtime | no white occlusion on pointer entry; menu/route evidence | native ROI stayed chromatic, but parent/HUD ROI became uniform after `move-y` exactly as in FLR-0225 | FAIL for this hypothesis |
| Teardown | no residual target/app/QMP socket | QMP quit and cleanup passed; residual target count 0 | PASS |

### Act

The explicit Material/Scaffold transparency correction did not change the
white-frame transition. Retain FLR-0226 as a completed falsification and use
FLR-0227 for the smallest `MenuAnchor`/hover-layer and compositor A/B. Do not
mix route activation or production light/material changes into that ticket.

## Facts

- FLR-0225 isolated the first visual divergence to Flutter-parent repaint after
  pointer motion into the Scenes control area.
- The native diagnostic cube ROI stayed unchanged while the HUD/background ROI
  became uniform white.
- Static source inspection shows route activation is on button `onPressed`;
  pointer hover is not the route callback.
- The canonical layer now contains the official generated patch and a single
  `SRC_URI` entry in the app recipe. No hand-authored patch content was used.
- The Mini image booted the diagnostic cube and 2D HUD before input. QMP
  native ROI analysis reported `chromatic_pixels=24178` in the initial and
  hover frames. The top-right HUD ROI changed from a non-uniform frame to
  uniform luma 255 with `chromatic_pixels=0`, `edge_pixels=0`, and all 12800
  pixels changed after the vertical pointer move.
- Focused runtime markers showed successful Vulkan present (`result=0`) and
  continued parent-surface attach/damage/frame/commit traffic. The native ROI
  did not change, so this run does not support a native 3D rendering failure.

## UNKNOWN

- Whether the clear/alpha contract or the hover layer owns the white pixels;
  the parent-level transparency correction alone is falsified.
- Whether route activation works after the parent remains transparent.
- Whether `MenuAnchor`/`FilledButton` introduces an opaque intermediate layer.

## Evidence

- Predecessor ticket: [FLR-0225](FLR-0225-diagnose-post-input-white-composition.md)
- Evidence root: `$EVIDENCE_ROOT/FLR-0226/`
- Working log: [2026-09-20-flr0226](../logs/2026-09-20-flr0226.md)
- Follow-up: [FLR-0227](FLR-0227-isolate-menuanchor-hover-composition.md)
