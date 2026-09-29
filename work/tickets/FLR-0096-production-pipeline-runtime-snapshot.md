# FLR-0096 — snapshot the production pipeline-create runtime boundary

- Status: Done
- Priority: High
- Owner: Fluorite runtime evidence / Vulkan driver boundary
- Created: 2026-09-12
- Depends on: [FLR-0095](FLR-0095-startup-pipeline-boundary-capture.md)
- Working log: `work/logs/2026-09-12-flr0096.md`
- Evidence manifest: `work/evidence/FLR-0096-production-runtime-snapshot-2026-09-12.md`

## Work unit

Capture a bounded runtime snapshot while the production scene is inside the
fourth Vulkan pipeline-create operation identified by FLR-0095. Use the same
authoritative image and fixed QEMU/QMP path. The aim is to distinguish a
long-running llvmpipe/shader compilation, a driver or syscall wait, an
application-side loop, or a missing trace completion. This is an evidence-only
ticket; it must not change source, recipe patches, fence/present behavior, or
Wayland stacking.

## Success criteria

- Reuse the fixed receiver, build/TMPDIR, image artifacts, and one short QMP
  socket alias; do not create another build, TMPDIR, receiver, or QEMU.
- Run one production case with one `flutter-auto` process and capture QMP
  before/late frames plus the startup and fourth-pipeline markers.
- While the fourth create is active, collect a bounded `ps`/`/proc` snapshot,
  GDB thread backtrace if available, and a short allowlisted syscall trace if
  available. Record missing tools as `UNKNOWN`.
- Prove QMP teardown, process cleanup, and evidence hashes.
- Classify the runtime state as compile/work-queue progress, driver/syscall
  wait, application-side stall, or insufficient evidence. Do not claim a
  production fix from a diagnostic snapshot.

## Out of scope

- No source or recipe patch and no image rebuild.
- No global kill, `cleanall`, `cleansstate`, or cache deletion.
- No changes to Vulkan synchronization, present, Wayland surface order, or
  alpha.

## Facts

- FLR-0095 captured production pipeline inputs 1–3 with create result `0` and
  a fourth input with no completion marker in the bounded late extraction.
- The production native region stayed at `0/223,200` while the HUD changed,
  so the runtime has not reached an evidenced native-pixel result.
- The neutral fixture reaches native pixels later than its initial pipeline
  create, so the snapshot timing must be tied to the fourth production input,
  not only to process startup.
- The image contains the project pipeline markers; availability of GDB,
  `strace`, and useful symbols on the target is not yet confirmed.

## Inferences

- A thread/syscall snapshot taken after the fourth input appears and before
  QMP teardown is the smallest observation that can separate a slow compile
  from an application-side or driver-side stall.
- If the fourth create eventually completes and native pixels appear, the
  prior failure was a bounded timing limit rather than a permanent render
  failure.

## Hypotheses

1. The fourth pipeline is still compiling in the software Vulkan driver.
   Prediction: worker threads or the main thread show bounded work/futex waits,
   and a later sample may emit `CREATE_RESULT`.
2. The create is blocked in a driver or kernel wait. Prediction: GDB or
   syscall evidence shows a stable ioctl/futex/epoll boundary without a
   corresponding completion marker.
3. The application is looping or waiting on a production resource before the
   driver returns. Prediction: the main thread remains in the application or
   resource-loading call chain while no driver progress is visible.
4. The completion exists but the current trace extraction misses it.
   Prediction: a direct bounded runtime-log read or a second marker extraction
   finds `CREATE_RESULT` even though the earlier output did not.

## UNKNOWN

- Whether the fourth create is active at the time a debugger can attach.
- Whether the image has usable GDB symbols and `strace` permissions.
- Whether the fourth create eventually completes beyond the FLR-0095 window.

## Plan / Do / Check / Act

### Plan

1. Verify fixed image identity and target cleanup.
2. Start one production QEMU and capture the startup/pipeline markers.
3. At the fourth input, take bounded process, `/proc`, GDB, and syscall
   snapshots, then capture a late QMP frame and extract the final marker set.
4. Quit through QMP, verify cleanup, classify the boundary, and open a source
   change ticket only if the evidence identifies a controllable source seam.

### Do

1. Reused the fixed receiver, existing build/TMPDIR, authoritative qemuboot,
   and one short QMP alias. The first two observation attempts exposed a
   harness alias-lifecycle error; both were recovered with QMP `quit`. The
   third attempt kept the alias alive until teardown and completed the
   observation.
2. Launched one production case with one `flutter-auto` process. The target
   exposed `ps`, `/proc`, GDB, `strace`, and `timeout`.
3. Captured bounded early/late process state, a non-destructive GDB thread
   snapshot, and a five-second allowlisted syscall trace. The GDB snapshot
   covered 38 threads; the syscall trace attached and detached all 38 cleanly.
4. Waited past the fourth pipeline input and captured the late marker set and
   QMP frame. Pipeline creates 1 through 6 all returned `result=0`; create 4
   took `21368217` microseconds.

### Check

- The fourth create eventually completed, so the permanent pipeline-stall
  hypothesis is rejected. The observed state is consistent with long
  software Vulkan/llvmpipe compilation and futex/epoll waits.
- GDB showed the main thread in `clock_nanosleep` and the engine/llvmpipe
  threads in Vulkan condition/futex wait paths; no crash or signal was seen.
  The syscall tail contained repeated `futex`/`epoll_wait` and no repeated
  ioctl boundary.
- The late QMP frame remained HUD-only: production native candidate region
  `0/223200`, HUD `1264/100000`, with bounding box `[200,113,29,66]`.
- QMP teardown and residual checks passed. No QEMU, `runqemu`,
  `flutter-auto`, `bitbake`, or QMP socket remained under the active run.
- Full raw paths and hashes are recorded in the evidence manifest linked above.

### Act

Keep the current image and pipeline patches unchanged. Split the next
evidence unit into FLR-0097 and inspect the first post-pipeline boundary:
resource/renderable readiness, frame/draw execution, and native-surface
handoff. Do not patch synchronization, present, Wayland, or alpha until that
boundary has a first-missing-marker result.

## Visual evidence

The QMP-only before, early, and late frames are listed with SHA-256 in
`work/evidence/FLR-0096-production-runtime-snapshot-2026-09-12.md`. They show
the same HUD activity and no accepted production native 3D pixels.
