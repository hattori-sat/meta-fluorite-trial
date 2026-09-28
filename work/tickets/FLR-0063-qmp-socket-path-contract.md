# FLR-0063 — QMP Unix socket path length contract

- Status: Inbox
- Priority: Medium
- Owner: QEMU/runtime harness role
- Created: 2026-09-10
- Depends on: [FLR-0055](FLR-0055-tps-bounded-qemu-harness.md)
- Working log: `work/logs/2026-09-10-flr0062.md`

## Problem

The QEMU harness accepted a run directory whose QMP Unix socket path was too
long for the host Unix-domain socket limit. QEMU/runqemu started, but the
harness timed out while connecting to QMP; negotiated quit was also impossible
through that path. The exact process had to be stopped by verified PID and the
socket cleaned up manually.

## Success criteria

- [ ] Preflight fails before QEMU start when the QMP socket path is outside the
  supported Unix-domain socket length.
- [ ] The failure reports one actionable reason and does not leave QEMU,
  runqemu, ports, or a socket behind.
- [ ] A short role-based run directory remains accepted by the existing
  runqemu/QMP profile.
- [ ] Static tests cover the boundary and the live harness check is recorded.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0062's first start attempt used a long evidence child and timed out at
  QMP greeting even though runqemu and qemu-system were alive.
- Reusing a short evidence child made the same artifact, ports, and profile
  pass preflight and QMP greeting.

### Hypotheses

- H1: a preflight byte-length check on the Unix socket path will prevent this
  false runtime-start failure.
- H2: only the path length is at fault; the runqemu profile and artifact are
  valid because the short-path retry passed.

### UNKNOWN

- Whether every supported host/filesystem uses the same effective Unix socket
  path limit.

## PDCA

- **Plan:** determine the portable limit from the harness/runtime contract,
  add a fail-fast preflight check, and test both reject and accept cases.
- **Do:** pending; do not mix the harness fix into FLR-0062's Filament target
  diagnosis.
- **Check:** pending live harness validation.
- **Act:** keep the fixed evidence-root role path and short child naming until
  this ticket is complete.
