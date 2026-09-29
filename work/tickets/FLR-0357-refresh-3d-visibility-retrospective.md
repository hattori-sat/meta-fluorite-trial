# FLR-0357 — refresh the Fluorite 3D visibility retrospective

- Status: Done
- Priority: High
- Owner: runtime evidence synthesis / production rendering / QMP acceptance roles
- Created: 2026-09-29
- Depends on: [FLR-0356](FLR-0356-stage-fifo-observer-before-qemu.md)
- Updates: [FLR-0345](FLR-0345-retrospective-3d-visibility-checklist.md), [FLR-0349](FLR-0349-audit-3d-countermeasure-effectiveness.md)
- Plan: [FLR-0357 plan](../../docs/superpowers/plans/2026-09-29-flr0357-refresh-3d-retrospective.md)
- Working log: [FLR-0357 log](../logs/2026-09-29-flr0357.md)
- Branch: `feature-flr-0357-3d-retrospective-checklist` (depends on FLR-0356 commit `d740424`)

## Purpose

Refresh the existing evidence-indexed retrospectives after the FLR-0356 Mini
run. Put the important 2D, fixture, historical Sequoia, production, and
workflow observations beside the interventions that produced them. The aim is
to choose the next smallest test from evidence, not to restart the discussion
or conflate a black pre-GO screen with a renderer failure.

## Acceptance contract

Fluorite is not accepted until one attributable QMP full frame shows the
production Sequoia geometry and the Flutter HUD/metrics together, with
recognizable non-grayscale vehicle pixels in the fixed native region and
repeatable clean teardown. A fixture, texture atlas, draw marker, successful
build, or screen captured before the production wrapper receives GO does not
meet this condition.

## Current capability checklist

| Capability or question | Evidence | Status | What it establishes / does not establish |
| --- | --- | --- | --- |
| Flutter 2D HUD and metrics | FLR-0347/0348 QMP full frames | PASS | HUD, CPU/GPU/FPS and Scenes pixels reach QMP; not a 3D pass |
| Self-made native 3D plus HUD | FLR-0271, FLR-0286, FLR-0349 | PASS — fixture only | Same-frame chromatic Filament geometry and HUD disprove a universal QMP/Wayland composition failure; not production Sequoia |
| Sequoia plus HUD in historical diagnostic runs | FLR-0066 / FLR-0070 p9 summaries in FLR-0345/0349 | Historical candidate, not repeatable | Recorded native candidates were `3290/223200` and `5510/223200`; p9 raw frame is unavailable at the documented location, and later replays did not reproduce it |
| Lighted Sequoia without the HUD | FLR-0049 historical visual reference | 3D-only reference | The native surface masked the HUD; it does not satisfy the combined acceptance contract |
| Current production Sequoia with HUD after GO | FLR-0347/0348 | FAIL on those post-GO runs | HUD visible; fixed lower ROI was `768000/768000` black. This is the latest actual post-GO production pixel evidence |
| Current FLR-0356 observer run | [FLR-0356](FLR-0356-stage-fifo-observer-before-qemu.md) | Runtime gate reached, host validation failed | Observer data matched the launched wrapper and run-owned FIFO, but serial framing caused `marker-not-first`; GDB/GO were not reached, so its black QMP image is not a renderer result |
| Whether removing HUD reveals Sequoia on the exact current image | No matched HUD-off run | UNKNOWN | Neither hidden-behind-HUD nor no-HUD production visibility is established |
| Whether a source/image regression explains historical versus current output | Historical and current identities/profiles are not a matched A/B | Plausible, not proven | Do not dismiss regression or claim it is confirmed |

The supplied Photo 1 is the static Sequoia GLB `HeadLights_Emission` texture
atlas (classified in FLR-0321/0323 and carried by FLR-0345/0349). It proves
that red texture data exists; it is not a runtime frame and does not prove
texture sampling, lighting, or visible vehicle pixels.

## Countermeasure and effect checklist

| Boundary / symptom | Intervention or control | Measured effect | Verdict |
| --- | --- | --- | --- |
| General 2D/3D composition | Self-made Filament fixture alongside HUD (FLR-0271/0286) | FLR-0286 lit fixture: `119716/144000` chromatic native pixels with `2845` HUD pixels | Positive fixture control; global compositor-impossibility theory falsified |
| Readback-mode black output | Same-image SHM-only control versus readback mode (FLR-0268/0349) | SHM fixture+HUD visible; tested readback-mode case black | Limited readback-mode regression demonstrated; not a general 3D/compositor failure |
| HUD repaint during pointer motion | Static clickable surface (FLR-0235) | HUD stayed at `2845` chromatic pixels and fixture at `24178` through tested motion | Effective for that UI repaint regression; not a Sequoia fix |
| Production camera/framing | Effective camera selection (FLR-0274) | Camera changed to local Playground view; production QMP remained zero-chroma | Camera change took effect but was insufficient |
| Production light/material/texture | Light, emissive, PaintColor, texture-ready/binding and unlit/magenta probes (FLR-0305, FLR-0314–0324, FLR-0334/0337) | Several code/resource markers became positive; production ROI remained zero; string-comparison bug was fixed without visible Sequoia pixels | Some defects/observability gaps fixed; missing texture file or light alone is not established as the root cause |
| Lavapipe Present wait | Two-predicate GDB watch (FLR-0348) | Both watches armed; neither changed in 8.07 seconds; fields stayed false/null; QMP HUD-only | Diagnostic boundary measured, no product behavior change or causal proof |
| FIFO observer descriptor contract | Object-identity parser and launch cleanup (FLR-0354) | Deterministic tests passed for actual FD and FIFO object checks | Harness correctness improved; no rendering result |
| Fresh run ID and receiver identity | FLR-0355/0351 handoff checks | Exact receiver/bundle and pinned artifact checks can pass; FLR-0355 still stopped before observer because the staging list omitted its command | Handoff/identity improved; FLR-0355 black QMP frame was not a renderer test |
| Guest command staging | One inventory, callsite-coverage regression, and pre-start staging (FLR-0356) | 28 tests pass; Mini staged all 11 commands before QEMU; actual observer ran and target/gate FIFO device+inode matched | Staging defect fixed and exercised; exposed a separate serial receive-buffer framing defect |
| QMP capture and cleanup | Full still, eight one-second frames, pixel analysis, targeted teardown (FLR-0356) | Black still and eight byte-identical frames before GO; zero target processes/QMP socket after cleanup | Evidence/cleanup controls passed; no post-GO product conclusion |

## Latest first divergence and next decision

In FLR-0356 the target emitted a complete observation whose PID/start time/UID/
command matched the paused wrapper, whose syscall was `read`, and whose target
FIFO device/inode matched the run-owned gate. The runner then rejected the
serial file as `marker-not-first`. The file contains the prior `stty -echo`
response and prompt before the marker. Source inspection found that
`serial-exec` clears its buffer before echo-off but retains the echo-off
response while collecting the requested command; the parser correctly insists
that the marker be the first token. No parser or product change was attempted.

Two repair paths were considered:

1. **Selected: establish an explicit echo-off completion/prompt boundary,
   consume only that completed setup response, then start a fresh capture for
   the requested command.** This keeps the strict identity parser unchanged
   and addresses the first proven divergence at the serial-helper boundary.
   The regression must prove the observer marker is unique and begins the new
   capture; an unverified blanket discard is not sufficient.
2. **Rejected for now: relax the marker parser to accept an arbitrary prompt
   prefix.** This could turn stale bytes or unrelated terminal output into an
   accepted observation and would weaken the exact framing contract before the
   helper is corrected.

[FLR-0358](FLR-0358-clear-serial-buffer-before-command.md) owns the selected
serial-helper repair and its one fresh runtime attempt. Only after that gate
passes should the paused wrapper receive GDB attach/GO. Then capture QMP full
frame/eight-frame pixels to decide whether to continue along producer/Present,
production scene/material, or surface-composition boundaries. Do not mix a
HUD-off, camera, Light, or texture change into that gate.

## Visual evidence

FLR-0356's QMP-only frame is attached for review. It was captured before GO and
is uniformly black; it is a harness/gate artifact, not evidence that Flutter
or Filament rendered black after release.

![FLR-0356 Mini QMP full frame before GO](../evidence/FLR-0356-qmp-pre-go-black.png)

The eight-frame H.264 review copy remains outside Git in the single per-run Mac
review directory: 1280×800, 1 fps, eight frames / eight seconds, SHA-256
`82e5f5a0490e7354ff44f6105d4eb6c17c31e16c51e064e33648f0a7d42df2e4`. No
kernel/rootfs/QEMU disk image is copied to the Mac.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- 2D HUD pixels and same-frame HUD plus self-made native 3D pixels have been
  observed by QMP.
- Production Sequoia with HUD was visible in historical diagnostic records,
  but that observation was not stable or repeated on a matched current
  source/image/profile. The raw FLR-0070 p9 frame is unavailable at its
  documented evidence location.
- On later post-GO production runs, HUD was visible while the fixed 3D ROI was
  black. FLR-0356 did not reach GO and must not be counted as another production
  rendering failure.
- Camera, light, material, texture-binding, and emissive probes have not
  restored current production pixels, although some identified/fixed code or
  observability defects.
- The FLR-0356 staging correction passed its regression and Mini checks; the
  serial helper/validator boundary is the next first divergence.
- An independent judgment-only review agreed with the ticket split and
  cautioned that a buffer reset must not hide an unverified session/prompt
  mismatch. FLR-0358 therefore requires an explicit setup boundary and a
  unique-marker regression while preserving all identity predicates.

### Inferences

- A universal inability to compose 2D and 3D is falsified for the tested
  fixture path. Production-specific rendering, surface, synchronization, or
  image differences remain possible.
- The serial-helper buffer boundary must be repaired before using another
  production QMP black frame to rank renderer causes.
- A successful parser result alone is insufficient if setup bytes were
  discarded without proving the echo-off handshake completed; the fresh
  capture boundary must be demonstrated by the regression and runtime marker.
- Historical production regression remains plausible but unproven; the evidence
  is not a matched before/after experiment.

### Hypotheses

| Rank | Hypothesis | Falsifiable prediction |
| --- | --- | --- |
| 1 | Retained echo-off response bytes cause the host marker rejection | After positively observing setup completion/prompt, consuming that response and opening a fresh capture makes the unchanged strict parser accept exactly one fresh, identity-matching marker; unexpected setup output fails closed |
| 2 | The observation remains invalid after clean framing | With no stale prefix, parser reports a specific identity/FIFO mismatch or another guest-side result; preserve it and do not attach/GO |
| 3 | Production renderer/Present still fails after GO | Only after an accepted FIFO gate and GO, the fixed QMP ROI remains black or Present fails; compare bounded GDB markers and pixels |
| 4 | Historical/current behavior reflects an image/source regression | A matched artifact/source/profile A/B changes the QMP result; unmatched historical records alone cannot prove it |

### UNKNOWN

- Whether the FLR-0356 observation will pass the official host validator after
  the serial helper is corrected.
- Whether GDB attach/GO reaches the producer/Present watch window on the next
  fresh run.
- Whether production Sequoia pixels appear after GO, with or without the HUD,
  on the exact current image.
- Which matched source, recipe, image, or launch-profile difference explains
  the historical Sequoia-positive versus current post-GO black results.

## Plan / Do / Check / Act

### Plan

1. Reuse the completed FLR-0345/0349 intervention matrices and inspect only
   their cited positive/negative tickets plus FLR-0356.
2. Refresh the present-state table and connect each measured effect to its
   source ticket/QMP image.
3. Record the serial-helper versus parser alternatives and select the
   smallest evidence-backed next ticket.
4. Run documentation/privacy/checkpoint gates; no runtime/build/source change.

### Do

- Reconciled QMP positive fixtures, historical Sequoia candidates, latest
  post-GO production negatives, and FLR-0356's pre-GO failure as separate
  evidence classes.
- Reviewed the exact FLR-0356 serial output, strict marker parser, and
  `serial-exec` receive-buffer lifecycle; selected the helper-boundary fix for
  a separate ticket.
- Created [FLR-0358](FLR-0358-clear-serial-buffer-before-command.md) in Inbox;
  no QEMU/build/product mutation was performed in this retrospective.

### Check

| Check | Expected | Result |
| --- | --- | --- |
| Evidence status table | Positive controls separate from production and pre-GO negatives | Recorded above with linked primary tickets |
| Intervention effects | Fix / diagnostic / failed / UNKNOWN classified | Recorded above; no isolated light/texture claim promoted to root cause |
| Regression judgment | Compare identities and label confidence | Plausible, not proven; historical/current runs are not matched |
| Independent judgment review | Check scope and hidden failure modes | Agreed with ticket split; added explicit prompt-boundary and unique-marker safeguards |
| Next action | One bounded and falsifiable task | FLR-0358 serial-helper buffer framing |
| Scope | No build/runtime/source change | PASS; documentation only |
| Canonical guard and `git diff --check` | Pass on this branch | PASS |
| Privacy | No sensitive values in the candidate changes | PASS |
| FLR-0357 runtime checkpoint | Exactly one active ticket and a linked Plan/Do/Check/Act log | PASS: `active=1` |
| File size and scoped links | Under repository limit; every FLR-0357 link target exists | PASS: 1,841 files; scoped links PASS |
| Repository-wide Markdown links | No broken links | FAIL: 9 pre-existing missing evidence targets in FLR-0338/0339/0340; none are introduced by FLR-0357 |
| Staged whitespace | Exact candidate diff has no whitespace errors | PASS |

### Act

- Closed as a retrospective only; the production 3D acceptance contract remains
  open.
- FLR-0358 is now the sole In Progress ticket. It preserves the existing pinned
  Mini QEMU workflow and requires a fresh run ID; only post-GO QMP can decide
  production Sequoia visibility.
