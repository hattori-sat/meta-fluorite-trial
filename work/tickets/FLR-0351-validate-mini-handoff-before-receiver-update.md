# FLR-0351 — validate Mini handoff before receiver update

- Status: In Progress
- Priority: High (blocks the FLR-0350 Mini bundle handoff)
- Created: 2026-09-28
- Found during: [FLR-0350](FLR-0350-correlate-lavapipe-sync-release-producer.md)
- Owner: bundle handoff / Mini build configuration roles

## Objective

Make the standard Git-bundle handoff validate the active build's effective
`TMPDIR` and every receiver precondition before changing the fixed Mini
receiver. A rejected handoff must leave receiver `HEAD` and its working tree
unchanged.

## Facts

- `scripts/reuse-mini-build-receiver.sh` performs `git fetch` and detached
  checkout before its final exact-string check for
  `TMPDIR = "$BUILD_TMPDIR"` in `conf/local.conf`.
- A bounded, target-less `bitbake -e -T 5` query on the pinned Mini build
  succeeded and resolved `TMPDIR` to `TOPDIR/tmp`; `TOPDIR` matched the build
  directory derived from the saved FLR-0335 runqemu command. The explicit
  server-idle-timeout option was accepted and no BitBake process remained.
- The pinned build's `conf/local.conf` has zero active `TMPDIR` assignments.
  The saved QEMU kernel, rootfs, and qemuboot inputs resolve under `TOPDIR`
  but outside `TOPDIR/tmp`; that staged artifact location is not used as a
  substitute for BitBake's effective variable.
- The FLR-0350 Mac command environment did not contain the required
  `BUILD_*` role variables. No replacement values or paths were guessed.
- At the original preflight checkpoint, no bundle had been transferred and no
  Mini receiver had been changed. A later helper invocation is recorded below;
  its receiver-side outcome is UNKNOWN.
- The only ignored local remote-role file contains SSH/MCP connection fields,
  not the fixed bundle inbox, receiver, build, or TMPDIR roles. The current
  process and `launchd` have all five `BUILD_*` roles unset; documentation
  contains placeholders only. No values were inferred.
- The receiver helper no longer falls back to historical hard-coded receiver,
  build, or TMPDIR paths. Missing fixed roles fail locally before SSH; failure
  to source the fixed build's OE initialization script now stops before any
  BitBake command is attempted.
- Five local integration tests pass: missing roles reject before SSH, OE-init
  failure, BitBake query failure, and TMPDIR mismatch all preserve receiver
  state; the valid case checks out exactly the advertised tip.
- Final `make verify` passed after the implementation and working-log edits:
  privacy, shell syntax (53 files), the 96-test Python suite, the 52-test
  MCP-focused suite, MCP smoke, Markdown links, file-size, QEMU/runtime,
  Devtool, Mini recipe, and bundle-handoff gates passed.
- The final FLR-0351 runtime checkpoint passed with exactly one `In Progress`
  ticket at the original implementation checkpoint. The fixed local role
  configuration was unavailable in that process. A later read-only probe
  confirmed the effective-TMPDIR role match; actual bundle handoff remains
  unverified.
- Follow-up read-only probe on the previously recovered role values passed:
  `TOPDIR`, effective `TMPDIR`, BitBake-idle, QEMU/app process, and runqemu
  listener checks all matched the expected fixed build state.
- One standard exact-tip handoff invocation was launched for feature tip
  `5e46a1ecc97cb1e5e0df76ea1cbecceaa83df103`. The local fixed bundle verifies
  and contains that tip. The helper's final output/exit status was truncated
  and is unavailable; a later local process check found no handoff, SSH, or
  SCP process (only the persistent SSH agent). Process absence does not prove
  successful or failed receiver update, so receiver tip/state is UNKNOWN.
- Current shell and `launchd` have all five `BUILD_*` values unset. The ignored
  `.fluorite-mcp/remote-role.conf` contains only remote-MCP fields and is not an
  authoritative source for the fixed build inbox, receiver, build, or TMPDIR.
  No second transfer or receiver mutation was initiated during reconciliation.
- Astra judgment-only review recommends a fresh read-only receiver check
  before classifying this handoff or retrying it; missing client output alone
  is not a retry condition.
- The local implementation commit was amended to the repository-approved
  role identity after the privacy gate rejected the initial Git metadata.
  No push or Mini transfer had been performed at that original checkpoint.

## Inferences

- If the handoff helper reaches the current TMPDIR check with this configuration,
  it can report failure after already moving the receiver to the bundle tip.
- The check must use an authoritative effective setting or a narrowly proven
  default, and must run before any receiver fetch/checkout.

## Hypotheses

1. The effective `TMPDIR` is the resolved `TOPDIR/tmp` value, whether it comes
   from BitBake's default or an override that evaluates to the same path.
2. The local fixed role value may not match this effective value; this remains
   UNKNOWN until the helper compares them using the exact existing role
   argument. A mismatch must reject before receiver mutation.

Use the successful target-less `bitbake -e` form for the comparison. Do not
run BitBake tasks, create a new TMPDIR, or inspect unrelated caches.

## Success criteria

- Establish the exact effective `TMPDIR` for the fixed build without printing
  role paths into Git-managed logs.
- Move all remote preflight checks ahead of `git fetch` and `git checkout`.
- On any rejected preflight, prove receiver `HEAD` and non-evidence worktree
  status are unchanged.
- On a valid bundle, reuse the existing inbox/receiver/build/TMPDIR, verify
  bundle SHA-256 and exact tip, and prove successful handoff.
- Add focused regression tests for both unchanged-on-failure and successful
  exact-tip handoff. Do not create per-ticket receiver, build, or TMPDIR paths.
- Keep host addresses, hostnames, personal paths, and credentials in the
  existing local role configuration only.

## Plan / Do / Check / Act

### Plan

1. Implement the reviewed plan in
   [the FLR-0351 plan](../../docs/superpowers/plans/2026-09-29-flr0351-mini-handoff-preflight.md).
2. Move every receiver precondition and the effective TMPDIR query ahead of
   `git fetch`/`git checkout`.
3. Exercise failure-without-mutation and success-on-exact-tip regression tests.
4. Run repository verification and, if the fixed local roles are available,
   use only the documented bundle helper for the authorized handoff.

### Do

- Started on `feature-flr-0351-mini-handoff-preflight`; FLR-0350 is Waiting so
  the one-In-Progress limit is preserved.
- Astra judgment-only review could not start because the agent-thread limit
  was full; implementation choices are based on the observed Mini metadata
  query and the documented workflow.
- The receiver helper now queries target-less effective metadata with a client
  timeout and explicit server idle timeout before Git mutation. Local
  integration coverage uses real temporary Git bundles/receivers behind a
  fake SSH transport; missing roles reject before SSH, OE-init/query/TMPDIR
  failures preserve receiver state, and a valid bundle reaches the exact tip.
  Final full repository verification and runtime checkpoint pass.
  A later read-only check with previously recovered values passed. One
  standard handoff invocation followed, but its final result is unavailable;
  the fixed Mini handoff remains UNKNOWN until the current receiver is read
  without mutation. No build or QEMU task was run.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Effective TMPDIR source | Exact effective value resolved and process exits | Target-less `bitbake -e` resolved `TOPDIR/tmp`; the later read-only role probe confirmed the fixed-role match and BitBake idle | PASS (at probe time) |
| Failure preflight ordering | Receiver unchanged before any rejected handoff | Local real-Git tests prove missing roles stop before SSH; unchanged HEAD/index/status/`FETCH_HEAD` on OE-init, metadata-query, and TMPDIR failures; exact-tip success passes | PASS (local integration) |
| Repository gates | Final verification and checkpoint pass | Focused five-test suite, final `make verify`, and final runtime checkpoint all pass | PASS |
| Bundle transport | Fixed inbox and receiver, SHA and exact tip verified | One standard exact-tip invocation was launched; local bundle verifies and contains the expected tip, but final helper output and receiver tip are unavailable | UNKNOWN |
| Current receiver state | Exact expected tip or a safe, idle pre-retry state proven | No active local transfer process; no fresh receiver evidence from the authoritative build roles | UNKNOWN |

### Act

- FLR-0350's diagnostic scripts are locally committed. Do not transfer that
  bundle until this ticket's preflight and exact-tip handoff gates pass.
- Do not mutate the receiver to discover whether the current check passes.
- Do not treat a missing helper result as either success or failure. First
  obtain a fresh read-only receiver revision and process-state check using the
  authoritative fixed build roles. Retry only if that evidence proves the
  receiver is idle and the helper's failure/partial state is safe to replay.
