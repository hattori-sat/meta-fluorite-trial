# FLR-0151 — repair Podman tmpfs ownership after restart

- Status: Inbox
- Priority: Medium
- Owner: Mac Podman Devtool container lifecycle role
- Created: 2026-09-14
- Updated: 2026-09-14
- Depends on: [FLR-0150](FLR-0150-read-native-swapchain-pixels.md)

## Work unit

Make a restart of the existing Mac Podman Devtool container restore the
non-root Devtool user's access to the fixed container-local `/workspace/tmp`
without a manual ownership repair, a new container, a new TMPDIR, or cache
deletion.

## Success criteria

- [ ] Restart the existing `fluorite-mac-devtool` container once and prove
  `/workspace/tmp` and `/workspace/tmp/work` are writable by the configured
  Devtool UID.
- [ ] Run the wrapper's non-root recipe gate after restart without a manual
  `chown` and without a `mkfifo` permission error.
- [ ] Preserve the single container, bind-mounted source/state, and protected
  downloads/sstate/TMPDIR policy.
- [ ] Record the fix in the wrapper/container contract and run its tests.

## Facts

- After the fixed container restart during FLR-0150, `/workspace/tmp` was
  `501:20` but `/workspace/tmp/work` was `0:0`, causing non-root BitBake to
  fail before `do_recipe_qa` could create its work directory.
- Manually restoring the exact fixed tmpfs directory ownership allowed the
  same Mac `filament-vk:do_patch` gate to pass 104/104 tasks.
- No protected cache or second build/TMPDIR/container was used.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: restart creates the nested work directory after the wrapper's repair scan | an explicit post-create ownership repair makes the next gate pass | a clean restart still leaves the directory root-owned |
| H2: the configured UID/GID is not available during repair | wrapper logs show missing or mismatched identity values | repair sees configured `501:20` and still fails |

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | ownership of the fixed container-local Devtool TMPDIR |
| Where | existing `fluorite-mac-devtool` `/workspace/tmp/work` |
| When | after container restart, before any non-root Devtool/BitBake task |
| Who | Podman wrapper lifecycle role |
| How | one fixed container, one ownership probe, one recipe gate |

## PDCA

### Plan

1. Reproduce the restart state using the existing container.
2. Trace when `/workspace/tmp/work` is created relative to the repair scan.
3. Apply the smallest wrapper/container lifecycle correction.
4. Restart and rerun the non-root recipe gate without manual repair.

### Do

Not started. FLR-0150 uses a bounded manual repair only to complete its
rendering evidence gate.

### Check

Pending clean restart and wrapper gate.

### Act

Keep this operational fix separate from Vulkan/Wayland rendering changes.
