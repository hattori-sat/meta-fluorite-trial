# FLR-0388 Sequoia LIT Runtime Verification Plan

> **Objective:** Verify the known patch-0332 LIT material on production Sequoia in the exact built image, and determine whether the already-known SUN changes a healthy negative result.

**Ticket:** `work/tickets/FLR-0388-test-sequoia-lit-on-exact-image.md`
**Working log:** `work/logs/2026-10-01-flr0388.md`
**Branch:** `feature-flr-0388-direct-sequoia-lit-runtime` (local, no push)

## Constraints

- Follow the saved FLR-0385/0387 Mini runqemu command and fixed build/evidence roots; do not guess paths.
- One run directory, one 6144-MiB QEMU, ports 10930–10932. No additional TMPDIR, VM, container, image copy, source edit, build, transfer, or cache deletion.
- Verify the exact rootfs/kernel/qemuboot and helper hashes before startup; the Mini receiver's current HEAD is not candidate-image identity.
- Launch Example Demo as UID 1001 with Sequoia selector + LIT override. Profile A leaves production light unchanged. Profile B is conditional and changes only the existing SUN opt-in.
- Persist child/timeout exit status. PENDING is a non-failure poll state and must continue through the bounded 45-second window. Precheck each serial command for POSIX shell syntax and `<=4096` bytes.
- QMP is the only screen source. Capture the full frame and eight-frame video; bracket captures with exact app PID/UID/start-token checks. Keep raw PPM/log on Mini; preserve reviewed PNG/MP4 with this evidence unit.

## Task 1 — pin the run target

- [ ] Run canonical guard and FLR-0388 checkpoint; verify no other active ticket.
- [ ] Read the recorded successful FLR-0385 runqemu command, image paths, helper hashes, and FLR-0387 postflight.
- [ ] On Mini, verify candidate artifact hashes, exact helper hashes, zero QEMU/runqemu/Flutter/BitBake processes, free ports, and one existing evidence directory absent before creation.
- [ ] Start exactly one 6144-MiB QEMU through the official harness and prove guest identity/session/compositor/bundle.

## Task 2 — Profile A: known Sequoia LIT, production light unchanged

- [ ] Stage the checked guest preflight, launch, readiness, summary, live-gate, and stop command files; verify `sh -n` and size before SCP.
- [ ] Launch once with `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`, `FLR0026_NATIVE_MODEL_MATCH=sequoia`, and `FLR0026_NATIVE_MODEL_LIMIT=2`; unset production SUN and unrelated fixture/color overrides.
- [ ] Preserve exact PID/UID/start token, wrapper identity, and timeout/child status file.
- [ ] Run up to three 15-second readiness polls. Continue on PENDING; stop on hard fault, failed present, app exit, identity change, or persistent unmatched present.
- [ ] Capture full QMP still and eight-frame video; verify health and the same app identity immediately before/after capture. Measure full frame, Sequoia ROIs and HUD ROI; visually inspect the complete image.

## Task 3 — conditional Profile B and teardown

- [ ] Only when A is healthy, HUD-visible, and Sequoia-chroma-negative, stop A cleanly and launch one B profile changing only `FLR0305_PRODUCTION_SCENE_LIGHT=1`.
- [ ] Apply the same readiness, present-health, PID-bracket, QMP, ROI, and child-exit gates to B.
- [ ] On any fault, capture failure-only QMP still/video before shutdown when possible; do not call it a live-render result or run B after unhealthy A.
- [ ] Negotiate QMP quit, run independent postflight, and prove zero residual targets/socket, free ports, and unchanged candidate hashes.

## Task 4 — record and verify

- [ ] Update this plan, ticket, TASKS dashboard, and working log with facts/inferences/hypotheses/UNKNOWN, command outcomes, hashes, full-frame evidence, ROI counts, and the next ticket decision.
- [ ] Run repository privacy, shell/4096-byte, checkpoint, whitespace, link, and evidence-file checks; inspect the final diff.
- [ ] Commit the ticket-scoped runtime/evidence record locally; do not push.
