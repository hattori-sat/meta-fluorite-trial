# FLR-0187 — rebase 0232 on the current plugin source

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0186](FLR-0186-rebase-0227-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0187.md`

## Work unit

Regenerate only the 0232 camera-API registration-order patch against the
current effective `fluorite-plugins` source. Do not change 0231, 0227, the
camera fixture, compile settings, or runtime behavior in this ticket.

## Problem

The clean Mini recipe gate now applies 0251 and 0227 without fuzz, then stops
at 0232 because both patch hunks are accepted only with fuzz 2. Yocto's
`patch-fuzz` QA check rejects that result, so the stack cannot reach compile
or runtime validation.

## Success criteria

- [x] Record the exact next Mini failure boundary and raw-log location.
- [x] Select a source baseline that represents the current plugin source after
  the already-promoted effective stack.
- [x] Apply only the 0232 semantic change through the persistent Mac Devtool
  source repository and commit it there.
- [x] Generate 0232 with official `update-recipe --mode patch --append
  --no-remove`; copy it byte-identically to the canonical layer file.
- [x] Pass Mac recipe `do_patch` and repository verification.
- [x] Bundle once and prove Mini clean `flutter-auto:do_patch` advances beyond
  0232 without fuzz.

## Facts

- Mini receiver tip after FLR-0186:
  `013d02b96623f059ad05eab32f5e8299be2cc715`.
- Mini gate status: preflight, metadata, and workdir reset PASS; 0251 and 0227
  apply; 0232 is the first failing patch.
- Mini raw task log:
  `/mnt/yocto/flr0023-tmp-835a04e-selfinstall/work/corei7-64-agl-linux/flutter-auto/2.0/temp/log.do_patch.3233737`.
- Historical Devtool commit `3d2582901653497a8e62349b3ab4813752d7def2`
  moves `DeserializeDataAndSetupMessageChannels()` below the one-time plugin
  registration, so generated APIs exist before scene deserialization can send
  initial camera property messages.
- Historical Devtool commit `3c08dbb36b073b16c2553925fa3478268e6ad362`
  is the preceding 0231 ECS-system wait change and is a separate source
  boundary.
- The current persistent source branch is
  `devtool-FLR-0186-source` at `41e1026d51bd2dad868ec4bf696d4f38d97a5f79`.
- FLR-0187 source branch is `devtool-FLR-0187-source` at
  `69bdd861419a4729fbf96bf3a0cd2476877bb614`.
- Official generated patch is
  `0001-fix-register-filament-camera-API-before-scene-load-o.patch`; the
  canonical 0232 SHA256 is
  `713910def6eca651c4dee7acbc8fae2c080b58f93df963fd1ffc6d681fc5907c`.
- Mac recipe-level `flutter-auto:do_patch` passed with the regenerated patch.
- Git bundle SHA256: `12955023d08aa8788a586a9c98cffe037f81fb477e1c189653eba986c6cc4f9f`.
- Mini evidence:
  `evidence/FLR-0187/patch-gate-flutter-auto.summary`.
- Mini preflight, metadata, recipe-workdir reset, and `do_patch` all passed at
  receiver tip `42689fdc5c66dbe537ae1cb2456fa0dd68c04c29`.

## Inferences

- The 0232 semantic change remains relevant because the current source still
  deserializes data before the one-time generated API registration block.
- 0231 should not be folded into this ticket: it changes system acquisition
  and is already a separate promoted patch in the recipe order.
- A patch generated from the current source should remove both fuzz and keep
  the change limited to `filament_view_plugin.cc`.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0232 is stale only in context | current-source official regeneration applies with zero fuzz | Mini still reports fuzz or failure at 0232 |
| H2: the historical source baseline is materially different | current-source edit needs API or behavior changes beyond block movement | generated diff changes more than the registration-order block |
| H3: a later patch is the next boundary | clean Mini gate advances beyond 0232 | Mini fails at 0232 after regeneration |

## 4W1H (Why excluded)

| Dimension | Record |
| --- | --- |
| What | Remove 0232 patch fuzz |
| Where | `fluorite-plugins/plugins/filament_view/filament_view_plugin.cc` |
| When | After 0227 and before compile/runtime |
| Who | Devtool source role, Yocto layer role, Mini patch-gate role |
| How | current source → one source commit → official update-recipe → canonical patch → bundle → clean gate |

## PDCA

### Plan

1. Read the promoted stack boundary, current source, old 0232 patch, and
   historical Devtool commits.
2. Compare historical effective-source reuse with a current-source rebase;
   select the smallest path that preserves the existing behavior.
3. Generate through the persistent Mac Devtool container and official
   `update-recipe` flow.
4. Verify Mac and Mini patch application before any compile/runtime work.

### Do

- Ticket opened after FLR-0186 cleanly advanced from 0227 to the 0232
  boundary.
- Historical 0231/0232 source commits were inspected before editing.
- Created FLR-0187 baseline/source branches from the FLR-0186 effective source
  commit and edited only `filament_view_plugin.cc`.
- Committed the source change through the bounded source-Git wrapper, then ran
  official `update-recipe --mode patch --append --no-remove` through the
  existing helper. The generated patch and canonical file compare
  byte-identically.

### Check

- Source diff check, official patch generation, canonical registration, and
  Mac `do_patch` are PASS.
- Mini bundle and clean recipe-gate verification are pending.
- Mini clean recipe-gate verification is PASS. The first attempt used the
  wrong evidence key `TICKET`; it was rerun with `FLR-0187` and the erroneous
  generated evidence directory was removed.

### Act

- Close this patch boundary and open FLR-0188 for compile/image/runtime
  validation. Do not mix compile/runtime evidence into this patch ticket.

## UNKNOWN

- Whether the current-source 0232 rebase will be byte-stable after 0231 is
  applied by Yocto is UNKNOWN until the clean Mini gate runs.
- Compile/runtime/QMP pixels/3D visibility are explicitly UNKNOWN and out of
  scope until the full patch stack reaches a clean boundary.
