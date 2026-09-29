# FLR-0371 — test LIT parameter color with RGB-only assignment

- Status: In Progress
- Priority: High
- Owner: Mac Podman Devtool / Mini build / direct guest SSH / Flutter / QMP roles
- Created: 2026-09-30
- Predecessor: [FLR-0370 material-color dataflow trace](FLR-0370-trace-fixture-material-color-dataflow.md)
- Baseline: current rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- Branch: `feature-flr-0371-lit-parameter-rgb-assignment` (local, no push)
- Working log: [FLR-0371 working log](../logs/2026-09-30-flr0371.md)

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
- Read-only inspection found the existing Podman container running, but no
  `view_target.cc` or `.git/HEAD` in its persistent source tree. FLR-0208 had
  previously recorded a complete source baseline. The current missing-tree
  cause is UNKNOWN; this ticket must first load the current recipe source via
  official Devtool, not hand-repair or hand-create source history.

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
- Run official Devtool against the currently registered `flutter-auto` recipe
  and its committed `meta-fluorite-trial` patch stack. Confirm a complete source
  Git baseline and the expected 0248/0249/0250/0251/0295 history before editing.
  If Devtool cannot provide that source identity, stop without editing.
- Change only the parameter-source assignment to `.baseColor.rgb`. Preserve
  parameter declaration/type, active-instance setter/value, `prepareMaterial`,
  LIT/SUN flag, geometry, camera, launch profile, and software Vulkan setup.
- Generate the canonical recipe patch through official Yocto Devtool; never
  hand-edit a patch or use `format-patch`/quilt as a replacement. Pass the Mac
  `do_patch`/target compile gates before committing the layer change.
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
trace. Rehydrate the Devtool source through the active recipe so existing
committed patches are part of its source history. Change one GLSL assignment,
then follow Mac Devtool → canonical layer commit/bundle → Mini build → manual
SSH Flutter launch → QMP pixel verdict. Do not edit or extend a launcher.

### Do

- Pending Devtool source identity and one-variable assignment change.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Devtool source baseline | Current recipe and complete source Git history include the active patch stack | Pending | PENDING |
| One-variable source diff | Only parameter-source assignment changes from whole vec4 to `.rgb` | Pending | PENDING |
| Official patch / Mac gate | Devtool-generated patch applies and target compile succeeds | Pending | PENDING |
| Bundle / Mini build | Exact local commit is received; do_patch, compile, image pass | Pending | PENDING |
| Direct manual runtime | One `agl-driver` Flutter process; launch and native setup markers captured | Pending | PENDING |
| QMP acceptance | Visible native geometry and 2D HUD in same complete frame; ROI/video evidence retained | Pending | PENDING |
| Teardown | Exact app and QEMU stopped; process/socket/port checks clean | Pending | PENDING |

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

## Visual evidence

- Baseline negative: [FLR-0367 QMP screenshot](../evidence/FLR-0367-qmp-run-0001.png).
- UNLIT parameter positive: [FLR-0368 QMP screenshot](../evidence/FLR-0368-qmp-run-0001.png).
- LIT/SUN constant positive: [FLR-0369 QMP screenshot](../evidence/FLR-0369-qmp-run-0001.png).
- This ticket's result will add its own full QMP PNG and short video here.

## UNKNOWN

- Why the current persistent Devtool source files and Git HEAD are absent.
- Whether RGB-only parameter assignment makes the current LIT/SUN fixture
  visible.
- Why the FLR-0369 app process exited before intentional stop.
- Whether the production Sequoia scene is correctly visible with HUD.
