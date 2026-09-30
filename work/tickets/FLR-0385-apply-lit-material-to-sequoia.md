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
- The pre-change Sequoia material code is in patch 0331; this ticket generates
  patch 0332 to switch that diagnostic override to LIT. The persistent Devtool
  source was read-only checked before editing: clean branch
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
| Where | `ModelSystem::setupRenderable` in the split `fluorite-plugins` source; Mini's fixed authoritative Yocto build and QEMU | Patches 0331/0332 and fixed build/runtime runbooks |
| When | Fresh layer patch/image, then profile A and conditionally profile B in one QEMU instance | This ticket's single run ID `flr0385-0001` |
| Who | Devtool source, layer integration, Mini BitBake, guest `agl-driver`, Flutter, QMP evidence roles | Role-scoped runbook |
| How | Same shader/color as FLR-0371; bind all primitive slots; A keeps the production profile; B would add only the existing SUN opt-in | Patch 0332; A logs; live-QMP capture still missing |

### Process analysis

| Step | Expected | Current observation | Evidence |
| --- | --- | --- | --- |
| Material positive control | Fixture LIT/RGB path creates visible blue pixels with HUD | Proven on FLR-0371 candidate | FLR-0371-0004 screenshot/measurements |
| Sequoia override | Same material binds all selected primitive slots | Profile A logs `READY=1`, `BOUND=24` in A1–A3; LIT source is in patch 0332 | A1–A3 app logs on Mini |
| Scene lighting | A preserves production conditions; B adds only the existing SUN probe | A ran three times; B was correctly skipped because A reproduced an `FEngine::loop` kernel Oops and was not a healthy negative | A3 app log and bounded kernel journal window |
| Visible output | Live QMP image contains identifiable Sequoia and HUD together | UNKNOWN: no live-PID-bracketed QMP frame was captured. A post-exit frame is all black and is invalid as render evidence. | A3 live-gate output and post-exit QMP PPM/PNG |

### Problem point

The first runtime divergence is after the first successful queue-present return:
the next `FLR0026_VK_QUEUE_PRESENT_BEGIN` has no matching return, and the guest
records an `FEngine::loop` kernel page fault. LIT material setup later reaches
`READY=1`/`BOUND=24`, but there is no valid live QMP frame. The current evidence
does not distinguish a render/present stall from a capture-timing failure, and
does not establish whether the material itself emits visible pixels.

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
- Read-only Mini preflight: the current QEMU build's `bblayers.conf` selects the
  clean fixed receiver at `748978266c9a9c66dd1a5301b56927896ae9cb2f`. Its
  existing TMPDIR is the build's `tmp`; BitBake is idle and the build filesystem
  has 63 GiB available. The build's persisted `TEMPLATECONF` has exactly one
  matching AGL source root. The standard handoff helper will verify effective
  TOPDIR/TMPDIR before changing the receiver.
- Four pre-existing bundle files have different hashes; none was deleted. Use
  the existing path explicitly named `inbox` as the single incoming destination
  for this handoff.
- The verified Git bundle advanced the fixed Mini receiver to
  `fe92b7760deaf9feb2e09b5370565be7798b4eca`; the Mini layer tree is clean.
- Mini `flutter-auto do_patch`, `do_compile`, and the full
  `agl-ivi-image-flutter` build passed (11,898 tasks; seven warnings: six
  forced-task taint notices and one existing `flutter-auto-dbg` buildpaths QA
  warning). The existing build/TMPDIR and caches were reused.
- Candidate artifacts: rootfs SHA-256
  `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`,
  qemuboot SHA-256
  `4a82822cea7292210504c09eff6e57ab7ab0977d1dd0712a8df0c1c78c830910`,
  kernel SHA-256
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- Profile A was manually launched as UID 1001 with the LIT override and
  production lighting unchanged. A1/A2/A3 reached `READY=1`, `BOUND=24`; the
  first present returned `0`, while the second present had no recorded return.
  A2 and A3 have `FEngine::loop` kernel Oops evidence; A3's bounded app exit
  status is `124`, with no coredump.
- The A3 live gate ran after the 180-second timeout: saved PID 905 was gone,
  app count was zero, while the retained log still had `READY=1`, `BOUND=24`,
  and two present entries. The resulting post-exit QMP frame is 1280×800,
  uniformly black; SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  It matches the earlier A1 post-exit frame and is not a live-render result.
  The central 3D ROI `(440,220,400,360)` has 0 changed, edge, and chromatic
  pixels; HUD ROI `(1120,0,160,80)` has 0/12,800 pixels in each category; left
  vehicle ROI `(0,100,320,310)` has 0/99,200. Review PNG: [A3 post-exit QMP frame](../evidence/FLR-0385-0001/qmp-profile-a3-post-exit.png);
  8-frame video: [A3 post-exit QMP video](../evidence/FLR-0385-0001/qmp-profile-a3-post-exit.mp4), SHA-256
  `46ba4306456a4973d0d7b01e72416fb7fbc5d4cf357939f46cfe99a6069e448d`.
  These are local ignored review media; raw PPM and frames remain on Mini under
  `$BUILD_EVIDENCE/flr0385-0001/qemu/`.
- A3 kernel window records `BUG: unable to handle page fault`, Oops `[#3]`,
  CPU 2, `FEngine::loop`, kernel `6.6.111-yocto-standard`; no coredump was
  found. The SUN profile B was not run because the runtime was faulted, not a
  healthy material-only negative.
- QMP `quit` was accepted. The harness found zero QEMU/runqemu/flutter-auto
  residuals; QMP socket absent, ports 10930–10932 free, and no BitBake/pseudo/
  image-task residuals.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Canonical/branch/ticket | Canonical guard, one active ticket, clean feature base | PASS; feature branch clean at local layer commit | PASS |
| Devtool baseline | Exact 0331 source baseline, clean and single component | PASS; one component, clean source, exact full revision | PASS |
| Patch/build | Official 0332, Mini `do_patch`, compile and image pass | PASS at Mini receiver tip `fe92b77`; all three build gates passed, artifact hashes recorded | PASS |
| Runtime A | Live QMP shows Sequoia+HUD | `READY=1`/`BOUND=24`, but A1–A3 did not produce a valid live capture; A3 exited `124` after an `FEngine::loop` Oops. Post-exit screen is black and invalid for acceptance. | UNKNOWN |
| Runtime B | Add only existing SUN probe if A is healthy but visually negative | Skipped: A was faulted, so the precondition was not met | NOT RUN |
| Teardown/evidence | QMP-only records and zero QEMU/app/socket/port residuals | PASS; post-exit still and eight frames retained on Mini; no raw PPM copied to Mac | PASS |

### Act

- If A shows Sequoia and HUD, stop the experiment and preserve the simpler
  profile; do not add SUN or touch the original material path.
- Do not run B while the `FEngine::loop` Oops/unmatched present is present; the
  lighting comparison would not be a clean discriminator.
- Keep this ticket active until a live-PID-bracketed QMP frame is captured.
  Prearrange a bounded capture at the known material-ready window before any
  same-profile retry; do not rebuild or change light/camera/texture variables.

## Unknowns

- Whether profile A produces any visible Sequoia pixels while the app is live;
  no valid live QMP capture exists yet.
- Whether the recurring second-present/FEngine page-fault boundary is causal
  for the absent frame, and its root cause; correlation is established, cause
  is UNKNOWN.
- If B helps, whether the added SUN is causal by itself or interacts with
  other scene lights/material normals; this experiment does not replace
  unknown pre-existing scene lights.
