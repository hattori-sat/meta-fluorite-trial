# FLR-0371 — test LIT parameter color with RGB-only assignment

- Status: In Progress
- Priority: High
- Owner: Mac Podman Devtool / Mini build / direct guest SSH / Flutter / QMP roles
- Created: 2026-09-30
- Predecessor: [FLR-0370 material-color dataflow trace](FLR-0370-trace-fixture-material-color-dataflow.md)
- Implementation plan: [FLR-0371 plan](../../docs/superpowers/plans/2026-09-30-flr-0371-lit-parameter-rgb-assignment.md)
- Baseline: current rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- Branch: `feature-flr-0371-lit-parameter-rgb-runtime` (local, no push)
- Working log: [FLR-0371 working log](../logs/2026-09-30-flr0371.md)
- Build prerequisite: [FLR-0372](FLR-0372-fetch-plugin-git-submodules.md) is
  Done. The exact pinned `sdbus-cpp` gitlink is now fetched, and candidate
  `do_patch`, `do_configure`, and `do_compile` pass. The full image and the
  RGB-only candidate's runtime/QMP result remain unverified.

## Objective

Determine whether the parameter branch's whole-vector GLSL assignment is the
single difference preventing the self-made LIT/SUN 3D fixture from showing its
parameter color. Change only
`material.baseColor = vec4(materialParams.color, 1.0);` to
`material.baseColor.rgb = materialParams.color;`, using the existing Yocto
Devtool patch stack. Then build on the authoritative Mini and manually launch
Flutter over guest SSH; judge success only from full-frame QMP evidence.

This is a fixture/material discriminator, not production Sequoia acceptance.
No app-launch script changes are allowed in this ticket.

## Facts

- FLR-0367: current-image LIT/SUN + parameter source showed HUD and successful
  draw/present but a black native ROI.
- FLR-0368: the same parameter path rendered visible blue geometry with HUD in
  UNLIT mode (`119716/144000` native chromatic pixels).
- FLR-0369: the same current-image LIT/SUN fixture rendered dark-blue geometry
  with HUD when the constant-color flag was enabled (`119716` native chromatic
  pixels). The direct manual Flutter process later exited before the intended
  stop; that cause remains UNKNOWN.
- Patch 0249 changes both source and assignment form between branches. Patch
  0248's active-instance setter, FLOAT3 parameter value, LIT/SUN setup, camera,
  geometry, and renderable binding remain unchanged in this test.
- The fixed Mac `sources/fluorite-plugins` directory was incomplete at ticket
  start. It has now been rehydrated in place from the current Mini effective
  plugin source produced by recipe-scoped `do_patch` at exact
  `PLUGINS_COMMIT=2163242e9973336153871ed63b34bb5ed8282145`; target
  `view_target.cc` SHA-256 is
  `fe283fc5412ccbcc2d161bac814bc1683cf75c78bd1b60b035ef63abc8393413`.
- The patch-applied Devtool baseline is commit
  `599bf4ea72b2a5874fd3f296b756941eb05de946`, parent the pinned plugin HEAD.
  Official component-scoped `devtool add` succeeded and `devtool status`
  contains exactly the `fluorite-plugins` component/source pair.
- The one-line source change was committed as
  `7548f28bf50b3c3241efcfe8d4612440c0da0825`, directly on the complete
  baseline. The existing official Devtool helper generated the canonical
  patch `0330-flr0371-lit-parameter-rgb-assignment-devtool.patch`, SHA-256
  `069420d5293dc1f74ad739a18a4e9540cbf44efb16b4a3140d33113e122e3333`, and
  registered it once after patch 0327. The patch body was not hand-edited.
- Generated layer files were locally committed as
  `0e8aa99190a248784ab811bfe0008d2d0827db79` on
  `feature-flr-0371-layer-patch`, then fast-forwarded into the active feature
  branch without cherry-pick. The Devtool mount was restored clean to its
  original `devtool-flr-0371-mount` at `a3e779976d5dc74b777918d151835cf4c14cfd57`.
  A privacy-gate identity mismatch was repaired by amending only author and
  committer metadata; tree and parent stayed identical, and privacy then
  passed. No push occurred.
- The first generation-helper attempt stopped at its `baseline-branch`
  precondition because the source commit was on the baseline ref. This was a
  local branch-ordering mistake; no patch was generated on that attempt. The
  source commit was preserved on its own source branch, the baseline ref was
  restored, and the same helper then passed.
- `flutter-auto` is a composite recipe with a nested independent plugins Git
  source. Recipe-level `devtool modify flutter-auto` failed at existing patch
  0013's Git commit boundary; this was not a source hunk rejection. Historical
  FLR-0033/0113 and the project runbook establish component-scoped Devtool for
  this source. Continue from the exact Mini effective plugin baseline using
  official `component-add`/`update-recipe`; do not retry recipe-level
  `modify` or hand-edit generated patches.

## Hypotheses

1. **Assignment form is decisive.** With LIT/SUN and the parameter value fixed,
   RGB-only parameter assignment produces visible geometry. The current
   parameter full-vector assignment is the changed variable.
2. **LIT-specific parameter binding or shader generation is decisive.** The
   RGB-only parameter form remains black, while the constant-color LIT control
   remains visible.
3. **Lighting semantics are involved.** This remains lower-ranked because the
   constant-color LIT/SUN fixture is visible; separating LIT from SUN is a
   later test only if this one falsifies hypothesis 1.

## Scope and success criteria

- Use the one existing Mac Podman Devtool container and fixed persistent state.
  Do not initialize another Podman machine/container, create a second source
  workspace, edit `tmp/work`, or run Docker.
- Import the Mini post-`do_patch` `ivi-homescreen-plugins` source into the
  existing fixed Mac `fluorite-plugins` Devtool path, excluding only
  Quilt-generated `.pc/` and root `patches/` metadata. Confirm its upstream
  HEAD is exactly `PLUGINS_COMMIT`, record the effective source as a baseline
  commit, then use official component-scoped `devtool add` for
  `fluorite-plugins`. Verify the full patch-applied baseline before editing.
- Change only the parameter-source assignment to `.baseColor.rgb`. Preserve
  parameter declaration/type, active-instance setter/value, `prepareMaterial`,
  LIT/SUN flag, geometry, camera, launch profile, and software Vulkan setup.
- Generate the canonical recipe patch through official split-component
  `devtool update-recipe`; never hand-edit a patch or substitute
  `format-patch`/quilt. The Mini's recipe-scoped `do_patch` after bundle
  transfer is authoritative. Do not retry recipe-level `modify` or spend a
  Mac recipe-task loop on this nested Git source.
- Commit locally on this feature branch, create and verify a Git bundle, and
  transfer it to the fixed Mini receiver. No push. The Mini must prove exact
  bundle tip, `do_patch`, target compile, and full image build before runtime.
- Record disk headroom and expected duration before the long image build; do
  not clean caches or artifacts to make space.
- On the exact new image, use one fresh QEMU run and **manually** SSH into the
  guest as `agl-driver` to start exactly one `/usr/bin/flutter-auto` with the
  Example Demo bundle. Do not use an app-launch helper.
- Capture Flutter startup/readiness and fixture markers, then full 1280×800
  QMP still plus short QMP video. Stop after at most 8 successful presents or
  45 seconds. After the decisive capture, stop the recorded app PID immediately
  before evidence transfer/conversion. If it has already exited, capture the
  earliest available coredump/journal/app status and mark the cause UNKNOWN if
  evidence cannot establish it.
- Visually inspect the complete QMP frame. Report the fixed native ROI
  `(440,220,400,360)` and HUD ROI `(1120,0,160,80)` separately. A positive
  result requires recognizable self-made geometry and the 2D HUD together,
  with repeated successful presents and attributable image identity.
- Quit only this QEMU through its recorded QMP socket; verify no run-owned QEMU,
  runqemu, or flutter-auto process, socket, or forwarded port remains.
- Production Sequoia rendering and script automation are out of scope.

## Impact

- **Build-time:** one `flutter-auto` source patch, target compile, then the
  image build; reuse the existing Mini TMPDIR/downloads/sstate.
- **Packaging:** no intended package/dependency changes; the existing recipe
  patch stack carries one shader-expression change.
- **Runtime:** diagnostic LIT material source changes only the parameter
  assignment form; no compositor, scene, camera, light, or backend changes.
- **Integration risk:** limited to the opt-in native fixture. A passing fixture
  does not establish production Sequoia or a general color API fix.

## Plan / Do / Check / Act

### Plan

Use the 0367/0368/0369 three-way current-image comparison and FLR-0370's patch
trace. Rehydrate the split plugin source from the exact Mini post-`do_patch`
tree, commit that effective source as the Devtool baseline, then register it
with official component-scoped Devtool. Change one GLSL assignment and run
official `update-recipe`; follow canonical layer commit/bundle → Mini build →
manual guest-SSH Flutter launch → QMP pixel verdict. Do not edit or extend a
launcher.

### Do

- Official `devtool modify flutter-auto` was attempted once through the
  persistent Podman wrapper. It failed at existing patch 0013's Git commit
  boundary before the source edit. Current source identity and historical
  workflow records establish this as the wrong Devtool boundary for the nested
  plugin Git source. No source or patch was edited.
- Mini's fresh recipe-scoped clean→`do_patch` gate passed at the current pins
  and exact active layer tree. It provides the current post-patch plugin source
  for the component-scoped baseline; the earlier Sep 14 workdir/log is stale.
- Replayed the existing-image LIT/constant-color positive control by manually
  launching Flutter over strict guest SSH. This verifies the QEMU→SSH→Flutter
  route, not the RGB-only assignment under test.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Devtool source baseline | Component-scoped source begins at exact PLUGINS_COMMIT and includes current recipe patches | 478-file source/index baseline committed; exact pinned parent; one Devtool registration | PASS |
| One-variable source diff | Only parameter-source assignment changes from whole vec4 to `.rgb` | One file, one insertion/one deletion; source commit parent is full baseline | PASS |
| Official patch generation | Official Devtool patch is generated and registered unchanged | Patch 0330 SHA `069420d5…`; one exact hunk; bbappend registration once; privacy and whitespace checks pass | PASS; Mini apply pending |
| Mini candidate patch gate | Exact candidate commit is received and `do_patch` passes | Bundle tip `f4e32cb2da2301ecb502e31bcda746084e32bddb` reached the clean Mini receiver; candidate `do_patch=PASS` | PASS |
| Candidate configure / compile | Required plugin submodule is present; configure and compile pass | `do_compile -f` stopped at `do_configure`: required `sdbus-cpp/CMakeLists.txt` is missing; FLR-0372 owns the fetch prerequisite | BLOCKED |
| Candidate image / runtime | Exact candidate image boots; manual Flutter/QMP shows assignment result | Not started; production and RGB-only candidate verdict remain UNKNOWN | PENDING |
| Direct manual runtime | One `agl-driver` Flutter process; launch and native setup markers captured | Existing-image LIT/constant-color control; 10 presents at first gate, 163 recorded by log retrieval; exact PID stopped | PASS (control only) |
| QMP acceptance | Visible native geometry and 2D HUD in same complete frame; ROI/video evidence retained | QMP full frame shows dark-blue fixture and HUD together: native 92,352/144,000 chromatic pixels; HUD 2,845. RGB-only assignment remains unbuilt/unverified. Evidence retained under `$BUILD_EVIDENCE/flr0371-0001/qemu/` | PARTIAL |
| Teardown | Exact app and QEMU stopped; process/socket/port checks clean | App PID 812 stopped; QMP quit accepted; independent checks found no QEMU/runqemu/Flutter, QMP socket, or listeners on run ports | PASS |

### Act

- If parameter RGB-only assignment becomes visible under LIT/SUN, preserve it
  as the candidate fix and create a separate production Sequoia validation
  ticket; do not infer production success from the fixture.
- If it remains black while the constant branch remains visible, keep the
  result as a falsification and open the next ticket to separate shader
  parameter binding from LIT/SUN; do not alter launch scripts or multiple
  source variables in this ticket.
- If the app exits before controlled stop, keep the QMP result but split the
  process-exit diagnosis into a separate ticket unless the evidence directly
  identifies a blocker to this fixture verdict.
- Resume this ticket only after FLR-0372 proves the exact plugin source and
  its pinned `sdbus-cpp` submodule are fetched, patched, configured, and
  compiled. Do not treat the existing-image positive control as the candidate
  patch result.

## Visual evidence

- Baseline negative: [FLR-0367 QMP screenshot](../evidence/FLR-0367-qmp-run-0001.png).
- UNLIT parameter positive: [FLR-0368 QMP screenshot](../evidence/FLR-0368-qmp-run-0001.png).
- LIT/SUN constant positive: [FLR-0369 QMP screenshot](../evidence/FLR-0369-qmp-run-0001.png).
- Current-image positive control (not the assignment result): full QMP PPM
  SHA-256 `65ccb48597d2f227bd80c9dab23a541a6a79feba6fc4d7b8bbb2cbf1312aed07`;
  8-frame QMP video and original captures are retained under the Mini evidence
  role path `$BUILD_EVIDENCE/flr0371-0001/qemu/`.

## UNKNOWN

- Exact lower-level Git operation that caused recipe-level `devtool modify`
  to fail at the nested source commit boundary for existing patch 0013; its
  ephemeral task log was no longer present. Component-scoped Devtool is now
  used for the separately pinned plugin source.
- Whether RGB-only parameter assignment makes the current LIT/SUN fixture
  visible.
- Why the first manual screenshot had a black native ROI; that capture was
  taken without waiting for a successful-present readiness gate, so it is not
  evidence of a regression.
- Why the FLR-0369 app process exited before intentional stop.
- Whether the production Sequoia scene is correctly visible with HUD.
