# FLR-0024 — Replace legacy meta-local layer identity

Status: Waiting (Check — FLR-0025 compile/image acceptance)

## Outcome

The repository-owned layer must be named and surfaced as `meta-fluorite-trial`; `meta-local` is only a historical source label and must not remain an active layer path or BitBake collection name.

## Facts

- The previous implementation copied the historical custom layer into `layers/meta-local`.
- Active build templates and materialization scripts referenced that name.
- Mini PC and Mac were on different branches before synchronization; the Mini PC dirty work was preserved in a stash before switching to the Mac feature commit.
- `work/flourite` does not exist in the canonical repository. The authoritative working log is `work/logs/2026-07-19.md`.

## Do

- Rename the directory and BitBake collection to `meta-fluorite-trial`.
- Use `@PROJECT_ROOT@/layers/meta-fluorite-trial` in materialized build configurations.
- Update tests, hashes, documentation, and baseline tooling without embedding user or host identity.
- Revalidate metadata and patch gates on the synchronized Mini PC branch.

## Check

- `make verify` and privacy check pass.
- Mini PC and Mac feature branches point to the same commit.
- `bitbake-layers show-layers` reports the renamed layer and no historical app layer.
- `bitbake -e` resolves the project recipe and explicit scene patches.
- The renamed-layer bounded compile reached Flutter engine task `do_compile` and timed out at 1200 seconds around ninja step `1150/9648`; no compiler error was recorded, so compile acceptance remains UNKNOWN/Incomplete.

## Unknowns

- Whether the renamed layer changes task signatures enough to require a longer engine/image build.
- Whether the external Flutter revision's resolved SDK version is compatible with the target runtime.

## Smallest next action

Commit and push the rename after local gates, then run the metadata and bounded patch/compile checks on the synchronized Mini PC branch.
