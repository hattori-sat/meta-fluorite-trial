# FLR-0210 — repair Podman tmpfs work ownership after restart

- Status: Inbox
- Priority: Medium
- Owner: Podman Devtool harness
- Created: 2026-09-20
- Discovered during: [FLR-0209](FLR-0209-visible-shm-cube-fallback.md)

## Problem

After the persistent `fluorite-mac-devtool` container was reused, the fixed
`/workspace/tmp/work` directory was root-owned. The wrapper's non-root preflight
did not repair it because the owner marker already matched the Devtool UID.
BitBake then failed before `do_patch` with `PermissionError` while creating the
machine work directory.

## Countermeasure

The wrapper now always repairs ownership of the single disposable
`/workspace/tmp/work` root after creating it. It does not scan or delete the
persistent source, downloads, sstate, build, or TMPDIR contents.

## Verification

- [ ] Re-run the bounded Mac `flutter-auto:do_patch` gate.
- [ ] Reuse the same container after a restart and repeat the gate.
- [ ] Record the result in the working log and close this ticket only after
  the repeated gate passes.

## UNKNOWN

- Whether any task-created descendants can become root-owned later; this ticket
  intentionally starts with the observed fixed-root ownership failure.
