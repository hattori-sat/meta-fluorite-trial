# FLR-0383 Apply a Proven UNLIT Material to Production Sequoia

> **For agentic workers:** Execute inline with review checkpoints. Keep each
> checkbox tied to recorded evidence; do not mark an item complete by inference.

**Goal:** Replace the production Sequoia's bound materials with a known-visible
UNLIT blue material, then prove whether Sequoia and the Flutter 2D HUD appear
in the same live QMP frame on the current candidate image.

**Architecture:** Reuse the exact current `meta-fluorite-trial` patch stack and
the one persistent Mac Podman Devtool container/source checkout. Before source
editing, prove the mounted checkout, active Devtool component, source HEAD, and
recipe-applied baseline are clean and match the committed layer. Make an
opt-in diagnostic path that creates a proven UNLIT blue material and binds it
to every renderable primitive belonging to `sequoia_ngp.glb`; leave the normal
production material path unchanged when the flag is unset. Generate the
split-component patch only through
`scripts/rebase-fluorite-devtool-component.sh`, which invokes official
`devtool update-recipe --mode patch --append --no-remove`. Use current source
HEAD `7548f28bf50b3c3241efcfe8d4612440c0da0825` as the effective baseline so
patch 0330 is not re-emitted. Validate and commit the resulting layer patch,
transfer the verified Git bundle to the Mini receiver, run the authoritative
Yocto build there, and manually launch Flutter over the established guest SSH
path. Judge only full-frame QMP still/video captured while the app is live.

**Tech Stack:** Filament C++, Yocto/OpenEmbedded Devtool, Podman, Git bundles,
Mini PC BitBake, QEMU/runqemu, strict guest SSH, QMP PNG/MP4 evidence.

**Spec:** [FLR-0383 ticket](../../../work/tickets/FLR-0383-sequoia-known-material.md)

## Evidence and Decision Basis

- FLR-0368's UNLIT parameter material rendered bright-blue native geometry and
  the CPU/GPU HUD in one frame (`119716/144000` chromatic native pixels;
  `2845` chromatic HUD pixels).
- FLR-0371's LIT/SUN parameter fixture also rendered blue geometry and HUD,
  but the production Sequoia did not use that fixture material.
- FLR-0324/0325's production per-instance color override fired and the value
  reached the bound instance, yet the native ROI remained black.
- FLR-0326 replaced only primitive 0 / `PaintColor` with a generated magenta
  UNLIT material and did not produce native QMP pixels on its older image.
- FLR-0375 already verified all 23 embedded GLB images and material references;
  this ticket does not repeat that inventory.

These facts motivate applying the known-visible UNLIT material to **all**
Sequoia renderable primitives on the current image. They do not prove the
current production scene will render or that the original texture/light path
is defective.

## Global Constraints

- One active ticket at a time. FLR-0382 is Waiting while this independently
  scoped product-material test runs; do not mix its scene-stage trace A/B into
  this experiment.
- Use the existing canonical repository, persistent Podman container, bound
  project directory, Devtool source path, Mini receiver, and Mini build/TMPDIR.
  Do not create another container, source checkout, volume, or build tree.
- Inspect current files, patch order, effective recipe/source identity, and
  mounted Devtool state before editing. If the patch-applied baseline is dirty,
  mismatched, or not at the exact current layer state, stop and reconcile that
  same workspace before changing source.
- Do not hand-author or edit generated patch text. Commit the Devtool source
  change first, then use the split-component `rebase-fluorite-devtool-component`
  helper and its official `devtool update-recipe` operation. Never use the
  parent-recipe `finish` helper for `fluorite-plugins`.
- Keep the change opt-in. With the flag unset, preserve the original production
  GLB materials, textures, lighting, camera, scene, HUD, and launch behavior.
- Do not modify launch scripts, run `cleanall`, run `cleansstate`, delete
  caches, or copy a disk image to the Mac. Build only on the Mini and transfer
  the committed change as a Git bundle.
- Start Flutter manually as `agl-driver`. Capture QMP-only full-frame still
  and short video while that exact process is live; a QEMU boot frame or a
  post-timeout capture is not render evidence.
- Keep local commits on the ticket feature branch; do not push or cherry-pick.

## Task 1: Freeze the ticket and verify the Devtool baseline

**Files:** ticket, dated working log, `TASKS.md`, this plan; then read-only
inspection of the existing Devtool environment.

- [x] Record canonical-repository guard, branch/HEAD, clean tree, and FLR-0382
  handoff in the work log.
- [x] Confirm the exact current patch stack includes 0326, 0330, and 0279 in
  the expected order, and inspect their source/API changes before editing.
- [x] Inspect existing Podman container and bind, `devtool status`, fixed
  source path, source Git status/HEAD, active component recipe, and baseline
  provenance. Reuse them only if exact and clean.
- [x] Read the current `ModelSystem::setupRenderable()` and `onDestroy()` plus
  the existing material builder and asset-path/primitive APIs from source and
  patch history. Decide exact ownership/lifetime only from that code evidence.
- [x] Read the active Devtool workspace append: `initial_rev` is
  `599bf4ea…` and it contains earlier patch 0330. Use current source HEAD
  `7548f28…` as the next effective baseline so 0330 is not regenerated.
- [x] Record two alternatives and the chosen discriminator in the ticket:
  parameter override (already falsified on production), one-primitive magenta
  replacement (older-image negative), and all-Sequoia-primitives known-blue
  UNLIT replacement (chosen).

## Task 2: Implement the bounded production-Sequoia override

**Files:** only the existing Devtool source file(s) needed for the
`ModelSystem` material-selection seam; generated layer patch and its existing
recipe registration.

- [x] Add one new, clearly named opt-in flag. Do not reuse or overload the
  FLR-0326 legacy magenta diagnostic state.
- [x] Reuse the known-working UNLIT material construction and parameter
  contract from the current fixture/patch history, with its recorded blue
  color; do not add a dependency on SUN/light, texture lookup, or shader edits.
- [x] Bind that material to every renderable primitive belonging to the
  production `sequoia_ngp.glb`, not just primitive 0 or `PaintColor`.
- [x] Keep default production behavior identical when the flag is unset.
  Restrict markers to bounded setup/binding summaries; do not add per-frame or
  asset-loop log floods.
- [x] Verify ownership/destruction follows existing Filament lifetime rules;
  perform the two-file source diff and whitespace checks before layer
  generation. `clang-format` is unavailable on the host and in the fixed
  container, so Mini `do_compile` remains the authoritative C++ validation.
- [x] Commit only the source change in the existing Devtool source Git and run
  `scripts/rebase-fluorite-devtool-component.sh` with baseline
  `7548f28bf50b3c3241efcfe8d4612440c0da0825` and that source commit. It must
  reset/re-add the split component from this exact baseline and invoke official
  `devtool update-recipe --mode patch --append --no-remove`. Verify generated
  `From` matches source commit `4acaa4c0194303227a2207bbbed9ea2249b72efb`
  and the patch does not re-emit 0330; verify byte identity, exactly-one
  registration, and refreshed baseline lock. PASS: generated patch 0331 SHA-256
  `e16536160b52df0d0cdd13673ccc99af9337c1b2b862d58b0a9abcecb9ce11c7`; its
  `From` is the source commit, its two files are only `model_system.cc` and
  `model_system.h`, append registration count is one, and workspace
  `initial_rev` is `7548f28…`.
- [x] Deliver the committed patch to the Mini and run authoritative `do_patch`
  and `do_compile` before the full image build; do not compile through a
  Mac-side Yocto provider graph. PASS: bundle tip `6c08559`, remote SHA-256
  verified, `do_patch=PASS`, `do_compile=PASS` (2686 tasks; all succeeded).
  The first patch-gate invocation stopped before BitBake because the helper
  required explicit `BUILD_AGL_ROOT`; resolving the unique template-matched
  source root allowed the same gate to pass. FLR-0384 tracks the helper fix.

## Task 3: Validate and deliver the layer change

**Files:** canonical patch under
`layers/meta-fluorite-trial/recipes-graphics/toyota/files/` and the existing
`flutter-auto_2.0.bbappend` registration.

- [x] Confirm privacy, whitespace, canonical-repository, runtime-checkpoint,
  patch-registration, and focused Markdown checks. These passed; the full
  repository link scan still reports only nine pre-existing missing evidence
  links under FLR-0338/0339/0340, with no FLR-0383 link errors.
- [x] Commit only this ticket's patch/registration, required baseline-lock
  update, and evidence docs, with generic role identity; record full commit
  and parent. PASS: commit `39301804ab6991384bfdc0580c1d6a3c08fe6424`, parent
  `1c828a4647e6514024d4086727d48819b23bbd93`; no push.
- [x] Create a bundle from the verified Mini receiver base, validate its
  advertised commits and SHA-256, and transfer it to the fixed receiver. PASS:
  receiver base `f61566f`; bundle SHA-256
  `7c373dba7bf49c3be4fc8316883ec09ef433cec6c695f890207bbaa156caee1b`.
- [x] Verify Mini checkout is exactly the local ticket tip and that effective
  recipe inputs and fixed build/TMPDIR roles match the documented profile.
  PASS: receiver tip `6c0855957347a18ff3990545a02a2d7f94aa719a`, exact
  `bblayers.conf` receiver, TOPDIR/TMPDIR gates PASS. A following evidence-only
  documentation commit will be rebundled so the image build uses the exact
  current tip.
- [x] Record storage/build preconditions and notify before the long image
  build. Target `do_patch`, focused compile, and full image build passed at
  exact layer tip `748978266c9a9c66dd1a5301b56927896ae9cb2f`; all 11,898 tasks
  succeeded, 8 warnings were classified, and 63 GiB remained free. Caches were
  reused and preserved.

## Task 4: Prove the live visual result

**Files:** ticket-scoped QMP full-frame PNG, short MP4, selected runtime log
summary, hashes, and manifest; originals stay on the Mini evidence store.

- [x] Verify candidate kernel/rootfs/qemuboot hashes, exact Mini QEMU slot,
  strict guest SSH, Example Demo bundle, Wayland session, and zero stale
  `flutter-auto` processes. Exact candidate hashes and roles are in the ticket
  and evidence manifest.
- [x] Boot one exact-image QEMU through the established Mini `runqemu`
  procedure. Manually start exactly one Flutter process as `agl-driver` with
  only the new opt-in override enabled. First app attempt ended before capture;
  its evidence was excluded and a fail-closed retry was performed.
- [x] Capture a full 1280×800 QMP frame and short QMP video while the same PID
  was live; before/after process checks passed. Full frame and separate HUD / 3D
  ROI measurements are recorded in `work/evidence/FLR-0383-0001.md`.
- [x] Visual acceptance was evaluated and **FAILED**: HUD is visible, but
  central Sequoia ROI is uniformly black (`0/144000` changed/chromatic pixels).
  Runtime material markers show READY=1, BOUND=24, BUILD_FAILED=0; this does
  not prove visible geometry or identify camera/draw/present/composition cause.
- [x] Stop only the recorded app/QEMU processes; bounded fault/core evidence
  was retained. Independent checks found no QEMU/runqemu/flutter-auto process,
  QMP socket, or forwarded port listener.
- [x] Preserve the negative QMP result and keep texture/light/camera attribution
  UNKNOWN. Continue the next scene discriminator under the existing FLR-0373
  ticket; do not report the overall 3D goal as achieved.
