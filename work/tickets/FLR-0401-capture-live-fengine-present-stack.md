# FLR-0401 — capture the live FEngine stack at unmatched Present on image 0334

- Status: In Progress
- Priority: High
- Created: 2026-10-02
- Owner: Mac observer/test source / Mini QEMU / guest Flutter+GDB / QMP evidence roles
- Branch: `feature-flr-0401-live-present-stack` (local only; stacked on FLR-0400 observer dependency)
- Dependency: [FLR-0400](FLR-0400-bounded-live-observer-polling.md), observer commit `a113c0e` and evidence commit `1e4672b`
- Plan: [FLR-0401 implementation plan](../../docs/superpowers/plans/2026-10-02-flr0401-live-present-stack.md)
- Working log: [FLR-0401 working log](../logs/2026-10-02-flr0401.md)
- Fresh run reserved: `flr0401-0001`
- Reused candidate: patch 0334; rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`; kernel/qemuboot hashes are pinned in the FLR-0399 starter.

## Objective

On the exact already-built 0334 image, capture one bounded GDB stack from the
live `FEngine::loop` thread when a Flutter queue-Present begin has no matching
return. Keep the application, scene, image, launch arguments, runtime
environment, and QEMU profile fixed. Change only debugger supervision from a
GDB-owned `run` whose later backtrace is deferred, to a direct app launch plus
one identity-checked live attach. This is a diagnostic unit, not a rendering
fix or product-acceptance pass.

## Facts, inferences, hypotheses, and unknowns

### Facts

- FLR-0400 used the exact 0334 rootfs and one bounded run. A full identity-
  bracketed QMP frame while Flutter was `READY=1` shows the CPU/GPU/FPS HUD and
  Scenes control; the fixed Sequoia ROI is uniform black. The earlier WAITING
  full frame is black and byte-identical to the pre-launch frame.
- The same live samples report `READY=1`, `PRESENT_BEGIN=1`,
  `PRESENT_RETURN=0`, and `SUN=1`. The 120-second observer ended with
  `PRESENT_DEADLINE_EXPIRED`; QMP postflight found no target process, socket,
  or forwarded-port residue.
- The saved kernel journal records an `FEngine::loop` page-fault/Oops at
  `02:44:30 UTC`; the focused coredump query is `EMPTY`. The saved instruction
  bytes contain `ff <cf>`, and the low 32 bits of RSP match the reported fault
  address. No current-run shared-library mapping, GDB stack, or causal ordering
  between the Oops and the unmatched Present was captured.
- FLR-0400 launched Flutter under `/usr/bin/gdb --batch -ex run -ex 'thread
  apply all bt 8'`. The bounded collector ran before the 150-second inferior
  timeout; the `run` command had not returned, so the queued backtrace was not
  emitted into the preserved log.
- FLR-0341 previously attached GDB to a normally launched live process and
  captured an `FEngine::loop` stack reaching Lavapipe
  `lvp_pipe_sync_wait` → `wsi_common_queue_present` on an older image. That is
  prior evidence, not proof of the current 0334 stack.
- FLR-0366 and FLR-0391 document a similar `FEngine::loop` Oops / `ff <cf>`
  signature. FLR-0366 explicitly shows that opcode/RIP symbol resemblance
  alone does not establish the faulting operation or root cause.

### Inferences

- The absence of a FLR-0400 GDB backtrace is explained by command ordering and
  the observer deadline; it is not evidence against either a WSI wait or a
  separate FEngine fault path.
- The next information-rich boundary is a selected live thread stack while
  `PRESENT_BEGIN > PRESENT_RETURN`, before the bounded run is stopped.
- Visible HUD pixels prove some Flutter output reached the QMP framebuffer;
  they do not prove a Sequoia render, native-surface composition, or healthy
  present loop.

### Hypotheses

1. **The unmatched Present again waits in Lavapipe/WSI.** Support would be a
   live `FEngine::loop` stack containing `lvp_pipe_sync_wait` and
   `wsi_common_queue_present` (or a directly nested queue-submit path).
   Refutation would be a complete selected stack that remains outside that
   wait path.
2. **The page-fault/Oops is a distinct FEngine execution path, not the caller
   of the unmatched Present.** Support would be an Oops/thread exit before a
   stable unmatched-present sample, or a selected stack outside the Present
   wait. Refutation would be a live stack at the unmatched boundary directly
   inside the Lavapipe/WSI wait.
3. **The black Sequoia ROI is a separate output/composition problem that can
   coexist with the present stall.** A stack capture alone cannot prove or
   refute this; after the present boundary is understood, retain a separate
   QMP pixel/surface discriminator.

### UNKNOWN

- Whether the exact 0334 run reaches FLR-0341's Lavapipe/WSI wait path.
- Whether the missing Present return means blocking, thread fault/exit, or a
  different interruption; the observed event ordering is not causation.
- The current-run Oops faulting instruction's loaded object, source location,
  and root cause. Do not infer an LLVM defect or stack-address truncation from
  the opcode/address pattern alone.
- Why Sequoia pixels are absent, whether SUN setup produces visible scene
  output, and whether original material/texture/light or HUD composition is
  correct.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | One unmatched Present plus one selected live `FEngine::loop` stack |
| Where | Exact 0334 Mini QEMU guest, existing Example Demo and Lavapipe/WSI path |
| When | First identity-stable `PRESENT_BEGIN > PRESENT_RETURN` sample; attach once |
| Who | Flutter PID/UID/start identity, selected FEngine thread, guest graphics stack |
| How | Bounded host polling, one 20-second GDB attach, QMP still/video, focused journal |

## Scope and controls

- Reuse the exact 0334 kernel/rootfs/qemuboot hashes, 6144-MiB QEMU profile,
  ports 10930–10932, Example Demo bundle, scene, arguments, environment, and
  existing evidence/build roles. Fresh preflight must verify each immediately
  before the single run.
- Preserve the FLR-0400 render-test environment exactly:
  `FLR0026_NATIVE_MODEL_MATCH=sequoia`,
  `FLR0026_NATIVE_MODEL_LIMIT=2`,
  `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`, and
  `FLR0305_PRODUCTION_SCENE_LIGHT=1`. These are diagnostic overrides; this
  ticket cannot establish original material/lighting acceptance.
- Change only debugger supervision: launch the same Flutter app directly,
  observe its combined app/GDB log, and attach GDB once only after a live
  unmatched-Present precondition. Append bounded GDB output to that same log
  source so readiness and debugger evidence cannot diverge.
- At the trigger, bracket process identity and capture the full QMP still
  before GDB pauses the target. Preserve the controller's one four-frame video
  from the first identity-bracketed live state; label it WAITING if that was
  the first sample. GDB selects only threads
  named `FEngine::loop`, records at most eight frames per candidate, and
  expands only a stack containing `lvp_pipe_sync_wait` to 24 frames. Bound the
  attach to 20 seconds and detach.
- Preserve the marker slice, bounded GDB/inferior log, focused kernel Oops and
  coredump query before exact app/QMP teardown. One run ID, one QEMU, one GDB
  attach; no retry after any result.
- Do not change product source, patch, camera, GLB, material, texture, light,
  Flutter UI, recipe, image, build inputs, cache, or Mini TMPDIR. Do not disable
  HUD/input/repaint to make the frame look better.

## Success criteria

1. TDD proves the direct launch uses the pinned app/environment and shared log;
   the GDB command fails closed on changed identity or matched Present; the
   selected-thread stack cap is 8 frames/24 only for `lvp_pipe_sync_wait`; the
   observer attempts attach at most once and preserves logs before teardown.
2. Fresh Mini preflight confirms exact image hashes, receiver revision,
   processes, ports, QMP socket, and unused `flr0401-0001` evidence path.
3. One QEMU run either records a live identity-matched selected stack at the
   unmatched boundary or records a precise bounded no-trigger/process-exit/
   attach-failure/timeout outcome. A missing stack is never treated as a root
   cause.
4. Full QMP still and four-frame video are preserved and visually inspected;
   Sequoia and HUD ROIs, image hashes, exact marker counts, Oops state, and
   capture identity are recorded. No image is copied to Mac.
5. GDB, app, QEMU, socket, and ports are cleanly detached/stopped and independently
   verified after the run. No unrelated process is touched.
6. Record the resulting discriminator and open the next one-factor task based
   on the actual stack. This ticket cannot claim that 3D, original materials,
   HUD composition, interaction stability, five-minute present, or two-boot
   acceptance is complete.

## Impact

- **Build-time / packaging:** none; reuse the existing exact image and cache.
- **Runtime:** one bounded debugger attach briefly pauses the selected target;
  collect QMP video first and always detach.
- **Integration risk:** attaching to the wrong process, repeated GDB attaches,
  stale log parsing, or confusing another present-stall run could alter the
  observation. Prevent this with one run ID, strict PID/UID/start checks,
  unmatched-counter gating, one attach, and one shared bounded log.
