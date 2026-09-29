# FLR-0200 — isolate native surface compositor visibility

- Status: Waiting
- Priority: High
- Owner: QEMU runtime + Wayland/native surface roles
- Created: 2026-09-16
- Predecessor: [FLR-0199](FLR-0199-isolate-wayland-native-surface-composition.md)
- Working log: `work/logs/2026-09-16-flr0200.md`

## Work unit

Explain why the native child surface has non-zero RGBA data in the exact 3D
candidate ROI while the paired QMP parent-frame ROI is uniformly black. Keep
the first pass diagnostic-only. Do not change Filament rendering, scene,
camera, light, swapchain, or blend behavior until the visible-pixel owner is
identified.

## Facts inherited

- FLR-0199 passed the deterministic Mac Devtool → bundle → Mini
  `do_patch`/`do_compile`/image → one QEMU → QMP capture loop.
- Driver ROI statistics reported non-zero RGB and alpha in
  `[300,250,620,400]`; the same QMP ROI was all black while the HUD was
  visible.
- Runtime proved native surface creation, present result `0`, and commit
  completion, but did not expose final child-surface geometry, scale, opaque
  region, input region, or compositor-layer visibility.

## Hypotheses

1. The native child surface is committed but positioned, scaled, stacked, or
   alpha-composited outside the visible QMP parent frame.
2. QMP captures only the Flutter parent surface and omits the native child
   surface's compositor path.
3. The runtime child-surface metadata is insufficient to establish visibility,
   so an independent compositor-side observation is required.

## Success criteria

- [ ] Collect bounded runtime evidence for child-surface attach, position,
  buffer scale, alpha/opaque/input regions, and stacking where available.
- [ ] Determine whether QMP includes the child surface, or record the exact
  limitation and select a reproducible compositor-side capture.
- [ ] Do not modify production composition behavior until one owner is
  identified.
- [ ] Preserve one-process and one-QEMU rules, save bounded evidence and
  hashes, and tear down with zero residual targets.

## Plan / Do / Check / Act

### Plan

1. Inspect the existing Wayland child-surface source and available runtime
   markers only.
2. Add the smallest diagnostic boundary needed through the existing
   deterministic Devtool flow if static evidence cannot answer the question.
3. Run one QMP/compositor observation and compare it with the driver ROI.

### Do

Static comparison found that the Filament `ViewTarget` child-surface path
creates the child and sets `place_above`/`desync`, but does not set position or
call `wl_surface_commit()` in the current source. The separate generic
`CompositorSurface` path does commit, so those paths must not be conflated.
Historical explicit-commit/flush A/B evidence kept QMP native pixels at zero;
therefore a missing explicit commit is not sufficient as a fix.

The current effective recipe/source was then checked against the older known-
good fixture. The current `flutter-auto_2.0.bbappend` does not register the
scene-deserializer pure-fixture patch (`0177`, `0209`, or `0235`), and the
current Mini unpacked `RunPostSetupLoad()` contains no
`FLUORITE_NATIVE_PURE_FIXTURE` branch. The current runtime variable therefore
does not establish the same pure-fixture condition used by the historical
test. FLR-0042 independently recorded a visible Filament cube through QMP at
1280x800 (`5608/100000`, bbox `[501,285,99,65]`), so QMP's inability to include
native child pixels is not a sufficient global explanation. The patch-stack
regression comparison is split to [FLR-0201](FLR-0201-reproduce-known-good-native-fixture-stack.md).

### Check

The driver ROI/QMP split is reproducible, but final compositor attach,
buffer-scale, alpha/opaque-region, stacking, and QMP child-surface inclusion
remain UNKNOWN. In addition, the current run is not proven equivalent to the
historical pure-fixture run because the effective scene-deserializer branch is
absent.

The Devtool source integrity gate also found two distinct states: `filament-vk`
has zero tracked deletions after restoring its 74 HEAD-tracked 0-byte
placeholders, while `fluorite-plugins` has 256 unstaged deletions of
non-empty HEAD files. The WSI target files remain present and clean. The latter
state must be resolved before the required `git add .` → source commit →
official Devtool update flow can be used deterministically; no source recovery
for those 256 files was performed here.

The 256 files were subsequently restored from the exact source HEAD inside
the fixed Podman container, with a pre-restore deletion-list SHA-256 of
`7d80abc6fcf315d143db896f926f3cf44b8d5c1246d0b964ee751f2428be5c35`. The
source worktree became clean. The only source change then made was
`wl_subsurface_set_position(subsurface_, left_, top_)` after
`wl_subsurface_place_above()`. Guarded source commit
`de45b3607e19202d15ffb237cb4598a61aef6f4d` and official `update-recipe`
produced a one-file, one-insertion patch with SHA-256
`a12da313225fff8223431e58a9b36fb1f06cd18801bb3fc48d4c492b7e07b57d`.
The unchanged canonical registration is `0262` after `0259`.

### Act

At the earlier patch-generation checkpoint, Mini `do_patch` verification was
pending. The resulting authoritative image has since been exercised in one
QEMU run and the runtime discriminator below is now recorded. Any production
composition change must still be a separate patch commit generated by Devtool
from the verified source baseline. No 3D-visible success claim is made.

## Runtime discriminator result — 2026-09-16

The exact same QEMU launch was inspected at both the driver readback boundary
and the final QMP frame. The effective runtime trace contains
`wl_subsurface.set_position(0,0)`, a valid native fixture contract
(`vertices=8`, `indices=36`), valid pipeline state, `index_count=36`, and
`vkQueuePresentKHR result=0`. Driver readback reports 82,992 non-zero RGB
pixels and 82,992 non-zero alpha pixels in ROI `(300,250,620,400)`, while the
QMP frame remains uniformly black in that ROI (`changed=0`, `nonzero=0`).

This falsifies “missing position is the sufficient fix” for the current black
screen and weakens “the fixture never rendered.” The leading boundary is now
between driver readback and final Wayland/QMP composition; the exact cause is
UNKNOWN. The driver extent was `1280x720` and the QMP frame was `1280x800`, so
surface-size composition is a concrete next check. Historical FLR-0042 QMP
evidence prevents treating QMP child omission as a global explanation.

The QEMU teardown completed through the exact run-directory QMP socket with
zero residual targets and zero residual QMP sockets. The first serial stop
attempt failed closed with `empty-serial-prompt`; no broad process kill was
used.

Evidence remains under the FLR-0200 receiver run directory:

- `qemu-0262-position/launch-readback-output.txt`
- `qemu-0262-position/runtime-slice-output.txt`
- `qemu-0262-position/qmp-after-readback.ppm`
- `qemu-0262-position/qmp-quit-output.txt`

Next action is the FLR-0201 historical/current patch-stack comparison and one
bounded A/B test selected from that comparison. No 3D-visible success claim is
made.

## Source-integrity clarification

The approved `filament-vk` restoration refers to 74 HEAD-tracked regular files
whose exact HEAD blobs have size zero. “Empty” describes their recorded blob
size; it does not mean an accidental untracked file or an empty source tree.
The fixed-container check now reports exactly 74 such HEAD blobs and a clean
worktree. The separate `fluorite-plugins` tree reports zero zero-byte HEAD
blobs and a clean worktree after all 256 deleted non-empty HEAD paths were
restored.

The recovery is deterministic: enumerate porcelain status, resolve tracked
deletions against the exact source HEAD, restore only the approved paths,
verify clean status, then perform the guarded `git add .` → source commit →
official Devtool update flow. No filename-based inference or hand-authored
patch body is used.
