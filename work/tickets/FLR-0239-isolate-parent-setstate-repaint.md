# FLR-0239 — isolate parent setState from the repaint boundary

- Status: Done
- Priority: High
- Owner: Flutter parent-composition and repaint roles
- Created: 2026-09-20
- Predecessor: FLR-0238

## Objective

Determine whether the white post-Scenes frame requires the parent
`setState` call itself. Compare the FLR-0238 marker-only control with an
otherwise identical callback that records the tap but does not call
`setState`. Keep the native 3D fixture, QMP-only evidence contract, and Mini
build flow unchanged.

## Facts

- FLR-0235 proves the static clickable surface can show the 2D HUD and the
  self-made native 3D cube simultaneously.
- FLR-0236 proves the Scenes callback reaches the Planetarium activation path.
- FLR-0237 removed the route's full-surface gesture build, but the post-tap
  HUD still became uniform white.
- FLR-0238 replaced route activation with a marker-only callback and
  `setState(() {})`; the post-tap HUD still became uniform white while the
  native ROI remained `24178` chromatic pixels.
- FLR-0239 removed only the parent `setState` call while preserving the same
  clickable surface and marker. Initial, motion, down, and up QMP frames all
  retained HUD `2845` and native ROI `24178` chromatic pixels.
- The bounded guest marker was
  `FLR0239_SCENE_TAP_NO_SETSTATE id=3 name=Planetarium`; pointer button down
  and up were recorded in the same runtime slice.
- The FLR-0239 Mini image completed with `IMAGE_RC=0` after 11,758 tasks; the
  rootfs was
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260920135809.ext4` with SHA-256
  `099c7ca71cb80f21bf89cff079b1a517f73c2e86bd60061534922360d7268af4`.
- The qemuboot SHA-256 was
  `8148a5560864440d592ad191a59bfee023ad1ed9abe28c079876151ad8532509` and
  the kernel SHA-256 remained
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Calling parent `setState` is sufficient to trigger the white repaint | no-`setState` callback retains HUD `2845`; FLR-0238 control becomes white | scene state cannot yet be changed through the parent path |
| 2 | Pointer/tap handling or a lower embedder repaint is sufficient | no-`setState` callback also becomes white | requires a Flutter/Wayland repaint-boundary probe |
| 3 | The marker callback's timing or logging causes a secondary effect | a minimal no-op callback differs from the marker-only control | timing evidence must stay bounded and comparable |

The first experiment removes only the parent `setState` call. It is the
smallest discriminator before designing an imperative scene-update path that
does not repaint the parent surface.

## Result

The no-`setState` callback preserved the HUD and native fixture through the
same QMP tap sequence. The parent `setState` call is therefore the immediate
trigger for the white composition failure; pointer delivery alone is not
sufficient. This ticket does not yet activate the Planetarium widget. FLR-0240
owns the child-only scene-subtree transition.

## Verification

- Mac source commit: `9a38c2ac41e64eea2b936985dc630005d001fa48`.
- Canonical patch:
  `0071-flr0239-isolate-no-setState-tap-devtool.patch`.
- Canonical patch SHA-256:
  `e310e7db9c25069acdeec2cdba089aceb5b925d3b6a982ec55b1201492251837`.
- Canonical layer commit: `8a3c9ed`.
- Mini bundle SHA-256:
  `7b01ee65c3ebcc3f29a4f88f2e1088af64424b660acbc5bfff1fb238f1be6c78`.
- Mini `do_patch`, compile, and image gates passed for the exact bundle tip.
- QMP evidence: `$EVIDENCE_ROOT/FLR-0239/qmp-no-setstate/` and
  `$EVIDENCE_ROOT/FLR-0239/pixel-analysis.jsonl`.
- Bounded runtime evidence:
  `$EVIDENCE_ROOT/FLR-0239/app-runtime-no-setstate.raw` and
  `$EVIDENCE_ROOT/FLR-0239/app-marker-no-setstate.out`.
- Runtime and marker SHA-256 values:
  `0442744d07e20fa40780c4eeed3e33f588e13d0898dc082ccf1b980e3f8f65ee` and
  `619684528ff805ddb54a3ddaa065060e486dc6004b3c61eac71c0f532c7a1543`.
- QMP quit and cleanup passed with zero residual target processes and no QMP
  socket.

## Success criteria

- The source change is generated through the official Mac Devtool flow from
  the FLR-0238 effective source commit.
- Mini `do_patch`, compile, and full image gates pass for the exact bundle tip.
- QMP initial and post-tap frames quantify HUD and native ROI with the same
  coordinates and thresholds as FLR-0238.
- Guest marker/log, artifact hashes, and clean QEMU teardown are retained.
- The result explicitly selects the next implementation boundary without
  changing native fixture, camera, light, or material code.

## Evidence

- Predecessor: [FLR-0238](FLR-0238-isolate-route-state-mount-repaint.md)
- Working log: [2026-09-20-flr0239.md](../logs/2026-09-20-flr0239.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0239/`

## UNKNOWN

- Whether an isolated scene-subtree update preserves the HUD while mounting
  the actual Planetarium widget.
- Whether scene selection can be updated without rebuilding the parent
  `Stack`.
- Whether Planetarium's native callbacks are needed after the composition
  boundary is repaired.
