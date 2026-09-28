# FLR-0114 — reconcile flutter-auto patch-stack baseline

- Status: Done
- Priority: High
- Owner: Yocto recipe + Mac Devtool source roles
- Created: 2026-09-12
- Depends on: [FLR-0113](FLR-0113-isolate-explicit-light-contribution-boundary.md)
- Working log: `work/logs/2026-09-12-flr0114.md`

## Work unit

Identify and repair the source/recipe baseline mismatch that prevents the
existing `meta-flutter` patch stack from reaching the current Fluorite
diagnostic patches. Use the locked Yocto metadata and the persistent Devtool
workspace; do not hand-edit generated patch hunks.

## Problem

The reused Mac Devtool container parsed the current configuration successfully,
but `flutter-auto:do_patch` failed at the existing
`0001-diag-probe-Flutter-parent-alpha-before-present.patch`, hunk 3, in
`shell/backend/wayland_vulkan/wayland_vulkan.cc`. The failure occurred before
0211 was attempted. The exact source/recipe revision relationship is not yet
identified.

## Success criteria

- [x] Capture effective `SRCREV`, `S`, `SRC_URI` order, and the locked source
  revision from the same Yocto configuration.
- [x] Compare the rejected patch against the persistent Devtool post-patch
  baseline and determine whether the mismatch is source revision, patch order,
  stale work state, or another recipe override.
- [x] Resolve the mismatch only through the documented Yocto/Devtool lifecycle;
  no manual hunk-offset or generated-patch edits.
- [x] Reused Mac container passes `flutter-auto:do_patch` and recipe QA with
  the current applicable patch stack.
- [x] Record failed observations, exact log identity, and the next Mini build
  gate; do not claim runtime or 3D success in this ticket.

## Facts

- The current Podman machine/container reuse and mount contract pass.
- The current feature layer contains 0211 with SHA-256
  `f853fb52cba3f13bc4f91fc493aa80a1ebbd3733c1c9a6995d2b23b4b5c0fc5e`.
- The failing task reached `flutter-auto:do_patch` and rejected hunk 3 of
  existing patch 0001 before attempting 0211.

## Static evidence collected before activation

- The unpacked flutter-auto source in the reused build state resolves to
  `bc85acbad58b61da5fbfa97926c267ddb8e07abc`.
- Its `shell/backend/wayland_vulkan/wayland_vulkan.cc` source contains
  `barrier.srcAccessMask = 0` in the present-transition block.
- The rejected 0001 hunk 3 has a deleted preimage containing
  `barrier.srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT`; its first
  failing context therefore differs from the current source before the hunk
  can be applied.
- Source history attributes the `srcAccessMask = 0` form to commit
  `778d88f4` (`Vulkan Backend`) in the unpacked source repository.
- The persistent Podman recipe gate passed after the stack was reconciled:
  `flutter-auto:do_patch` succeeded, recipe QA succeeded, and all 104 tasks
  in the bounded task set completed successfully. The only remaining warning
  was the pre-existing Python invalid-escape deprecation from `meta-flutter`.
- Devtool-managed replacement patches were generated for parent-alpha/AGL
  baseline (`0220`), current plugin light/frame/swapchain APIs (`0221`–`0223`),
  indirect-light API (`0224`), shape insertion/readiness (`0226`), and deferred
  async model source release (`0227`). The QEMU-only quality control was then
  regenerated against the current plugin API as `0228` from source commit
  `9ea29dd`; its patch SHA-256 is
  `198c5eeb65e1d8b21fa4503511ff4a3c0beddf086f674c9115965c884f8c4f4e`.
  The current model-release source commit
  is `b90e6ac`; its canonical patch SHA-256 is
  `c66b59f15c9ca0174f7cd8532f5e15f702699fb436d814b767419ef3267586aa`.
- Obsolete registrations were removed rather than force-applied: old parent
  0001/0003, stale plugin API patches 0015/0017/0027/0029/0035/0036/0042/
  0043/0045/0047/0049/0050/0051/0053/0054, the old SHM/readback branches,
  stale camera/light branches, and the fuzzing `0071` renderer probe.
- The intermediate failed `0225` patch artifact was removed; the final shape
  change is the corrected `0226` Devtool-generated patch.

## Inferences

- The first divergence is in the inherited `meta-flutter` patch baseline, not
  in the new explicit-light diagnostic or the runtime-debug packagegroup.
- A successful parse does not prove that the patch stack is applicable to the
  unpacked source tree.
- The observed Mac failure is a concrete source/patch preimage mismatch, not
  a missing runtime-debug package or a malformed 0211 patch.
- The eventual gate failure after source reconciliation was QA fuzz in old
  `0071`, not a patch hunk rejection; removing that obsolete diagnostic made
  the gate deterministic.
- The final qemux86-64-scoped gate also passed `flutter-auto:do_patch`, recipe
  QA, fetch, unpack, and all 104 tasks after `0228` replaced stale QEMU-only
  `0018`.

## Hypotheses

1. The unpacked `flutter-auto` source differs from the source baseline against
   which patch 0001 was authored.
2. The persistent `tmp/work` state or patch order selects a different source
   shape than the known-good build.
3. A recipe/layer override changes `SRC_URI` or source selection for the
   current feature revision.

## UNKNOWN

- Whether the authoritative Mini build has the same mismatch or only the Mac
  recipe gate did before the bundle is transferred.
- Whether the current-tip image contains the requested debug binaries; the
  prior exact FLR-0104 image proved the package contract, but this ticket did
  not build a new image.

## Out of scope

- Changing the 0113 light-contribution diagnostic.
- Modifying the runtime-debug packagegroup.
- Mini image build, QMP capture, and production 3D classification.
