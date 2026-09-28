# FLR-0052 — Canonical repository reproducibility gate

- Status: Done
- Priority: High
- Owner: repository + runtime diagnosis + build-host roles
- Created: 2026-09-09
- Depends on: FLR-0050, FLR-0051
- Working log: `work/logs/2026-09-09-flr0052.md`
- Resumed after: FLR-0053 static Podman contract committed; runtime remains Waiting until a machine is available.
- Resumed after: FLR-0054 fixed active bundle handoff completed; receiver tip ad8e1cd passed the progressive BitBake gates.

## Work unit

Make `meta-fluorite-trial` the only reproducible source of truth for the
Fluorite investigation inputs: branch/revision, layer recipes and patches,
tickets, working logs, evidence indexes, Devtool handoff instructions, and the
bundle consumed by the authoritative Mini PC build.

## Problem

The active Mac source was once treated as a separate temporary Git repository,
while the canonical clone held a stale linked-worktree registration. Historical
tickets also retained `In Progress` status after their boundaries had moved to
new tickets. Raw QEMU/build artifacts were mixed with repository-managed
records, so a clean bundle gate could not identify the exact input.

## Facts / inferences / hypotheses

### Facts

- The canonical feature branch has the project origin, the `feature-flr-0023-3d-qemu-validation` branch, and revision `ad8e1cd`.
- The active source now resolves to that canonical branch and passes the repository guard.
- The duplicate standalone Git metadata was removed after verification; source and runtime evidence files were not removed.
- The checkpoint harness initially found three stale `In Progress` ticket headers; their boundaries are now separated as Waiting/Done plus this ticket.

### Inferences

- The previous authority failure was a repository-layout failure, not evidence that the Flutter or Filament runtime changed.
- A reproducible repository should version concise instructions, ticket/log/index records, and layer patches, while keeping raw captures, bundles, and Devtool scratch outside Git.

### Hypotheses

1. If status and artifact boundaries are corrected, the checkpoint and privacy gates will pass and the bundle script will see only intentional source changes.
2. If a clean receiver is materialized from the resulting layer commit, its BitBake inputs will match the Mac-recorded revision without copying the Mac worktree.
3. If the clean receiver still diverges, the remaining cause is build-host provenance or missing manifest/config input, not the Mac worktree layout.

## Success criteria

- [x] Exactly one ticket is `In Progress`, and `runtime-checkpoint.sh verify` passes.
- [x] Canonical guard, privacy, shell/Markdown checks, and `git diff --check` pass on the feature worktree.
- [x] `.gitignore` keeps raw QMP/build/Devtool payloads out of commits while preserving the ticket/log/index contract.
- [x] The layer change and the reproducibility tooling are committed locally on the feature branch with role-only metadata.
- [x] A clean Git bundle can be created from the committed layer revision and verified without changing the canonical checkout.
- [x] The Mini PC receiver checked out the exact bundle tip and completed `do_patch`, `do_compile`, and full `agl-ivi-image-flutter`; failures were recorded as checkpoints.

## Verification plan

1. Run the checkpoint contract and repository guard from the canonical feature worktree.
2. Run privacy, shell, Markdown-link, and file-size checks; redact or exclude only generated artifacts identified by the checker.
3. Inspect the staged diff for source/layer/ticket/log/index scope and ensure no personal path, host, address, credential, raw capture, bundle, or Devtool scratch is staged.
4. Commit the reproducibility gate locally, then run the official bundle creation and verification scripts if available.
5. Transfer only the verified bundle to the fixed Mini PC receiver and run `bitbake -e` before any long build.

## UNKNOWN

- The clean Mini PC receiver path, exact build-host checkout identity, and progressive BitBake results are proven through the fixed receiver handoff and image build.
- The existing Mac Devtool source may still contain uncommitted diagnostic edits; they must be represented by an official `devtool finish --mode patch` layer change before being included in a runtime build.
- Repository records do not by themselves prove QMP pixels; FLR-0050 remains the runtime acceptance gate after this repository gate.

## Decision

This repository/build gate is complete. FLR-0050 is now the only active ticket
for the runtime parent-alpha/frame-loop investigation; it must not alter the
authoritative image input without a new Devtool patch and bundle checkpoint.
