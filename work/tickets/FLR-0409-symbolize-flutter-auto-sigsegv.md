# FLR-0409 — resolve exact flutter-auto SIGSEGV symbols

- Status: Done (bounded symbol and source-boundary investigation)
- Priority: High
- Created: 2026-10-03
- Owner: existing Yocto package/debug artifacts / Mini evidence role / GDB-symbolization role
- Branch: `feature-flr-0409-symbolize-flutter-auto-sigsegv`
- Depends on: [FLR-0408](FLR-0408-replay-known-positive-sequoia-profile-on-0334.md), evidence run `flr0408-0001`, checkpoint `6bc260c`
- Plan: [FLR-0409 bounded symbol-recovery plan](../../docs/superpowers/plans/2026-10-03-flr0409-symbol-recovery.md)
- Working log: [FLR-0409 working log](../logs/2026-10-03-flr0409.md)

## Objective and boundary

Use only already-existing image/package/debug/link/install artifacts to find
symbols that exactly match the crashed `flutter-auto` executable from the 0334
image. If an exact match exists, resolve the faulting instruction and caller
chain far enough to identify the first defensible source boundary. If none
exists in the bounded approved search scope, record the checked locations and
stop with symbols unavailable. Do not regenerate artifacts in this ticket.

This is crash-boundary symbolization, not a rendering verdict or a product fix.
It does not reopen the FLR-0408 QEMU run: that process has exited and no live
QMP frame exists. Sequoia/HUD pixels remain UNKNOWN.

## Facts

- FLR-0408 used the exact 0334 rootfs SHA-256
  `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`, with
  the matching kernel and qemuboot hashes documented in its ticket.
- `flutter-auto` PID 765 / UID 1001 / start token 239895 ended with SIGSEGV at
  `2026-10-02T22:35:52Z`. Its core is retained at
  `$EVIDENCE_ROOT/flr0408-0001/qemu/core-pid765.elf.zst` on the Mini, SHA-256
  `9961abd4e8adc9fb69298e43772fd7674e486df0a85617fe8ff8f18a865548b0`.
- The mapped executable was stripped `/usr/bin/flutter-auto`, Build-ID
  `529c5d321d81192f82f146d9d23736722aec2208`; no matching guest
  `/usr/lib/debug/.build-id` file was found during FLR-0408.
- GDB recorded signal thread LWP 812, `SEGV_MAPERR`,
  `si_addr=RAX=0x7f0a79cbc1c4`, and RIP `0x56032183498d`. The decoded instruction was
  `mov (%rax),%rax`. The instruction lies in the mapped executable at the
  currently recorded mapping-relative offset `0xd5198d`.
- The mapped GDB transcript is retained at
  `$EVIDENCE_ROOT/flr0408-0001/qemu/gdb-core-pid765-mapped.out`, SHA-256
  `5fa2e889fbe4101db4217e0a1a052c83575aa9ed3ac190067be1afead1b626a7`.
- The transcript contains unresolved application frames. The core and original
  image were not copied to the Mac or committed. FLR-0408 captured no QMP
  screenshot or video.

## Result — exact symbol and first source boundary

- The exact already-existing package-split debug executable was found at the
  role path
  `$TMPDIR/work/corei7-64-agl-linux/flutter-auto/2.0/packages-split/flutter-auto-dbg/usr/bin/.debug/flutter-auto`.
  Its Build-ID is exactly
  `529c5d321d81192f82f146d9d23736722aec2208`, matching the stripped image ELF;
  it is x86-64 ET_DYN and contains `.debug_info`, `.debug_line`, and `.symtab`.
- Core map base `0x560320ae3000` agrees with the executable's first PT_LOAD
  (`p_vaddr=0`, file offset 0). Thus runtime RIP `0x56032183498d` maps to ELF
  VMA `0xd5198d`.
- Exact symbols identify the faulting frame as
  `plugin_filament_view::FilamentViewPlugin::CallEvent(...)`, called from
  `ViewTarget::DrawFrame(unsigned int)`, then the `ViewTarget::OnFrame` lambda.
  The saved LWP 812 instruction reads the first word of the static
  `_eventCallbacks` map and dereferences it; the dereference faults on unmapped
  `RAX=si_addr=0x7f0a79cbc1c4`.
- The effective source at the matching recipe work tree inserts into
  `_eventCallbacks` in `CallEvent`, then waits on the returned future. Its
  MethodResult callbacks and registered `ret_*` handler call `set_value()`
  before erasing entries. There is no mutex guarding the map.
- The exact Flutter embedder header states that its platform-message callback
  runs on the thread calling `FlutterEngineInitialize`/`FlutterEngineRun`.
  `shell/main.cc` constructs `App`; `App` initializes `FlutterView`; that path
  initializes the engine on the application thread. The engine callback calls
  `IncomingMessageDispatcher::HandleMessage` directly, without a thread hop.
- `ECSManager::setupThreadingInternals` creates a separate
  `ECSManagerThreadRunner`. The QEMU software-frame source path calls
  `DrawFrame`, waits for the Flutter callback, and posts the next frame to the
  ECS strand. Because callback code fulfils the promise before erasing the map
  entry, the next insertion can run while the prior erase is still pending.
  This is a reachable unsynchronized map-mutation defect. Whether this exact
  interleaving caused the preserved SIGSEGV remains UNKNOWN.
- Historical FLR-0277 had already noted the map race as possible but left it
  open because its frame-event A/B did not establish a reachable conflicting
  schedule. The current thread contract and software-frame recurrence close
  that process-level evidence gap; they do not retrospectively prove the old
  crash's cause.
- The host's GNU binutils 2.38 resolves function names but does not decode the
  DWARF 5 forms in the debug companion, so source-line lookup is unavailable
  with that tool version. The exact source was inspected directly. No rebuild,
  QEMU start, source write, cache operation, or artifact copy occurred.

See the bounded, sanitized [FLR-0409 evidence manifest](../evidence/FLR-0409-0001.md).

## Inferences

- The immediate bad value was read while `std::map::operator[]` traversed
  `_eventCallbacks`; its invalid state is consistent with concurrent map
  mutation, but does not alone identify when or who corrupted it.
- Source and callback-thread contracts establish an unsafe concurrent access
  path independent of whether it explains the saved SIGSEGV.
- The fault occurred after a `DrawFrame` call boundary. It does not establish
  a Vulkan, Wayland, Filament rendering, present-completion, or pixel failure.

## UNKNOWN

- Whether the reachable `_eventCallbacks` race caused the saved LWP 812 SIGSEGV;
  that requires a new fixed/runtime comparison.
- Whether earlier memory corruption or a separate lifetime violation also
  contributed.
- Any FLR-0408 pixels, scene visibility, HUD composition, or rendering/present
  relationship. That run captured no live QMP frame, so Sequoia/HUD visibility
  remains UNKNOWN, not black.

## Hypotheses and falsifiers

1. **Concurrent `_eventCallbacks` mutation caused the saved crash.** The exact
   source permits next-frame insertion to overlap callback-side erase; support
   for attribution requires a same-path reproduction or a fix eliminating the
   crash across repeated comparable runs. A crash at an unrelated boundary
   after synchronization weakens this hypothesis.
2. **The observed race is real but another invalid write/lifetime issue caused
   the saved crash.** Support would be a later crash with the map synchronized
   and evidence localizing it elsewhere. Absence of a crash alone does not
   prove the historical cause.
3. **The visual/present failure is independent of this crash boundary.**
   FLR-0408 has no pixels; a fresh full-frame QMP capture is required to assess
   it.

## Search and execution boundary

Follow this order, using paths established from the exact image manifest and
existing environment documentation:

1. Read the exact image's package manifest and existing package metadata; look
   for already-produced `flutter-auto` debug packages, split debug files, or
   deployed debug artifacts. The ELF Build-ID must match exactly.
2. If absent, inspect only the identified recipe's existing link/install
   outputs for the final unstripped executable or separate debug file. Do not
   run a task to regenerate an output.
3. If exact executable symbols are absent, inspect only directly associated
   existing maps/objects/source and report them as partial leads, not exact
   symbolization.
4. For any candidate, verify Build-ID, architecture, executable sections, and
   PIE load bias using the saved core mapping and ELF program headers before
   resolving RIP and frames. Preserve the input artifact in place.

No BitBake task, build, QEMU start, guest package installation, cache cleanup,
source mutation, Devtool action, branch change in another worktree, or copying
the raw core/image to the Mac is in scope. Do not inspect unrelated caches or
other tasks' build outputs. Stop if the next step would mutate shared state or
needs an artifact-owner handoff.

## Success criteria

- [x] Revalidate the recorded core/transcript identities in place; keep large
  artifacts on the Mini.
- [x] Identify the exact image manifest and matching package-split debug ELF;
  verify Build-ID, architecture, segments, and PIE load bias.
- [x] Resolve the LWP 812 faulting function/caller boundary and inspect the
  exact effective source and thread contract.
- [x] Compare the thread/schedule evidence with FLR-0277 without changing its
  historical record.
- [x] Record the map race as a confirmed process defect while keeping its
  causal relation to the saved SIGSEGV UNKNOWN.
- [x] Keep FLR-0408 visual state UNKNOWN and create separate FLR-0410 for the
  synchronization fix and fresh runtime validation.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | exact Build-ID symbol availability and faulting instruction/caller |
| Where | existing 0334 image/package/debug/link/install outputs and preserved core |
| When | after the FLR-0408 process exited and before any new runtime replay |
| Who | image/package owner role, Mini evidence role, symbolization role |
| How | read-only manifest-to-recipe-to-existing-artifact search; GDB/ELF mapping check |

## Plan / Do / Check / Act

### Plan

- Reuse only the exact run/image identity and Mini-resident core from FLR-0408.
- Compare the existing packaged-debug route with the existing link/install
  output route; prefer the package tied to the image manifest.
- Verify Build-ID, architecture, ELF segments, and load bias before any
  symbolizer invocation.
- Stop if exact symbols are not already present; do not trigger a rebuild.

### Do

- Revalidated the in-place core/transcript hashes against FLR-0408 evidence.
- Found the exact Build-ID-matched `flutter-auto-dbg` package split; no rebuild
  or package installation was performed.
- Correlated the ELF load bias and resolved `CallEvent` → `DrawFrame` →
  `OnFrame` symbols. GNU binutils 2.38 emitted DWARF-form warnings and could
  not provide source lines; inspected the exact matching recipe source instead.
- Traced Flutter's exact platform-message callback contract, the App/Engine
  initialization route, direct inbound dispatch, the separate ECS thread, and
  the QEMU software-frame recurrence.
- Read the historical FLR-0119 and FLR-0277 records before selecting a fix.
  GPT-6.1 Sol's judgment-only review concluded that the source proves a
  reachable unsynchronized map-mutation defect, but not that it caused the
  historical SIGSEGV; it recommended one mutex, erase-before-fulfil, and no
  lock across waits/messages.
- The initial ViewTarget lookup omitted its `core/scene` directory; a targeted
  `find` resolved it. The first recursive listing included `.pc` patch-history
  snapshots, so later searches excluded `.pc` and `.git`. No source state was
  changed.

### Check

- Exact Build-ID match and ELF mapping: **PASS**.
- Faulting function/caller source boundary: **PASS**.
- Unsafe map access schedule: **CONFIRMED IN SOURCE**; historical crash
  causality: **UNKNOWN**.
- Mini core/GDB hashes and exact 0334 artifact identities: **PASS**.
- QMP pixels, Sequoia/HUD visibility, and relation to the fault: **UNKNOWN**;
  FLR-0408 has no live frame.
- No BitBake, QEMU, cache, source, Devtool, or artifact-copy operation ran.

### UNKNOWN

- Whether the source race caused the saved SIGSEGV; whether independent memory
  corruption/lifetime problems remain; and all FLR-0408 pixel/scene state.

### Act

- Close FLR-0409 as the bounded source-boundary investigation.
- Start FLR-0410 as the sole In Progress task: synchronize all
  `_eventCallbacks` accesses, erase the completed entry before waking the ECS
  waiter, then rebuild on the existing Mini build/TMPDIR and capture QMP
  immediately after live identity confirmation.
- Keep the production visual goal open; a crash fix, build success, or
  diagnostic fixture is not Sequoia/HUD acceptance.
