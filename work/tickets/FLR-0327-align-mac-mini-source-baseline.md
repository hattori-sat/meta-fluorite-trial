# FLR-0327 — align Mac and Mini flutter-auto source baseline

- Status: Done
- Priority: High
- Owner: Mac Devtool / Mini authoritative Yocto source identity
- Created: 2026-09-25
- Related: [FLR-0326](FLR-0326-probe-production-fragment-target-boundary.md)

## Objective

Make the Mac patch gate and Mini authoritative build resolve the same
`flutter-auto` v2.0 homescreen/plugin source pair, without creating another
build directory, source copy, container, or patch stack.

## Facts

- Mini `bitbake -e` records `HOMESCREEN_COMMIT=dd6d9224...` and
  `PLUGINS_COMMIT=2163242...`.
- The Mac external `meta-flutter` recipe defaulted to `bc85ac...` and
  `451aa...`, causing existing patch 0220 to fail before FLR-0326.
- Mac self-install metadata already contains the Mini pair, but the current
  Podman setup selects the external recipe layer.

## Decision

The first minimal mitigation is to pin the authoritative pair in the
project-owned `flutter-auto_2.0.bbappend`. If that does not make the Mac gate
advance beyond 0220, update the Podman layer-selection contract in a separate
iteration and preserve the failed evidence.

## Success criteria

- [x] Mac `bitbake -e flutter-auto` reports the Mini pair.
- [x] Mac `do_patch` advances past 0220 without modifying the generated 0220
  patch (104/104 tasks).
- [x] Mini bundle handoff and bounded `do_patch` resolve the same pair.
- The fixed Podman container, state bind, TMPDIR, and build directory are
  reused.

## Check

- Project commit `40395e9` was handed off with bundle SHA
  `a121b5a257e8...`; Mini `do_patch` passed.
- The subsequent command-only commit `7b78697` was handed off with bundle SHA
  `6295179745ee12bc...`; the same receiver/build/TMPDIR remained in use.

## UNKNOWN

- Whether the external recipe's `git://` plugin fetcher has any behavior
  difference from the Mini self-install `gitsm://` declaration after the
  revisions are pinned.
