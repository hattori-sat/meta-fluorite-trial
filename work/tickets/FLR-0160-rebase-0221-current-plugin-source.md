# FLR-0160 — rebase 0221 against the resolved current plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0159](FLR-0159-rebase-0220-current-source.md)
- Working log: `work/logs/2026-09-15-flr0160.md`
- Resume note: FLR-0161 is Done; the in-progress 0222 source edit remains
  preserved in the fixed Devtool source workspace/stash and is resumed here.

## Work unit

Reconcile `0221-reconcile-visible-default-light-with-current-plugin-api-devtool.patch`
with the resolved current `ivi-homescreen-plugins` source, using the existing
persistent Mac Devtool workspace and official Yocto patch-generation operations.
Preserve the current plugin source identity and the visible-default-light
behavior under test.

## Problem

The fixed-Mini `flutter-auto:do_patch` gate advanced past the current-source
0220 patch and stopped at 0221. The failing patch targets the nested
`ivi-homescreen-plugins` component and changes
`plugins/filament_view/core/systems/derived/light_system.cc`. The exact source
context and whether the default-light change is already present must be
established before editing or removing the patch.

## Success criteria

- [x] Record the exact 0221 failure and current plugin source identity using
  bounded evidence.
- [x] Compare at least two explanations: stale patch context versus behavior
  already present/redundant in the current plugin source.
- [x] Use official Devtool source registration and `update-recipe --mode patch`
  for the split component; do not hand-edit the generated patch body.
- [x] Register one unchanged official output in `meta-fluorite-trial`, preserve
  0220 and 0251 registrations, and update the baseline lock.
- [x] Send the committed layer through the fixed bundle receiver and prove one
  bounded Mini `do_patch` gate advances beyond 0221.

## Facts

- Receiver revision is `e003c11...` and the current preflight resolved
  `0220 → 0251` after confirming the obsolete 0002 item is absent.
- The single bounded `do_patch` run failed at
  `0221-reconcile-visible-default-light-with-current-plugin-api-devtool.patch`.
  The exact task log is
  `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3138799`; the
  raw task output is outside Git under `$RECEIVER/evidence/flr0159/`.
- The 0221 patch changes the default light to color temperature `6500.0f`,
  intensity `100000.0f`, direction `{0, -1, 0}`, position `{0, 5, 0}`, and
  cast-light enabled.
- The Mini current plugin HEAD is `2163242...`; its default-light function uses
  lower-case setters, keeps intensity `200`, and does not set color temperature.
- The existing Mac Devtool plugin source was on unrelated source HEAD
  `2d3b0a4...`; its source function also had a different entity/API context.
  This confirms a source-baseline mismatch rather than a missing Mini fetch.
- The existing Devtool source was branched for FLR-0160. One baseline commit
  `6a5cd5b...` aligned only the target function with the Mini source context,
  then official `component-add` registered `fluorite-plugins`. Source commit
  `3915929...` added only the two default-light assignments.
- Official `update-recipe` generated one patch, byte-copied unchanged into the
  existing 0221 layer slot. Its SHA-256 is
  `88ee28446bfe2bb08c861c1b12d7d1c8e935bbfff7ff766a6815b280c1e754a5`.
- The current-source 0222 baseline is `09d01950...` and source commit is
  `74d6154127e211622dc8dc91d86e9ad9b59b7cd9`. Standard official
  `update-recipe` generated the current patch, copied unchanged to the 0222
  slot with SHA-256
  `d54a77c21647167759ad60f34e64327c14c3d5c204c46889d49f2e8dc38c17f4`.
- The committed layer bundle was transferred to the fixed receiver with
  matching remote SHA-256 and receiver revision `3a6f1df...`; the bounded
  preflight passed and confirmed 0220, 0221, and 0222 in effective `SRC_URI`
  order.
- The Mini `do_patch` rerun applied 0220 and 0221, then failed at 0222. Hunk 1
  failed at line 37 while hunks 2 and 3 succeeded with offsets. The exact task
  log is `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3143812`;
  the bounded command output is `$RECEIVER/evidence/flr0160/`.
- The failed 0222 patch expected an include context containing
  `filamat/MaterialBuilder.h` and related headers that are absent from the
  post-0221 Mini source. This proves the previous Devtool baseline was not the
  recipe's effective source after its prior patches.
- The Mini post-0221 target file SHA-256 was
  `42c4d6617a840fda8d9224d5caadce6c5fd49c37e5c30b7a056b49ebf01c032d`; the
  previous Mac Devtool target file was `b77ec38f...`. The Mini file was
  imported into the existing fixed Devtool source and committed as effective
  baseline `aabdd129038e0f405fcfb56ed41559e05a35256b`.
- From that baseline, only the 0222 frame-timing change was edited and
  committed through the Devtool wrapper as
  `956b5e44f5d60cc65dccb764f3726aa432c84d82`. Official `update-recipe`
  regenerated the canonical patch with SHA-256
  `664423345d068d344deb5bfcafc6c136a573f8f746543eaa6bafe357bc6b2ab2` and
  refreshed the baseline lock.

## Inferences

- 0220 is no longer the blocking boundary; its current-source replacement
  applied successfully.
- 0221 is an independent nested-component source/API boundary and must not be
  folded back into FLR-0159.
- The stale-context hypothesis is selected: the generated current-source patch
  changes only `setIntensity(200)` to color-temperature plus
  `setIntensity(100000.0f)`, and preserves the current Mini API spelling.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0221 has stale context but required behavior | current plugin source differs in API/context; official Devtool rebase yields one equivalent patch | generated output cannot express the change or later behavior is missing |
| H2: default-light behavior is already present | bounded current source contains the same values and no patch is required | current source lacks one or more required assignments |
| H3: plugin source identity is wrong | recipe resolves a different component revision than the persistent Devtool source | bounded recipe/source identities match exactly |
| H4: Devtool baseline omitted prior recipe patches | effective post-0221 source differs from the source used to generate 0222 | effective-source import baseline and official regeneration produce an applyable 0222 |

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Reconcile 0221 with current `ivi-homescreen-plugins` source |
| Where | Existing persistent Mac Devtool plugin source and canonical layer |
| When | After 0220 passes and before compile/image/QEMU |
| Who | Plugin source-baseline, Mac Devtool, Mini BitBake roles |
| How | exact task log → bounded source comparison → official Devtool output → one fixed do_patch gate |

## PDCA

### Plan

1. Read only the exact 0221 task log and target source file.
2. Compare the current recipe component revision with the persistent Devtool
   plugin source; select rebase or removal only from evidence.
3. Reuse the same Podman container/state, source directory, receiver, build,
   and TMPDIR. Do not create a ticket-specific copy or volume.
4. Generate and register the official patch, commit, bundle, then run only the
   bounded recipe preflight and one `do_patch` gate.

### Do

- Created after FLR-0159's one fixed-Mini `do_patch` run advanced through 0220
  and stopped at 0221.
- Read the exact task failure and compared only the current Mini light source,
  the existing persistent Devtool source, and the 0221 patch target. H1 was
  supported; H2 was falsified because current default light remains intensity
  `200` with no color-temperature assignment. H3 was also observed as a
  baseline mismatch: the persistent source HEAD was `2d3b0a4...` while Mini
  resolved `2163242...`.
- Reused the same persistent source directory, created a ticket branch, aligned
  only the target function to the current Mini context, committed the baseline,
  ran official `component-add`, edited the two desired source assignments, and
  committed the source change through the wrapper.
- Ran official `update-recipe` for the split component. It generated one patch
  for source HEAD `3915929...`; the output was copied unchanged to the
  canonical 0221 file with SHA-256
  `88ee28446bfe2bb08c861c1b12d7d1c8e935bbfff7ff766a6815b280c1e754a5`.
- Resumed the preserved 0222 source on baseline `09d01950...`, committed the
  nanosecond frame-time/deduplication change as `74d6154...`, and ran the
  one-shot helper with component recipe `fluorite-plugins`.
- The helper used standard official `update-recipe`, validated the existing
  multiline registration before copy, replaced 0222 only with explicit
  `--replace-canonical`, and refreshed the baseline lock.
- Transferred the committed layer bundle to the fixed receiver. Remote bundle
  hash matched the local hash and receiver revision reached `3a6f1df...`.
- The bounded Mini preflight passed. `do_patch` then failed at 0222 with one
  include-context hunk failure while two later hunks were accepted with
  offsets; no compile, image build, or QEMU was started.
- Compared the failed target and patch hunk, confirmed the baseline mismatch,
  and imported the Mini post-0221 target file into the existing Devtool source.
  Committed the effective baseline as `aabdd129...`, then committed only the
  0222 change as `956b5e44...` through the wrapper.
- Ran the official standard `update-recipe` path again. It generated one
  patch, replaced 0222 with explicit registration validation, and refreshed
  the baseline lock. The new patch SHA-256 is
  `664423345d068d344deb5bfcafc6c136a573f8f746543eaa6bafe357bc6b2ab2`.

### Check

- PASS for the bounded source/rebase unit: exact failure, source identities,
  two hypotheses, and official split-component patch generation are recorded;
  canonical 0220/0221/0222/0251 registration is consistent and the lock is
  updated.
- The first post-rebase Mini gate failed at 0222, proving the prior baseline
  was incomplete. The effective-source rebase was committed as `c789dc4`,
  transferred to the fixed receiver, and the corrected gate advanced through
  0222 before stopping at 0223. No compile, image build, or QEMU was started.

### Act

- Keep FLR-0158 and FLR-0156 Waiting. This ticket is Done because the corrected
  fixed-Mini gate advanced through 0222; FLR-0167 owns the next 0223 boundary.
- Do not compile, build an image, or start QEMU until the remaining patch
  boundaries pass.

## Evidence

- Predecessor task summary: `$RECEIVER/evidence/flr0159/do_patch-current-0220.summary`
- Predecessor exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3138799`
- Fixed-Mini preflight summaries: `$RECEIVER/evidence/flr0160/bitbake-e-image.summary`,
  `$RECEIVER/evidence/flr0160/bitbake-e-flutter-auto.summary`
- Fixed-Mini 0222 failure output: `$RECEIVER/evidence/flr0160/do_patch-flr0160.stdout`
- Exact failed task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3143812`
