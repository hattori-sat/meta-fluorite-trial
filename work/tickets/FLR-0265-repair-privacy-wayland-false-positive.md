# FLR-0265 — repair privacy checker false positives and personal paths

- Status: Done
- Priority: Medium
- Owner: repository privacy gate
- Created: 2026-09-24

## Objective

Keep the privacy gate strict for real personal identifiers while allowing
captured Wayland protocol object names and removing personal absolute paths
from project documentation.

## Facts

- Patch `0271` already used the anonymous Devtool identity; it was not the
  current failure source.
- The checker treated Wayland trace tokens such as
  `wl_subsurface@31.set_position` as email-like values.
- Three historical logs contained personal absolute paths and were not
  compliant with the project privacy rule.

## Change

- Added a narrow checker exclusion for `wl_<object>@<numeric>.<method>` trace
  tokens.
- Added a regression test for `wl_subsurface` and `wl_pointer` traces.
- Replaced the three personal absolute paths with role placeholders only.
- No patch hunk, runtime source, recipe behavior, or `index.local` was added.

## Git index decision

- `index.local` is not required by this workflow and must not be created or
  tracked.
- `.git/index.lock` is a transient file created by Git while atomically
  rewriting the normal `.git/index`, even when only one agent is active. It
  should not be pre-created, committed, or deleted blindly. If it remains,
  first verify that no Git process is running; if no stale lock exists and Git
  still cannot create it, the cause is repository `.git` write permission.

## Check

- Privacy checker passes after the correction.
- The new Wayland false-positive test passes.
- Git working tree and canonical repository checks pass.
