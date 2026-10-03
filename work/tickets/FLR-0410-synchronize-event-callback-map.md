# FLR-0410 — synchronize Flutter event completion with the ECS frame loop

- Status: In Progress
- Priority: High
- Created: 2026-10-03
- Owner: Flutter platform-message callback / Filament ECS frame-event roles
- Branch: `feature-flr-0410-event-callback-map-race`
- Depends on: [FLR-0409](FLR-0409-symbolize-flutter-auto-sigsegv.md),
  [FLR-0408](FLR-0408-replay-known-positive-sequoia-profile-on-0334.md), and
  historical [FLR-0277](FLR-0277-isolate-production-call-event-segv.md)
- Plan: [FLR-0410 implementation plan](../../docs/superpowers/plans/2026-10-03-flr0410-event-callback-map-race.md)
- Working log: [FLR-0410 working log](../logs/2026-10-03-flr0410.md)

## Work unit

Repair the reachable, unsynchronized access to `FilamentViewPlugin::_eventCallbacks`
between the Flutter platform-message thread and the ECS frame thread. The
callback must remove its entry under synchronization before fulfilling the
promise that wakes the next frame. Then build through the established
Devtool→layer commit→bundle→Mini `do_patch`/BitBake flow and capture a fresh
QMP-first ordinary Example Demo run. This ticket fixes one process-safety
boundary; it does not claim that the saved FLR-0408 crash was caused by it or
that production Sequoia/HUD acceptance is complete.

## Facts

- FLR-0409 found exact Build-ID-matched symbols for the FLR-0408 SIGSEGV. LWP
  812 faulted in `FilamentViewPlugin::CallEvent`, called by
  `ViewTarget::DrawFrame`, at ELF VMA `0xd5198d`; the first-word read from
  `_eventCallbacks` yielded an unmapped value.
- The effective matching source stores `std::shared_ptr<std::promise<void>>`
  entries in a static `std::map`. `CallEvent` inserts then waits. Both the
  MethodResult callbacks and the `ret_*` method handler fulfil a promise
  before erasing the matching map entry. No mutex protects those operations.
- Flutter 3.32.5's exact Embedder header documents platform-message callback
  execution on the `FlutterEngineInitialize`/`FlutterEngineRun` caller thread.
  The app constructs and initializes the engine on its application thread;
  `OnFlutterPlatformMessage` dispatches directly to the handler.
- The ECS manager starts a separate `ECSManagerThreadRunner`. In the QEMU
  software-frame source path, after the waiter resumes, the next frame is
  posted to the ECS strand. Therefore next-frame insertion can overlap the
  still-pending callback-side erase.
- Historical FLR-0277 explicitly left this map race open because its A/B did
  not establish a reachable conflict. The new thread and scheduling evidence
  establishes a reachable unsafe access pattern; it still does not prove that
  the pattern caused the historical core.
- GPT-6.1 Sol's judgment-only review approves a narrow fix: use one mutex for
  every map operation; remove/copy the callback under the lock; release the
  lock before `set_value()`; never hold it while sending a Flutter message or
  waiting on a future.
- FLR-0408 produced no QMP screenshot/video. Its Sequoia/HUD pixel state is
  UNKNOWN, not black.

## Inferences

- Unsynchronized concurrent `std::map` mutation is undefined behavior and is a
  confirmed process defect in the effective source.
- Erasing before promise fulfilment prevents the just-woken ECS frame from
  reaching another map insertion until the previous entry has been removed;
  one mutex must also protect every other lookup/insert/erase to make the map
  itself safe.
- The saved SIGSEGV in the same map path is consistent with this defect, but
  consistency is not causal proof. A previous memory overwrite or independent
  lifetime failure remains possible.
- A process-stability fix will not by itself prove Sequoia pixels, original
  material/texture/lighting, HUD composition, camera depth, or interaction.

## Competing explanations

1. **The map race contributed to FLR-0408's SIGSEGV.** Prediction: the
   exact-profile crash stops recurring after all map operations are serialized
   and completion removes the event before waking ECS. Falsifier: the same
   fault recurs with source audit confirming the synchronized path.
2. **The race is real but the historical crash came from another invalid write
   or lifetime issue.** Prediction: map access is safe after the patch, but a
   comparable run still faults at another boundary or the same unrelated
   boundary. Absence of a crash alone does not prove this explanation.
3. **Scene/present/pixel failure is independent of event bookkeeping.**
   Prediction: process health improves but the immediately captured QMP image
   still lacks identifiable production Sequoia or HUD. The QMP-first capture
   distinguishes pixels from process-exit artifacts.

## Fix boundary and impacts

- Modify only the Devtool-managed `plugins/filament_view/filament_view_plugin.cc`
  source to add a file-local mutex and a single completion helper that takes
  the shared callback pointer and erases the entry while locked, then fulfils
  the promise after unlocking. Guard the insertion with that same mutex and
  route success, error, not-implemented, and `ret_*` paths through the helper.
- Do not hold the mutex while calling `InvokeMethod`, waiting on the future,
  or fulfilling a promise. Audit every `_eventCallbacks` access, including
  header/source references, before commit.
- Generate the source patch only with official Yocto Devtool after committing
  the Devtool source change. Register the byte-identical generated patch as
  `0335-flr0410-synchronize-event-callback-map-devtool.patch` under
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/` with
  `patchdir=ivi-homescreen-plugins`.
- Expected build-time impact: one small C++ source recompilation before the
  normal image dependency graph; no global CFLAGS or broad rebuild override.
  Runtime impact: a short mutex critical section on event-map operations only.
  Packaging impact: one source patch, no new package/runtime dependency.
  Integration risk: missed map access would retain undefined behavior; avoid
  holding the lock across callbacks/waits to prevent deadlock.

## Success criteria

- [x] The Devtool source baseline is the exact current recipe-applied
  `fluorite-plugins` history; no uncommitted pre-existing source changes are
  overwritten or reset.
- [x] A focused source audit finds one synchronization policy for every
  `_eventCallbacks` access, and completion erases the event before waking ECS.
- [x] A source commit is created first; official Devtool `update-recipe` then
  produces one patch whose `From` header matches that source commit. The patch
  is copied byte-identically and registered once under `meta-fluorite-trial`.
- [ ] The canonical repository/privacy/recipe gates pass; the authorized layer
  baseline lock is refreshed only by the standard helper if the tracked layer
  changes. Do not create or track an `index.local` file.
- [ ] One verified full-history bundle reaches the fixed Mini receiver; exact
  candidate `do_patch`, `do_compile`, and full image tasks pass on the existing
  `BUILD_DIR`/`TMPDIR`, with no cache deletion, cleansstate, or second build
  tree.
- [ ] Before QEMU, confirm no other owner is using the Mini build/TMPDIR/QEMU.
  Run only one QEMU at a time, using the established 4096 MiB profile if
  required, and capture a full QMP frame immediately after exact guest
  PID/UID/start-identity confirmation and before teardown.
- [ ] The ordinary Example Demo keeps `flutter-auto` alive, presents continue,
  and has no new kernel Oops or core during the bounded run. Record exact
  counters and raw evidence hashes; do not equate process liveness with pixels.
- [ ] Report production Sequoia, original material/lighting, HUD, depth,
  interaction, five-minute stability, and two-boot gates separately. If any
  remains unproven, leave the overall goal open and open a separate ticket for
  the next independent boundary.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | all `_eventCallbacks` operations and promise-completion ordering |
| Where | `filament_view_plugin.cc`; QEMU software frame loop; Mini candidate image |
| When | callback return while the next ECS frame is eligible to run |
| Who | Flutter platform callback thread and ECS frame thread roles |
| How | source audit, official Devtool patch, Mini progressive build, QMP-first runtime |

## Plan / Do / Check / Act

### Plan

1. Confirm the canonical repository, exactly one active ticket, Devtool/Podman
   identity, clean source baseline, fixed Mini receiver/build/TMPDIR, and no
   active build or QEMU owner.
2. Compare the minimal mutex/helper approach with moving callbacks to the ECS
   executor. Reject executor marshalling for this synchronous wait path because
   posting completion to the strand blocked in `future.wait()` can deadlock.
3. Edit only the Devtool-managed source, commit the source change, then invoke
   the documented component-rebase helper, which runs official
   `devtool update-recipe --mode patch --append --no-remove` from the exact
   baseline/source commits.
4. Commit the canonical layer delta, make one verified Git bundle, transfer it
   to the fixed Mini receiver, and run `do_patch`, `do_compile`, then one full
   image build without cache cleanup.
5. Run one fresh QEMU, capture the full QMP frame as soon as the guest app
   identity is confirmed, save the evidence before teardown, and inspect the
   original production scene plus HUD.

### Do

- Devtool source commit `0290b78ad139c9572b15b9e02f077421f3903b09` implements
  the map synchronization policy on top of baseline `c9ffc87`.
- Official Devtool `update-recipe` generated patch 0335, which is byte-identical
  to its registered layer copy and changes only `filament_view_plugin.cc`.
- The effective Mini build-layer checkout was distinguished from the separate
  staging repository. No Mini-side write, BitBake task, or QEMU run has yet
  occurred.

### Check

- Source diff/status, callback-map audit, official Devtool generation,
  byte-identical copy, unique registration, and `git diff --check`: PASS.
- Mini `do_patch`, compile, image, and QMP runtime: pending. Do not use the
  FLR-0408 post-exit black state or missing frame as a rendering verdict.

### UNKNOWN

- Whether synchronizing the map prevents the specific saved SIGSEGV.
- Whether the ordinary Example Demo will show identifiable Sequoia and HUD on
  the resulting candidate image.
- Whether the production material/texture/lighting, depth, interaction,
  five-minute present, and two-boot requirements will pass.

### Act

- If the runtime is stable but Sequoia/HUD pixels fail, classify the QMP frame
  by Gate A/Gate B and open a new ticket for the first unproven render or
  composition boundary. Do not extend this map ticket to unrelated scene fixes.
- Complete the overall goal only after every user-specified acceptance gate
  passes on the same final candidate image.
