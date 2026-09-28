---
name: yocto-runtime-checkpointing
description: Use when Yocto or embedded-Linux investigation spans multiple build/runtime loops, separate Mac and target hosts, QEMU evidence, Devtool patches, or context compression
---

# Yocto Runtime Checkpointing

## Overview

Treat each investigation loop as a recoverable checkpoint, not as chat history. The
working log is the continuity boundary: a later agent must be able to resume from
the ticket, facts, evidence, decision, and next falsifiable action alone.

## Required loop

1. Read `TASKS.md`, the current ticket, and its working log before acting.
2. Keep exactly one `In Progress` ticket. If a new hypothesis, fix, route, or
   independent boundary is outside the current Success criteria, create a new
   Markdown ticket in `Inbox` before starting it.
3. At every meaningful loop boundary, write `Facts`, `Inferences`, `Hypotheses`,
   `UNKNOWN`, `Evidence / command result`, `Decision`, and `Next action`.
4. Record both failed and successful commands with exit status. Preserve the first
   actionable error; do not replace it with a later summary.
5. Link exact image/source/layer/target identity, QMP-only evidence, artifact role
   path, pixel statistics, and SHA-256. Keep bulky artifacts outside Git.
6. Run the project harness before and after a checkpoint:

```sh
scripts/runtime-checkpoint.sh verify \
  --ticket FLR-0050 --log work/logs/2026-09-08-flr0050.md

scripts/runtime-checkpoint.sh new \
  --ticket FLR-0050 --log work/logs/2026-09-08-flr0050.md \
  --iteration 2 --title "short boundary name" \
  --facts "observed result" \
  --inferences "what the result supports" \
  --hypotheses "next falsifiable explanation" \
  --unknowns "what is not proven" \
  --decision "continue, stop, or split" \
  --next "one bounded next action"
```

Use `--dry-run` to inspect the block before appending. The harness refuses a
missing ticket/log, duplicate iteration, non-In-Progress `new`, or multiple active
tickets. It never creates a second container, build directory, TMPDIR, QEMU, or
working log.

## Context-compression handoff

The latest checkpoint must state: current ticket/status, exact boundary reached,
what is proven, what is only inferred, rejected hypotheses, UNKNOWNs, current
image/commit identity, preserved evidence, and the single next action. A new agent
starts by reading that checkpoint and does not infer progress from chat memory.

## Scope and evidence rules

- 2D HUD, CPU/GPU/FPS, a clear color, or a self-made fixture is not production 3D.
- QMP framebuffer pixels are the display claim for QEMU; host-window screenshots are
  not equivalent evidence.
- Static source evidence does not prove runtime behavior; runtime logs do not prove
  visible pixels without QMP evidence.
- A diagnostic switch that changes the result is a boundary probe, not a permanent
  product fix. Split the fix or route validation into a new ticket.
- Use Yocto `devtool` source edits, source commits, and `devtool finish --mode patch`;
  never hand-edit a generated layer patch.

## Fixed provider and handoff contract

- Mount the canonical `meta-fluorite-trial` directory directly at
  `/workspace/project:rw`; mount AGL at `/workspace/agl:ro`; reuse the same
  container and four state mounts. Before Devtool runs, require a
  `mount-permission=PASS` check for project, AGL, and state paths.
- Keep Podman fail-closed when its machine/socket is absent. Do not auto-create a
  machine, source copy, volume, build directory, TMPDIR, or QEMU to recover.
- After a local feature commit, use `scripts/handoff-fluorite-bundle.sh <base>
  <tip>` with local role variables `BUILD_HOST`, `BUILD_BUNDLE_INBOX`,
  `BUILD_RECEIVER`, `BUILD_DIR`, and `BUILD_TMPDIR`. It creates one stable
  external bundle, verifies local/remote hash, and updates the fixed receiver to
  the exact tip. The fixed receiver may be a normal checkout or a Git linked
  worktree; validate it through Git (`rev-parse --is-inside-work-tree`), never
  by assuming `.git` is a directory. Cherry-pick is reserved for later PR
  integration.
- After handoff, use `scripts/run-mini-recipe-patch-gate.sh <ticket> <recipe>`
  for the authoritative patch boundary. It checks the fixed receiver/build/
  TMPDIR contract, rejects an active BitBake duplicate, stores only a filtered
  `bitbake -e` summary, runs one forced `do_patch`, and returns the first
  bounded patch/error boundary plus the exact task log on failure. Do not
  paste or scan the complete BitBake output when this gate is sufficient.
- For the QEMU loop, use `scripts/qemu-runtime-harness.sh` with the official
  `runqemu` profile. `preflight` checks one-instance state, exact QMP socket
  location, ports, qemuboot/image identity, and artifact hashes; `serial-login`
  waits for the exact guest prompt; `summary` selects only bounded markers and
  first actionable errors; `qmp-quit` negotiates `qmp_capabilities` before
  teardown and verifies that no target process or socket remains. Do not use a
  second launch wrapper, per-run build/TMPDIR, broad process kill, or raw-log
  dump as a substitute.

## TPS / 4S evidence discipline

- 整理: keep raw QMP/serial/video/core artifacts outside Git; record only the
  selected result, role path, and hash in the ticket.
- 整頓: reuse one canonical source, container, build, TMPDIR, cache, and
  evidence root; vary only the run-owned QMP socket and run metadata.
- 清掃: run preflight and negotiated teardown checks on every attempt; preserve
  the first actionable failure and cleanup result.
- 清潔: make Facts, Inferences, Hypotheses, UNKNOWN, and the next gate
  machine-checkable through the checkpoint script.
- 自働化: when the same manual error appears twice, add a failing static
  contract test before changing the runtime or image.

## Red flags

Stop and checkpoint when you hear yourself saying:

- “次でまとめて記録する”
- “同じticketの続きだから追記でよい”
- “ログは成功したものだけでよい”
- “2Dが見えたので3Dも通った”
- “新しいcontainer/TMPDIRを作れば早い”

These are continuity or evidence failures, not harmless shortcuts.
