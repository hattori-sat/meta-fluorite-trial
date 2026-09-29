# FLR-0254 — repair Mac app recipe do_patch gate dependency profile

- Status: Done
- Priority: Medium
- Owner: Mac Podman Devtool recipe-gate harness
- Created: 2026-09-21
- Predecessor: [FLR-0253](FLR-0253-restore-production-frame-event-registration.md)

## Objective

Make the Mac-side focused recipe gate report app patch applicability without
failing on an unavailable `quilt-native` provider, or document the deliberate
scope boundary if the app gate must remain Mini-only.

## Fact

- `scripts/run-podman-devtool.sh recipe-task
  toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo do_patch`
  stopped at dependency resolution with `Nothing PROVIDES 'quilt-native'`.
- The official generated FLR-0253 patch was produced before this failure and
  has a valid source baseline and recipe registration.

## Current failure evidence — 2026-09-24

- The fixed Podman container, project bind, AGL bind, and state bind all pass
  their preflight checks.
- The focused profile writes `BBFILES =` with only the target app recipe after
  the layer configuration has been loaded. This removes the standard layer
  file list, so BitBake cannot provide `quilt-native`.
- Re-running the same official `devtool modify` with `full` profile did not
  produce an app source tree within the bounded wrapper run. This is not yet
  evidence that the recipe or its patch stack is invalid.

## Hypothesis

H1: The focused profile should preserve the layer-provided `BBFILES` and add
the target recipe, rather than replacing the provider list. The predicted
result is that `quilt-native` resolves and `devtool modify` reaches source
extraction; a remaining patch failure is a separate source-baseline issue.

H2: The app recipe or its current patch stack is intrinsically unbuildable.
This is weakened by the earlier official app patch workflow, but remains
UNKNOWN until H1 is tested.

## Next check

Change only the focused-profile assignment from replacement to additive
`BBFILES +=`, run the focused wrapper contract test, then retry official
`devtool modify` in the same persistent container. Do not edit a generated
patch by hand.

## Resolution — 2026-09-24

- The focused profile now preserves layer-provided `BBFILES` for normal
  extraction and adds the target recipe, so native providers remain visible.
- The no-extract path uses the target-only file list because it reuses a
  prepared Git tree and does not need to expand the provider graph.
- `bash tests/test-podman-devtool.sh`: PASS.
- Official `modify --no-extract` registered the clean app source at the fixed
  state path, and `devtool status` showed exactly one app recipe mapping.
- The first official `finish-source` retry exposed the same profile boundary:
  preserving all layer `BBFILES` parsed 2,553 recipes and stopped on an
  unrelated stale image `.bbappend`. The focused finish-source path is now
  narrowed to the already prepared target source, matching no-extract.
- No container, volume, source tree, or Yocto cache was deleted or duplicated.

## Act

Return to FLR-0272. The next source change must be made in this registered
Devtool source, committed there, and materialized with the official patch
generator.

## Scope boundary

This ticket does not change the Fluorite application or native renderer. It
only covers the Mac validation profile and its error handling.
