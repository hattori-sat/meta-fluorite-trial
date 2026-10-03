# FLR-0420 — reconcile repository Markdown-link verification baseline

- Status: Inbox
- Priority: Medium
- Created: 2026-10-04
- Owner: repository verification / evidence-retention roles
- Related work: [FLR-0418](FLR-0418-preserve-serial-wait-completion.md)

## Objective

Explain and stabilize the repository-wide Markdown-link gate without deleting
evidence, inventing replacement screenshots, weakening the checker, or folding
historical cleanup into an unrelated runtime ticket.

## Facts

- `make verify` on the recovered canonical checkout reports 55 missing
  Markdown targets, all emitted from older ticket/evidence/log documents.
- None of the newly added FLR-0417/0418/0419 ticket, plan, log, or evidence
  targets appears in the reported failures.
- The FLR-0417 working log recorded 11 missing targets during an earlier
  verification. The current checkout reports 55, so the recorded baseline
  counts do not agree.

## Inference

- The failure may combine historical media intentionally stored outside Git,
  genuinely missing retained evidence, or a changed checkout/verifier input.
  The present output alone cannot distinguish these cases.

## UNKNOWN

- Whether all 55 missing targets were absent at the earlier 11-error check.
- Whether affected images/videos should be restored from their canonical
  evidence source, or their links should be changed to durable tracked paths.
- Whether repository history or workspace projection explains the difference.

## Success criteria

1. Compare the same canonical Git revision and verifier across a clean isolated
   checkout; report exact baseline and current missing-target sets.
2. Classify each missing target as intentionally external, recoverable evidence,
   or invalid reference, with source/hash provenance where available.
3. Restore or correct only evidence supported by provenance; do not synthesize
   image/video substitutes or silently reduce verification coverage.
4. Demonstrate the Markdown gate has a stable, documented result and preserve
   all unrelated working-tree data.

## Plan / Do / Check / Act

### Plan

- Reproduce the two reported counts at their exact revisions and compare path
  sets before making any document changes.

### Do

- Not started; remains in Inbox. No historical evidence was changed during
  FLR-0418 verification.

### Check

- Current `make verify` reached `check-markdown` only after 340 Python and 52
  MCP tests passed; its 55 missing targets are recorded in the FLR-0418 log.

### Act

- Start after FLR-0418 runtime evidence is finalized; keep the active ticket
  count at one.
