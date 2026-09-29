# FLR-0372 — fetch pinned flutter-auto plugin submodules

- Status: In Progress
- Priority: High
- Owner: Yocto recipe metadata / Mini authoritative build roles
- Created: 2026-09-30
- Predecessor: [FLR-0371 LIT parameter RGB assignment](FLR-0371-lit-parameter-rgb-assignment.md)
- Branch: `feature-flr-0372-plugin-submodule-fetch` from
  `dev-flr-0372-build-prerequisite-integration` (local, no push)
- Integration base: `f4e32cb2da2301ecb502e31bcda746084e32bddb`; this dev branch
  intentionally contains the unverified FLR-0371 candidate and is not a
  production/main promotion.
- Working log: [FLR-0372 working log](../logs/2026-09-30-flr0372.md)

## Objective

Make the existing pinned `ivi-homescreen-plugins` source fetch its declared
`sdbus-cpp` Git submodule so `flutter-auto:do_configure` receives the files its
CMake build requires. Change only the fetch scheme for the existing `plugins`
URI. Preserve its URL, protocol, branch, `name`, destination, `PLUGINS_COMMIT`,
all patch content, and the separate homescreen source.

This is a Yocto source-acquisition prerequisite. It does not modify Flutter,
Filament, a generated Devtool patch, the runtime image behavior, or any QEMU /
Flutter launch script. It does not establish that the FLR-0371 RGB assignment
renders or that production Sequoia is visible.

## Facts

- On the exact Mini receiver tip `f4e32cb2da2301ecb502e31bcda746084e32bddb`,
  candidate patch 0330 passes `flutter-auto:do_patch`.
- The subsequent forced candidate compile ran 483 seconds and failed one
  task, `flutter-auto:do_configure`; no image build or QEMU run started.
- The first actionable CMake error is the missing
  `ivi-homescreen-plugins/plugins/common/sdbus/third_party/sdbus-cpp/CMakeLists.txt`.
  Later CMake property/link errors follow that missing directory.
- `PLUGINS_COMMIT` remains
  `2163242e9973336153871ed63b34bb5ed8282145`. Its tree has a gitlink at
  `plugins/common/sdbus/third_party/sdbus-cpp` for commit
  `7fbfcec455a2af6efe3910baa3089ecba48a9d6d`; the source checkout is not
  initialized in the failed worktree.
- The Mini's effective `SRC_URI` has three source entries; the plugin entry is
  `git://` with `protocol=https;branch=v2.0;name=plugins` and destination
  `${S}/ivi-homescreen-plugins`. Its base recipe declares that same URI.
- The plugin repository's `.gitmodules` declares this one submodule using
  HTTPS. The build has no separately observed submodule checkout step.
- Historical FLR-0327 explicitly left the external-recipe `git://` versus
  self-install `gitsm://` behavior unresolved. FLR-0286 had a missing
  submodule in a Mac Devtool baseline; this ticket addresses the distinct
  Mini fetch/unpack worktree boundary.
- BitBake documents `gitsm://` as its Git-submodule fetcher and notes that it
  has mirror, licensing, and source-archiving limitations. See the [official
  BitBake Git Submodule Fetcher documentation](https://docs.yoctoproject.org/bitbake/dev/bitbake-user-manual/bitbake-user-manual-fetching.html).

## Hypotheses

1. **Fetcher omission (leading):** `git://` fetches only the pinned plugin
   repository; `gitsm://` fetches its declared submodule at the parent
   gitlink's exact commit. The missing CMake file then disappears as the first
   configure error.
2. **Stale/unpack-state alternative:** the plugin source worktree is stale or
   incomplete independently of the fetch scheme. A recipe-scoped clean and
   fresh fetch/unpack with the current scheme will distinguish this from the
   fetcher hypothesis.

## Scope and impact

- One project-layer `SRC_URI:remove`/`SRC_URI:append` pair changes only the
  plugin fetch scheme from `git://` to `gitsm://`.
- **Build-time:** a clean recipe fetch may retrieve one additional pinned
  submodule; network/cache effects are bounded to this recipe. Keep the
  existing downloads, sstate, build directory, and TMPDIR.
- **Packaging/runtime:** no package or runtime behavior changes are intended.
- **Integration risk:** BitBake's Git-submodule fetcher has mirror,
  licensing, and source-archiving caveats. Validate the exact effective URI,
  gitlink checkout, and patch/configure/compile sequence on the authoritative
  Mini before relying on the result.

## Success criteria

- [ ] The effective `plugins` URI is exactly one `gitsm://` item with the
      existing URL, protocol, branch, name, destination, and pinned revision;
      no `git://` item remains for `name=plugins`.
- [ ] Recipe-scoped clean → `do_fetch` → `do_unpack` places the expected
      `sdbus-cpp` commit and `CMakeLists.txt` in the recipe worktree.
- [ ] Candidate `do_patch`, `do_configure`, and `do_compile` pass on Mini at
      the recorded receiver commit; exact logs/status and available storage
      remain preserved.
- [ ] No downloads/sstate/TMPDIR cleanup, unrelated source-revision change,
      runtime script change, QEMU run, or push occurs in this ticket.
- [ ] FLR-0371 remains blocked until the prerequisite is proven; a compile
      pass here is not a 3D-rendering verdict.

## Plan / Do / Check / Act

### Plan

Keep the current FLR-0371 branch untouched. Use the new integration dev branch
at its exact current tip, then isolate FLR-0372 on its own feature branch.
Change only the `plugins` fetcher, refresh the project-layer tree lock through
the repository helper, commit locally, and transfer a verified bundle to the
existing Mini receiver. Since Yocto requires recipe cleanup when changing
between Git and Git-submodule fetchers, clean only `flutter-auto`; then inspect
the bounded effective metadata and run the dependent tasks in order. The
existing-image manual SSH→Flutter→present-gated QMP positive control remains
the runtime baseline; no runtime launcher is edited here.

### Do

- Current-image direct guest-SSH baseline and full-frame QMP evidence are
  already preserved under FLR-0371: dark-blue self-made LIT fixture and HUD
  appeared together after waiting for successful presents.
- Candidate patch 0330 was transferred with the project layer and
  `do_patch` passed. Its compile attempt found the missing submodule described
  above. The fetcher correction and its validation are now this separate work
  unit.

### Check

Pending Mini URI, fetch/unpack, `do_patch`, `do_configure`, and `do_compile`
results.

### Act

- If all source/build checks pass, close FLR-0372 and resume FLR-0371 from a
  new feature branch based on the integration dev branch; build the image,
  then manually start Flutter over guest SSH and capture complete QMP
  screenshot/video before teardown.
- If the submodule is still absent, preserve the first failing task/log and
  open a distinct diagnosis only after classifying the new boundary. Do not
  alter the Devtool source patch or fetch other unrelated submodules.

## UNKNOWN

- Whether switching only this effective plugin URI to `gitsm://` will populate
  the expected gitlink checkout under the Mini's current cache/mirror policy.
- Whether the FLR-0371 RGB-only assignment renders once the candidate image
  can be built.
- Whether production Sequoia can be composed with the 2D HUD; no current
  candidate image or production-scene QMP frame has been produced.
