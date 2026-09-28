# FLR-0036 — isolate light setter and capture timing

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament bridge + target-validation roles
- Depends on: [FLR-0035](FLR-0035-isolate-light-position-vs-identity.md)
- Working log: `work/logs/2026-09-06-flr0036.md`

## Problem

FLR-0035 found that both position override variants restore 3D, even when GUID136 remains at its original position. The result does not follow the replacement coordinate alone.

## Purpose

Separate the effect of invoking a position setter or mutating the Light object from QMP capture timing and ordinary run-to-run variability. Do not modify production scene data.

## Success measure

- Test a same-value position override for GUID136.
- Repeat an unmodified baseline capture with the same startup/log timing and capture at more than one delay.
- Preserve QMP-only photos, logs, hashes, and clean teardown.
- Create a new focused ticket for the confirmed mechanism before any production fix.

## Hypotheses

1. Any `setPosition` call changes the result through object state or initialization. Prediction: same-value override restores 3D.
2. The baseline result is timing-sensitive. Prediction: unmodified repeated runs or delayed QMP captures alternate between HUD-only and 3D.
3. The override path changes an unrelated memory/layout condition. Prediction: same-value setter is sufficient, but a source-level no-op control is not.

## PDCA

### Plan

- Reuse the existing FLR-0035 image/profile and run only the minimum controls.
- Keep diagnostic variables gated and use the same fixed Mini PC build/TMPDIR.

### Do

- Reused the fixed FLR-0035 image, existing Mini PC build/TMPDIR, and one QEMU run directory per variant. No new Docker container, Yocto TMPDIR, or production scene change was introduced.
- Same-value setter control: set GUID `136` to its existing position `(74.5,1.2,67.15)` while tracing GUIDs `136,138` and selecting six lights.
- Timing control: ran the unmodified six-light baseline and captured QMP-only frames at approximately 18 seconds and 43 seconds after launch.
- Same-value setter log markers were captured. The setter executed, the traced value remained unchanged, and the light setup selected six lights.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Same-value setter | setter-only effect isolated | Same-value setter remained HUD-only; no visible 3D | QMP photo + app log | PASS |
| Timing repeat | baseline variability quantified | 18 s and 43 s images were identical HUD-only frames | two QMP photos + PPM hashes | PASS |
| Runtime health | no native fault during comparison | Present returned success; no `SIGSEGV`, `SIGBUS`, or page-fault marker | app log | PASS |
| Teardown | no residual QEMU process/socket | QMP socket closed after each run; no FLR-0036 QEMU remained | remote post-check | PASS |

### Act

- The setter itself is not sufficient to restore 3D, and the two delayed baseline captures are stable HUD-only results. Split the next ticket around the duplicate-position/light-interaction hypothesis.
- Do not call this a production fix. The diagnostic image still uses the established model/environment skip controls.

## Facts / Inferences / UNKNOWN

### Facts

- Both FLR-0035 override variants produced the same visible-3D QMP PPM.
- The unmodified six-light baseline was HUD-only in the preceding run.
- The same-value setter executed for GUID `136`, but the QMP image remained HUD-only.
- The unmodified baseline captured at approximately 18 s and 43 s produced the same local PNG SHA-256 `9914b0aaad35897d75ab9c776f7177d2f29c1d9bce2dce9ea7e374102d419fcb`; both images are HUD-only.
- Same-value setter QMP PPM SHA-256 was `59a8fa836597bafe1ee9afe77ecad041be235c673a9c7e4830ecae91d66b7eed`; its app-log SHA-256 was `d545ca3e70be7fbbe162e414b491a55b85742de68d3d0470d8be0ff0aba0577e`.
- Baseline-repeat QMP PPM SHA-256 was `4a42011a48ce9c848fd21f1f20916f52dc257ff4e813dfc4e1eccf03145fbc6f` for both delays.

### Inferences

- The result does not follow from the setter call alone.
- The repeated baseline did not alternate between HUD-only and 3D, so capture timing alone is not a sufficient explanation.

### UNKNOWN

- Whether duplicate positions between selected lights are the relevant trigger.
- Whether the failure is caused by scene-light data, entity/resource identity, or a downstream light-buffer operation.

## Evidence

QMP-only images are the visual record for this ticket:

- Same-value setter, GUID `136` set to its original position; HUD-only: [same-value136-late.png](../evidence/flr0036/same-value136-late.png)
- Unmodified baseline at approximately 18 s; HUD-only: [baseline-18s.png](../evidence/flr0036/baseline-18s.png)
- Unmodified baseline at approximately 43 s; HUD-only: [baseline-43s.png](../evidence/flr0036/baseline-43s.png)

All three images are 720x400 QMP captures. The two baseline PNGs are byte-identical. The same-value app log contains successful `FLR0026_VK_QUEUE_PRESENT result=0` markers and no native fault marker. The remote QMP socket was closed after each run.

## Handoff

- New independent task: [FLR-0037](FLR-0037-isolate-duplicate-light-position.md).
