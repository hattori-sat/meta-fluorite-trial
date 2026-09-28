# FLR-0340 — map the present wait to the exact semaphore/source path

- Status: Done
- Priority: High
- Owner: Mesa/Lavapipe source provenance and Filament Vulkan synchronization roles
- Created: 2026-09-28
- Predecessor: [FLR-0339](FLR-0339-capture-vulkan-present-stall-stack.md)
- Working log: `work/logs/2026-09-28-flr0340.md`
- Baseline evidence: [FLR-0339 run 0001 QMP screenshot](../evidence/FLR-0339-qmp-run-0001.png) and [QMP frame sequence](../evidence/FLR-0339-qmp-run-0001-sequence.mp4)

## Objective

Determine whether the Lavapipe pending-sync wait captured in FLR-0339 belongs
to the production `vkQueuePresentKHR` wait on Filament's finished-drawing
semaphore, or to an unrelated queue/fence synchronization path. Establish the
exact source revision used by the fixed Mini image before interpreting source
lineage. This is a read-only source-mapping task; it does not attempt a fix.

## Success criteria

- Identify the exact Mesa recipe/source revision and patch set that produced
  the runtime's Mesa 24.0.7 symbols, or explicitly record provenance UNKNOWN.
- Map `lvp_pipe_sync_wait_locked` / `lvp_pipe_sync_wait` to the relevant Mesa
  callers, distinguishing `vkQueuePresentKHR` wait-semaphore handling from
  queue-submit/fence waits.
- Map the Filament semaphore logged by FLR-0339 from creation through the
  queue submission that signals it and the `vkQueuePresentKHR` wait list.
- State whether the captured sync pointer can be tied to that API semaphore;
  pointer proximity is not accepted as identity proof.
- Record a ranked hypothesis result and one next falsifiable probe. If source
  provenance or the mapping cannot be verified read-only, stop with UNKNOWN.

## Ranked hypotheses

1. The FEngine loop is inside Lavapipe's queue-present wait for the logged
   finished-drawing semaphore. Predicted: the exact Mesa call chain reaches
   the implementation's present function and consumes that wait semaphore.
2. The captured Lavapipe wait belongs to another queue or fence operation.
   Predicted: its caller path resolves to queue submission or fence handling,
   independent of the logged Present call.
3. The wait is downstream of an earlier submission/signal ordering defect.
   Predicted: Filament's submit path does not signal the semaphore before the
   present wait is issued, or the same semaphore is reused/reset incorrectly.
4. The Mesa source available on the Mini does not match the binary identity
   in the image. Predicted: source revision/patch provenance cannot be joined
   to the image's package manifest or build metadata.

## Facts from predecessor

- FLR-0339 run 0001 observed one queue-present enter/begin and zero return/done
  markers after the two-second grace; the Flutter parent stayed alive.
- Nineteen draw-end and native Wayland commit markers were observed. QMP showed
  the 2D HUD/metrics/Scenes control and 768,000 black pixels in the lower 3D ROI.
- The partial GDB transcript reached LWP 718, `FEngine::loop`, in Mesa 24.0.7
  `lvp_pipe_sync_wait_locked` / `lvp_pipe_sync_wait` with
  `VK_SYNC_WAIT_PENDING` and an infinite timeout. GDB timed out after 20 sec.
- The logged Vulkan semaphore handle and GDB's Lavapipe sync-object pointer
  differ; their relationship is UNKNOWN.

## Bounded result

- The exact saved `runqemu` arguments for FLR-0335/0339 were re-hashed on the
  Mini: rootfs `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`,
  qemuboot `ef5309f471e4bd159febbbc2c630368ec609d21900179b3694a6fb6c16f8c44a`,
  and kernel `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
  all match the recorded FLR-0335 image. A separate configured deploy candidate
  did not match and was not the image used by this QEMU run.
- The exact image manifest lists Mesa/Lavapipe 24.0.7 and Filament 1.65.4.
  The cached Mesa 24.0.7 source archive SHA-256 is
  `7454425f1ed4a6f1b5b107e1672b30c88b22ea0efea000ae2c7d96db93f6c26a`,
  matching its download completion metadata. Mesa's exact applied patch set
  remains UNKNOWN: the image TMPDIR has no retained Mesa fetch/unpack/patch
  task logs or source checkout.
- The image's retained Filament worktree is based on Git revision
  `2a86c0c60ecce9443fc34631570e924721b20b40`; its exact `do_patch` log records
  71 applied patches, including the Present and submit-semaphore diagnostics.
- Filament source maps one path from command-buffer submit signaling
  `mSubmission` to `mLastSubmit`, through `acquireFinishedSignal()`, into
  `VulkanPlatformSurfaceSwapChain::present()` and `VkPresentInfoKHR`'s
  `pWaitSemaphores`. FLR-0339's two Present markers carry the same semaphore
  handle and report `wait=true`; its retained serial evidence does not include
  the submit-signal handle.
- **Correction recorded by FLR-0342:** the cached Mesa 24.0.7 source does not
  unconditionally return for `VK_SYNC_WAIT_PENDING`. Lavapipe first waits while
  `!sync->signaled && !sync->fence`; the pending flag affects only the later
  fence-wait path. The earlier immediate-return statement was a source-reading
  error. The similarly named `vk_queue_wait_before_present()` remains ANV-only.
  FLR-0342's exact-image GDB stack reaches `cnd_wait` in this loop, and its
  runtime disassembly corroborates the source. The FLR-0340 caller was still
  UNKNOWN at the time; FLR-0341 established the WSI caller.

This ticket is complete as a bounded read-only source/provenance map, not as a
root-cause finding. FLR-0341 owns the single-thread runtime caller and
submit-to-Present marker capture.

## Scope and controls

### In scope

- Read-only inspection of the fixed Mini image's package/build identity,
  selected Mesa recipe metadata, exact source checkout/patches, and relevant
  Filament source already used for the image.
- Bounded source searches around `lvp_pipe_sync_wait`, its direct callers,
  queue-present wait processing, Filament semaphore creation, queue submit,
  and present wait-list construction.
- Record commands, source revisions, patch identities, and concise excerpts
  with role-based paths only.

### Out of scope

- QEMU, another GDB attach, target runtime changes, or additional video.
- Devtool, `do_patch`, BitBake tasks/builds, bundle transfer, or image changes.
- Source edits, patch creation, changing light/camera/material/texture, or
  declaring a root cause from a source resemblance alone.
- Broad log dumps, full-repository scans, or cleaning any build state.

## PDCA

### Plan

1. Confirm canonical repository, sole active ticket, and checkpoint contract.
2. Resolve the exact Mini image/package/Mesa source identity using existing
   manifests/build metadata without starting BitBake or changing files.
3. Follow only the relevant Mesa wait callers and Filament semaphore
   create/signal/present path; compare them against FLR-0339's selected stack
   and markers.
4. Record facts, inference, remaining UNKNOWN, and a falsifiable next gate.
5. Close this static mapping ticket; create a separate ticket before any new
   runtime probe or source/build change.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Image identity | Exact source/image/build link or bounded UNKNOWN | Exact FLR-0335 rootfs, qemuboot, and kernel hashes revalidated from saved runqemu arguments | PASS |
| Mesa provenance | Exact recipe/source/patch set or explicit UNKNOWN | 24.0.7 archive hash and package version identified; downstream patch set UNKNOWN because Mesa task logs/source were absent | PARTIAL |
| Mesa caller path | Present wait distinguished from submit/fence wait | Stock-source pending-wait behavior found; ANV helper ruled out for Lavapipe; exact runtime caller remains UNKNOWN | PARTIAL |
| Filament semaphore lifecycle | Create/signal/wait path mapped or explicit UNKNOWN | Exact worktree revision/71-patch log and source signal→acquire→Present-wait path mapped; submit handle not captured in FLR-0339 serial evidence | PARTIAL |
| Scope | No runtime/build/source mutation | Read-only Mini inspection only; no BitBake, Devtool, QEMU, patch, or source change | PASS |

### Act

- No patch is justified. Close this bounded source-mapping unit with the Mesa
  caller, downstream patch set, and runtime submit handle explicitly UNKNOWN.
- FLR-0341 is the next independent runtime unit: one exact-image QEMU run,
  QMP full-frame/sequence evidence, only `FEngine::loop` GDB threads examined,
  and the submit-signal/Present-wait markers captured together.

## UNKNOWN

- Whether the exact LWP 718 wait is called by Mesa queue-present code.
- Whether the logged Vulkan semaphore handle maps to the captured Lavapipe
  sync object and which submit operation signals it.
- Whether the synchronization boundary explains missing 3D pixels.
- Whether the exact downstream Mesa patch set changes this wait/fence path.
- Whether Lavapipe's WSI present route, a queue-submit worker, or an unrelated
  synchronization path is the captured caller.

## PDCA checker

- Status: PASS for the bounded read-only mapping; causal path remains UNKNOWN.
- Evidence: exact saved runqemu artifact hashes; image manifest; matching
  Mesa archive completion checksum; Filament source revision and 71-entry
  `do_patch` log; selected runtime Present markers.
- Follow-up: [FLR-0341](FLR-0341-capture-lavapipe-present-wait-runtime.md).
