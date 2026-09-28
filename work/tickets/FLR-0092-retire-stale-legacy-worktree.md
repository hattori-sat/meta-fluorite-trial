# FLR-0092 — retire stale legacy FLR0026 worktree registration

- Status: Done
- Priority: Medium
- Owner: repository/workspace hygiene
- Created: 2026-09-12
- Working log: `work/logs/2026-09-12-flr0092.md`

## Work unit

Stop using the old FLR0026-named local worktree and remove only the stale Git
worktree registrations that point at already-deleted temporary directories.
Keep the historical FLR-0026 ticket, logs, evidence notes, and source patches
read-only for provenance.

The follow-on operating rule is stricter: no new worktree, build/TMPDIR,
receiver, QEMU evidence directory, marker, or environment variable may use the
`FLR0026` name. Existing historical strings may be read when comparing old
results, but they are not an active namespace.

## Success criteria

- No active local worktree is registered under the FLR0026 namespace.
- The canonical `meta-fluorite-trial` repository and the fixed Mini PC
  receiver/build/TMPDIR are unchanged.
- Historical FLR-0026 records remain available and are explicitly classified
  as read-only provenance.
- The cleanup reason, command result, and remaining branch policy are recorded.

## Facts

- The canonical repository had no `work/evidence/flr0026/` directory.
- The Mini PC had no FLR0026-named directory under the checked active roots;
  the fixed receiver, build, and TMPDIR use the `flr0023-835a04e` identity.
- A separate legacy `tcna-packages` clone had four prunable worktree
  registrations, including the old FLR0026 baseline and three temporary
  Devtool-check worktrees. Their gitdir files pointed to paths that no longer
  existed.
- The legacy branches were not deleted because they are historical source
  references, not active work directories.

## Inferences

- The persistent confusion came from stale Git worktree metadata and the old
  ticket-number namespace, not from the current Yocto receiver or build.
- Removing the prunable registrations is sufficient to stop accidental reuse;
  rewriting historical FLR-0026 logs or patch markers would damage provenance.

## Hypotheses

1. A live old worktree was still being used. Rejected: all four entries were
   prunable and their target directories were absent.
2. The current Mini PC receiver was still FLR0026-scoped. Rejected: the active
   receiver/build/TMPDIR are the fixed neutral-role paths.
3. Stale worktree registrations were the remaining local source of confusion.
   Supported by the dry-run and post-prune worktree listings.

## UNKNOWN

- Whether an external shell or editor still has a manually typed old path; the
  repository no longer registers or creates such a worktree.

## Plan / Do / Check / Act

### Plan

Inspect canonical and Mini paths, inspect the legacy clone's worktree list,
preview the exact prune targets, then remove only prunable registrations.

### Do

Ran `git worktree prune -v` in the legacy `tcna-packages` clone after the
dry-run showed four missing-target registrations.

### Check

The post-prune worktree list contains only the parent `tcna-packages` clone.
The canonical repository remains on its existing feature branch with no
unrelated changes, and the Mini active paths remain unchanged.

A current recheck on 2026-09-12 found no `FLR0026`-named active directory in
the canonical repository, Mac temporary roots, or the checked Mini receiver
roots. The current FLR-0101 evidence is under its neutral ticket directory;
the last scene-render run left no QEMU process or QMP socket.

### Act

Use only the canonical `meta-fluorite-trial` worktree for new work. Keep
FLR-0026 records and branches as historical read-only references; use the
current ticket number, neutral `work/evidence/<ticket>/` directories, and the
fixed receiver/build/TMPDIR roles for all new work.

New runtime diagnostics use `FLUORITE_*` names. The old `FLR0026_*` strings
remain only where required to interpret already-deployed historical controls
or preserve prior evidence; they are not copied into new operation paths.
