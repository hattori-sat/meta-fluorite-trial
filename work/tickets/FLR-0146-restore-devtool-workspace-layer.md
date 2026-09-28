# FLR-0146 — restore Devtool workspace layer after Podman restart

- Status: Done
- Priority: High
- Owner: Mac Podman/Yocto Devtool environment role
- Created: 2026-09-14
- Updated: 2026-09-14
- Depends on: [FLR-0053](FLR-0053-podman-devtool-runtime.md), [FLR-0145](FLR-0145-test-planetarium-unlit-material.md)
- Working log: `work/logs/2026-09-14-flr0146.md`

## Work unit

Make the fixed Podman Devtool workflow restart-safe without creating a second
container, volume, build directory, TMPDIR, or source workspace. When the
standard Devtool workspace layer is missing from the mounted workspace, restore
its Yocto-standard `conf/layer.conf` from a tracked project template before
BitBake parses the fixed control configuration.

## Problem

After the existing Podman container was reused, `modify --no-extract` stopped
before source inspection with:

`FileNotFoundError: /tmp/fluorite-bitbake-control/workspace/conf/layer.conf`

The active control symlink correctly pointed at
`/workspace/state/build/workspace`, but that mounted workspace had no
`conf/layer.conf`. A stale legacy copy existed below `build/control/workspace`,
which is not the active workspace and must not be selected as a second layer.

## Facts

- The single container, project/AGL/state mounts, rootful Podman contract, and
  fixed `/workspace/tmp` probe all passed.
- The active BBLAYERS entry is the fixed control path's `workspace` symlink to
  `/workspace/state/build/workspace`.
- The active workspace already contains its `recipes`, `appends`, `sources`,
  and persistent Devtool metadata, but its `conf/layer.conf` is missing.
- The old `/workspace/state/build/control/workspace/conf/layer.conf` is a
  legacy duplicate and must remain outside the active BBLAYERS path.
- Yocto's workspace layer format is stable and can be tracked as a small
  project-owned template; restoring only this missing metadata does not alter
  source, recipe patches, downloads, sstate, or TMPDIR.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: restoring the standard workspace layer file repairs parse/reconnect | the same container can run `modify --no-extract` and `devtool status` | parse still reports a missing workspace layer |
| H2: the old control workspace must be used instead | active BBLAYERS must point to `build/control/workspace` | active workspace template is sufficient and no duplicate layer is needed |

## Success criteria

- [x] Track the standard workspace `conf/layer.conf` template under the
  repository's Devtool tooling.
- [x] Make the wrapper restore only the missing file in the existing mounted
  workspace and preserve non-root Devtool ownership.
- [x] Keep one container, one project bind, one state bind, and one fixed
  container TMPDIR; do not use the legacy control workspace as a second layer.
- [x] Verify shell/static tests and rerun the same `modify --no-extract`.
- [x] Record the failure and successful reconnect, then return FLR-0145 to the
  sole In Progress state.

## PDCA

### Plan

1. Add the standard workspace-layer template and a missing-only restore gate.
2. Run canonical verification and the same Devtool reconnect operation.
3. Confirm the active BBLAYERS/workspace identity and proceed with FLR-0145.

### Do

- Added the tracked Yocto-standard workspace-layer template at
  `tools/yocto-devtool/workspace-layer/conf/layer.conf`.
- Updated `scripts/run-podman-devtool.sh` to restore only the missing active
  workspace `conf/layer.conf` and repair its ownership. The legacy
  `build/control/workspace` copy remains outside active BBLAYERS.
- The first `modify --no-extract` failed at the missing layer parse boundary.
  The same operation after the repair passed and reconnected the source tree.

### Check

- `make verify` passed: privacy, shell syntax, Python 85 tests, MCP smoke 52
  tests, Markdown links, file size, and QEMU/runtime harness contracts.
- The repeated `modify --no-extract` passed with fixed mount-permission gates;
  the active workspace was `/workspace/state/build/workspace` and the source
  branch reconnected successfully.
- No second container, named volume, build directory, TMPDIR, or BBLAYER was
  created.

### Act

- Close FLR-0146 as a restart-safety fix and resume FLR-0145 as the sole active
  material/API unit. Do not select the legacy control workspace.

## PDCA checker

- Status: PASS
- Checked by: Fluorite Podman/Yocto environment role
- Findings: the missing active workspace-layer metadata was restored from the
  tracked Yocto-standard template, and the same Devtool reconnect passed using
  the existing container/mount contract.
