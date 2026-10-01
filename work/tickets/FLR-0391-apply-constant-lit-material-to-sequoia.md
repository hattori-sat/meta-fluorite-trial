# FLR-0391 — apply the known-positive constant LIT material to Sequoia

- Status: Waiting
- Priority: High
- Created: 2026-10-01
- Predecessors: [FLR-0369 current-image LIT constant-color positive](FLR-0369-lit-hardcoded-material-control.md), [FLR-0385 Sequoia LIT parameter override](FLR-0385-apply-lit-material-to-sequoia.md), [FLR-0389 same-image fixture control](FLR-0389-replay-lit-fixture-correct-marker-current-image.md)
- Branch: `feature-flr-0391-sequoia-constant-lit`
- Plan: [FLR-0391 implementation plan](../../docs/superpowers/plans/2026-10-01-flr0391-sequoia-constant-lit.md)
- Working log: [FLR-0391 working log](../logs/2026-10-01-flr0391.md)
- Evidence manifest: [FLR-0391 QMP evidence](../evidence/FLR-0391-0001.md); raw PPMs and logs remain on the Mini PC.

## Objective

Replace only the Sequoia diagnostic override's dynamic FLOAT3 material color
input with the constant blue LIT shader expression that produced visible
geometry on the current-image fixture. Generate the layer patch through the
existing Yocto Devtool component workflow, commit it locally, transfer the
Git bundle to the fixed Mini receiver, build the image there, and manually run
Example Demo with Sequoia selected. Judge the result from a complete QMP frame
and short video, not from READY/BOUND logs or a booted QEMU.

This is a diagnostic material substitution. It does not claim that Sequoia's
original PBR materials/textures are fixed, and it does not change the GLB,
camera, transform, model selection, HUD/composition, launch scripts, or normal
behavior when the override is absent.

## Facts

- FLR-0369 used the same pinned rootfs for LIT parameter-source and
  constant-source fixture runs. Parameter source had no native chromatic
  pixels; adding only `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR=1` selected
  `hardcoded=true shading=lit source=constant` and produced 119,716 chromatic
  native pixels plus 2,845 HUD chromatic pixels in a complete QMP frame.
  The working shader expression in patch 0249 is
  `material.baseColor.rgb = vec3(0.05, 0.45, 1.0);`.
- FLR-0371 also recorded a positive parameterized LIT/SUN fixture, but on a
  different candidate rootfs/engine lineage. Its success does not cancel the
  same-image FLR-0369 parameter-vs-constant discriminator.
- Patch 0332 currently installs a parameterized FLOAT3 material on each
  selected Sequoia renderable. It preserves LIT shading and the all-primitive
  binding loop, but uses `materialParams.color` and `setParameter` rather than
  the current-image constant-source positive.
- FLR-0388/0389 on rootfs
  `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`
  reached Sequoia READY/BOUND and correct fixture geometry setup, but present
  completion was unhealthy. Their post-exit black QMP frames cannot classify
  material visibility.
- The known-positive fixture also used a SUN. Existing
  `FLR0305_PRODUCTION_SCENE_LIGHT=1` supplies the recorded SUN profile; this
  ticket reuses that control rather than inventing a light implementation.
- The persistent Podman Devtool container is bound to the canonical
  repository. The Sequoia constant-source edit is committed as
  `6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e` on
  `devtool-FLR-0391-source`, based on exact post-0332 commit
  `b9793ce70deb18081660679796d8288efe90a78a`.
- The first rebase-helper attempt reset the active Devtool component, which
  moved the exact source tree into `workspace/attic/sources/`; the helper then
  checked the old path and stopped before patch generation. The source commit
  was retained, and the archived path was passed on retry.
- The retry reached official `devtool add` but failed while reloading BitBake
  metadata with duplicate `BBFILE_COLLECTIONS`. Both
  `/workspace/state/build/workspace` and
  `/tmp/fluorite-bitbake-control/workspace` resolve to the same directory;
  the workspace `layer.conf` declares `workspacelayer`. Yocto's
  `edit_bblayers_conf()` compares normalized path strings, not realpaths, so
  the configured canonical `workspace_path` is appended beside the wrapper's
  symlink alias. This is the current leading cause, not a material/runtime
  failure.
- The timed-out helper left child processes. Only the recorded Devtool,
  recipetool, and BitBake server PIDs were terminated. A later exact-PID
  check showed those PIDs gone, and the fixed wrapper's `devtool-status`
  returned no registered recipes.
- Yocto `devtool create-workspace` was applied to the existing control-path
  symlink. This aligned `devtool.conf` with the sole workspace path in
  BBLAYERS; the fixed wrapper's `devtool-status` passed with no duplicate
  collection. This runtime-state correction is not yet a permanent wrapper
  fix; FLR-0392 tracks that work.
- The existing rebase helper then passed with baseline
  `b9793ce70deb18081660679796d8288efe90a78a` and source
  `6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e`. It generated patch 0333 with
  SHA-256 `3df6ff90232a3456e47f9a6d5147f2ac704f8eefe324ddc13c427fdb3c14b079`,
  registered it once after 0332 in the `flutter-auto` bbappend, and refreshed
  the explicitly authorized project-layer baseline lock. Layer commit
  `2c531a8ddce315ab958629d082586ffe85e69c21` was transferred to Mini in one
  verified bundle; Mini `do_patch`, component compile, and full image build
  passed. The resulting rootfs SHA-256 is
  `54da69d06c4a5d38c027453f7af4bec7e52b762fa732935766c04bebf533b690`.

## Competing hypotheses

1. **Constant-source LIT can render Sequoia when the present loop is healthy.**
   The current run reached READY/BOUND but had only one successful present and
   a repeated FEngine Oops, so this remains UNKNOWN.
2. **A shared renderer/present fault blocks native pixels despite successful
   material binding.** The repeated unmatched present/Oops supports this as the
   leading boundary, but does not prove causality.
3. **The failure is Sequoia-specific.** A same-image known-positive native
   fixture control is needed to distinguish it from a general render/present
   failure.

The alternative to the one-line constant-source discriminator would be to
change texture loading, camera, or original PBR lighting now. Those alter
different boundaries and are not justified while the existing same-image
fixture directly distinguishes parameter from constant color.

## 4W1H and problem point

| Dimension | Scope |
| --- | --- |
| What | Constant blue LIT diagnostic material applied to all selected Sequoia primitive slots; CPU/GPU HUD in same QMP frame |
| Where | `ModelSystem::setupRenderable` in the split `fluorite-plugins` source; canonical `meta-fluorite-trial`; fixed Mini build and runqemu |
| When | One fresh patch/build candidate and one bounded QEMU run, ID `flr0391-0001` |
| Who | Mac Podman Devtool source role; layer integration role; Mini BitBake role; guest `agl-driver` Flutter role; QMP evidence role |
| How | Official `devtool update-recipe` after source commit; verified bundle; Mini `do_patch` → component compile → image; manual Flutter with existing Sequoia and SUN controls; QMP screenshot/video at first successful present |

**Problem point:** on the same pinned image, the fixture's dynamic LIT color
path was black while its constant LIT color path emitted blue pixels. Sequoia
currently uses the dynamic path. This is the smallest code-level difference
that can be transferred without touching the vehicle asset or scene setup.

## Scope and safety

- Edit the persistent Devtool-managed `model_system.cc`; keep the existing
  opt-in `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE`, `prepareMaterial`, LIT
  shading, target/platform, asset predicate, primitive loop, and cleanup.
- Use the exact fixture expression `vec3(0.05, 0.45, 1.0)`. Remove only the
  now-unused FLOAT3 parameter declaration and instance setter. Make the
  READY marker identify `source=constant`; keep existing READY/BOUND token
  prefixes for selectors.
- Generate patch 0333 with the repository's split-component helper and
  official Devtool `update-recipe`; never hand-author or edit patch content.
  Register exactly once after 0332 in the existing `flutter-auto` bbappend.
- Commit locally; no push. Transfer only a verified bundle through the fixed
  handoff helper. Mini is the only authoritative BitBake/image-build host.
- Reuse the current Podman container/state/TMPDIR, Mini receiver/build/TMPDIR,
  official QEMU harness, one 6144 MiB QEMU, and existing ports. No Docker,
  extra container, volume, build tree, TMPDIR, cache cleanup, Mac QEMU, or
  QEMU disk-image copy.
- Use existing `FLR0026_NATIVE_MODEL_MATCH` and `_LIMIT` selectors only if
  required by the saved working launch command; create no new FLR0026 files,
  markers, variables, or evidence paths. All new records use FLR-0391.
- Capture the full QMP frame and short video at the first successful present
  while the exact Flutter PID remains live; do not wait for a late frame-count
  gate before preserving the decisive visual. Then evaluate health separately.
  If a live present is unmatched, collect one bounded GDB thread/backtrace
  snapshot, then stop; preserve failures as well as successes.

## Success criteria

1. Source baseline is clean and exactly the post-0332 effective source; source
   diff changes only the Sequoia shader expression, unused parameter/setter,
   material name/READY source annotation. All primitive binding and cleanup
   remain intact.
2. Official Devtool output patch 0333 has `From` equal to the source commit,
   is byte-identical to the generated output, applies once after 0332, and
   passes Mini `do_patch`; compile and full image build pass.
3. Exact image/helper hashes, guest identity, model selection, material
   READY/BOUND, known SUN setup, app liveness, and selected present markers
   are recorded. No broad log dump.
4. Full-frame QMP still and short video show recognizable Sequoia in the
   diagnostic blue together with the CPU/GPU HUD. Record full-image SHA,
   dimensions, fixed 3D/HUD ROI metrics, and pre/post PID identity. A black
   post-exit image or boot-only screen is not a visual verdict.
5. Independently classify visual output and render-loop health. Healthy
   acceptance also requires repeated successful presents, no unmatched
   present/Oops, and exact QEMU teardown with zero residual processes/socket/
   ports. If visual output is positive but the loop later faults, report that
   split result and keep the top-level objective open for a dedicated health
   ticket.

## Impact

- **Build-time:** one focused C++ source patch, component compile, and image
  build using existing Mini caches.
- **Packaging:** no dependency/package change; one new patch in the existing
  `flutter-auto` append.
- **Runtime:** only the opt-in Sequoia override changes; default production
  GLB material path is unchanged when the override is absent.
- **Integration risk:** diagnostic blue masks original PBR/texture output and
  proves only Sequoia geometry/material/present visibility under the tested
  conditions.

## Plan / Do / Check / Act

### Plan

See the linked implementation plan. The source discriminator comes from
FLR-0369, not an assumption that the parameterized FLR-0371 shader is the
current-image positive.

### Do

- **Done:** one-file source edit and source commit
  `6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e`.
- **Blocked before patch output:** the first rebase-helper call used the path
  invalidated by reset; retry reached `component-add` and failed on duplicate
  workspace collection. Both failures and their exact stop points are retained
  in the working log.
- **Patch generated:** after aligning the existing workspace alias using
  standard `devtool create-workspace`, the official split-component helper
  passed. Patch 0333 has `From=6946d02…`, matches generated output byte-for-byte,
  reverse-apply check passes, registration follows 0332 exactly once, and the
  baseline lock is refreshed.
- Repository privacy scan passed; source tree remains clean at the source
  commit, and `git diff --check` plus reverse-apply check passed.
- Layer commit `2c531a8ddce315ab958629d082586ffe85e69c21` was transferred in
  one verified bundle. Mini recipe `do_patch`, `flutter-auto do_compile`,
  and full `agl-ivi-image-flutter` build passed; all 11,898 image tasks
  succeeded. Rootfs SHA-256:
  `54da69d06c4a5d38c027453f7af4bec7e52b762fa732935766c04bebf533b690`.
- Two manual attempts ran under one 6144-MiB Mini QEMU. Attempt 0001 captured
  before material READY and is not a material-output verdict. Attempt 0002
  reached `READY=1 BOUND=24 SUN=1` with `source=constant`, then was captured
  while the exact Flutter PID/UID/start identity remained unchanged before
  and after QMP.
- Attempt 0002 full-frame QMP showed the CPU/GPU HUD and Scenes control over
  a black native scene. Sequoia ROI `(440,220,400,360)` was 0/144000 changed,
  edge, or chromatic pixels. The 8-frame QMP review video is identical in all
  frames. See the linked evidence manifest and screenshot.
- Runtime health failed: two present begins, one successful return, zero
  present-done markers; the second call was unmatched. The guest recorded
  `FEngine::loop` Oops #2 with the same `ff <cf>` instruction bytes seen in
  prior fault records; the bounded app exited with status 124.
- The GDB step was attempted only after the bounded app had exited, so the
  evidence says `GDB=SKIP_no_unmatched_live_process`; no new backtrace was
  captured. Earlier FLR-0366/0339 results remain the prior knowledge, not a
  root-cause proof.
- A remote evidence query first used `rg`, unavailable on Mini, then recovered
  with focused `grep`. The first postflight call exceeded the wait window
  without a retained session handle; the same read-only official preflight was
  rerun and passed.
- QMP quit and official postflight passed: zero target processes, absent QMP
  socket, and ports 10930–10932 free. Only QMP screenshot/video media were
  transferred to the Mac workspace; no rootfs, kernel, or VM disk image was
  copied.

### Check

- Patch provenance: PASS (`From` equals source commit; canonical output is
  byte-identical; reverse apply checks against source HEAD; 0333 is registered
  once after 0332; baseline lock refreshed; repository privacy scan passed).
- Mini `do_patch`, compile, and full image build: PASS.
- Runtime material construction/binding and SUN setup: PASS
  (`READY=1`, `BOUND=24`, `SUN=1`, `source=constant`).
- Live PID-bracketed full QMP capture: PASS. The HUD and Scenes control are
  visible; Sequoia ROI is uniformly black (0/144000 changed, edge, or chromatic
  pixels), so visible-Sequoia criterion FAILS.
- Present loop: FAIL (`PRESENT_BEGIN=2`, `PRESENT_RETURN=1`,
  `PRESENT_DONE=0`, second present unmatched; `FEngine::loop` Oops #2;
  app status 124).
- Teardown and image identity: PASS (QMP harness quit, zero residual targets/
  socket/ports, exact rootfs hash verified).

### Act

- Keep this ticket Waiting: material patch and runtime test are complete, but
  its visible Sequoia+HUD acceptance condition did not pass.
- Do not modify camera, texture path, light, or composition based on this
  faulted frame. The material marker followed the Oops, while the second
  present remained unmatched.
- FLR-0393 now replays the known-positive constant LIT/SUN fixture on this
  exact image with the HUD. Its result distinguishes a shared current-image
  render/present regression from a Sequoia-specific path without another
  build or material change.

## UNKNOWN

- Whether constant-source LIT produces Sequoia pixels during a healthy present
  loop on the exact image.
- Whether the recurring Oops causes the missing native pixels or is only
  correlated with them.
- Whether the general constant LIT/SUN fixture still renders with HUD on the
  exact FLR-0391 image; FLR-0393 owns that control.
- Whether original Sequoia PBR materials/textures render correctly after this
  diagnostic material is removed.
