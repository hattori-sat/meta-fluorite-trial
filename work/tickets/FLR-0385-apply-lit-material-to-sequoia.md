# FLR-0385 — apply the proven LIT material to production Sequoia

- Status: In Progress
- Priority: High
- Owner: Mac Podman Devtool / meta-fluorite-trial / Mini BitBake / manual guest Flutter / QMP evidence roles
- Created: 2026-09-30
- Predecessors: [FLR-0371 LIT/SUN parameter fixture positive](FLR-0371-lit-parameter-rgb-assignment.md), [FLR-0383 Sequoia UNLIT override negative](FLR-0383-sequoia-known-material.md)
- Implementation plan: [FLR-0385 plan](../../docs/superpowers/plans/2026-09-30-flr0385-lit-material-sequoia.md)
- Branch: `feature-flr-0385-sequoia-lit-material` (local; no push)
- Dev baseline: `dev-flr-0385-sequoia-lit-material-baseline` at `8f0b2267e781722cf85bf29b02565bf6d500ecc0`, including patch 0331; this is a development base, not a 3D-success claim.
- Working log: [FLR-0385 working log](../logs/2026-09-30-flr0385.md)

## Problem

### Purpose

Use the exact parameterized LIT material that made the self-created fixture
visible, and apply it to every selected renderable primitive in production
`sequoia_ngp.glb`. Prove from a complete QMP frame whether colored Sequoia and
the CPU/GPU HUD are visible together.

### Facts

- FLR-0371-0004 showed a dark-blue LIT/SUN fixture and the CPU/GPU HUD together
  in one 1280×800 QMP frame. Its shader assigns
  `material.baseColor.rgb = materialParams.color`, with FLOAT3 parameter
  `(0.05, 0.45, 1.0)` in linear RGB; the fixture used a SUN with color
  `(1.0, 0.9, 0.8)`, intensity `110000`, direction `(0.7, -1.0, -0.8)`, and
  angular radius `1.9`.
- FLR-0383 applied a generated blue UNLIT material to all 24 selected Sequoia
  renderables. `READY=1`, `BOUND=24`, `BUILD_FAILED=0`; HUD visible, central
  3D ROI uniformly black. This did not prove visible Sequoia geometry.
- The existing opt-in `FLR0305_PRODUCTION_SCENE_LIGHT` installs the same
  diagnostic SUN parameters in the default production scene. It can be reused
  for a conditional second profile; no new light implementation is needed.
- The latest committed Sequoia material code is in patch 0331. The persistent
  Devtool source was read-only checked before editing: clean branch
  `devtool-FLR-0383-source`, HEAD exactly
  `4acaa4c0194303227a2207bbbed9ea2249b72efb`. Patch 0331's `From` matches that
  HEAD and is registered once after 0330. Its all-primitive binding and
  teardown are intact.

### Inferences

- The existing UNLIT negative means another UNLIT repeat would add little
  information. A parameterized LIT override tests the fixture's proven shading
  path against the same production geometry while preserving camera, asset,
  scene, HUD, and renderer settings.
- LIT success on Sequoia would prove that the production geometry can emit
  visible pixels under this diagnostic material; it would not prove that the
  original GLB PBR materials or textures are correct.
- If LIT-only is black but adding the existing SUN changes it, lighting
  conditions contribute to visibility. Because the SUN is added to the
  production scene rather than replacing unknown scene lights, that result is
  not by itself proof of a missing-light root cause.

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Known-positive LIT material on all selected Sequoia renderables; HUD and visible colored car in one frame | FLR-0371-0004 and FLR-0383-0001 |
| Where | `ModelSystem::setupRenderable` in the split `fluorite-plugins` source; Mini's fixed authoritative Yocto build and QEMU | Patch 0331 and fixed build/runtime runbooks |
| When | Fresh layer patch/image, then profile A and conditionally profile B in one QEMU instance | This ticket's single run ID `flr0385-0001` |
| Who | Devtool source, layer integration, Mini BitBake, guest `agl-driver`, Flutter, QMP evidence roles | Role-scoped runbook |
| How | Same shader/color as FLR-0371; bind all primitive slots; A keeps the production profile; B changes only the existing SUN opt-in | Source diff and PID-bracketed QMP evidence |

### Process analysis

| Step | Expected | Current observation | Evidence |
| --- | --- | --- | --- |
| Material positive control | Fixture LIT/RGB path creates visible blue pixels with HUD | Proven on FLR-0371 candidate | FLR-0371-0004 screenshot/measurements |
| Sequoia override | Same material binds all selected primitive slots | Prior UNLIT path bound 24; new LIT path not yet implemented | FLR-0383-0001 |
| Scene lighting | Profile A preserves production conditions; profile B adds only the existing SUN probe | A/B not yet run | To be recorded in this ticket |
| Visible output | Full QMP image contains identifiable Sequoia and HUD together | UNKNOWN | QMP capture pending |

### Problem point

The first unproven boundary is whether a proven LIT material, bound to Sequoia
renderables, produces visible pixels in the production view. The current record
does not isolate material from light or downstream visibility/present/composition.

### Ideal condition and success measure

At least one liveness-bracketed, full-frame QMP capture from the exact built
image visibly shows recognizable Sequoia body geometry in the diagnostic blue
and the CPU/GPU HUD at the same time. `READY`/`BOUND`, runtime logs, build
success, or a colored HUD alone do not pass. Record the complete screenshot,
short QMP video, image identities, material/light markers, fixed vehicle and
HUD pixel measurements, and successful-present/liveness result.

## Root-cause hypotheses

1. **Material profile is sufficient.** LIT/RGB override under the current
   production lighting profile yields blue Sequoia pixels and HUD; the prior
   black ROI depended on the UNLIT profile or its rendering interaction.
2. **The fixture's SUN condition is additionally required.** Profile A remains
   black with material READY/BOUND; profile B, changing only
   `FLR0305_PRODUCTION_SCENE_LIGHT`, produces visible Sequoia pixels.
3. **Failure is downstream or Sequoia-specific.** Both profiles bind the
   material but show no recognizable car in live QMP; camera/visibility,
   geometry submission, present, or composition remains unresolved.

## Scope

### In scope

- One opt-in LIT material override on every primitive of the selected Sequoia
  models, generated through the existing persistent Devtool component source.
- Exact parameterized shader/color from FLR-0371; existing SUN switch only as
  the conditional profile B.
- Official Devtool patch generation, local layer commit, verified Git bundle,
  fixed Mini receiver/build/TMPDIR, and target-level QMP screenshots/video.

### Out of scope

- Camera, vehicle transform, GLB asset/texture, HUD/surface, scene route,
  renderer/compositor, or launcher-script changes.
- Rebuilding Mac-side images, transferring QEMU disk images to Mac, deleting
  caches, `cleanall`, `cleansstate`, or creating another Podman/container/TMPDIR.
- Claiming the original Sequoia PBR materials or texture path is fixed.

## Success criteria

1. Before source edit, fixed Devtool source is clean and matches patch 0331's
   exact `From` baseline; no duplicate component/container/build tree exists.
2. The Devtool source delta changes only the Sequoia diagnostic material from
   UNLIT to the parameterized LIT profile, with the proven RGB expression and
   color; all primitive slots stay covered and normal behavior stays unchanged
   when the opt-in is absent.
3. Official Devtool generates exactly one new patch 0332 from the immediate
   0331 source baseline; it is registered once after 0331. `do_patch`, target
   compile, and the full image build pass on Mini at the exact bundle tip.
4. Profile A, and profile B only if needed, use the same candidate image, QEMU,
   app bundle, model selection, session, and capture conditions. Profile B
   adds only `FLR0305_PRODUCTION_SCENE_LIGHT=1`.
5. At least one live-PID-bracketed QMP full frame visibly shows colored,
   recognizable Sequoia and the CPU/GPU HUD together. If neither profile does,
   classify this ticket as a bounded negative result and keep the top-level
   3D goal open.
6. Exact app/QEMU teardown and independent zero-residual process/socket/port
   checks pass. Raw QMP PPM/log evidence stays on Mini; only QMP-derived review
   media may be kept locally. No QEMU disk image is copied to Mac.

## Impact

- **Build-time:** one `flutter-auto` source delta, recipe patch gate, component
  compile, and authoritative image build; reuse the fixed Mini caches/TMPDIR.
- **Packaging:** no package/dependency changes; patch 0332 is on the existing
  `fluorite-plugins` recipe patch stack.
- **Runtime:** opt-in material override only; profile B adds the existing
  default-scene SUN probe. No change when the new material flag is unset.
- **Integration risk:** diagnostic override may mask production PBR/texture
  behavior. It is bounded to the Example Demo Sequoia model and remains opt-in.

## Plan / Do / Check / Act

### Plan

- Compare material-only A first, then add the exact existing SUN probe in B
  only if A remains visually negative while liveness and material binding pass.
- Keep one variable changed between A and B; capture both from one QEMU image
  and do not infer success from log markers.
- Use the established Mac Podman Devtool → locally committed layer patch →
  verified bundle → Mini `do_patch`/compile/image build → manual guest Flutter
  → QMP evidence path.

### Do

- The persistent Devtool source was clean at exact 0331 baseline `4acaa4c`.
  Only `model_system.cc` and `.h` were edited: the Sequoia material is now LIT
  with the same RGB parameter expression and linear blue value as FLR-0371;
  the override remains opt-in and all-primitive binding/teardown remain intact.
- Devtool source commit: `b9793ce70deb18081660679796d8288efe90a78a`.
- Official component-rebase helper generated canonical patch 0332 from that
  commit. Patch SHA-256 is
  `395f3b86033c65786fc212a94356bc67d48bffe10156b9327ae82fc8a6f86339`; its
  file list is exactly the two `ModelSystem` files. The recipe registers it
  once after 0331, and the authorized baseline lock refresh records 425 files.
- The layer patch, registration, baseline lock, and evidence are locally
  committed as `c4be4e997f5926b26dfb3c3df429ca1961308545` (no push).
- Layer patch, registration, baseline lock, and evidence are locally committed
  as `c4be4e997f5926b26dfb3c3df429ca1961308545`; no push.
- Read-only Mini preflight: the current QEMU build's `bblayers.conf` selects the
  clean fixed receiver at `748978266c9a9c66dd1a5301b56927896ae9cb2f`. Its
  existing TMPDIR is the build's `tmp`; BitBake is idle and the build filesystem
  has 63 GiB available. The build's persisted `TEMPLATECONF` has exactly one
  matching AGL source root. The standard handoff helper will verify effective
  TOPDIR/TMPDIR before changing the receiver.
- Four pre-existing bundle files have different hashes; none was deleted. Use
  the existing path explicitly named `inbox` as the single incoming destination
  for this handoff.
- Bundle transfer, Mini `do_patch`, compile, image build, and QEMU runtime
  evidence are still pending.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Canonical/branch/ticket | Canonical guard, one active ticket, clean feature base | PASS; feature branch clean at local layer commit | PASS |
| Devtool baseline | Exact 0331 source baseline, clean and single component | PASS; one component, clean source, exact full revision | PASS |
| Patch/build | Official 0332, Mini `do_patch`, compile and image pass | Official 0332 provenance and local registration PASS; Mini handoff/build pending | PENDING |
| Runtime A/B | Live QMP shows Sequoia+HUD; profile B only if needed | Pending | PENDING |
| Teardown/evidence | QMP-only, retained logs, zero QEMU/app/socket/port residuals | Pending | PENDING |

### Act

- If A shows Sequoia and HUD, stop the experiment and preserve the simpler
  profile; do not add SUN or touch the original material path.
- If A is visually negative but healthy, try B with only the existing SUN
  switch. If B is also negative, use the captured boundary to choose the next
  separate ticket; do not sweep light/camera/texture variables.

## Unknowns

- Whether profile A produces any visible Sequoia pixels on the newly built
  candidate.
- If B helps, whether the added SUN is causal by itself or interacts with
  other scene lights/material normals; this experiment does not replace
  unknown pre-existing scene lights.
