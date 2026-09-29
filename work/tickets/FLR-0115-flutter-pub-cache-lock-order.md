# FLR-0115 — restore deterministic Flutter pub-cache lock flow

- Status: Done
- Priority: High
- Owner: Mac Yocto recipe + Mini authoritative build roles
- Created: 2026-09-12
- Updated: 2026-09-13
- Depends on: [FLR-0113](FLR-0113-isolate-explicit-light-contribution-boundary.md), [FLR-0104](FLR-0104-runtime-debug-tools.md)
- Working log: `work/logs/2026-09-12-flr0115.md`

## Work unit

Make the project-owned Flutter Example Demo recipe use the same
`pubspec.lock` during `meta-flutter` pub-cache archive generation and offline
compile. This is a build-reproducibility repair only; it does not change
rendering, light, camera, compositor, or runtime-debug package behavior.

## Problem

The authoritative current-tip image build reaches the Example Demo compile,
but `flutter pub get --enforce-lockfile --offline` exits 65. The recipe
installs its layer-provided lock in `do_configure:prepend`, while the standard
`meta-flutter` `do_archive_pub_cache` task runs before `do_configure`. The
archive is therefore generated from a source tree without the layer lock and
contains `built_value-8.13.0`; the later compile sees the injected lock pinned
to `8.12.6`, which is absent from the restored cache.

## Success criteria

- [x] The recipe applies its existing layer `pubspec.lock` before the standard
  pub-cache archive task runs.
- [x] An existing WORKDIR archive marker is safely invalidated by marker
  replacement, without deleting any protected downloads/sstate/TMPDIR tree.
- [x] The fix uses the existing `meta-flutter` archive/restore flow and does
  not change the lock content, enable network access for `do_compile`, or add
  a second cache/TMPDIR.
- [x] Existing current-tip `flutter-auto` `do_patch` and `do_compile` remain
  PASS.
- [x] Example Demo `do_archive_pub_cache` and `do_compile` pass on the same
  Mini build/cache roles.
- [x] The full image completes and its manifest contains the project-owned
  runtime-debug packagegroup.
- [x] FLR-0113 has the current-image QMP-only guest tool probe prerequisite;
  the production launch crash is split to FLR-0116 before the 3D A/B.

## Facts

- Current-tip `agl-ivi-image-flutter` stopped at Example Demo `do_compile` with
  `flutter pub get --enforce-lockfile --offline` exit 65 after 11876/11898
  tasks.
- The focused error says `built_value 8.13.0 (was 8.12.6)` and reports that
  one dependency would change.
- The recipe-provided lock pins `built_value` to `8.12.6` with its recorded
  pub.dev SHA-256.
- The restored pub cache contains `built_value-8.10.1` and
  `built_value-8.13.0`, but not `8.12.6`.
- An unlocked offline resolver run in the same existing WORKDIR/cache passes,
  selects `8.13.0`, and rewrites only the ephemeral build-tree lock.
- `meta-flutter` standard flow is `do_patch` → `do_archive_pub_cache` →
  `do_restore_pub_cache` → `do_configure` → `do_compile`.
- The current layer packagegroup resolves independently and already owns
  `gdb`, `gdbserver`, `systemd`/`coredumpctl`, `clang`/`llvm-symbolizer`,
  syscall/profiling tools, and targeted debug packages.
- Commit `5136925` changed the recipe append to a Python task body because the
  inherited `do_patch` task is Python; the previous shell fragment caused a
  parse-time `SyntaxError` and was removed.
- On the existing Mini build/cache roles, the corrected forced
  `do_archive_pub_cache` task passed and generated the lock-bearing archive
  ending in `187f81ba6c3d902e4aae56fbdadd9c02-3.32.5.tar.bz2`. The restored
  cache contained the pinned `built_value-8.12.6` package.
- The focused Example Demo `do_compile` passed 2590/2590 tasks and the full
  `agl-ivi-image-flutter` build passed 11898/11898 tasks. The current rootfs
  manifest includes the project-owned runtime-debug packagegroup and its
  requested debugger, coredump, LLVM, syscall, profiling, and debug-symbol
  packages.
- One QEMU preflight/start/guest-ready/serial-exec run passed on the resulting
  image. The guest tool probe found `gdb`, `gdbserver`, `coredumpctl`,
  `llvm-symbolizer`, `strace`, `perf`, `eu-stack`, `addr2line`, and `readelf`.

## Inferences

- The failure is a task-order/cache-identity mismatch, not a missing runtime
  debug package and not a rendering regression.
- Preserving the existing lock and making it visible before archive creation
  is more reproducible than changing the pinned dependency merely to match a
  stale archive.
- The repair belongs in the project recipe task ordering; changing the
  external `meta-flutter` class or enabling online compile would broaden the
  scope and weaken the offline contract.

## Hypotheses and falsifiers

1. **Lock timing is causal.** If the archive task after the fix contains the
   pinned package set and offline compile passes, this is supported.
2. **The lock itself is stale or invalid.** If archive generation with the
   lock present cannot resolve `8.12.6` even with its normal network-enabled
   archive task, the lock must be regenerated from the current app graph; do
   not infer this from the offline cache miss alone.
3. **A different source/cache identity is involved.** If the archive and
   compile still disagree after the task-order fix, compare the exact
   `PUB_CACHE_ARCHIVE`, `PUBSPEC.lock`, source revision, and task logs before
   changing dependencies.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | lock pins 8.12.6; archive/cache resolves 8.13.0 | lock, archive listing, pub log |
| Where | Example Demo recipe and standard meta-flutter archive boundary | recipe, task log |
| When | current-tip full-image build after flutter-auto compile | image log, task sequence |
| Who | project recipe integration and Mini build roles | working log |
| How | install lock in `do_patch`, then use standard archive/restore/offline compile | recipe diff, BitBake gates |

## PDCA

### Plan

1. Preserve the failed full-image log and prove the lock/cache mismatch in the
   existing WORKDIR.
2. Move the existing lock installation to a task boundary before
   `do_archive_pub_cache`.
3. Commit the recipe change on Mac, transfer one complete-history bundle, and
   rerun only the affected Mini tasks before the full image.
4. Verify the current rootfs debug tools and hand back to FLR-0113.

### Do

- Current-tip metadata, `flutter-auto` patch, and `flutter-auto` compile pass.
- Full image failed only at Example Demo pub dependency resolution.
- Lock/cache mismatch was reproduced with an unlocked offline resolver.
- The minimal recipe edit was committed as `5136925`, transferred as one
  complete-history bundle, and applied on the clean authoritative Mini
  receiver without touching the dirty receiver.
- The corrected archive, Example Demo compile, full image, current manifest,
  and current-image guest tool probe all passed. The runtime launch result is
  intentionally handed to FLR-0116 because it is a separate application
  startup/rendering gate.

### Check

- Failure evidence: `$EVIDENCE_ROOT/flr0113-authoritative/agl-ivi-image-flutter-current.log`.
- Focused pub evidence: `$EVIDENCE_ROOT/flr0113-authoritative/pub-get-offline-unlocked.log`.
- Corrected archive/task evidence: `$EVIDENCE_ROOT/flr0113-authoritative/`.
- Example Demo compile evidence: `$EVIDENCE_ROOT/example-do-compile-5136925.log`.
- Full image evidence: `$EVIDENCE_ROOT/agl-ivi-image-flutter-5136925.log`.
- Current-image tool probe: `$EVIDENCE_ROOT/flr0115-runtime-tool-probe-5136925.output`.
- QMP-only tool-probe and production-late frames were captured at 1280x800;
  both were all black in this run because the later production launch aborted
  before a comparable 2D/3D presentation. This is not a rendering verdict for
  FLR-0115 and is handed to FLR-0116.

### Act

- If the pinned lock works once present before archive generation, retain the
  lock and close this build-reproducibility unit.
- If the pinned lock cannot be archived with normal network access, stop and
  record the exact resolver constraint before considering a separately
  generated lock update.
- Resume FLR-0113 only after the current image is built and the debug-tool
  probe is recorded; if the app aborts before its first frame, split that
  runtime cause into a new ticket before changing the renderer.

## UNKNOWN

- Whether the rebuilt image reaches the requested 3D evidence; this ticket
  does not claim a rendering result. FLR-0116 owns the pre-frame abort found
  during the first current-image launch.
