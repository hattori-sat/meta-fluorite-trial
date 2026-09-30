# FLR-0383 — apply a known-visible material to every Sequoia primitive

- Status: In Progress
- Priority: High
- Owner: Mac Podman Devtool / meta-fluorite-trial / Mini BitBake / QEMU / guest Flutter / QMP evidence roles
- Created: 2026-09-30
- Predecessors: [FLR-0368 UNLIT material positive control](FLR-0368-manual-unlit-fixture-control.md), [FLR-0326 one-primitive production material probe](FLR-0326-probe-production-fragment-target-boundary.md), [FLR-0371 LIT parameter positive control](FLR-0371-lit-parameter-rgb-assignment.md), [FLR-0375 GLB texture inventory](FLR-0375-inspect-production-sequoia-glb-image-paths.md), [FLR-0382 scene-stage trace comparison](FLR-0382-isolate-scene-stage-trace.md)
- Implementation plan: [FLR-0383 plan](../../docs/superpowers/plans/2026-09-30-flr-0383-sequoia-known-material.md)
- Branch: `feature-flr-0383-sequoia-known-material` (local; no push)
- Starting commit: `35a7a28` (FLR-0382 evidence correction)
- Candidate kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Candidate rootfs SHA-256: `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`
- Candidate qemuboot SHA-256: `8582ac80d4c58fc9e852abed0e6fd6e6077bf6e5f0f7727341033fb405d0a17c`
- Working log: [FLR-0383 working log](../logs/2026-09-30-flr0383.md)

## Objective

Use a material already proven to render in the native 3D target and bind it to
every renderable primitive of the production `sequoia_ngp.glb`. Build the
change through the established Devtool → committed layer patch → Git bundle →
Mini BitBake flow. Manually launch Flutter on the resulting image and determine
from live QMP evidence whether recognizable blue Sequoia geometry and the 2D
CPU/GPU HUD appear together.

This is a material-path discriminator. It does not assume whether the
production asset's original material, lighting, texture, camera, or composition
is the root cause. With the new diagnostic flag unset, normal Sequoia behavior
must remain unchanged.

## Success criteria

1. The current exact Devtool source baseline is verified clean and patch-stack
   identical before editing; no second container, source checkout, or build
   tree is created.
2. An opt-in material override uses the previously visible UNLIT blue material
   and binds it to all renderable Sequoia primitives, not only primitive 0 or
   `PaintColor`.
3. The source change is committed in Devtool first; the split-component
   rebase helper uses effective baseline `7548f28…` and official
   `devtool update-recipe --mode patch --append --no-remove` to generate only
   the new delta (not patch 0330), register it once, and refresh the baseline
   lock before a local layer commit.
4. The Mini receiver builds the exact committed bundle tip with the established
   Yocto build directory and caches.
5. A live, PID-bracketed, QMP-only full-frame image/video proves or falsifies
   recognizable blue Sequoia and the CPU/GPU HUD in the same frame. Teardown
   and residual process/socket/port checks pass.

## Facts

- FLR-0368 rendered bright-blue self-made UNLIT geometry and the CPU/GPU HUD in
  one QMP frame: native ROI `(440,220,400,360)` had `119716/144000` chromatic
  pixels and HUD ROI `(1120,0,160,80)` had `2845` chromatic pixels.
- FLR-0371 also rendered a dark-blue self-made LIT/SUN fixture with the HUD;
  it did not apply that fixture material to production Sequoia.
- FLR-0324's production material parameter override fired with magenta values;
  FLR-0325 confirmed the same bound MaterialInstance/value, but native ROI
  remained black.
- FLR-0326 generated an UNLIT magenta material but assigned it only to
  primitive 0 / `PaintColor`. Its QMP native ROI was `0/144000`; that run used
  the older rootfs `2da3de…`, not this ticket's current rootfs. It is not the
  all-primitives test proposed here.
- FLR-0375 validated all 23 embedded Sequoia GLB PNGs and material references;
  no external image URIs or missing references were found.
- Current candidate identities are pinned above. Example Demo 3.32.5 and
  6144 MiB QEMU memory were used in the recent Mini runtime trials.
- The fixed Podman container is running with the documented project RW, AGL
  RO, and state RW binds; the wrapper `status` probe passed. The mounted project
  worktree is clean on `devtool-flr-0371-mount` at `a3e7799`; normalized Git
  common-dir and origin checks match this active feature worktree. Its branch
  is intentionally older and remains untouched; the rebase helper runs from
  the active feature checkout for canonical layer writes while the existing
  mount remains the fixed metadata input to the Devtool container.
- Official Devtool status reports exactly one active component:
  `fluorite-plugins` at the fixed `sources/fluorite-plugins` path. The source
  repository is clean on `devtool-FLR-0371-source`, HEAD
  `7548f28bf50b3c3241efcfe8d4612440c0da0825`, parent
  `599bf4ea72b2a5874fd3f296b756941eb05de946`. At that baseline inspection,
  committed layer patch 0330 had `From 7548f28...` and SHA-256
  `069420d5293dc1f74ad739a18a4e9540cbf44efb16b4a3140d33113e122e3333`; it is
  the final plugin patch registration in the active `flutter-auto_2.0.bbappend`.
- Before generation, the Devtool workspace append recorded
  `initial_rev=599bf4ea…` and already contained patch 0330. The split-component
  helper reset/re-added the component at exact effective baseline `7548f28…`;
  afterward, `initial_rev` is `7548f28…`, so 0330 was not regenerated.
- The proven fixture material is defined by
  `material.baseColor.rgb = materialParams.color`, a FLOAT3 `color` parameter,
  UNLIT shading, and linear blue `(0.05, 0.45, 1.0)`. These exact shader,
  parameter, shading, and value are present in the committed FLR-0371 source.
- The production `ModelSystem` already exposes `model->getAssetPath()`, a
  renderable primitive-count loop, `_rcm->setMaterialInstanceAt()`, and an
  `onDestroy()` sequence that destroys model assets before diagnostic material
  instances/materials. The old FLR-0326 branch uses a different fixed-magenta
  shader and is restricted to primitive 0 / `PaintColor` inside the optional
  model-content trace block.
- The source change is committed in the fixed Devtool source repository as
  `4acaa4c0194303227a2207bbbed9ea2249b72efb`, parent
  `7548f28bf50b3c3241efcfe8d4612440c0da0825`; it changes only
  `model_system.cc` and `model_system.h`.
- Official `scripts/rebase-fluorite-devtool-component.sh` completed PASS and
  generated canonical patch
  `0331-flr0383-sequoia-known-unlit-material-devtool.patch` with SHA-256
  `e16536160b52df0d0cdd13673ccc99af9337c1b2b862d58b0a9abcecb9ce11c7`.
  Patch `From` matches source commit `4acaa4c`; its diff excludes 0330 and
  other source files. The existing bbappend registers 0331 exactly once after
  0330; the baseline lock was refreshed from 423 to 424 layer files. The layer
  patch, registration, baseline lock, ticket, plan, working log, and dashboard
  were committed locally as `39301804ab6991384bfdc0580c1d6a3c08fe6424`, parent
  `1c828a4647e6514024d4086727d48819b23bbd93`; the branch is clean and was not
  pushed. At commit time no Mini tasks had run; subsequent bundle, patch, and
  compile results are recorded immediately below.
- Read-only Mini preflight resolved the active receiver from the QEMU build's
  effective `bblayers.conf`: it is clean at `f61566f1fe74110479152301b9c1cb86f950615b`.
  The documented fixed inbox bundle has SHA-256
  `075a52a8608ea2c193871c44d679bf00c4e1ec2ad322b0a16d3b5c2263248f8d` and
  advertises that same tip. The existing QEMU build/TMPDIR profile matches its
  layer path, there are zero active BitBake processes, and 63 GiB is free on
  the build filesystem. At this initial check no receiver/build/TMPDIR state
  had changed; subsequent handoff and recipe-task results follow.
- The standard bundle helper PASSed from receiver base
  `f61566f1fe74110479152301b9c1cb86f950615b` to exact tip
  `6c0855957347a18ff3990545a02a2d7f94aa719a`. Local and remote bundle
  SHA-256 matched at
  `7c373dba7bf49c3be4fc8316883ec09ef433cec6c695f890207bbaa156caee1b`;
  receiver checkout and effective TOPDIR/TMPDIR checks PASSed.
- The first recipe-patch gate call stopped before BitBake because this fixed
  build directory requires explicit `BUILD_AGL_ROOT`; no clean or patch task
  ran. Resolving the existing source by the build's persisted TEMPLATECONF and
  rerunning the same gate produced `do_patch=PASS` after its recipe-scoped
  `clean`.
- On the same exact receiver/build/TMPDIR, `flutter-auto do_compile=PASS`:
  2686 tasks attempted, 2681 already current, all succeeded. Four warnings
  only report the intentional forced `do_patch`/`do_compile` tasks as tainted.
  Evidence summaries and the bounded full compile log are in the receiver's
  FLR-0383 evidence directory. After compile, no BitBake process remained and
  64 GiB was free. No image build or FLR-0383 QEMU/runtime has run yet.
- FLR-0382 runs 0003–0005 reached scene/draw and two successful present
  returns, but the third present was unmatched; run 0005's QMP still/video
  were captured after timeout and are not live render evidence. Its live
  trace-on/off visual comparison remains UNKNOWN and is now Waiting.

## Inferences

- A generated UNLIT material applied to every Sequoia renderable primitive is
  the highest-information next intervention: the blue native material itself
  is a known positive control, and this bypasses the production material/light
  path while preserving the production asset, scene, and camera.
- FLR-0326 does not falsify this all-primitives test because it targeted only
  one primitive and used an older image; its negative result still requires
  care and must be recorded as relevant contrary evidence.
- A positive result will establish that the production Sequoia geometry can
  render under the override; it will not establish that original PBR lighting
  or embedded texture sampling works.

## Hypotheses

1. **The default production material path is the differentiator.** With the
   blue UNLIT material bound to every Sequoia primitive, recognizable blue
   geometry will appear alongside the HUD. A positive result narrows the
   remaining issue to original material/shading/texture behavior; it does not
   isolate which of those is faulty.
2. **Material replacement is insufficient because the failure is downstream
   or the scene geometry is not reaching visible pixels.** The new markers will
   prove selection/binding, but the live QMP vehicle ROI will remain absent or
   black/gray. That result redirects the next ticket to the smallest boundary
   supported by runtime and image evidence (camera/visibility, draw/present,
   or compositor), not to another broad sweep.

## Stratification — 4W1H excluding Why

| Dimension | Scope |
| --- | --- |
| What | Opt-in known-visible blue UNLIT material override for all production Sequoia renderables |
| Where | Existing Filament `ModelSystem` setup seam; current exact Mini image and Example Demo |
| When | Manual Flutter launch after candidate build; QMP capture immediately while PID is live |
| Who | Devtool source role, meta-fluorite-trial integration role, Mini BitBake role, guest `agl-driver`, QEMU/QMP evidence roles |
| How | Official Devtool-generated patch, local commit, verified bundle to Mini, authoritative BitBake build, manual runtime and QMP evidence |

## Plan / Do / Check / Act

### Plan

- **Chosen approach:** all-primitives Sequoia override using the blue UNLIT
  material already proven on the native target.
- **Alternative A:** continue changing per-instance color values. FLR-0324/0325
  showed the override and bound value, with no native pixels; this repeats a
  low-information path.
- **Alternative B:** repeat the FLR-0326 magenta replacement on primitive 0.
  That is an older-image, one-primitive negative and does not test the whole
  production model; repeating it unchanged is not selected.
- Verify exact source/material APIs and persistent Devtool state before edits.
  Then implement the bounded opt-in, commit its Devtool source change, and run
  `scripts/rebase-fluorite-devtool-component.sh` from baseline `7548f28…` so
  official `devtool update-recipe` generates the new delta only. PASS: source
  commit `4acaa4c`, generated patch 0331 hash above, and 0330 is not duplicated.
  Build on Mini and run one manually controlled live-QMP trial.

### Do

- The opt-in all-Sequoia primitive override is committed in fixed Devtool
  source commit `4acaa4c0194303227a2207bbbed9ea2249b72efb`.
- The official split-component helper generated patch 0331 from exact baseline
  `7548f28…`; its `From`, two-file scope, SHA-256, single bbappend registration,
  and baseline-lock refresh are independently verified. Record remaining
  commands/results in the dated working log; keep QMP originals and checksums
  on the Mini evidence store.

### Check

- PASS: exact Devtool baseline, source commit, official 0331 generation,
  no-duplicate-0330 check, single registration, refreshed baseline lock, and
  layer `git diff --check`.
- PASS: canonical guard, privacy checker, `runtime-checkpoint.sh verify`,
  and `git diff --check`. The full Markdown scan reports nine pre-existing
  missing FLR-0338/0339/0340 evidence links and no FLR-0383 link errors.
- PASS: local commit `39301804ab6991384bfdc0580c1d6a3c08fe6424` with parent
  `1c828a4647e6514024d4086727d48819b23bbd93`; branch clean, no push.
- PASS: bundle SHA-256 above reached the fixed inbox; receiver is exact tip
  `6c0855957347a18ff3990545a02a2d7f94aa719a`; effective TOPDIR/TMPDIR match.
- PASS: Mini `do_patch` and `do_compile`; no active BitBake process, 64 GiB
  free. The first gate invocation lacked the explicit AGL-root role and stopped
  before BitBake; resolving it from TEMPLATECONF made the same gate pass.
- Pending: full image build, runtime binding markers, live blue Sequoia ROI
  with simultaneous HUD, and exact teardown.

### Act

- If both regions are visible in one live frame, preserve that evidence and
  open a separate ticket for restoring original material appearance / lights.
- If all-primitive binding is proven but no visible model appears, open a new
  ticket at the earliest runtime/image boundary proven by this run. Do not
  attribute the result to texture, light, camera, or composition without
  discriminating evidence.
- If build, launch, or live-capture gates fail, record the failed gate and stop
  at that boundary; do not reinterpret a stale or post-timeout frame.

## UNKNOWN

- Whether runtime selects the production Sequoia and reaches the verified
  `ModelSystem` setup path for every expected renderable.
- Whether the newly built image's live QMP capture can be obtained before the
  known third-present stall.
- Whether successful UNLIT replacement restores the expected model outline or
  only partial geometry due to camera framing/asset geometry.
