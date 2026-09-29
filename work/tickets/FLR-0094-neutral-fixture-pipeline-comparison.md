# FLR-0094 — compare neutral fixture and production pipeline inputs

- Status: Waiting
- Priority: High
- Owner: Fluorite fixture / Filament Vulkan runtime
- Created: 2026-09-12
- Depends on: [FLR-0093](FLR-0093-isolate-production-pipeline-create.md)
- Working log: `work/logs/2026-09-12-flr0094.md`

## Work unit

Reproduce the self-made native fixture and the production scene on the same
authoritative image, using only neutral current diagnostic controls. Compare
the effective Vulkan pipeline inputs, frame progression, and QMP pixels so the
fixture/production difference is measurable without reusing the historical
namespace or changing fence/present semantics.

## Success criteria

- Add the smallest neutral opt-in controls needed to select the existing
  self-made fixture and minimal geometry path.
- Generate the source patch through the Mac Devtool source workspace and its
  official recipe update flow; do not hand-author a patch.
- Pass Mini metadata, `do_patch`, `do_compile`, and full-image gates using the
  existing fixed receiver, build, TMPDIR, and bundle flow.
- Run one bounded fixture case and one bounded production case with exactly
  one QEMU and one application process per run.
- Preserve QMP-only screenshots/video frames, runtime logs, hashes, and clean
  teardown in the fixed receiver, with a concise tracked evidence manifest.
- State whether the fixture/production divergence is before pipeline create,
  after successful create, or at frame/fence/present, and select the next
  independent ticket if a product fix is still required.

## Facts

- FLR-0093 recorded six production pipeline-create results with `result=0`,
  but the native QMP region remained black while the 2D HUD remained visible.
- Earlier controlled fixture evidence demonstrated native pixels on the same
  general runtime path, but the controls and markers were named for the
  historical investigation namespace.
- The current canonical layer already contains the fixture implementation and
  the production pipeline-input trace; this ticket should add only neutral
  aliases/markers required for a clean A/B comparison.
- The current active receiver, build, TMPDIR, and Podman Devtool state are
  fixed and must be reused rather than creating another per-ticket tree.

## Inferences

- A successful neutral fixture run would separate the source fixture setup and
  production-scene/resource path from the later synchronization boundary.
- A fixture run that also remains black would shift the focus back toward the
  shared command execution or display path, not production assets alone.
- The comparison is meaningful only when image provenance, launch identity,
  QMP capture, and teardown are equivalent.

## Hypotheses

1. The existing fixture path still completes pipeline creation and reaches
   native pixels when selected through neutral controls.
2. Production-only resource or pipeline inputs create the later pending work
   observed in FLR-0093, while the fixture avoids it.
3. The apparent difference is caused by run timing or incomplete evidence;
   equivalent bounded captures will show no stable fixture/production split.

## UNKNOWN

- The exact source operations and effective pipeline fields that differ between
  the fixture and production cases.
- Whether the current Devtool source state can be reused without first
  preserving unrelated existing source-worktree changes.
- Whether the neutral fixture aliases alone are sufficient to produce visible
  QMP pixels on the current full image.

## Plan / Do / Check / Act

### Plan

1. Inspect the existing Devtool component state and preserve unrelated source
   changes before editing.
2. Add only neutral fixture controls/markers in the Devtool-managed source,
   commit the source change, and generate the official patch.
3. Import that patch byte-for-byte into the canonical layer, bundle the
   canonical commit, and run the authoritative Mini build gates.
4. Capture equivalent QMP/runtime evidence for neutral fixture and production
   launches, then classify the first stable divergence.

### Do

1. Created a clean Devtool source branch from `544f451` and committed the
   two source-file changes as `6517bad` and `6bce593`.
2. Re-registered the existing component at the correct baseline after the
   first update attempt produced no patch; the official Devtool
   `update-recipe` then generated two patches.
3. Copied the generated patches byte-for-byte into the canonical layer as
   `0209` and `0210`, registered them after `0208`, refreshed the authorized
   baseline lock, and committed the work as `054e3c5`.
4. Handed that commit to the existing fixed Mini receiver as one verified
   bundle. Mini `bitbake -e`, `do_patch`, `do_compile`, and full-image gates
   passed.
5. Ran one bounded neutral-fixture QEMU case and one equivalent production
   case with QMP-only captures, 20-frame videos, runtime log tails, one app
   process each, and QMP teardown.

### Check

`make verify` passed after the authorized baseline lock refresh: 78 Python
tests, 52 MCP smoke tests, Markdown links, file size, and QEMU harness
contract all passed. The generated and canonical patch SHA-256 values match.

The neutral fixture final frame is 1280x800 with `41,750/223,200` changed
native pixels and a visible bbox `[501,278,278,162]`; the HUD is also visible.
The production final frame is the same size with `0/223,200` native pixels and
`1,284/100,000` HUD pixels. Both runs recorded one `flutter-auto`, 20 QMP
video frames, and clean QMP teardown.

The installed binary and effective recipe contain the neutral controls. The
bounded fixture log tail did not retain the startup neutral marker, so marker
selection is UNKNOWN even though the binary/recipe identity and native QMP
pixels agree. The fixture log also contains repeated non-fatal `Light not
found` handler messages while queue-present continues successfully.

### Act

The fixture/production split is confirmed on one image, but the fixture
startup selection marker was not retained in the bounded log evidence. This
ticket is therefore Waiting rather than Done. FLR-0095 is the separate
evidence unit for live startup-marker extraction and complete pipeline-record
comparison; no source or synchronization change is carried forward here.
