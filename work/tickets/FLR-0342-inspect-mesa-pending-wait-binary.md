# FLR-0342 — inspect the exact Mesa pending-wait implementation

- Status: Done
- Priority: High
- Owner: Mesa/Lavapipe binary provenance and Vulkan WSI runtime roles
- Created: 2026-09-28
- Predecessor: [FLR-0341](FLR-0341-capture-lavapipe-present-wait-runtime.md)
- Baseline image: FLR-0335 rootfs `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- Working log: `work/logs/2026-09-28-flr0342.md`

## Objective

Correct FLR-0340's pending-wait interpretation by matching FLR-0341's live
`lvp_pipe_sync_wait_locked(wait_flags=VK_SYNC_WAIT_PENDING)` stack to the exact
FLR-0335 image's Mesa binary, debug ELF, source archive, and retained build
metadata. Determine where the pending flag is tested relative to the actual
`cnd_wait`. This is a static task: no BitBake, Devtool, QEMU, source edit,
patch, or image change.

## Success criteria

- Revalidate the exact FLR-0335 input and match the runtime library and
  separate debug ELF by SHA-256/Build ID. Use only the exact build's manifest
  and configured `DL_DIR`; transfer no rootfs or ELF to Mac.
- Compare the exact archive's wait/signal source with the runtime binary's
  bounded `lvp_pipe_sync_wait` disassembly and the saved GDB source line.
- Search only the exact image's retained Mesa recipe/task/build metadata for
  SRCREV and applied patch order. If unavailable, record the specific evidence
  gap and keep the downstream patch set UNKNOWN.
- Decide whether the apparent conflict was a source-reading error, a
  binary/source mismatch, or an unresolved downstream change.
- Preserve all findings and non-results, then define one falsifiable next gate;
  do not patch or build in this ticket.

## Inherited facts

- FLR-0341 captured an FEngine thread in
  `lvp_pipe_sync_wait_locked(wait_flags=VK_SYNC_WAIT_PENDING,
  abs_timeout_ns=UINT64_MAX)` and a caller frame in
  `wsi_common_queue_present`.
- The second `FLUORITE_VK_SUBMIT_RETURN` signal handle exactly matched the
  subsequent Present wait handle, yet Present-enter had no return.
- FLR-0340 incorrectly summarized `lvp_pipe_sync_wait_locked()` as an
  immediate return for `VK_SYNC_WAIT_PENDING`. FLR-0342 corrects this: the
  function waits while `!sync->signaled && !sync->fence`, then handles the
  pending flag on the later fence path.
- QMP showed the 2D HUD, while the lower 768,000-pixel 3D ROI remained
  uniformly black through the screenshot and all eight frames. The app and QEMU
  were cleanly stopped.

## Ranked hypotheses

1. **Supported by the runtime stack and disassembly:** execution reached
   `cnd_wait` before the `WAIT_PENDING` test in this Lavapipe wait function.
   The exact `signaled` and `fence` field values were not read directly.
2. **Disfavored:** source-line mapping or binary identity is wrong; the exact
   runtime/debug ELF Build IDs match, and GDB's line is the `cnd_wait` line in
   the hash-verified Mesa 24.0.7 archive.
3. **UNKNOWN:** downstream patches may alter other code; the exact Mesa
   `do_patch` log/source checkout was not retained.
4. **Next discriminator:** FLR-0343 observes the exact wait object's
   `signaled` and `fence` fields and catches a writer, or records a bounded
   no-hit result.

## 4W1H (Why intentionally excluded)

| Dimension | Target |
| --- | --- |
| What | Exact `lvp_pipe_sync_wait_locked` runtime implementation and pending branch |
| When | After FLR-0341's same-handle Present stall |
| Where | Fixed Mini image and existing Mesa download/build metadata |
| Who | Mesa recipe/build provenance and Lavapipe binary roles |
| How | Exact hashes/build ID, bounded source/disassembly, retained task metadata |

## Scope and controls

### In scope

- Read-only inspection of the saved runqemu input, rootfs manifest/library
  identity, cached source archive, exact build logs/recipe metadata, and bounded
  source/disassembly excerpts.
- Reuse only existing build/download locations. Do not create another TMPDIR or
  extract a second source tree.
- Extract only the runtime and matching debug ELF to one unique Mini evidence
  directory for local disassembly; do not transfer or commit either binary.
- Record role paths, hashes, command outcomes, and explicit unknowns.

### Out of scope

- QEMU or app launch, Devtool, BitBake, source/patch/image changes, or Git
  history alteration.
- Broad filesystem searches, entire task-log dumps, or transferring a QEMU
  image/rootfs to Mac.
- Treating pointer proximity or debug line numbers alone as source identity.

## PDCA

### Plan

1. Verify canonical repository, sole active ticket, checkpoint, and exact
   FLR-0335 rootfs identity from its saved runqemu record.
2. Identify the matching installed Lavapipe library's package metadata,
   SHA-256, and ELF build ID using bounded existing artifacts.
3. Compare only the stock Mesa 24.0.7 pending-wait function and direct caller
   against the exact binary's corresponding disassembly.
4. Inspect retained task/build metadata for Mesa source revision and patch
   order; do not infer them from a similarly named source archive.
5. Record which hypothesis is supported, what remains UNKNOWN, and whether a
   further runtime probe is justified.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Exact image/library identity | Rootfs and build pair, package manifest, runtime/debug ELF hash and Build ID | FLR-0335 rootfs/qemuboot match the one exact build config; manifest lists `mesa-vulkan-drivers`/`mesa-dbg` 24.0.7; runtime SHA `5f72d1fb…d789b1`; both ELFs share Build ID `18eb7b64…59a403` | PASS |
| Source comparison | Exact configured archive and wait/signal source | Archive SHA `7454425f…3f6c26a`; source lines 143–188 wait on `!signaled && !fence`; GDB source line 174 is `cnd_wait` | PASS |
| Runtime binary branch | Bounded machine-code branch | `lvp_pipe_sync_wait_locked` is DWARF-inlined in `lvp_pipe_sync_wait`; `cnd_wait` call at ELF offset `0xc5ec3`; `WAIT_PENDING` test is later at `0xc5f40` | PASS |
| Patch provenance | Exact SRCREV/patch list or explicit gap | Exact TMPDIR has no Mesa fetch/unpack/patch/compile logs or source checkout; downstream patch set UNKNOWN | PARTIAL |
| Scope | No QEMU/build/source/image mutation | No QEMU, BitBake, Devtool, source, patch, recipe, or image changes; two ELFs and one debuglink symlink created only under Mini FLR-0342 evidence | PASS |

### Act

- Correct the FLR-0340/0341 record: `VK_SYNC_WAIT_PENDING` does not bypass the
  Lavapipe loop while the sync has neither `signaled` nor `fence`.
- Close this static unit. FLR-0343 owns one bounded Mini runtime capture of the
  exact sync's initial state and signal/fence writer.

## UNKNOWN

- Exact downstream Mesa SRCREV and applied patch stack.
- Whether/where the exact waiter object's signal or fence is produced.
- Whether the blocked Present is sufficient to explain the missing 3D pixels.
