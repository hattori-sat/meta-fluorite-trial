# FLR-0212 — preflight QMP socket path length

- Status: Inbox
- Priority: Medium
- Owner: QEMU evidence harness role
- Created: 2026-09-20
- Discovered during: [FLR-0211](FLR-0211-reconcile-shm-geometry-and-native-wsi.md)

## Goal

Make the QEMU harness reject an overlong Unix QMP socket path during
preflight, before starting `runqemu`, and provide one deterministic short-path
layout for evidence runs.

## Facts

- The first FLR-0211 corrected-image start attempted a socket under the full
  ticket/run directory and QEMU rejected it because the Unix socket path was
  too long.
- The harness reported the failure only after invoking `runqemu`, although no
  guest process remained.
- The same image and ports passed when the QMP socket was placed under the
  shorter fixed evidence path `.../evidence/FLR-0211/q/qmp.sock`.

## Success criteria

- Preflight checks the platform socket-path limit and fails with an actionable
  message before `runqemu` starts.
- Existing evidence paths remain reusable; no ticket-specific TMPDIR, volume,
  or second QEMU is introduced.
- Harness tests cover a passing short path and a rejected long path.

## Plan / Do / Check / Act

### Plan

1. Confirm the portable limit used by the target Unix socket implementation.
2. Add a bounded preflight check and tests without changing the QMP capture
   protocol.

### Do

Pending.

### Check

Pending.

### Act

Pending.
