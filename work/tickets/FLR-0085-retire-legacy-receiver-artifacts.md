# FLR-0085 — retire legacy receiver artifacts

- Status: Done
- Priority: Medium
- Owner: build-handoff maintenance role
- Created: 2026-09-11
- Working log: `work/logs/2026-09-11-flr0085.md`

## Work unit

Stop using the legacy `FLR0026` receiver artifact namespace. Retire only the
old Mini PC evidence directories and inbox bundles from active paths. Preserve
the repository's historical ticket, log, evidence, and patch contents so old
runtime conclusions remain reproducible.

## Success criteria

- No `FLR0026`-named directory or bundle remains under the active Mini PC
  receiver evidence/inbox roots.
- The fixed receiver remains
  `/mnt/yocto/flourite-receivers/flr0023-835a04e` and the fixed inbox remains
  `/mnt/yocto/flourite-receivers/inbox`.
- The retired artifacts are recoverable under a neutral archive path and their
  contents are unchanged.
- `TASKS.md`, the environment contract, and this ticket state clearly that
  `FLR0026` is history-only and must not be reused.

## Facts

- The current handoff helper targets the fixed `meta-fluorite-trial-active.bundle`
  inbox entry and the `flr0023-835a04e` receiver; it does not target the old
  namespace.
- The Mini PC had two old evidence directories and ten old inbox bundles named
  with the legacy namespace. They were created by prior failed or superseded
  handoff iterations, not by the current FLR-0084 run.
- The old artifacts occupied approximately 11.4 MiB of evidence directories
  and 12.4 MiB of bundles. No receiver-root reference to those names was found
  outside the artifacts themselves.

## Inferences

- The namespace persisted because each earlier handoff created another
  per-attempt bundle/evidence name without a retention rule; it was not needed
  by the current build flow.
- Moving the old artifacts, rather than deleting them, removes active-path
  ambiguity without destroying the historical evidence.

## Hypotheses

- UNKNOWN before the move: another active process might still have depended on
  one of the old paths. The current fixed receiver/inbox inspection found no
  such reference.

## UNKNOWN

- Historical copies on other hosts are outside this one Mini PC receiver and
  are not part of this retirement unit.

## Plan / Do / Check / Act

### Plan

Inventory exact old paths and hashes, verify the current receiver/inbox, then
perform a reversible move into a neutral archive and verify the old active
paths are gone.

### Do

Moved the two old evidence directories and ten old bundles from the active
receiver roots to:

`/mnt/yocto/flourite-receivers/archive/legacy-runtime-2026-09-05/`

with separate `evidence/` and `bundles/` subdirectories and neutral `run-*`
names.

### Check

- The move completed without touching the fixed receiver or current inbox.
- A post-move inventory showed no old namespace directory or bundle under the
  active `evidence/` and `inbox/` roots.
- The old repository files still present inside the fixed receiver are tracked
  historical work records, not active handoff directories; they remain
  unchanged for provenance.

### Act

All new handoffs use the fixed receiver/inbox and current ticket name. Any
future legacy cleanup must be a separate ticket and must preserve a reversible
archive or an explicit operator-approved deletion.

### Final runtime cleanup

The QEMU instance used for the contemporaneous FLR-0084 verification was
stopped through QMP. The follow-up check found no QEMU/`runqemu` process and no
QMP socket under the active evidence root. This confirms that retiring the old
receiver namespace did not leave a runtime process holding an old path.
