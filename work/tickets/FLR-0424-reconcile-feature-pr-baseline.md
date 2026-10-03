# FLR-0424 — reconcile the feature PR baseline

- Status: Done
- Priority: High
- Created: 2026-10-04
- Owner: Git branch provenance / milestone integration
- Blocks: [FLR-0423](FLR-0423-capture-caller-mapping-provenance.md)
- Related: [FLR-0421](FLR-0421-preserve-journal-cursor-evidence.md)
- Evidence: FLR-0421 branch audit in the [working log](../logs/2026-10-04-flr0421.md)
- Branch: this was a read-only baseline disposition; no feature branch was
  created for it. The approved publication sequence belongs to FLR-0421. No
  merge or history rewrite is authorized by this disposition.

## Purpose

Restore a reproducible, policy-compliant path for reviewing FLR-0421 and then
starting FLR-0423. The current feature is narrow against a local milestone
branch, but that milestone has not been shown to be the correct publishable PR
base. Existing remote `dev` branches would produce a very broad feature diff.

## Facts

- `origin/main` is `5770cec`; it is an ancestor of local
  `dev-flr-0421-runtime-evidence` (`1fb42ee`), which is 155 commits ahead.
- The local milestone interval contains 122 first-parent commits and 4 merge
  commits; the latest first-parent sequence covers FLR-0410 through FLR-0418.
- The local milestone branch's reflog records that it was created from `HEAD`
  at the FLR-0418 feature tip, rather than recording an explicit `main`
  starting point.
- The FLR-0421 feature is 3 commits / 24 files ahead of that local milestone.
- Against `origin/dev-fluorite-demo` (`3616e71`), the feature has 158
  local-only and 14 remote-only commits; its three-dot diff is 2,080 files.
- A push dry-run made no remote change. No actual push, PR, merge, history
  rewrite, or branch deletion has occurred.

## Competing hypotheses

1. The local milestone is an intentional integration snapshot descended from
   `main`; its accumulated commits are required dependencies for current
   runtime tooling, and the safe path is to publish that named `dev` branch,
   then review the 3-commit feature PR against it.
2. The local milestone inherited unintegrated or unrelated feature work; the
   safe path requires reconstructing a clean milestone/dependency chain before
   publishing. A narrow three-commit comparison alone does not prove this
   chain is valid.

Neither explanation is established. Compare the commit graph and ticket
ownership/dependencies; do not infer validity from the local diff size alone.

## Reviewed disposition

- GPT-6.1 Sol's final read-only review judged that descent from `origin/main`
  plus the inspected topology is sufficient for a **narrow publication-only
  path**, not for certifying the preceding milestone history.
- Publish the existing local `dev-flr-0421-runtime-evidence` at exactly
  `1fb42ee` as a new remote ref. Then push the FLR-0421 feature ref and create
  a PR with that `dev` ref as base. Do not merge the PR or merge the dev branch
  into `main` as part of this disposition.
- At review tip `29c4294`, feature-to-local-dev was 4 commits / 25 files
  (+2,823/−236); the only planned addition to that reviewed tip is this
  docs-only disposition commit. Recompute the exact PR diff before pushing.
- Full-range privacy checks for `origin/main..dev-flr-0421-runtime-evidence`
  and `dev-flr-0421-runtime-evidence..HEAD` passed before this docs update;
  rerun both ranges after commit and before any push.
- The user explicitly authorized commits and pushes. This does not authorize a
  merge, and the 155 prior commits remain subject to review.

## Scope and guardrails

- Map local/remote `main`, `dev-*`, and relevant `feature-*` ancestry and exact
  merge bases.
- Classify the milestone commits necessary for FLR-0421 and FLR-0423 without
  indiscriminately replaying the full history.
- Do not change product/runtime source, image, build cache, ticket evidence, or
  existing branch refs; preserve current work and identity.
- No force push, merge, rebase, deletion, or cherry-pick while provenance is
  unresolved. Do not use either existing remote `dev` as a target merely to
  make a PR possible.
- Keep FLR-0423 Inbox until the exact safe milestone base is resolved and
  FLR-0421 is integrated through the approved PR path.

## Success criteria

1. A concise evidence-backed branch/commit provenance map distinguishes facts,
   inferences, and UNKNOWN.
2. A reviewed disposition names the exact safe base and the minimal
   policy-compliant publish/PR sequence, or records why no safe sequence can
   yet be selected.
3. The simulated diff against the selected base is bounded to the intended
   feature and documented handoff records; no broad unrelated history is
   hidden.
4. All existing refs and work remain recoverable; the decision and verification
   are recorded before any external mutation.

## Next action

Execute the recorded FLR-0421 publication sequence only after the post-commit
full-range privacy checks pass. Keep the existing `main` and remote `dev` refs
unchanged; do not merge.
