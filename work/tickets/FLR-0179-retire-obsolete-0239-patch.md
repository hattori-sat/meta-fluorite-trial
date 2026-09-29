# FLR-0179 — retire obsolete 0239 recipe patch

- Status: Done
- Priority: High
- Owner: Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0178](FLR-0178-deterministic-mini-recipe-workdir.md)
- Working log: `work/logs/2026-09-15-flr0179.md`

## Work unit

Remove the stale 0239 patch from the active `flutter-auto` recipe patch
sequence after proving that it fails from a clean, deterministic workdir.
Keep the historical patch file in Git until a later cleanup decision; only
the active recipe registration changes in this unit.

## Problem

0239 was generated against the former `vOnInitSystem`/
`vSetCameraFromSerializedData` API. The current clean source uses
`onSystemInit`, `update`, and the current ViewTarget API, so both 0239 hunks
fail after a successful recipe-scoped reset. Re-generating a patch against
the wrong API would hide an unrelated source/API migration issue.

## Success criteria

- [x] 0239 is absent from the active `flutter-auto` `SRC_URI` patch list.
- [x] The historical 0239 file remains available for Git history and is not
  applied by the recipe.
- [x] The clean Mini recipe gate advances past 0239 and reports the next first
  failing patch, or passes the full patch stack.
- [x] Layer metadata, tests, and evidence are committed locally.

## Facts

- FLR-0178 clean→do_patch passed its reset and reproduced 0239 hunk 1/2.
- The current source API is not the 0239 patch's API.
- 0239 has no current recipe consumer after this metadata change.

## Inferences

- 0239 is obsolete for the resolved current source; its behavior must not be
  silently claimed as implemented.
- The next gate boundary, after removing 0239, is the correct source/API
  migration unit to investigate.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0239 is the only stale boundary at this point | clean do_patch advances beyond 0239 | another earlier patch fails after reset |
| H2: removal is correctly scoped | only active recipe metadata changes; historical file remains | historical file is deleted or another recipe changes |
| H3: later patches match current source | gate reaches the next meaningful boundary | a later patch also has stale API context |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | retire stale 0239 from active recipe registration |
| Where | `meta-fluorite-trial` flutter-auto bbappend |
| When | after clean deterministic 0239 failure |
| Who | Yocto layer integration role |
| How | remove one SRC_URI item → bundle → clean do_patch gate |

## PDCA

### Plan

1. Remove only the 0239 `SRC_URI` entry.
2. Run repository verification and commit the layer/ticket change.
3. Hand off the commit and run the clean Mini patch gate once.

### Do

- Removed only the 0239 `SRC_URI` registration; retained the historical patch
  file in Git.
- Updated the authorized baseline lock and ticket evidence.

### Check

- Repository `make verify`: PASS before the local commit.
- Mini clean gate: preflight PASS, metadata PASS,
  `workdir-reset=PASS mode=recipe-clean`; 0239 was skipped and 0228 became
  the first failing patch.
- Summary SHA256:
  `bbeb81c3c191a380825410af66cebb848b7046b29707991489a5b140fd71caee`.
- Bounded failure SHA256:
  `67ea2f198c83cc413ea9564265fbbf63da9f805203ee19c96a8faf3ba6a03d43`.
- Mini task log SHA256:
  `b44a4af5972e76f51ee11cbec0c69aeb4b9aa7d3f9e75362c08ec8a1019db7c9`.

### Act

- FLR-0180 owns the next first failing patch, 0228.

## UNKNOWN

- The next first failing patch after 0239 removal is UNKNOWN.
- Whether the current camera behavior needs a new current-API patch is
  UNKNOWN and remains separate from this metadata cleanup.

## Evidence

- Predecessor clean gate summary SHA256:
  `049eda25f508e557e223bee22c6db203d11bb6af15cdf17deb61f59ed8db7bd5`.
- Predecessor bounded failure SHA256:
  `2267ef90c031ff275d1ac3b56a6115f79a928f74499972497573c9cdda09ed2d`.
- Local commit: `8ac4589` (no push).
