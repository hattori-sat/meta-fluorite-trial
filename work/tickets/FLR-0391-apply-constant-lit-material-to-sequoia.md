# FLR-0391 — apply the known-positive constant LIT material to Sequoia

- Status: In Progress
- Priority: High
- Created: 2026-10-01
- Predecessors: [FLR-0369 current-image LIT constant-color positive](FLR-0369-lit-hardcoded-material-control.md), [FLR-0385 Sequoia LIT parameter override](FLR-0385-apply-lit-material-to-sequoia.md), [FLR-0389 same-image fixture control](FLR-0389-replay-lit-fixture-correct-marker-current-image.md)
- Branch: `feature-flr-0391-sequoia-constant-lit`
- Plan: [FLR-0391 implementation plan](../../docs/superpowers/plans/2026-10-01-flr0391-sequoia-constant-lit.md)
- Working log: [FLR-0391 working log](../logs/2026-10-01-flr0391.md)
- Evidence directory: `work/evidence/FLR-0391-0001/`; raw QMP/log evidence remains on the Mini PC.

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
  the explicitly authorized project-layer baseline lock. No Mini transfer,
  image build, or QEMU run has occurred.

## Competing hypotheses

1. **Dynamic LIT color input is the relevant difference.** Replacing it with
   the proven constant blue source while retaining LIT, Sequoia, all-primitive
   binding, and the known SUN makes the car visible in a live frame with HUD.
2. **The failure is beyond the material expression.** The constant material
   binds but the app still has no live visible Sequoia, or its frame/present
   loop faults before a valid capture; then preserve the GDB/journal evidence
   and do not claim a material verdict.
3. **Geometry/camera/placement or composition is the next boundary.** The
   complete live frame may show the constant-blue geometry outside the
   historical center ROI or not at all. Only then open a separate ticket for
   camera/visibility/composition, based on the full QMP image.

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
- **Next:** run checkpoint gate, commit only this ticket's patch,
  bbappend, lock, and records; bundle to Mini, build there, then run the manual
  Sequoia/HUD QMP trial. The permanent helper correction is FLR-0392 Inbox.

### Check

- Patch provenance: PASS (`From` equals source commit; canonical output is
  byte-identical; reverse apply checks against source HEAD; 0333 is registered
  once after 0332; baseline lock refreshed; repository privacy scan passed).
- Mini `do_patch`/compile/image gates, live Sequoia pixels, HUD coexistence,
  present health, and teardown: PENDING. No candidate image/runtime result is
  available to evaluate yet.

### Act

- Pending measured QMP/runtime outcome. If constant LIT is visible, next
  ticket will remove the diagnostic override only after comparing original
  Sequoia materials; if it is not visible, use the first live failing boundary
  to select the next ticket.

## UNKNOWN

- Whether the constant-source LIT material produces visible Sequoia on the
  exact current candidate image.
- Whether the same run's present loop remains healthy through the capture.
- Whether original Sequoia PBR materials/textures render correctly after this
  diagnostic material is removed.
