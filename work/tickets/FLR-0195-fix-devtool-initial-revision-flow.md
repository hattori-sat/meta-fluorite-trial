# FLR-0195 — fix deterministic Devtool initial-revision flow

- Status: Done
- Priority: High
- Owner: Mac Devtool/tooling role
- Created: 2026-09-15
- Predecessor: [FLR-0194](FLR-0194-readback-direct-fixture-swapchain.md)
- Working log: `work/logs/2026-09-15-flr0193.md`

## Work unit

Make the component rebase helper follow the pinned Yocto Devtool behavior
deterministically: create the component registration while the source is at the
requested baseline, verify the workspace bbappend records that baseline, then
run the official `update-recipe --mode patch --append --no-remove
--force-patch-refresh` flow without a conflicting CLI `--initial-rev`.

## Facts

- The current helper passed `--force-patch-refresh <baseline>` to the wrapper.
- The pinned Yocto `standard.py` skips the embedded `# initial_rev .:` line when
  a CLI initial revision is supplied, without replacing it in `initial_revs`.
- This causes a successful parse with zero generated patches. No patch body was
  manually created or accepted.

## Success criteria

- [x] Helper verifies exactly one requested baseline line after `component-add`
  and invokes update-recipe without CLI `--initial-rev`.
- [x] Contract test passes and the helper diff is committed locally.
- [x] FLR-0194 rebase then produces exactly one official patch whose `From`
  line is the committed source SHA, byte-identical to the canonical copy.

## Plan / Do / Check / Act

### Plan

Patch the helper and its contract test, commit the tooling fix, then rerun the
FLR-0194 rebase from the same persistent source and baseline.

### Do

The two failed no-output attempts and their cause are recorded in the shared
working log. The helper was corrected and committed as `b93dcfb`; the official
FLR-0194 patch was then generated and committed as `7c63e9e`.

### Check

Contract test, official patch generation, canonical registration, and local
commits all passed. The generated patch SHA256 is
`e48ddabed0153b535677ea77bf339a45e9e06b66ddc55261a89d3dc8a33169db`.

### Act

Return the sole active ticket to FLR-0194 and continue the Mini build/runtime
loop there.
