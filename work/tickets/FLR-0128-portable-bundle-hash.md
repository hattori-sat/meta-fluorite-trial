# FLR-0128 — make the Mac bundle handoff hash portable

- Status: Done
- Priority: Medium
- Owner: Mac handoff tooling role
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0127](FLR-0127-isolate-dart-fixture-black-region.md)
- Working log: `work/logs/2026-09-13-flr0128.md`

## Work unit

Make the existing Mac-to-Mini Git bundle helper work when the Mac provides
`sha256sum` but not `shasum`, without changing the fixed bundle path, receiver,
build directory, TMPDIR, or bundle protocol.

## Success criteria

- The helper prefers `shasum` when available and falls back to `sha256sum`.
- The local digest is still compared with the Mini-side digest.
- Existing no-duplicate bundle/receiver behavior remains unchanged.
- Shell and handoff contract tests pass.

## Facts

- The helper previously computed its local digest with `shasum -a 256` only.
- The current Mac shell has `/sbin/sha256sum` and no `shasum` command.
- The failure was observed before bundle transfer; no Mini receiver or build
  state was changed by this failed attempt.

## Inferences

- The handoff failure is a host-tool portability defect, not a Git bundle or
  Mini receiver defect.
- A small local fallback preserves the existing transfer and verification
  contract.

## Hypothesis

| Hypothesis | Prediction | Probe | Result |
| --- | --- | --- | --- |
| H1: local digest command is hard-coded to an unavailable tool | replacing the local digest implementation with a `sha256sum` fallback makes the helper pass its preflight on this Mac | shell test plus one real bundle handoff | CONFIRMED; handoff passed |

## PDCA

### Plan

1. Add a bounded local digest helper with `shasum`/`sha256sum` fallback.
2. Extend the existing static contract test.
3. Run project verification and commit locally.
4. Return to FLR-0127 and hand off its already generated A/B commit.

### Do

- Added the fallback implementation and static assertions.
- The targeted handoff contract test and the full project verification both
  passed.
- The real bundle handoff passed with the fixed active bundle, remote SHA-256
  `c0d64f5df1573766b6ba1b52f45fca5745a6b85300675034431040c494f50ab4`, and
  receiver tip `116bbfa1c9e634b9e6a463fa978ef5a905b91328`.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Portable digest helper | both local hash tools supported | `file_sha256` prefers `shasum` and falls back to `sha256sum` | PASS |
| Existing bundle contract | fixed active bundle and receiver paths unchanged | static contract test and full verification passed | PASS |
| Tests | shell/handoff checks pass | targeted handoff test and `make verify` passed | PASS |
| Real bundle handoff | fixed receiver accepts exact tip | remote bundle verified and receiver is at `116bbfa1c9e634b9e6a463fa978ef5a905b91328` | PASS |

### Act

- Close this tooling ticket and resume FLR-0127. Do not add a new receiver or
  temporary build directory as a workaround.

## PDCA checker

- Status: PASS
- Checked by: repository verification and fixed handoff helper
- Findings: local and remote bundle hashes matched; receiver advanced to the
  exact requested tip.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings:
