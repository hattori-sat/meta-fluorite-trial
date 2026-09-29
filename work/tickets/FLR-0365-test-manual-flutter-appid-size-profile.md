# FLR-0365 — test manual Flutter app-id and size arguments

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / guest SSH / Flutter surface / QMP evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Predecessor: [FLR-0364 manual guest-SSH baseline](FLR-0364-reproduce-flutter-launch-over-guest-ssh.md)
- Historical control: [FLR-0347 exact-image HUD-visible run](FLR-0347-retest-empty-log-arm-poll-on-exact-image.md), [FLR-0344 launch command](../commands/FLR-0344-launch-production.cmd)
- Working log: [FLR-0365 working log](../logs/2026-09-29-flr0365.md)
- Run ID: `flr0365-0001` (one attempt only)

## Objective

On the same pinned QEMU rootfs as FLR-0364/FLR-0347, manually launch the same installed Example Demo over guest SSH and add only the historical Flutter shell app-id and explicit size arguments: `--xdg-shell-app-id fluorite --width 1280 --height 800`. Keep all renderer/scene diagnostic environment variables unset. Determine whether these command-line surface parameters restore the HUD and classify the native 3D pixels independently.

## Facts

- FLR-0364 used direct guest SSH and one agl-driver process on rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`. The app produced scene/light and Vulkan activity, but its QMP frame had no HUD, no chromatic pixels, and one unidentifiable monochrome polygon.
- FLR-0347 used the same FLR-0335 rootfs and showed HUD/metrics in QMP while the lower production 3D ROI was black. Its command included the app-id/size parameters plus diagnostic environment variables.
- FLR-0364's ordinary launch already set the Wayland session variables and used the same installed bundle. This ticket changes only the three related CLI surface parameters; it does not copy the full diagnostic environment profile.
- The existing Mini QEMU helper and image are pinned. No image build or bundle transfer is required for this command-only experiment.

## Problem stratification — 4W1H (Why excluded)

| Dimension | Evidence | Discriminator |
| --- | --- | --- |
| What | HUD absent on bare launch, present in the historical same-image profile | Add app-id/size arguments only and measure HUD ROI |
| Where | Flutter xdg-shell surface metadata and QMP framebuffer | Direct guest SSH launch with the same bundle/rootfs |
| When | After one fresh QEMU guest reaches SSH-ready | One fresh run ID; no reuse |
| Who | Mini QEMU, guest SSH session, agl-driver Flutter process | Verify one exact process identity |
| How | Preserve session variables, add only app-id and dimensions, capture QMP | No scene/light/debug environment overrides |

## Hypotheses

1. **Leading:** the app-id/size arguments are sufficient to restore HUD pixels on the same rootfs. Prediction: the prior HUD ROI becomes non-uniform and contains CPU/FPS/Scenes indicators.
2. **Alternative:** those arguments are insufficient; one or more historical diagnostic environment settings or another runtime-state difference explains the prior HUD. This run falsifies only sufficiency of the CLI arguments.
3. **Independent 3D hypothesis:** HUD restoration does not guarantee colored Sequoia pixels; native 3D may remain black, monochrome, partial, or become recognizable.

## Scope

### In scope

- One fresh QEMU run using the existing pinned image and helper.
- Direct guest SSH, read-only prelaunch process/bundle/Wayland checks, and one manual agl-driver launch.
- Same bundle and session variables as FLR-0364, adding only the historical app-id/size CLI arguments.
- Bounded app log, full-frame QMP still/eight-frame video, historical HUD/native ROI analysis, and safe teardown.

### Out of scope

- Running the Flutter staging/FIFO/GDB wrapper, editing any shell script, or changing QEMU automation.
- Diagnostic environment overrides, model/material/light/camera/texture changes, or source/recipe/image rebuilds.
- Copying QEMU disk images to Mac or retrying the consumed run ID.

## Success criteria

1. Pinned QEMU helper preflight and guest SSH pass; there are no pre-existing app/runtime targets or occupied ports.
2. Before launch, app count is zero and the installed bundle and Wayland socket exist.
3. Exactly one agl-driver process starts with the Example Demo bundle and the specified CLI arguments; no FLR/FLUORITE diagnostic overrides are present.
4. Save bounded startup/runtime evidence and a full post-launch QMP still plus eight-frame sequence.
5. Quantify the historical HUD ROI `[1120,0,160,80]` and the full frame. Confirm the actual CPU/FPS/Scenes indicators visually rather than counting geometry alone.
6. Report the native 3D ROI separately: identifiable geometry, chromatic pixel count, and any red-tail candidate. Do not call this production 2D+3D success unless both HUD and colored Sequoia are in the same frame.
7. Stop only the recorded app PID, quit QEMU through its QMP socket, and verify zero residual targets/sockets/ports.

## Impact

- **Build-time:** none.
- **Packaging:** none.
- **Runtime:** one manual app launch on the unchanged pinned image.
- **Integration risk:** low; no persistent product or harness change.

## Plan / Do / Check / Act

### Plan

- Use the proven direct-SSH path, not the failed app runner.
- Keep bundle, rootfs, Wayland variables, and all environment overrides fixed/empty relative to FLR-0364; add only the historical app-id and width/height arguments.
- Capture and classify the complete QMP frame and short video, then clean up.

### Do

- Pending. Do not edit the runner or add environment overrides in this ticket.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| QEMU/SSH preflight | Exact pinned image; guest SSH ready | Pending | PENDING |
| Prelaunch app/session | Zero app; bundle and Wayland present | Pending | PENDING |
| Manual CLI-parity launch | One agl-driver process; only CLI args differ | Pending | PENDING |
| QMP still/video and ROI | Full frame + 8 frames + measured HUD/native regions | Pending | PENDING |
| 2D HUD restored | CPU/FPS/Scenes visible in QMP | Pending | PENDING |
| Colored production 3D | Recognizable Sequoia with chromatic pixels | Pending | PENDING |
| Teardown | QMP quit and zero residual targets | Pending | PENDING |

### Act

- If app-id/size alone restores the HUD, carry that proven CLI contract into a separate minimal launch-script ticket. If not, the next ticket compares the remaining historical environment profile as a separately controlled runtime test. Do not infer a lighting/texture cause from a HUD result.

## Evidence

- Mini evidence root: `$EVIDENCE_ROOT/flr0365-0001/qemu`
- Post-launch QMP screenshot/video, raw log, ROI metrics, and hashes: pending.
