# FLR-0423 — capture exact caller-frame and map provenance at the GDB hit

- Status: Inbox
- Priority: High
- Created: 2026-10-04
- Owner: Runtime capture harness / guest GDB observer / bounded evidence
- Depends on: [FLR-0421](FLR-0421-preserve-journal-cursor-evidence.md)
- Evidence: [FLR-0421-0001](../evidence/FLR-0421-0001.md)
- Candidate: unchanged [FLR-0410-0001](../evidence/FLR-0410-0001.md)
- Branch: create from `dev-flr-0421-runtime-evidence` only after FLR-0421 is
  integrated through the repository PR workflow; do not cherry-pick or push as
  part of this Inbox ticket.
- Planned fresh run ID: `flr0423-0001` (do not create its evidence directory or
  activate this ticket before the branch prerequisite is met)

## Purpose

The single FLR-0421 run passed the journal/load release boundary and reached the
first temporary hardware breakpoint, but the host correctly refused release
because the GDB callback could not resolve `caller_resume_pc` to one executable
mapping. Capture the exact stopped-frame provenance and a bounded, redacted
same-stop mapping snapshot so the next decision distinguishes a bad unwind from
a resolver/mapping condition. This is a harness-observability ticket, not a
product-render fix.

## Facts

- The target PC and process identities matched at the hardware breakpoint;
  all app threads were stopped and the QMP bracket verified.
- `caller_mapping` was `UNKNOWN`, `errors.caller_mapping` was `ValueError`, and
  release was blocked by `caller_mapping_unknown`.
- The saved run has no exact hit-time maps artifact. The callback records only
  the exception class, so the reason for `ValueError` cannot be reconstructed.
- No post-release QMP capture or production Sequoia/HUD verdict exists.

## Competing hypotheses

1. `gdb.selected_frame().older().pc()` returned an unreliable caller PC because
   the selected frame/unwind provenance was invalid or incomplete.
2. The caller PC was valid but the resolver found no unique executable mapping
   (including a non-executable/out-of-range or interval-boundary address).

Neither is established. Replaying the exact caller PC against the exact hit-time
maps, while retaining a finite failure code and executable-match count, is the
single most informative next check. Do not substitute load-time mappings.

## Scope and guardrails

- At the stopped hit, capture bounded frame provenance and the caller PC, read
  `/proc/PID/maps` once for both resolution and evidence, and retain enough
  normalized range/permission rows on the Mini to replay address matching.
- Strip file paths and unrelated map metadata; cap bytes/lines; store hashes,
  match counts, mapping classification, and allowlisted error codes. Do not put
  raw runtime addresses or map rows in Git, tickets, or host logs.
- Preserve the existing fail-closed release condition. Unknown/missing,
  ambiguous, malformed, or over-limit provenance still must not release GDB.
- Add deterministic tests for valid/no-match/multiple/non-executable/boundary
  mappings, invalid/unavailable older frames, bounded redacted artifacts, and
  no raw-value leakage before any new Mini run.
- Do not change product source, material, lighting, image, or build. Use the
  fixed bundle handoff, unchanged FLR-0410 image, a fresh ID, and one QEMU only
  after the branch prerequisite and immediate preflight pass.

## Success criteria

1. A deterministic host replay classifies the exact captured caller PC against
   the exact same-stop normalized map rows and reports why mapping accepted or
   rejected without exposing paths.
2. The callback reports frame validity/provenance and finite resolver status;
   fault cases remain fail-closed and contain no free-form exception text.
3. Focused tests and privacy/runtime-checkpoint gates pass; local changes are
   committed without push and transferred only with the standard bundle helper.
4. One fresh-ID unchanged-image capture preserves a full-screen hit-stage QMP
   still and the next valid post-release frame only if all existing gates pass.
   If the provenance remains invalid, stop and keep product pixels UNKNOWN.

## Next action

Keep this ticket in Inbox until FLR-0421 has a valid path into the milestone
`dev` branch. Once ready, create its feature branch from that `dev`, write the
execution plan, and begin with a failing unit test for the currently
unexplained caller-map rejection. Never weaken the release gate to obtain a
frame.
