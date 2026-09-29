# FLR-0082 — bound Podman status on the reused workspace

- Status: Done
- Priority: High
- Owner: Mac Podman/Devtool environment role
- Created: 2026-09-11
- Depends on: [FLR-0053](FLR-0053-podman-devtool-runtime.md), [FLR-0054](FLR-0054-podman-bundle-handoff-simplification.md)

## Work unit

Keep the single operator-managed rootful Podman machine, one persistent
container, and one canonical project/state bind. Make `status` a bounded
readiness probe instead of re-scanning the persistent downloads tree and
rewriting BitBake configuration before every check.

## Success criteria

- Do not create a machine, named volume, container, state root, or per-ticket
  TMPDIR.
- Keep `/workspace/project` read-write, `/workspace/agl` read-only, and the
  fixed `/workspace/state` bind unchanged.
- Keep ownership repair for real Devtool operations, but defer it for the
  observational `status` operation.
- Run the same `status` twice and prove both calls pass with the same
  container/bind contract.
- Record the change and its static test in this ticket.

## Facts / Inferences / Hypotheses / UNKNOWN

### Facts

- The validated `fluorite-devtool` machine was already present and running;
  the existing `fluorite-mac-devtool` container was the only managed container.
- Before this change, `status` entered the ownership-repair path and enumerated
  the persistent downloads tree. A bounded diagnostic showed that path still
  running after 20 seconds; no duplicate provider was created.
- The wrapper now returns
  `status=PASS project=rw agl=ro state-bind=rw
  tmpdir=state-bind-ownership-fifo-xattr=PASS repair=deferred` twice.
- Both calls reused container ID
  `00db1333498686bfd2e732580ae912eb0c21daac30f5781936ef8dc95beeb99a`.
  The verified mounts are project RW, AGL RO, and state RW; `/workspace/tmp`
  remains the single container-private tmpfs.

### Inferences

- The previous apparent Podman startup instability was partly an unbounded
  status/repair scan, not evidence that a second machine or container was
  required.

### Hypotheses

- H1: bounded status is sufficient to detect provider/bind breakage before a
  Devtool operation. Prediction: both repeated calls complete without touching
  the large downloads tree.
- H2: Devtool operations still need ownership repair after status. Prediction:
  recipe-scoped operations retain the existing repair path.

### UNKNOWN

- Whether a long recipe-scoped Devtool operation will complete on this reused
  state without a fresh ownership repair. That is intentionally not hidden by
  this status change.

## Plan / Do / Check / Act

### Plan

Add a status-only fast path after container readiness and stale-process checks.
It runs the same project/AGL/state/tmpfs/FIFO/xattr probes but skips ownership
repair and BitBake configuration writes.

### Do

- Updated `scripts/run-podman-devtool.sh` and its static contract test.
- Did not start, stop, create, remove, or duplicate a Podman machine/container.

### Check

- `bash tests/test-podman-devtool.sh`: PASS.
- Two consecutive wrapper status calls: PASS, same container and bind mounts.

### Act

Keep this contract as the required first step before Mac Devtool editing. If a
real Devtool operation fails, inspect its exact ownership/process error and do
not bypass it by creating another state tree.
