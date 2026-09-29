# FLR-0363 — fix FLR-0350 guest-script staging and capture the actual runtime

- Status: In Progress
- Priority: High
- Owner: Mac runner / Mini runtime / QMP evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Predecessor: [FLR-0362 FIFO/attach gate](FLR-0362-align-fifo-gate-with-shell-read-fd.md)
- Plan: [implementation plan](../../docs/superpowers/plans/2026-09-29-flr0363-fix-flr0350-guest-script-stage.md)
- Working log: [FLR-0363 working log](../logs/2026-09-29-flr0363.md)
- Historical procedure: [FLR-0116 production launch](../logs/2026-09-13-flr0116.md), [FLR-0235 HUD + native fixture](FLR-0235-replace-material-hover-button.md), [FLR-0286 lit fixture + HUD](FLR-0286-reproduce-known-good-combined-sequoia-hud.md)
- Run ID: `flr0363-0001` (fresh; use at most once)

## Objective

Fix the first actionable failure in the exact FLR-0350 run path so it can reach a real `agl-driver`-owned Flutter launch, then produce attributable post-launch QMP evidence. The goal of this ticket is a valid runtime observation, not a claim that product Sequoia lighting is repaired.

## Current state and failure point

- FLR-0362 run `flr0362-0001` passed bundle/receiver/TOPDIR/TMPDIR, runner static checks, pinned-image preflight, QEMU start, and guest-ready.
- First divergence was the first guest `.sh` chunk stage. The runner creates `install_file=$run_dir/install-guest-script-$chunk_index.cmd` but passes `"$install-guest-script-$chunk_index.cmd"`; in Bash this expands `$install` (the command body), not the prepared filename. Mini serial evidence reported `command-file-not-readable`.
- `launch.serial.log`, GO, app runtime log, and post-launch QMP capture were absent. QMP quit and cleanup passed with zero residual targets/sockets. `flr0362-0001` is consumed and will never be retried.
- Therefore the black QMP frame was pre-launch only. Whether Flutter displayed 2D or 3D in that run is UNKNOWN; it is not evidence of a product regression.

## Historical evidence and correct runtime contract

- FLR-0116's successful production launch used exactly one `agl-driver`-owned `flutter-auto`, verified Vulkan/Flutter library loading and guest scene/frame log markers, then inspected a post-launch QMP frame. HUD was visible while the corrected 3D ROI was black.
- FLR-0235 proves same-frame HUD plus a self-made native 3D cube. FLR-0286 proves a self-made lit Filament fixture plus HUD. Those are positive controls, not production Sequoia success.
- The current runner explicitly switches to `agl-driver`; its GO helper verifies same PID/start, `comm=flutter-auto`, `/usr/bin/flutter-auto`, and the expected UID. The later bounded runtime-state command and `capture_evidence` are only meaningful after those launch/GO gates pass.
- The FLR-0350 profile contains diagnostic overrides. Results must be labeled profile-specific and not generalized to neutral production.

## Problem stratification — 4W1H (Why excluded)

| Dimension | Evidence | Next discriminator |
| --- | --- | --- |
| What | Guest helper command file cannot be read by the serial runner | Use the prepared `install_file` and prove exact file handoff |
| Where | `work/commands/FLR-0350-run-sync-producer.sh`, first guest-script chunk `guest_run` call | Focused regression plus one Mini serial stage |
| When | `flr0362-0001`, after QEMU/guest-ready and before `launch.serial.log` | Fresh `flr0363-0001` after exact-bundle handoff |
| Who | Mac runner creates/stages the file; Mini serial adapter consumes it; guest app launch is a later owner | Preserve each boundary and marker |
| How | `$install` is the generated command body, but the call-site expression accidentally interpolates it into a purported filename | Assert `"$install_file"` exactly; then verify guest helper SHA and launch logs |

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| Runner passes the command body instead of the stage filename | Existing test is red; Mini says command file unreadable before app launch | Test exact call-site argument; after fix, normal runner stages first `.sh` chunk and emits its PASS marker | Source/log match; focused regression observed red in preliminary probe; repeat the authoritative red on this feature branch | FLR-0362 working log and Mini runner evidence |
| `flutter-auto` starts but produces a black screen | Requires `launch.serial.log`, GO/EXEC, app log, then post-launch QMP | Those artifacts are absent in `flr0362-0001` | NOT TESTED; cannot explain the earlier staging failure | FLR-0362 artifact-presence audit |

### Confirmed root cause

Host-side Bash argument expansion in the guest-helper staging call passes the wrong path. The product renderer has not been exercised by this run.

### Minimal countermeasure

Use the already computed `install_file` path, backed by a test that fails on the malformed expression. No guest payload, image, product code, FIFO policy, or GDB predicate changes.

## Scope

### In scope

- One runner call-site correction and a focused static regression.
- Existing exact-bundle transfer and one fresh Mini run on the pinned image.
- Verify user switch, process identity, GO/exec, bounded app startup/render/fault logs, QMP post-launch still/eight-frame sequence, and cleanup.

### Out of scope

- Flutter/Filament/Yocto recipe or image edits, BitBake/Devtool, lighting/camera/material changes, or bypassing the GDB/FIFO gate.
- Treating QEMU boot or the pre-launch black frame as an app/render result.
- Reusing `flr0362-0001`, launching a second QEMU, copying VM images to Mac, or deleting caches.

## Success criteria

1. A concise regression fails on the current malformed call and passes when the runner passes `"$install_file"`.
2. Mac runner `--check` passes the full static suite once; shell syntax, privacy, file-size, checkpoint, and diff checks pass. Any known baseline Markdown failures are recorded separately.
3. The exact Mini bundle and pinned image identities pass; the normal runtime runner executes its static suite once and invokes one fresh run ID.
4. Guest logs prove one `agl-driver` launch, same-PID `/usr/bin/flutter-auto` exec with expected UID, GO, and relevant scene/frame/present or explicit startup/fault markers. Preserve bounded app log output and hash before teardown.
5. QMP-only full-frame post-launch still and eight frames are captured after app execution. Visually inspect the full screen and record HUD CPU/FPS/Scenes plus native 3D geometry/color separately; simultaneous visibility is credited only when both appear in the same frame.
6. The result is labeled diagnostic-profile-specific. A black 3D ROI after proven app/frame activity opens the next renderer ticket; this ticket does not claim to fix Sequoia or lighting.
7. QMP quit, run-owned app stop, and residual counts pass. Any earlier failure is retained as the exact first divergence; no retry of the run ID.

## Impact

- **Build-time:** none; no BitBake tasks or image artifacts invalidated.
- **Packaging:** none; no recipe/package changes.
- **Runtime:** only the harness path used to stage diagnostic guest commands changes; the pinned QEMU image and diagnostic environment remain unchanged.
- **Integration risk:** low and isolated to a Bash argument plus a regression test. The Mini serial handoff remains the decisive integration check.

## Hypotheses and UNKNOWN

1. **Confirmed:** the stage path interpolation is wrong; a focused test will reject it.
2. **Open:** once staged, FIFO observation, GDB attach, GO, and same-PID exec may pass or stop at a later named boundary.
3. **Open:** post-launch HUD and 3D may be visible, partial, or black under this diagnostic profile.

### UNKNOWN

- Whether the fixed runner reaches Flutter startup and produces scene/frame logs on the pinned Mini image.
- Whether this diagnostic profile yields any recognizable native 3D pixels alongside the HUD.
- Whether neutral production Sequoia lighting/color reproduces; this ticket cannot settle it.

## PDCA

### Plan

- See the linked implementation plan. Keep the investigation tied to actual post-launch evidence, not QEMU readiness alone.

### Do

- Read FLR-0116, FLR-0235, FLR-0286 and the current runner/logs. Astra's judgment-only recommendation was to repair the confirmed stage typo before switching profiles.
- A preliminary local regression probe failed as expected; its first assertion printed the whole runner, so it was made concise. A temporary one-line edit was not accepted as verified and was removed before ticket-branch separation. Repeat the red test and correction on the feature branch.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Current-run launch evidence | App/GO/runtime logs present | All absent in `flr0362-0001` | FLR-0362 addendum | NOT REACHED |
| Regression and path correction | Red before, green after | Authoritative ticket-branch run pending | This ticket's working log | PENDING |
| Mini app + QMP render observation | Same-PID app, bounded logs, post-launch still/video | Pending one fresh run | This ticket's working log/evidence | PENDING |

### Act

- Fix only the file argument, then perform one bundle-backed run. Use its app log and full QMP screenshot to decide the next renderer boundary.

## Visual evidence

- Pre-launch control only: `$EVIDENCE_ROOT/flr0362-0001/qemu/pre-launch.ppm`, SHA-256 `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`; it is not a Flutter frame.
- FLR-0363 post-launch still/video: pending; record Mini role path, local review link, dimensions, pixel metrics, and hashes after capture.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings:
