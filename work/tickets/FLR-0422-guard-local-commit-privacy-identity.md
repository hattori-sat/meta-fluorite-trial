# FLR-0422 — guard the local commit privacy identity

- Status: Inbox
- Priority: Medium
- Created: 2026-10-04
- Owner: Local Git workflow / privacy gate
- Links: [FLR-0418 working log](../logs/2026-10-04-flr0418.md)

## Problem

### Purpose

Prevent the local commit flow from creating a commit that only fails the
repository privacy check after the commit has already been written.

### Success measure

A deterministic local commit helper or equivalent preflight sets the approved
role identity for both author and committer, verifies the resulting HEAD
metadata immediately, and refuses success if either differs. A temporary-repo
test covers inherited Git identity overrides and proves no push is performed.

## Facts and gap

- During FLR-0418, the privacy scan passed before commit because it could not
  inspect the not-yet-created commit.
- The first local commit used an identity that did not match the repository's
  exact approved role metadata; the post-commit privacy check caught it.
- Amending with only a committer override retained the old author; reset-author
  was required. The corrected local commit then passed privacy validation.
- Current process gap: pre-commit file scanning does not verify the identity
  that the next Git commit will record.

## Scope

- In scope: local no-push helper/preflight, author+committer validation,
  temp-repository regression tests, and runbook update.
- Out of scope: rewriting unrelated history, changing privacy patterns, or
  push/PR automation.

## Success criteria

1. Test fails when an inherited identity override would create mismatched
   author/committer metadata, and passes with the fixed role identity.
2. The helper verifies its new HEAD and never pushes.
3. Existing repository privacy tests and the FLR-0421 workflow remain green.

## Unknowns

- Whether an existing shared local commit wrapper can host this check without
  adding a second commit workflow.
