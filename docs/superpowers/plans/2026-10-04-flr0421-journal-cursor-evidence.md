# [Feature] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Safely classify a verified no-new-entry journal result, preserve bounded redacted evidence, and use one new-ID capture to reach the first live post-release QMP frame on unchanged FLR-0410-0001 if the cursor gate passes.

**Architecture:** Keep the existing snapshot-helper/controller boundary. Replace post-hoc subprocess size checks with one small dual-pipe streaming collector for journalctl queries and anchor probes. Retain hashes, counters, cursor equality, classifications, and anchor outcomes only. Do not emit raw cursor or journal lines. Accept the empty marker only when the saved anchor is verified before and after and the optional single returned cursor exactly equals it. Keep all other failures fail-closed. Update the active fixed run identity to flr0421-0001 across its helper stack and tests; old committed revisions preserve FLR-0418 reproducibility.

**Tech Stack:** Python 3 on guest and Mac, selectors/subprocess, SHA-256, unittest, existing Mini runqemu/QEMU/QMP flow. No product build or image change.

**Spec:** work/tickets/FLR-0421-preserve-journal-cursor-evidence.md

## Global Constraints

- Follow AGENTS.md, canonical guard, ticket/checkpoint rules, privacy check, and the official fixed-path Git-bundle workflow.
- FLR-0418-0001 is consumed. Use only the new immutable ID flr0421-0001; no automatic retry, second QEMU, or parallel BitBake.
- Do not modify product source, recipe, patch, image, cache, rootfs, or unrelated runtime helpers.
- Collector limits apply before retaining output: fixed-size concurrent stdout/stderr reads, total byte cap, line-state cap, and timeout. Oversize, truncation, timeout, or parser-state overflow must terminate/reap and fail closed.
- No raw journal text or cursor is emitted to serial/host evidence. The cursor is necessarily passed to journalctl as a temporary process argument; do not persist that argument in logs.
- Use the exact unchanged FLR-0410-0001 rootfs. No BitBake build is required. Fresh ownership/resource/image/run-ID preflight is mandatory before one QEMU attempt.
- Capture QMP only from the running owned guest; product rendering remains UNKNOWN unless actual post-release pixels prove it.
- Local commits are allowed; never push.

---

## Task 1 — Establish red tests for the cursor boundary

- [x] Add a failing case where exact empty marker plus one returned cursor equal to the anchor is accepted only after both anchor checks; the pre-fix parser rejected it.
- [x] Retain negative cases for a changed cursor, failed/rotated anchor, missing cursor where required, duplicate/malformed cursor, extra output, nonzero return, and stderr.
- [x] Add evidence leak assertions: raw cursor and journal-line strings never appear in marker output or returned snapshot JSON.

**Gate:** Run the focused snapshot tests and record the expected red failure before implementation.

## Task 2 — Implement the bounded journal collector

- [x] Implement a small collector using Popen and selectors. Drain stdout and stderr concurrently in fixed chunks; hash/count bytes without retaining full streams.
- [x] Keep only bounded per-line parser state. Count fault categories and retain hash/byte summaries for at most the configured number of matches; never store raw line text in snapshot evidence.
- [x] Enforce total byte and line-size limits before buffer growth. On limit or timeout, terminate, kill if needed, reap, record partial/incomplete fields, and fail closed.
- [x] Record process return code, stdout/stderr byte counts and hashes, completion/truncation state, empty-marker count, cursor count/hash/equality, and before/after anchor-probe result fields.
- [x] Record the journalctl/systemd version in redacted diagnostics; the exact image/rootfs identity remains in the host run manifest and is not inferred from version alone.
- [x] Accept NO_NEW_ENTRIES only for the exact empty marker with zero returned cursors, or exact empty marker plus one valid cursor byte-for-byte equal to the saved anchor. Require query rc=0, empty stderr, complete nonoversized output, and successful exact anchor checks before and after.
- [x] Keep any changed/ambiguous output fail-closed. Preserve the original anchor when the result is NO_NEW_ENTRIES.

**Gate:** Focused parser, collector, process-reaping, timeout, oversize, dual-pipe, and no-leak tests pass.

## Task 3 — Bind one fresh run identity

- [x] Change active helper/test literals from flr0418-0001 to flr0421-0001 in the live controller, snapshot, GDB observer/callback, QEMU-start, media exporter, GDB command files, and directly associated tests only.
- [x] Confirm the active helper/test set contains no consumed 0418 ID and uses the fresh identity, including the QMP socket and artifact paths.
- [x] Run focused affected tests and the full Python/MCP/shell/privacy/file-size/QEMU-harness gates; record the repository's pre-existing Markdown-link failures separately and verify that this ticket's links are clean.

**Gate:** Source/tests show one consistent fresh run ID; no product/build files changed.

## Task 4 — Commit, bundle, and one Mini attempt

- [ ] Review exact diff, stage exact task files, run whitespace/privacy/checkpoint/Markdown gates, and commit locally with the repository role identity. Do not push.
- [ ] Use scripts/handoff-fluorite-bundle.sh with the fixed role configuration; verify exact Mini receiver tip and effective TOPDIR/TMPDIR. No manual receiver reset or separate temporary checkout.
- [ ] Freshly verify no active owner/QEMU/build, unchanged rootfs/qemuboot identity, free immutable ID/socket/ports, and adequate memory/disk.
- [ ] Perform one flr0421-0001 run. Continue only if the cursor rule passes. Save full-screen QMP stills and available frame sequence after renderer release, plus redacted snapshot, present, GDB, kernel, and process evidence.
- [ ] On first failure, capture it, fail closed, stop/teardown exact owned QEMU, run postflight, and do not retry.

**Gate:** One attempt only; exact teardown and user-visible full-screen evidence (if a post-release frame exists) are verified.

## Task 5 — Close the bounded unit without closing the 3D goal

- [ ] Update TASKS, ticket, working log, and evidence with facts/inferences/hypotheses/UNKNOWN, command results, hashes, image identity, complete QMP evidence, and exact teardown.
- [ ] Run runtime-checkpoint, privacy, whitespace, file-size, link, focused test, and relevant repository gates after the final log update.
- [ ] Mark this ticket Done only for its bounded parser/one-attempt/teardown scope. Keep the overarching real Sequoia + HUD + interaction + five-minute + two-boot goal open unless every global criterion is independently evidenced.
