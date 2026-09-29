# FLR-0345 — retrospective checklist for Fluorite 3D visibility

- Status: Done
- Priority: High
- Owner: runtime evidence synthesis / production render and composition roles
- Created: 2026-09-28
- Follow-up ticket: [FLR-0344](FLR-0344-capture-lavapipe-watch-failure-deterministically.md)
- Working log: `work/logs/2026-09-28-flr0345.md`

## Objective

Before another runtime experiment, put the 3D-display evidence in one compact,
evidence-linked checklist. Separate known-positive controls from production
Sequoia results, list every consequential probe and its measured effect, mark
whether each action fixed behavior or only improved diagnosis, and identify
whether a regression remains plausible. End with one ranked next discriminator.

## Scope and hold point

- Read the linked FLR-0066/0070 historical results, FLR-0285/0286 fixture
  controls, FLR-0316/0323 asset/material findings, and FLR-0333/0344 current
  runtime evidence. Prefer the bounded ticket/log sections; do not reread
  unrelated full logs.
- Record What/Where/When/Who-role/How before causal explanations. Keep facts,
  inferences, hypotheses, decisions, and UNKNOWN separate.
- Include QMP frame identity, pixel counts, relevant image/rootfs identity,
  expected result, actual effect, and artifact availability for each positive
  or negative claim.
- Explicitly answer whether the user's Photo 1 proves a runtime image, whether
  hiding the HUD has been tested, whether 2D+3D composition is generally
  possible, and what still blocks product acceptance.
- Do not run QEMU, BitBake, Devtool, a build, or a HUD/camera/light/material/
  texture/source change in this retrospective. Resume one runtime ticket only
  after the checklist chooses the discriminator.

## Checklist deliverable

- [x] Establish the present capability target and precise 3D ROI/QMP pass
      signal.
- [x] List the 2D HUD/CPU/GPU screen result separately from 3D success.
- [x] List self-made 3D fixture + HUD results separately from Sequoia results.
- [x] Reconcile historical Sequoia/HUD positive records with later failures;
      include source/image/profile differences and missing raw evidence.
- [x] Classify the Photo 1 texture atlas and runtime texture-ready/binding
      markers without treating either as visible screen pixels.
- [x] For every relevant camera/light/material/texture/present/debugger probe,
      record its observed effect and whether it was a fix, a control, or only
      diagnostic.
- [x] Identify workflow/evidence failures that caused wasted or repeated
      loops, and the countermeasure plus measured effect for each.
- [x] Compare at least three falsifiable explanations, including a possible
      image/source regression; state evidence that supports and weakens each.
- [x] Recommend exactly one next test, with expected signal, invariant inputs,
      evidence, and stop condition.
- [x] Run privacy, Markdown-link, checkpoint, and staged-whitespace checks;
      record a local commit, without push.

## Acceptance criteria

- One compact table lets a reader find the observation, intervention, effect,
  verdict, evidence, and next discriminator without replaying the conversation.
- Known-positive and negative results are not conflated; visual evidence is
  QMP-only or explicitly labeled static/non-runtime.
- A regression is neither dismissed nor declared proven without matched image,
  source, and launch-profile evidence.
- The 2D+3D finish condition is a same-frame production Sequoia result with a
  visible HUD and acceptable camera/material/color, not merely a fixture, GLB
  texture, build, or isolated 3D-only surface.
- No runtime/build/source mutation occurred in this ticket.

## Plan / Do / Check / Act

### Plan

1. Read only the ticket/log/evidence sources listed above and re-open the
   current QMP screenshot and Photo 1 provenance.
2. Fill the intervention/effect checklist and compare historical/current
   artifact identity and controls.
3. Rank falsifiable hypotheses and recommend one next runtime ticket/action.
4. Run documentation/privacy/checkpoint gates and commit locally.

### Do

- Re-read the bounded FLR-0066/0070, FLR-0285/0286, FLR-0321/0323,
  FLR-0333/0334/0335/0337/0343/0344 records and the 0343 QMP screenshot.
- Verified the supplied Photo 1 SHA against the FLR-0323 classification and
  re-displayed both the user-supplied texture atlas and current FLR-0343 QMP
  full frame. Queried only the documented Mini evidence paths for historical
  FLR-0070 p9 media; no raw image was found there.
- Filled the intervention/effect table, ranked hypotheses, and selected one
  next runtime discriminator. No remote mutation or QEMU/build was performed.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Canonical/ticket state | Canonical repo; exactly one active ticket through the transition | PASS | Retrospective closed and FLR-0344 resumed as the sole In Progress ticket |
| Evidence matrix | Positive, negative, intervention, effect, and provenance rows complete | PASS | Working-log intervention table links historic positives, current negatives, controls, and artifact gaps |
| Regression assessment | Plausible / falsified / unknown classification with matched-identity limits | PASS | Plausible but not proven; historic/current rootfs identities differ and no matched source/image A/B exists |
| Next action | One falsifiable discriminator with controls and stop conditions | PASS | Resume FLR-0344 one-run same-image Present-wait GDB capture; HUD-off is conditional follow-up, not mixed into the run |
| Repository gates | Privacy, links, checkpoint, whitespace; local commit | PASS | Privacy, Markdown links, checkpoint, and staged whitespace passed; committed locally as `fe85290`, no push |
| Scope | No Mini transfer, QEMU, build, patch, or scene mutation | PASS | Retrospective used saved records only; FLR-0344 runner remains untransferred/unrun |

### Act

- Resume [FLR-0344](FLR-0344-capture-lavapipe-watch-failure-deterministically.md)
  only if the retrospective confirms Present-wait synchronization is still the
  highest-value discriminator; otherwise open a distinct ticket for the
  evidence-selected next test. Do not mix HUD-off, camera, lighting, and
  texture variables into the same run.

## Facts / inferences / hypotheses / UNKNOWN

- See `work/logs/2026-09-28-flr0345.md`; the checklist must preserve these
  categories and link each claim to a source ticket/log or QMP artifact.
