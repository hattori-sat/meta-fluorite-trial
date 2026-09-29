# FLR-0234 — repair pointer-motion parent repaint

- Status: Done (hover-overlay hypothesis falsified; follow-up FLR-0235)
- Priority: High
- Owner: Flutter parent-surface redraw and pointer-motion consumer roles
- Created: 2026-09-20
- Predecessor: FLR-0233

## Objective

Keep pointer motion enabled while preventing the Flutter parent/HUD from
becoming uniform white after the combined QMP motion sequence. Preserve the
native 3D pixels and prove stable 2D+3D output.

## Facts

- FLR-0233 confirmed that suppressing only pointer-motion delivery preserves
  the HUD (`2801` chromatic pixels), while native 3D remains `24178`.
- The diagnostic gate is not an acceptable product fix because it removes
  pointer motion.
- The QMP combined sequence maps to the top-right `Scenes` control: the HUD
  ROI is `[1120,0,160,80]`, the button content is `[1157,24,99,32]`, and the
  second motion lands at the button's vertical center.
- Static source tracing shows `Display::pointer_handle_motion` selecting
  `kHover` when no mouse button is pressed, `Engine::CoalesceMouseEvent`
  queueing the event, and `FlutterView::RunTasks` forwarding queued events to
  `FlutterEngineSendPointerEvent`.
- The control run commits new buffers on parent `wl_surface@14` immediately
  after `wl_pointer.motion`; the motion-skip run does not. The native child
  surface remains unchanged in both runs.
- The app source currently retains a `FilledButton` at the `Scenes` position.
  Its default hover overlay is therefore the smallest product-side boundary
  that can be changed without disabling pointer motion or changing native 3D.
- The official FLR-0234 image built successfully, but the transparent overlay
  change did not preserve the frame: the initial QMP frame had HUD `2801` and
  native `24178`, while the post-motion frames were uniform white with both
  ROI chromatic counts at `0`.
- The selected runtime log still shows native Vulkan present result `0`, native
  and parent Wayland commits, and clean app/QMP teardown. No app crash was
  observed.

## Hypotheses

| Rank | Hypothesis | Prediction | Discriminator |
| --- | --- | --- | --- |
| 1 | Flutter event processing after `CoalesceMouseEvent` invalidates or repaints the parent with an opaque white buffer | a parent-surface/frame correction preserves HUD while motion remains delivered | static consumer trace plus one minimal source correction |
| 2 | Wayland parent damage/import ordering is wrong when motion is delivered | a protocol-side correction preserves HUD without changing Flutter event delivery | selected attach/damage/frame markers and QMP A/B |
| 3 | The `Scenes` button's default hover overlay is the opaque repaint | transparent overlay preserves button geometry, pointer delivery, and native 3D | app-source A/B with the same QMP sequence |

## Plan / Do / Check / Act

### Plan

1. Trace the motion event from `CoalesceMouseEvent` to the parent-surface
   redraw/commit owner, using source and bounded runtime logs.
2. Choose one minimal product-safe correction that leaves pointer motion
   enabled and removes only the button hover state machinery.
3. Generate the patch through the Mac Devtool baseline, then Mini
   do_patch/do_compile/image and QMP A/B.

### Success criteria

- Pointer motion remains enabled in the tested image.
- HUD remains non-white through the combined `x → 4s hold → y` sequence.
- Native 3D remains at least `24178` chromatic pixels.
- QMP evidence proves stable 2D+3D output and clean teardown.
- No route, light, camera, or native geometry changes are mixed into this
  parent-repaint repair.

## Check

| Gate | Expected | Result |
| --- | --- | --- |
| Source history | official baseline → source commit → generated patch | PASS: source `cc28d2a`; patch SHA recorded in the working log |
| Mini recipe | metadata, workdir reset, do_patch | PASS |
| Mini compile/image | Flutter API compiles and image completes | PASS: 1674/1674 compile tasks and 11758/11758 image tasks succeeded |
| QMP initial frame | HUD and native 3D visible | PASS: HUD `2801`, native `24178` |
| QMP combined motion | HUD remains non-white and native ROI remains `24178` | FAIL: post-motion frame became uniform white; both measured ROIs were chromatic `0` |
| Runtime health | no crash and native present remains successful | PASS: present result `0`, selected Wayland commits, clean teardown |

## Conclusion

The `overlayColor: transparent` correction is not a product fix. It changes
the post-hover result from a white button ROI to a white full frame, while
pointer delivery remains enabled. Close this discriminator and continue with
[FLR-0235](FLR-0235-replace-material-hover-button.md), which will replace the
Material stateful button with a static clickable surface without changing the
route, camera, light, or native 3D code.

## Evidence

- Predecessor: [FLR-0233](FLR-0233-isolate-pointer-motion-repaint.md)
- Working log: [2026-09-20-flr0234.md](../logs/2026-09-20-flr0234.md)
- Follow-up: [FLR-0235](FLR-0235-replace-material-hover-button.md)
