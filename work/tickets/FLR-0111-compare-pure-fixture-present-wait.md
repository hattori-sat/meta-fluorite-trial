# FLR-0111 — compare pure fixture present wait with production

- Status: Waiting
- Priority: High
- Owner: runtime-debug + Filament/Vulkan + target-validation roles
- Created: 2026-09-12
- Updated: 2026-09-12
- Depends on: [FLR-0109](FLR-0109-present-wsi-blocked-owner.md), [FLR-0110](FLR-0110-bound-gdb-memory-observation.md)
- Working log: `work/logs/2026-09-12-flr0111.md`

## Work unit

Run the existing self-made pure native fixture on the same fixed debug image
and QEMU profile used by FLR-0109. Compare its native QMP pixels, queue-present
return, marker order, and bounded Mesa stack with the production result. This
is a control comparison; it does not change source or scene semantics.

## Success criteria

- Reuse the fixed receiver, build/TMPDIR, rootfs/kernel/qemuboot identity, and
  one-QEMU QMP-first contract.
- Launch exactly one `flutter-auto` with
  `FLUORITE_NATIVE_PURE_FIXTURE=1` and
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`.
- Capture QMP-only evidence showing whether the self-made native 3D region is
  nonzero and retain the HUD region separately.
- Retain queue-present enter/return/done markers and a bounded low-memory GDB
  snapshot of the fixture's relevant FEngine/llvmpipe threads.
- Clean QMP quit and residual checks must pass.
- Return a comparison to FLR-0109; do not declare production 3D fixed from a
  fixture-only PASS.

## Plan / Do / Check / Act

### Plan

1. Run the pure fixture with the production marker set and capture normal QMP.
2. Wait for the fixture present marker, collect a low-memory GDB stack, and
   verify queue-present return/done markers.
3. Compare against FLR-0109 r12 and classify the Mesa wait as common or
   production-specific.

### Do

- Ticket created as a separate fixture-control unit after FLR-0109 r12
  identified a lavapipe synchronization wait candidate.
- No source or image change is included.
- First control run completed with one fixture process, QMP-only native/HUD
  evidence, repeated queue-present return/done markers, and a low-memory GDB
  snapshot. The evidence is in
  `work/evidence/FLR-0111-pure-fixture-present-2026-09-12.md`.
- A second same-image run was started to deepen the selected-thread stack
  comparison. It reached guest-ready and repeated fixture present returns,
  but its final deep-GDB/QMP collection is pending.

### Check

- First run: QMP native candidate `41,750/223,200`, HUD `6,148/100,000`,
  repeated `QUEUE_PRESENT_RETURN result=0`/`PRESENT_DONE`, low-memory GDB RC=0,
  and clean QMP teardown all passed.
- The first bounded fixture GDB snapshot placed FEngine threads in Wayland
  `poll` or glibc futex/condition waits; no `libvulkan_lvp.so` frame appeared
  in the requested top four frames. This is weaker than a full deep-stack
  exclusion because auto symbol loading was intentionally disabled.
- Compared with FLR-0109 r12, the fixture does not reproduce the production
  native-black/no-present-return symptom. This is a control classification,
  not a production fix.
- The second run's final deep-GDB/QMP/teardown check is pending after the
  remote execution approval service rejected the collection call at its usage
  limit. No workaround or source change was made.

### Act

- Use the existing pure fixture flags only; do not add a new TMPDIR, QEMU, or
  source patch.
- Keep the fixture evidence separate from the production verdict and hand the
  comparison back to FLR-0109.
- When remote execution is available, finish only the already-started second
  run: capture its QMP baseline, collect selected FEngine/llvmpipe stacks with
  `auto-solib-add off`, capture post-GDB QMP, then issue QMP quit and record
  residuals. Do not start a third QEMU for this ticket.

## UNKNOWN

- Whether the pure fixture reaches the same `lvp_pipe_sync_*` frames.
- Whether the fixture returns from queue present while production remains in
  the same Mesa condition wait.
- Whether the second run's deeper selected-thread stacks will expose any
  in-process `libvulkan_lvp.so` frame.
