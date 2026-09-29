# FLR-0359 — use the committed QEMU runtime helper

- Status: In Progress
- Priority: High
- Owner: Mac runtime runner / Mini QEMU / QMP evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Work unit: Prove that the runner and QEMU starter execute one run-scoped copy of the helper from the exact committed bundle tip, then classify one fresh Mini runtime attempt.
- Links: [FLR-0358 predecessor](FLR-0358-clear-serial-buffer-before-command.md), [FLR-0360 attach-predicate follow-up](FLR-0360-diagnose-gdb-attach-precondition.md), [FLR-0361 checkpoint-matcher follow-up](FLR-0361-fail-closed-ticket-status-matcher.md), [FLR-0357 retrospective](FLR-0357-refresh-3d-visibility-retrospective.md), [FLR-0286 fixture positive control](FLR-0286-reproduce-known-good-combined-sequoia-hud.md), [FLR-0287 production Sequoia boundary](FLR-0287-compare-production-sequoia-light-material.md), [working log](../logs/2026-09-29-flr0359.md), [implementation plan](../../docs/superpowers/plans/2026-09-29-flr0359-bind-qemu-runtime-helper.md)

## Problem

### Purpose

The FLR-0358 serial capture fix was not exercised by its Mini run: both the host runner and QEMU starter executed a saved FLR-0335 helper instead of the helper in the exact received commit. Bind both callers to the same per-run staged helper so local checks, transferred source, and runtime behavior are the same bytes.

### Success measure

- Fast local checks fail if runner or starter selects a prior evidence helper, and pass only when the executable repository helper's bytes match `HEAD`, are staged once into the fresh run directory, and both callers use that same copy.
- Before guest-ready/serial/QMP operations, the run log records source commit plus committed-blob, source-file, and staged-file SHA values; the three must match the exact receiver commit.
- The historical QMP pixel-capture helper remains pinned to its recorded SHA; this ticket changes helper provenance only, not pixel-analysis behavior.
- One fresh run on the existing pinned Mini QEMU image uses the verified helper. The official FIFO validator remains unchanged. Any failure is recorded at its first divergent gate; no run ID is retried.
- If the gate reaches GO, preserve the bounded runtime result and QMP full-frame/eight-frame evidence. Only post-GO pixels may update the production Sequoia/2D+3D verdict.
- QEMU, runqemu, Flutter, QMP socket, and run-owned FIFO teardown is proven; no BitBake, Devtool, product image build, or rootfs/kernel transfer is performed.

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | The FIFO observer stream begins with setup tokens; validator returns `marker-not-first`. | FLR-0358 run `flr0358-0001`; bounded serial capture and official validator result in the FLR-0358 log. |
| Where | Host runtime helper selection, before serial command capture and before GDB/GO. | `work/commands/FLR-0350-run-sync-producer.sh`, `work/commands/FLR-0350-qemu-start.sh`. |
| When | After the exact FLR-0358 bundle was received and the existing pinned image booted, during the single fresh run. | Bundle SHA/tip, run ID, preflight, and gate result in the FLR-0358 log. |
| Who | Runner owns source staging; QEMU starter owns launch; the serial helper owns command framing; validator owns the strict FIFO decision. | Static call chain and run evidence. |
| How | Both callers resolved the previous-run evidence helper; its bytes differ from the helper in the received tip. | Old SHA `339472…`; received helper SHA `088e8e…`. |

### Priority selection

- Compared strata: Flutter/Filament rendering; native surface composition; runtime helper provenance; strict FIFO parser.
- Selected focus: runtime helper provenance, the first observed mismatch before GDB/GO.
- Selection evidence: FLR-0358's actual helper SHA differs from the exact bundle helper SHA. A rendering or parser change cannot make the wrong executable source test the FLR-0358 fix.

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| Bundle receive | Exact committed Mac tip | Fixed receiver clean at exact tip | PASS for FLR-0358 | FLR-0358 bundle SHA and receiver HEAD |
| Runner setup | Repository helper in received tip | Stage one run-owned helper and record SHA | Both callers selected archived FLR-0335 helper | Old/new SHA comparison |
| Guest command | Staged static command + staged helper | Fresh capture starts after verified echo-off response | Three setup tokens preceded the FIFO marker | `marker-not-first` result |
| Strict gate | Observer output | Preserve all process/FIFO identity predicates | Failed closed before GDB attach/GO | Official validator output |
| QMP / cleanup | Existing pinned image | Capture and teardown; classify frame by GO state | Pre-GO all-black frame; cleanup passed | FLR-0358 QMP SHA and teardown table |

### Problem point

Confirmed at runtime-helper source selection: the runner and starter resolve a prior-run evidence copy rather than a helper staged from the current committed source. The official serial capture code path therefore bypasses the FLR-0358 commit.

### Ideal condition

For one unique run ID, both the host runner and QEMU starter execute the same run-scoped `qemu-runtime-harness.sh`, byte-identical to the helper at the exact bundle tip; its SHA and source commit are recorded. The capture parser and identity predicates remain unchanged.

### Current condition — Facts

- FLR-0358's exact bundle receiver tip contained helper SHA `088e8e39ed1fc7dce175ad0fd2a027325b04815c68337a9e52fead2c9fb64fee`.
- Runtime selected the saved FLR-0335 helper SHA `339472336f14387fd1b72c3d702e510de19ff710c5c203441733a7a59d79aa6d` from both orchestration scripts.
- The official FIFO validator failed at `marker-not-first`; GDB attach and GO were not reached. Teardown passed.
- Pre-FLR-0359 baseline: FLR-0356's observer had matching target and FIFO identity fields before host framing failed; FLR-0358's loopback tests covered only their tested transcript, so Mini compatibility was then untested. FLR-0359 subsequently ran the exact committed helper on Mini and passed framing plus the official FIFO gate. Only the later GDB-attach boundary remains unclassified.
- FLR-0109 records an earlier wrong-OE-tree/TEMPLATECONF failure; FLR-0351 later verified the persisted template and unique AGL OE source before receiver update. Reuse that successful source/build preflight rather than rediscovering directories.
- FLR-0286 proves same-frame HUD plus self-made lit Filament geometry through QMP. FLR-0287 separately reached production Sequoia load, scene-add, draw, and present while the native ROI had `0/144000` changed/chromatic pixels and the HUD had 2,845 chromatic pixels. The fixture success does not prove production Sequoia, and the production result does not invalidate the fixture control.
- FLR-0359 run `flr0359-0001` used the exact received helper: committed/source/staged SHA-256 all matched `088e8e39ed1fc7dce175ad0fd2a027325b04815c68337a9e52fead2c9fb64fee` at source commit `8de11b0e47304724f436d5567b55e62640a237d3`. All 11 guest commands staged and the unchanged FIFO validator passed.
- The next stage reported only `FLR0350_GDB_ATTACH=FAIL precondition`; there was no GDB attach, release-GO, or `FLR0350_EXEC`. The captured observer saw `read(0)` (`arg1=0x0`), while the attach command requires `read(3)` (`arg1=0x3`). Its observed fd-0 FIFO device/inode matched the gate, but the attach-time individual predicates were not logged; the first exact failed predicate is therefore UNKNOWN.
- The post-run QMP frame is pre-GO evidence, not a Flutter/renderer result. Cleanup explicitly reported `FLR0350_FIFO_CLEANUP=PASS removed=run-owned-fifo`, stopped the run-owned wrapper, and found `flutter_processes=0`, `residual_targets=0`, and `residual_qmp=0`.

### Gap

The source validated locally is not guaranteed to be the source selected by the runtime orchestrator. That provenance gap caused a false loop: the same `marker-not-first` symptom recurred without executing the fix.

### Impact

Repeated QEMU attempts consume time and run IDs while yielding no evidence about the serial fix or the renderer. A black pre-GO frame can be mislabeled as a product regression unless GO state is explicit.

### Point of occurrence

The path assignment in both the runner and QEMU starter, followed by the absence of a regression that connects current repository bytes to those selected paths.

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| Both scripts pin the prior evidence helper | Resolved paths and SHA match FLR-0335, not current source | Inspect both runtime call sites and compare bytes | Confirmed | FLR-0358 source inspection and hashes |
| The FLR-0358 helper itself still rejects the Mini setup transcript | With exact current helper SHA in use, the official gate still reports a serial framing/setup error | One fresh run using the run-scoped helper; preserve exact first gate | Falsified for this attempt: current helper serial capture and official FIFO gate passed; later guest stages remain untested | `flr0359-0001` exact-helper run markers |
| The strict FIFO validator is too strict | Correctly framed current helper output still fails a named identity/FIFO predicate | Keep validator unchanged; observe its result after provenance passes | Not implicated in this attempt: unchanged FIFO gate passed; do not relax it | `FLR0350_FIFO_READ_GATE=PASS` |

### Confirmed root cause

The two orchestration entry points used a pinned historical helper path/hash, while local regression exercised `scripts/qemu-runtime-harness.sh` directly. No integration contract asserted that these were the same source. This source-selection mismatch is confirmed. The exact-helper path now passes the observed source-to-runner/stage integration contract, and `flr0359-0001` Mini serial capture plus the official FIFO gate passed. Negative missing/mismatch execution branches were deferred. The separate GDB attach precondition failed generically before GDB/GO.

### Minimal countermeasure

Set the source to `$repo_root/scripts/qemu-runtime-harness.sh`, stage it once as `$parent/qemu-runtime-harness.sh` before QEMU start, assign the runner to that staged path, and require the starter in `start` mode to `cmp` the staged copy with repository source and log the matching SHA. Keep the prior evidence directory only for immutable pinned artifacts such as the QMP pixel-capture helper and saved runqemu argv. Add a fail-closed static contract covering both scripts and staging order.

## Scope

### In scope

- Runner/starter helper selection and run-scoped staging.
- Fast static regression, shell/Python/QEMU-harness checks, privacy/size/checkpoint gates.
- Exact committed Git bundle to the established Mini receiver; read-only effective OE/build/TMPDIR and pinned-image preflight; one fresh QEMU runtime ID.
- QMP-only still, eight-frame capture/video, bounded gate/runtime logs, and cleanup evidence.

### Out of scope

- Flutter, Filament, material, texture, camera, lighting, Wayland surface, or image changes.
- Relaxing the official FIFO validator or identity/FIFO predicates.
- BitBake, Devtool, product image rebuild, new receiver/TMPDIR, or QEMU image transfer to Mac.
- Retrying any consumed run ID. A separate post-GO renderer finding becomes a separate ticket.

## Success criteria

1. `--check` and unit tests statically assert the repository helper is staged once, both orchestration scripts use that run copy, the staged and source bytes/hash match, and staging occurs before QEMU `start`. Missing/mismatch runtime branches were deferred and are not claimed tested.
2. No executable helper reference remains to the FLR-0335 evidence path; the separate pixel-capture helper remains hash-pinned.
3. The standard bundle transfer identifies exact local/receiver commit and SHA; target source/build/TMPDIR, image artifact hashes, ports/processes, and unused run ID pass preflight without BitBake or Devtool.
4. Exactly one fresh Mini QEMU attempt is made. Gate PASS is required before GDB/GO; on any gate failure, stop without retry, save QMP evidence as pre-GO, and prove teardown.
5. Record the first failing runtime stage and its evidence. If its marker is generic, retain the inner predicate as UNKNOWN. If GO is reached, record bounded runtime markers and QMP pixels with full frame/ROI counts and hashes. Do not update the rendering verdict from a pre-GO frame.
6. The working log records facts, inferences, ranked hypotheses, UNKNOWNs, failed/corrected probes, and resulting next discriminator. No unbounded log dump.

## Visual evidence

- Run ID: `flr0359-0001`; pinned qemux86-64 profile, 6144 MiB. Runtime artifact hashes were checked by the QEMU starter: kernel `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, rootfs `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`, qemuboot `ef5309f471e4bd159febbbc2c630368ec609d21900179b3694a6fb6c16f8c44a`.
- QMP pre-launch full frame is saved locally at `/private/tmp/flr0359-0001/qemu/qmp-pre-launch.png`; raw PPM SHA-256 `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`; 16/1,024,000 changed pixels (a small gray mark at `[0,14,8,2]`), zero chromatic pixels. No HUD or recognizable scene.
- QMP post-run full frame is saved locally at `/private/tmp/flr0359-0001/qemu/qmp-post-run.png`; raw PPM SHA-256 `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`; 0/1,024,000 changed or chromatic pixels, luma `[0,0]`, all black. The PNG is a lossless local conversion of the captured PPM.
- QMP eight-frame video is saved locally at `/private/tmp/flr0359-0001/qemu/qmp-post-run.mp4` (1280×800, 1 fps, 8 seconds), SHA-256 `65323ba165b9334b042df38fad9b737b11ddbb7d8298178c990159fb616e0c76`. All eight source PPM frames have the same SHA-256 as the post-run still.
- QMP quit was accepted; cleanup passed with zero QEMU/QMP residuals. Only QMP screenshots/frames/video were copied to Mac; no kernel, rootfs, or QEMU image was copied.
- Historical comparison: FLR-0286's self-made lit Filament fixture + HUD is a positive composition control. FLR-0287's production Sequoia draw/present with a zero-chroma native ROI is a separate production boundary. Neither substitutes for this run, which never reached GO.

## Hypotheses

1. The exact helper is selected and the Mini serial capture fix passes the unchanged FIFO gate. **Observed:** confirmed for this run.
2. A separate GDB-attach precondition fails after the FIFO gate. **Observed:** `GDB_ATTACH=FAIL precondition`; exact inner predicate UNKNOWN.
3. The `read(0)` versus required `read(3)` mismatch is the failed predicate. **Leading but unconfirmed:** observer values support it, but attach does not report each predicate and fd-3 identity at that instant.

## PDCA

### Plan

- See [FLR-0359 implementation plan](../../docs/superpowers/plans/2026-09-29-flr0359-bind-qemu-runtime-helper.md).
- Test source-to-runner/starter provenance first; then run local gates, commit, bundle, preflight, and use one fresh Mini ID.
- Stop before GDB/GO on any failed strict predicate. Never retry a consumed ID.
- Risks: helper staging race/order, accidental loss of pinned QMP tool provenance, runtime gate failure after correction, and mistaking a pre-GO black frame for a renderer result.

### Do

- Record exact commands and results in [FLR-0359 working log](../logs/2026-09-29-flr0359.md); no product source or image change.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Fast provenance contract | Current source staged once; runner and starter use same bytes | 3 focused tests PASS; runner `--check` PASS (31 total); Bash syntax PASS | Local test/static contract | PASS |
| Mini receiver/image identity | Exact bundle tip and pinned image identity | Bundle SHA-256 `201a298a90beeeeecc49a2f89a8323a4e6862d86c2d296f182d580e85cee228e`; exact tip `8de11b0e47304724f436d5567b55e62640a237d3`; pinned kernel/rootfs/qemuboot hashes matched | Standard handoff and `qemu-start.log` markers | PASS |
| QEMU preflight | Fresh run ID/directory, no conflicting runtime process, forwarded ports free | Runner/starter enforce these guards and the run proceeded; exact `FLR0350_QEMU_PREFLIGHT` line and supplemental SSH inventory were not retained | Runner source + recorded run result; exact marker values UNKNOWN | Gate did not abort; independent inventory UNKNOWN |
| Helper provenance / command staging | HEAD/source/staged SHA match; all commands staged before start | SHA `088e8e39…` matched; 11/11 staged | `FLR-0350-runner.log` | PASS |
| FIFO/GDB/GO | Official validator passes before GDB/GO; otherwise stop at first gate | FIFO gate PASS. GDB attach reported generic precondition failure; no attach or GO. The exact inner predicate is UNKNOWN and is handed off | `observe-gate.serial.log`, `attach-gdb.serial.log`, bounded runner markers | STOP before GO |
| QMP pixels / cleanup | QMP evidence classified by GO; all owned targets stopped | Pre-GO post-run full frame all black; eight identical frames; run-owned FIFO removal, QMP quit, and cleanup PASS, residuals 0 | Local still/video paths above; run ID `flr0359-0001` | PASS for evidence/cleanup; renderer NOT REACHED |

### Act

- FLR-0359 can close only after the final PDCA/evidence/privacy checks pass. Its bounded runtime result is exact-helper provenance PASS, FIFO gate PASS, then GDB attach precondition STOP before GO. FLR-0360 now exists in Inbox to report each attach predicate at the same decision point without changing the acceptance rule; do not reuse `flr0359-0001`.

## Decision log

- Keep the strict parser and identity predicates unchanged; the first proven mismatch is helper provenance.
- Stack this feature from FLR-0358's committed tip because `dev-mini-recovery` does not include the prerequisite FLR-0354–0358 runner changes. Record that dependency rather than producing a branch that cannot reproduce the failure.
- Use one source/build receiver and existing pinned QEMU artifacts; no rebuild is needed for host-side orchestration changes.

## Unknowns

- Which exact attach precondition failed; the generic marker does not identify it.
- Whether fd 0 and fd 3 both refer to the run-owned FIFO at attach time, and whether fd 0 is an intended equivalent for the gate contract.
- Whether a corrected/verified attach gate can reach GO and start Flutter.
- Whether current production QMP shows Sequoia, HUD, both, or a post-GO black native ROI. No rendering conclusion is available from this ticket.
- The exact shell text and bounded output of supplemental pre-transfer/post-run SSH inventories were not retained. Do not reconstruct them; independent process/port/PID/socket observations from those ad-hoc commands are UNKNOWN. The standard bundle helper and Mini runner invocation are recorded; their built-in gates plus the observed run/teardown results are the evidence used here.

## PDCA checker

- Status: PASS
- Checked by: Astra (judgment-only independent audit)
- Findings: Final audit found no remaining closeout blockers. The four unfinished legacy tickets are Waiting; exact outputs from unretained supplemental SSH probes remain UNKNOWN; standard bundle/runner guards are distinguished from those observations. Pre-GO black QMP is not treated as a render result. This closes only helper provenance and the classified runtime attempt; overall 2D+3D remains open.
