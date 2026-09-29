# FLR-0202 — test opaque native swapchain composition

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Mini authoritative build + QEMU runtime roles
- Created: 2026-09-19
- Predecessor: [FLR-0201](FLR-0201-reproduce-known-good-native-fixture-stack.md)
- Working log: `work/logs/2026-09-19-flr0202.md`

## Work unit

Test whether the active transparent Filament swapchain prevents native 3D
pixels from reaching the final QMP parent frame, while the same 2D HUD remains
visible. This ticket changes one source-controlled variable only: an
environment-gated opaque swapchain configuration.

## Facts

- The current QMP frame displays the 2D HUD and `Scenes` button.
- The central QMP 3D ROI is uniformly black: 0 changed pixels in
  `[300,250,620,400]`.
- The native driver readback is non-zero in the candidate region:
  `nonzero_rgb=111758`, `nonzero_alpha=111758`, and
  `nonzero_rgb_zero_alpha=0`.
- `FLUORITE_NATIVE_FORCE_OPAQUE=1` changes only the Filament View blend mode
  and did not change the QMP frame or 3D ROI.
- The active 0223 source explicitly creates the swapchain with
  `filament::SwapChain::CONFIG_TRANSPARENT`.

## Hypotheses

1. H1: Vulkan/Wayland composite-alpha handling of the transparent swapchain
   suppresses the native child pixels in the final parent frame. Prediction:
   an opaque swapchain makes the QMP 3D ROI non-zero. Falsifier: the ROI stays
   black with otherwise identical runtime inputs.
2. H2: child-surface geometry, stacking, or commit metadata is independent of
   swapchain alpha. Prediction: the opaque swapchain A/B remains black. If so,
   the next ticket must inspect the Wayland child surface and parent-frame
   geometry rather than add more render changes.

## Success criteria

- [ ] Edit the existing fixed Mac Devtool source and commit the source change
  using the guarded official workflow; do not hand-edit a generated patch.
- [ ] Generate, register, and hash exactly one canonical layer patch for the
  opaque-swapchain switch.
- [ ] Pass Mac validation, bundle transfer, Mini `do_patch`, `do_compile`, and
  the authoritative image build in the fixed receiver/build/TMPDIR.
- [ ] Run exactly one QEMU instance with the established `fluorite` app-id and
  pure-fixture variables, capture QMP-only evidence, and compare the same HUD
  and 3D ROIs against FLR-0201.
- [ ] Stop the app and QEMU cleanly and record all hashes, results, and the
  next boundary. Do not claim 3D success unless the QMP ROI is non-zero.

## Plan / Do / Check / Act

### Plan

1. Revalidate the canonical repository, fixed Podman Devtool source status,
   and the current active patch registration.
2. Add only the environment-gated opaque swapchain selection to the existing
   ViewTarget source, preserving transparent behavior by default.
3. Generate the patch through official `devtool update-recipe`, register it
   unchanged, commit the layer, transfer a Git bundle, and run the Mini gates.
4. Capture driver and QMP pixels in one QEMU run with the same fixture and
   compare the exact ROIs.

### Do

The fixed Mac Podman Devtool source was edited at the existing
`fluorite-plugins` workspace and committed through the guarded source Git
operation as `417adbf2089f212b26e42183f1f4331c7b6be364`. The change is limited
to `plugins/filament_view/core/scene/view_target.cc`; the transparent
swapchain remains the default and `FLUORITE_NATIVE_OPAQUE_SWAPCHAIN` selects
the opaque configuration for the A/B.

Official `devtool update-recipe` generated one patch from that source commit.
The component handoff copied it unchanged to
`0264-diag-gate-native-swapchain-opacity-devtool.patch`, SHA-256
`84fd3d383ce68fc2647a691f03f51131b7b70dc2db7626604ce22ced9b6bcf1`.
The canonical SHA is checked separately below; the source patch itself is
registered once in `flutter-auto_2.0.bbappend` with
`patchdir=ivi-homescreen-plugins`, and the baseline lock was refreshed.

The current QEMU was shut down before this ticket was opened; no second QEMU
is allowed.

### Check

Mac source and handoff checks passed. Mini `do_patch`, `do_compile`, and the
11758-task `agl-ivi-image-flutter` build all passed. The new image was run in
one QEMU instance with the established `fluorite` app-id and the pure-fixture
variables plus `FLUORITE_NATIVE_OPAQUE_SWAPCHAIN=1`.

Runtime proved the variable was active: Vulkan reported
`FLR0026_VK_COMPOSITE_ALPHA transparent=false supported=0x3 selected=0x1`.
The driver readback remained non-zero (`nonzero_rgb=111758`,
`nonzero_alpha=111758`, `nonzero_rgb_zero_alpha=0`).

The QMP-only final frame retained visible 2D content with full-frame
`changed_pixels=7431`, `chromatic=2801`, and bounding box `[4,7,1252,193]`,
but the central 3D ROI `[300,250,620,400]` remained uniformly black
(`changed_pixels=0`, `edge_pixels=0`, `chromatic_pixels=0`, 248000 pixels).
The wide candidate `[300,80,620,360]` was also uniformly black. The final
frame SHA is
`b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
Three QMP frames were captured; frame 0 and frame 2 have the same SHA, so the
result is stable rather than a timing-only blank.

Receiver evidence is under
`evidence/FLR-0202/qemu-opaque-20260919/`, including `opaque-final.ppm`,
`opaque-frames/`, and `guest-journal.txt`. The guest journal SHA is
`995f101fc31b1b896ba4e069a5e6e10429c3025288a5273dc96100ae26e1d90f`.
QMP teardown returned `cleanup=PASS residual_targets=0 residual_qmp=0`, and
the QMP socket was absent.

### Act

QMP 3D remained black, so the opaque configuration is retained as a falsified
composition hypothesis, not as a production default. FLR-0203 owns the next
static/runtime comparison of Wayland child-surface geometry, stack, commit,
and damage. No additional rendering variable is combined into this ticket.

## UNKNOWN

- The first compositor owner after non-zero driver readback is not yet proven.
- It is UNKNOWN whether an opaque swapchain preserves the existing 2D HUD and
  whether it exposes the native pixels in the final parent frame.

## Completion decision

This ticket is complete as a one-variable A/B: swapchain composite alpha was
changed and verified in the runtime, but final QMP 3D visibility did not
change. The first missing boundary remains between non-zero native driver
pixels and the final parent-frame composition.
