# FLR-0386 — replay the known LIT fixture on the FLR-0385 image

- Status: Waiting
- Priority: High
- Owner: Mini QEMU / manual guest Flutter / LIT fixture / QMP evidence roles
- Created: 2026-10-01
- Predecessor: [FLR-0385 Sequoia LIT material](FLR-0385-apply-lit-material-to-sequoia.md)
- Historical positive control: [FLR-0369 LIT constant-color fixture](FLR-0369-lit-hardcoded-material-control.md)
- Candidate rootfs SHA-256: `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`
- Mini receiver tip: `fe92b7760deaf9feb2e09b5370565be7798b4eca`
- Branch: `feature-flr-0386-current-image-lit-fixture-control` (local; inherited from the FLR-0385 candidate; no push)
- Implementation plan: [FLR-0386 plan](../../docs/superpowers/plans/2026-10-01-flr0386-current-image-lit-fixture-control.md)
- Working log: [FLR-0386 working log](../logs/2026-10-01-flr0386.md)

## Objective as opened

Determine whether the `FEngine::loop` / unmatched-present fault seen while
testing Sequoia on the FLR-0385 candidate is shared by the current image's
known LIT fixture or specific to the production Sequoia scene/asset path. The
ticket as opened referred to FLR-0369's constant-color LIT fixture. Later plan
text drifted to FLR-0371's parameterized material without reconciling the
original objective; the attempted command also selected the hardcoded branch.
The runtime attempt omitted fixture-selection flags, so it tested neither
fixture. [FLR-0387](FLR-0387-replay-parameterized-lit-on-current-image.md) is
the valid follow-up for the parameterized LIT/RGB path that patch 0332 uses.

This is a diagnostic control only. It does not prove production Sequoia or
overall Fluorite acceptance.

## Result classification

The one runtime attempt is closed, but it was **not a valid LIT fixture
replay**. It omitted the fixture-selection, geometry, camera, and force-render
environment variables required by the historical profile. It also enabled
`FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR`, which does not match the
parameterized LIT/RGB material used by FLR-0371 and patch 0332. The ordinary
Example Demo startup reproduced a present/Oops signature, but that result
cannot classify either material path. FLR-0387 owns the corrected
parameterized replay; do not retry under this ticket.

## Facts

- FLR-0369 used rootfs `5c8ca252…`. Its LIT constant-color fixture showed
  `119716/144000` chromatic native pixels and `2845` chromatic HUD pixels;
  242 successful present-boundary completions were recorded.
- FLR-0371 showed the parameterized LIT/RGB fixture with HUD on a different
  rootfs (`949921c…`), with 146 successful presents.
- FLR-0385 A4 uses rootfs `ff0f801c…`: Sequoia material reached
  `READY=1`/`BOUND=24`, but the second Vulkan present had no recorded return;
  a kernel Oops in `FEngine::loop` occurred before the material-ready marker.
  A live QMP frame showed the HUD and a black Sequoia ROI. A4 is not a healthy
  material-only negative.
- The FLR-0385 image includes patch 0332, but this run left Sequoia overrides
  and model selectors unset. No source/build change was made.
- The actual FLR-0286/0367 functional fixture profile also requires
  `FLUORITE_NATIVE_PURE_FIXTURE=1`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`,
  `FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1`, and
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`. This run set only fixture light
  and hardcoded color. Thus the fixture was not selected, and the selected
  material branch also differed from the parameterized FLR-0371/patch-0332
  path. Zero fixture markers do not mean a correctly selected fixture failed.
- Ordinary startup logged two present begins and one successful result, then
  a user-mode page-fault Oops in `FEngine::loop`; the Flutter process exited.
  This signature overlaps historical records but is not evidence about the
  LIT fixture.
- FLR-0366, FLR-0308, and FLR-0333 contain related FEngine/present records.
  They establish historical recurrence, not root cause.

## Ranked hypotheses

1. **Shared current-image startup/present failure.** The incomplete launch
   reproduced a two-enter/one-return sequence and `FEngine::loop` Oops. This is
   an ordinary-app observation only; fixture specificity remains UNKNOWN.
2. **Correct fixture works on the candidate.** UNKNOWN because required
   fixture-selection and geometry flags were omitted.
3. **Correct fixture reaches draw/present but loses pixels.** UNKNOWN; no
   fixture setup or draw-end markers were observed.

## Scope

### In scope

- One run on the exact FLR-0385 rootfs, kernel, qemuboot profile, and fixed Mini
  build/TMPDIR.
- One manual `agl-driver` launch of Example Demo 3.32.5 using the complete
  FLR-0286/0367 functional fixture profile: pure fixture, minimal geometry,
  local camera, fixture light, and force-render-on-skipped-frame. This scope
  was intended to use the parameterized material branch, but the ticket's
  original FLR-0369 constant-color objective was not reconciled before launch.
  FLR-0387 now owns the consistent parameterized profile.
- Full-frame QMP still and eight-frame video with the same PID/UID/start-time
  verified immediately before and after capture; bounded present/Oops/core
  summary; exact teardown.

### Out of scope

- Source/recipe/patch edits, Devtool, bundle transfer, BitBake, image rebuild,
  cache cleanup, camera/light/texture changes, Sequoia override, route changes,
  or general launcher-script edits.
- Claiming fixture visibility as production Sequoia success.
- Copying raw PPM or QEMU images to Mac; raw QMP evidence stays on Mini.

## Success criteria

1. The single QEMU run is attributable to the exact rootfs
   `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`,
   uses the fixed 6144 MiB profile/ports, and has no pre-existing target
   processes.
2. Exactly one manual `flutter-auto` process runs as UID 1001. The LIT fixture
   and its SUN are enabled; Sequoia override, production SUN, and model selector
   are unset.
3. Record setup, draw/render, present counts, and bounded kernel/coredump
   status. Preserve only concise diagnostic excerpts on Mini, not the complete
   multi-megabyte guest log.
4. Capture and visually inspect a complete 1280×800 QMP still plus eight QMP
   frames. Report native ROI `(440,220,400,360)` and HUD ROI
   `(1120,0,160,80)` separately. A positive fixture control requires visible
   chromatic native geometry and HUD in the same liveness-bracketed frame plus
   at least eight successful present returns and no matching Oops during the
   capture interval.
5. If a matching Oops/unmatched present occurs before that gate, stop this
   bounded run, record it as a red result, and do not retry the same profile or
   run a SUN/material variant in this ticket.
6. Stop only the recorded app and QEMU; verify no run-owned Flutter/QEMU,
   QMP-socket, or forwarded-port residual remains.

## Plan / Do / Check / Act

### Plan

- Reuse the exact FLR-0385 candidate image and established Mini runtime
  harness; create only the one run-specific evidence directory
  `$BUILD_EVIDENCE/flr0386-0001/qemu`.
- Use the FLR-0369 historical fixture profile and manual launch path. Change
  no product/source/build inputs.
- Capture at first fixture readiness or by 45 seconds, whichever comes first;
  keep the app bound to a 60-second maximum and stop immediately after the
  decisive capture or first fault.

### Do

- Ticket/plan/log were created before the run; no source, layer, build, or
  image state changed.
- The command mistakenly omitted `PURE_FIXTURE`, `MINIMAL_GEOMETRY`,
  `FIXTURE_LOCAL_CAMERA`, and `FORCE_RENDER_ON_SKIPPED_FRAME`. The bounded
  readiness probe also used top-level `exit`, closing the serial login shell;
  `serial-exec` therefore did not receive its completion marker. Its saved
  output still contains the `READY=NO` counts and kernel Oops excerpt.
- The one app launched as PID 648 / UID 1001 / start token 30567, then exited
  after two present begins and one return. No fixture setup markers appeared.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Candidate identity/preflight | Exact FLR-0385 image, one QEMU, no stale app | Kernel/rootfs/qemuboot hashes matched; guest preflight passed; one QEMU, ports free | PASS |
| Fixture runtime | Full FLR-0286 functional flags and parameterized LIT setup | Only fixture-light and hardcoded-color flags were set; four required selection/render flags were omitted; fixture markers 0 | FAIL — invalid profile |
| Present/fault boundary | Bounded present sequence or exact first fault | 2 begins, 1 `result=0`, second return absent; `FEngine::loop` user-mode page-fault Oops; app PID 648 exited | FAULT — ordinary startup only |
| QMP pixels | Fixture geometry and HUD visible in one liveness-bracketed frame | Post-Oops full frame black; native and HUD ROIs both 0; capture was not PID-bracketed | NOT A FIXTURE VERDICT |
| Fault/core evidence | Bounded Oops/coredump evidence captured | Selected Oops block and empty bounded coredump listing retained | PASS — evidence only |
| Teardown | Exact app/QMP stopped; processes/socket/ports absent | App/wrapper already absent; QMP quit and postflight passed; image hashes unchanged | PASS |

### Act

- Close this attempt as an invalid fixture procedure, not a material result.
  The Oops observation is ordinary-app startup evidence and overlaps known
  history.
- A separate follow-up ticket is required for the corrected one-run replay
  with every required behavior flag and the parameterized LIT material. Do not
  change patch 0332, camera, asset, or production lighting before that valid
  control.

## Visual evidence

The following PNG/MP4 are post-Oops captures and are not fixture evidence. The
predecessor A4 live frame is linked in [FLR-0385](FLR-0385-apply-lit-material-to-sequoia.md).

![FLR-0386 post-Oops QMP frame; screen black, no fixture verdict](../evidence/FLR-0386-0001/qmp-post-oops.png)

[Eight-frame post-Oops QMP video](../evidence/FLR-0386-0001/qmp-post-oops.mp4).

## UNKNOWN

- Whether the FLR-0385 candidate runs the correctly selected known LIT fixture
  without the production Sequoia path.
- Whether any A4 Oops is causal to the black Sequoia ROI or merely correlated.
