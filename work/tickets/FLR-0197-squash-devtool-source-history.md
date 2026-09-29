# FLR-0197 — make complete Devtool patch baseline deterministic

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Mini patch/compile roles
- Created: 2026-09-15
- Predecessor: [FLR-0196](FLR-0196-fix-readback-callback-api.md)
- Working log: `work/logs/2026-09-15-flr0193.md`

## Work unit

Ensure the canonical 0259 patch is one complete baseline-to-final Devtool
patch. Do not register only an incremental patch whose parent commit is absent
from the recipe patch stack.

## Facts

- The first callback correction created a source commit whose parent was the
  earlier readback commit. Devtool emitted `0001` and `0002`; the helper
  selected only `0002` by matching the final source SHA.
- Mini do_patch then failed at 0259 with `Hunk #1 FAILED at 870`.
- The source history was squashed from the fixed baseline to the final source
  content as one commit, and Devtool emitted one `0001` patch.
- The final generated patch SHA256 is
  `880f7979eaa8325d1e928911d6259f7fc4fa7b2ec646d51002470341f8160ec7`.
- Mini do_patch and `flutter-auto:do_compile` passed at receiver revision
  `2dfaee6ae21a...`.

## Success criteria

- [x] Source history is one baseline-to-final commit in the persistent Devtool
  workspace.
- [x] Official Devtool output is one complete patch and is byte-identical to
  canonical 0259.
- [x] Canonical whitespace/contract tests, Mini do_patch, and do_compile pass.
- [x] Return ownership to FLR-0194 without starting QEMU from this ticket.

## Plan / Do / Check / Act

### Plan

Squash the committed source changes in the Devtool workspace, regenerate 0259
through the official helper, and rerun only the Mini patch and compile gates.

### Do

The incremental-patch failure was reproduced and recorded before changing the
source history. No manual patch-body edit was used.

### Check

All success criteria passed. The fixed QEMU/image run remains owned by
FLR-0194.

### Act

Mark this history-boundary ticket Done and continue FLR-0194 with the full
image build and one QMP/readback experiment.
