# FLR-0023 — Project-owned Fluorite layer and build input

Status: In Progress (Check)

## Outcome

Make `layers/meta-local` in `meta-fluorite-trial` the source of truth for Fluorite-specific recipes, packagegroups, patches, runtime configuration, and image additions. Use only the fixed upstream Flutter layer for the `flutter-app` class; do not require the historical external `self-install/meta-flutter-apps` layer.

## Facts

- The existing Fluorite demo recipe lived in `self-install/meta-flutter-apps` while project-owned scene patches lived in `meta-local` but were not listed in effective `SRC_URI`.
- `meta-vulkan` is independently pinned and correctly added to active `bblayers.conf`.
- The active build therefore mixed project overlays with an unpinned/dirty Flutter app layer.

## Do

- Add the demo recipe and Fluorite packagegroup to `layers/meta-local`.
- Connect scene patches 0001–0003 explicitly through the recipe `SRC_URI`.
- Remove the external app-layer dependency from the target templates.
- Keep the upstream `external/meta-flutter` layer for the shared `flutter-app` class.

## Check

- First gate: `bitbake-layers show-layers` must show `meta-local` and `external/meta-flutter`, without `self-install/meta-flutter-apps`.
- Second gate: `bitbake -e toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo` must show the three patches in `SRC_URI` and the project-owned package path.
- Third gate: bounded demo `do_patch`/`do_compile`, then image build; no cache deletion.

### Evidence (2026-07-20)

- `bitbake-layers show-layers` on the Mini PC trial build listed project `meta-local`, fixed `external/meta-flutter`, and `vulkan-layer`; the historical `self-install/meta-flutter-apps` layer was absent.
- `bitbake -e toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo` resolved the project-owned recipe and showed all three scene patches plus `config.toml` in `SRC_URI`.
- The first project `do_patch` attempt exposed a malformed imported patch hunk. Patch `0001` was corrected to remove its no-op hunk and use the actual upstream context; the bounded rerun completed with `do_patch: Succeeded`.
- A bounded project `do_compile` reached task 2585/2590, `flutter-engine-3.32.5:do_compile`. It exceeded the 900-second client bound during first-time engine generation; no application compile error was observed before the bound. This is an infrastructure/cache warm-up observation, not a pass for the compile acceptance criterion.
- Local `make verify` passed, including privacy, metadata, MCP, link, and file-size checks.

## Smallest next action

Reuse the now-populated Flutter SDK/engine cache and rerun the demo compile with a longer bounded window; only after a successful compile proceed to package and image tasks.
