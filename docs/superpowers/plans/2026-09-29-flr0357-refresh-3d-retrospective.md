# FLR-0357 Refresh 3D Visibility Retrospective — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Refresh the evidence-linked Fluorite 3D retrospective with the latest FLR-0356 runtime observation, measured intervention effects, and one evidence-selected next action.

**Architecture:** Keep the retrospective read-only with respect to product/build state. Reuse the bounded FLR-0345/0349 history, add only newer ticket evidence, distinguish fixture success from production Sequoia acceptance, and create a separate Inbox ticket for the serial-buffer framing defect.

**Tech Stack:** Markdown ticket/log/dashboard, existing QMP PNG evidence, Git privacy/checkpoint/link/file-size gates.

**Spec:** User request to create a separate retrospective ticket listing problems, countermeasures, and their effects; existing FLR-0345 and FLR-0349 checklists; FLR-0356 Mini runtime evidence.

## Global Constraints

- Canonical repository guard must pass before edits; no push.
- One task per ticket Markdown; keep one ticket `In Progress`.
- Preserve facts, inferences, hypotheses, decisions, and UNKNOWN as separate categories.
- Do not run QEMU, BitBake, Devtool, builds, or product/source/image mutations in the retrospective.
- Use QMP-only screenshots; never interpret a pre-GO black frame as a renderer result.
- Keep raw frames/video and runtime logs outside Git; link the small review video by its evidence role and attach a single QMP PNG to the ticket.
- FLR-0357 depends on the just-recorded FLR-0356 commit `d740424`; this branch carries that explicit prerequisite because its evidence is the retrospective's newest input.
- Do not retry consumed run IDs.

---

### Task 1: Reconcile bounded historical and current evidence

**Files:**
- Read: `work/tickets/FLR-0345-retrospective-3d-visibility-checklist.md`
- Read: `work/tickets/FLR-0349-audit-3d-countermeasure-effectiveness.md`
- Read: `work/tickets/FLR-0271-trace-readback-child-surface-visibility.md`
- Read: `work/tickets/FLR-0273-isolate-post-activation-render-surface-visibility.md`
- Read: `work/tickets/FLR-0286-reproduce-known-good-combined-sequoia-hud.md`
- Read: `work/tickets/FLR-0348-watch-lavapipe-signal-without-fence-type.md`
- Read: `work/tickets/FLR-0355-relay-run-id-and-retest-fifo-gate.md`
- Read: `work/tickets/FLR-0356-stage-fifo-observer-before-qemu.md`
- Read: `work/logs/2026-09-29-flr0356.md`
- Inspect: `work/evidence/FLR-0356-qmp-pre-go-black.png`

**Output:** A bounded status table for 2D HUD, fixture+HUD, historical Sequoia+HUD, current production Sequoia, image-regression uncertainty, runtime gate, and evidence/cleanup controls. Each row links to its source ticket and states the measured effect and remaining unknown.

- [x] Read the bounded FLR-0345/0349 retrospective tables and the positive/negative tickets listed above.
- [x] Confirm that the new FLR-0356 black QMP image is pre-GO and that its raw FIFO observation is distinct from the rejected host framing.
- [x] Carry forward Photo 1 as static texture-atlas evidence only, not framebuffer proof.

### Task 2: Write the refreshed retrospective ticket and working log

**Files:**
- Create: `work/tickets/FLR-0357-refresh-3d-visibility-retrospective.md`
- Create: `work/logs/2026-09-29-flr0357.md`
- Create: this plan
- Modify: `TASKS.md`

**Output:** A single compact intervention/effect checklist with verified positives, failed controls, diagnostic improvements, current first divergence, ranked next discriminator, and explicit product acceptance criteria.

- [x] Record at least two competing next paths and why repairing serial framing is the smallest next gate before any renderer inference.
- [x] Embed the QMP-only FLR-0356 screenshot and record the eight-frame MP4 review copy location without adding raw frames to Git.
- [x] Keep FLR-0356 Waiting because its official FIFO gate is FAIL; do not mark it Done until the gate evidence is accepted.
- [x] Make FLR-0357 the sole In Progress ticket and put the independent serial-framing follow-up in Inbox as FLR-0358.

### Task 3: Define the independent serial-framing follow-up

**Files:**
- Create: `work/tickets/FLR-0358-clear-serial-buffer-before-command.md`
- Modify: `TASKS.md`

**Output:** A separate one-outcome ticket to prevent the `stty -echo` prompt from contaminating a later serial command's captured output, with a red-capable local test and one fresh Mini runtime ID after local gates.

- [x] Compare an explicit setup-prompt/capture boundary against loosening the marker parser; choose the smallest change that preserves the identity gate and cannot silently discard an unverified handshake.
- [x] State the known `flr0356-0001` observer fields and rejected `marker-not-first` result without claiming an official FIFO-gate pass.
- [x] Require QEMU preflight, one fresh run, QMP still/eight frames, exact cleanup, and no ID reuse.

### Task 4: Verify and commit the retrospective

**Files:**
- Verify: `TASKS.md`, FLR-0357/0358 tickets, FLR-0357 log, this plan

- [x] Run canonical guard, `git diff --check`, staged-whitespace check, privacy check, ticket checkpoint, file-size check, and Markdown link check; record the repository-wide Markdown baseline failure separately.
- [x] Record the nine unrelated pre-existing Markdown-link failures without silently repairing out-of-scope evidence files.
- [x] Commit only the retrospective and its explicit follow-up issue locally; do not push (`6b43802`).

**Acceptance:** The checklist supports the next action without replaying the conversation, reports the current production 3D state without overclaiming, attaches QMP evidence, leaves exactly one active ticket, and preserves the serial-framing fix as a separate future unit.
