# FLR-0406 — make the serial-exec echo-off gate deterministic

- Status: Done (serial-harness scope only; no rendering claim)
- Priority: High
- Created: 2026-10-02
- Owner: QEMU runtime harness / bounded mock serial server / regression-test roles
- Trigger: FLR-0405 same-boot wall-clock query was blocked before guest dispatch
- Work unit: diagnose and make the existing serial-exec setup gate deterministic; no product/image change
- Branch: `feature-flr-0406-serial-exec-gate` from `dev-flr-0405-first-fault` at `c37ee7c`
- Plan: [saved implementation plan](../../docs/superpowers/plans/2026-10-02-flr-0406-serial-exec-gate.md)

## Problem

FLR-0405 could not dispatch its bounded guest journal query. Two calls to the
unchanged local/Mini `scripts/qemu-runtime-harness.sh serial-exec` returned
`FAIL reason=echo-off-response-unexpected`. The first setup transcript was 52
bytes and byte-identical to a prior successful guest-launch setup. The second
was 38 bytes containing two adjacent shell prompts after the first call had
already disabled tty echo. In both attempts the guest command output remained
empty, so no journal query ran. This is an observation-path failure, not
evidence about Fluorite rendering.

## Facts, hypotheses, and UNKNOWN

### Facts

- Local and Mini harness SHA-256 matched:
  `436d010ea6de3a0acd74eac7777b033bbd6add29bdf9fa6f12fc7d4e67f83605`.
- Attempt 1 and 2 both failed before command dispatch with the same result.
- Attempt 1 captured the same complete setup bytes as a previous successful
  launch, while attempt 2 captured two adjacent prompts and no echoed
  `stty -echo` command.
- The bounded query command passed hash, one-line, size, and `sh -n` checks.
- FLR-0405's QEMU was shut down after preserving its QMP/log/PPM evidence; no
  runtime is active for this ticket.
- A bounded local RED mock showed that the current implementation can accept
  the first prompt before the rest of a chunked setup transcript arrives,
  dispatch the requested command once, and print `serial-exec=PASS` without
  observing a per-session setup marker.
- The first post-fix mock modeled a marker in command output but not the same
  nonce echoed as terminal input. Its 11/11 focused and 227/227 Python results
  are retained as observed results but superseded as proof of echo safety.

### Inferences

- The prompt-only recognizer has a premature-readiness failure mode on a
  controlled duplicate-prompt stream. This is a demonstrated harness defect
  class; it does not prove that this exact interleaving caused either FLR-0405
  Mini attempt.

### Hypotheses

1. Residual serial bytes from the previous connection are being consumed as a
   fresh echo-off response. Support: repeated adjacent prompts on attempt 2;
   refute: mocked/replayed stream boundaries show no stale bytes at the next
   command boundary.
2. The current recognizer assumes echo-on command text or one prompt frame and
   rejects a valid already-no-echo response. Support: the second response has
   no command echo and fails; refute: a byte- and chunk-faithful mock reaches a
   different gate with the same observed stream.
3. The first attempt failed for a different framing condition not preserved in
   the transcript. This remains UNKNOWN until the gate reports its exact
   predicate or a faithful test reproduces it.

## Scope and acceptance

- Start with the current `serial-exec` implementation and focused tests; inspect
  the exact gate predicates before editing.
- Build a bounded mock serial server/replay for prompt split across reads,
  already-disabled tty echo, residual/duplicate prompts, and the normal
  echo-enabled path. Do not start QEMU for these tests.
- Ensure a setup-gate failure never dispatches the requested guest command.
- Ensure valid normal and already-no-echo sessions dispatch once and retain the
  exact command exit status/output without mistaking stale prompts for the
  completion marker.
- Run focused tests and the relevant repository verification; report unrelated
  baseline failures separately.
- Do not edit product source, Yocto recipes, image settings, or the FLR-0405
  runtime evidence. After a committed fix, transfer/verify the exact harness
  through the documented handoff before resuming FLR-0405 with a fresh run ID.

## Plan / Do / Check / Act

### Plan

- Compare tolerant prompt parsing with a two-phase echo-off gate. The RED mock
  demonstrated premature dispatch on a prompt-only boundary. A later review
  found that a nonce in the same `stty` command could itself be echoed before
  execution, so the corrected protocol sends nonce-free `stty` first, then a
  nonce-bearing status probe. The first prompt remains only a sequencing
  barrier.
- Record the initial results as superseded; test both echo-on and already-off
  startup states, false-ready echo, nonzero `stty`, chunked duplicate prompts,
  and stale completion output.

### Do

- Replaced the one-phase nonce command with two phases: `stty -echo` stores its
  status without a nonce; after its prompt barrier, a second command prints a
  per-session nonce/status line. Dispatch requires exact status 0, one nonce
  occurrence across the probe transcript, and exactly one final prompt after
  the line. A 50 ms bounded quiet check rejects prompt residue arriving in
  separate TCP reads.
- Made the guest-command completion marker unique per invocation so stale
  output from the former fixed marker cannot complete a new command.
- Reworked the loopback mock to model initial echo-on and echo-already-off,
  second-command echo, nonzero `stty`, prompt residue and duplication split
  across reads, missing marker, exact-once dispatch, command output/status,
  stale fixed completion marker, and global deadlines.
- Removed an obsolete FLR-0350 FIFO-validator call from this serial-exec test
  fixture. It supplied two paths to a CLI that requires a run ID and three
  arguments, and its version-1 sample was not a valid version-2 FIFO gate.
  Serial-exec tests now assert their own output/status contract directly.
- Updated the shell-level QEMU harness contract test to assert the new two-phase
  gate and per-invocation marker instead of pinning the former fixed marker.

### Check

- Focused RED before the harness fix: the mock observed no setup marker,
  recorded one requested guest command, and the old helper returned
  `serial-exec=PASS`; the regression failed as intended.
- The initial one-phase correction reported 11/11 focused and 227/227 Python
  tests passing, but the mock omitted terminal echo of the nonce-bearing input.
  Those results are superseded and are not accepted as echo-safety evidence.
- Corrected `python3 tests/test_qemu_runtime_harness.py`: 16/16 PASS.
  Corrected `make check-python`: 231/231 PASS. These are host-tool tests, not a
  Mini runtime or rendering result.
- The first `make check-qemu-harness` after changing the completion marker
  failed because its static test still required `__FLR_SERIAL_COMMAND_DONE_7B31__`.
  Updating that contract to require per-invocation nonces made
  `make check-qemu-harness` PASS.
- `make check-canonical check-privacy check-shell check-file-sizes
  check-qemu-harness check-runtime-log-slice` — all PASS; shell syntax covered
  59 files and file-size gate covered 2,082 files.
- `bash scripts/runtime-checkpoint.sh verify --ticket FLR-0406 --log
  work/logs/2026-10-02-flr0406.md` — PASS, exactly one active ticket.
- `make check-markdown` — FAIL with the same 11 historical missing links in
  FLR-0338/0339/0340 evidence and old FLR-0391/0395 plans. None points to
  FLR-0406. These unrelated artifacts were not rewritten.
- `git diff --check` passed before the last ticket/task-state update and must be
  rerun after the final documentation edit. Staged checks and Mini handoff
  remain pending.
- The quiet interval is explicitly bounded: it detects bytes delivered during
  50 ms after the final prompt; it cannot guarantee that no later serial byte
  will ever arrive. Per-command completion nonces prevent old fixed markers
  from satisfying the guest-command completion test.

### Act

- Keep FLR-0405 Waiting until the mock-backed gate is verified and the exact
  harness is transferred through the documented Mini handoff. This ticket is
  not a rendering test and cannot establish any 3D acceptance criterion.
- After the exact helper is verified on Mini, resume FLR-0405 using a fresh run
  ID and preserve the original display goal; do not infer that historical
  failure was caused by this gate without matching runtime evidence.

## Impact

- **Build-time:** none; no BitBake or image build.
- **Runtime:** affects only host-driven serial observation. It requires the
  guest shell to execute `stty` and `printf`; failure to prove echo disabled,
  return status 0, or produce the unique marker prevents subsequent command
  dispatch. It adds 50 ms bounded quiet time per successful serial command.
- **Packaging:** none; the QEMU harness is not installed into the image.
- **Integration risk:** a Mini-side run is still required to verify the exact
  transferred harness against the real serial endpoint before FLR-0405 resumes.

## Post-commit handoff preflight (2026-10-02)

- Local commit `b1a9948` is clean, local-only, and not pushed. Post-commit
  canonical, privacy, and FLR-0406 checkpoint checks passed.
- All required `BUILD_*` role variables are unset in the current shell, and
  no role declarations were found in the standard shell startup files, the
  user environment.d directory, or either documented role-file location. No
  SSH/SCP or receiver command was attempted; remote receiver/QEMU ownership is
  therefore UNKNOWN.
- The default local bundle is valid but contains the older FLR-0401 branch tip,
  not `b1a9948`. It was not overwritten. Do not infer a Mini state from that
  stale local bundle.
- Resume handoff only after the existing local build-role configuration is
  loaded. Do not synthesize role values from connection details in chat. Once
  roles exist, verify receiver idleness/cleanliness and exact handoff target
  before invoking the documented bundle helper.

## Subsequent role and Mini-owner recheck (2026-10-02)

### Facts

- The active feature worktree is clean at local commit `c884836`; canonical
  guard passes. The five `BUILD_*` variables remain unset.
- A regular Git-ignored remote-role file exists in the canonical clone. Its
  SSH alias and repository-path fields pass local syntax checks, but
  `expected_project_revision` is not a valid 40-character lowercase commit.
  The official remote-MCP wrapper validates this field before `exec ssh`; the
  attempted `yocto` MCP launch failed closed locally, and no MCP/SSH operation
  occurred through that launcher. The existing bundle remains the older
  FLR-0401 tip and was not overwritten.
- A separate bounded read-only SSH check using the configured alias, batch
  mode, strict host-key verification, and a 20-second bound succeeded. It
  observed one QEMU process (PID 3081118, UID 1000, PPID 3081116; Mini-local
  `ps` start stamp `2026-10-02 23:12:16`, timezone UNKNOWN). No other process
  matched the bounded Flutter/Weston/BitBake/GDB/runqemu-wrapper filters.
- No listener was present on the expected QMP ports 10930–10932. This does not
  rule out a Unix-socket QMP endpoint or establish which image/guest the active
  QEMU owns. Its ticket, run ID, and operator role remain UNKNOWN.
- No QMP command, process signal, receiver inspection/update, build, bundle
  transfer, or second QEMU was issued. The guest's Flutter state is UNKNOWN;
  host process absence is not evidence about guest processes.

### Decision / stop condition

- Do not attach to, stop, replace, or capture from the unowned QEMU. Do not
  start BitBake or transfer a bundle while its ownership and receiver/build
  roles are unresolved.
- FLR-0406 remains In Progress for the exact Mini serial-helper gate;
  FLR-0405 remains Waiting. Resume only after the live QEMU is attributable or
  has independently exited, and a valid local role configuration identifies
  the exact receiver, build directory, TMPDIR, and project revision. Preserve
  the stale bundle until its overwrite target is verified.

### UNKNOWN

- Active QEMU command/profile, QMP socket, image hashes, visual output, owner
  ticket, and whether it is safe to reuse its evidence.
- Mini canonical repository revision/cleanliness, receiver tip/cleanliness,
  active BitBake state, and effective `TOPDIR`/`TMPDIR`.
- Exact FEngine Oops versus unmatched-present order and all production 3D/HUD
  acceptance criteria.

## Follow-up process-state poll (2026-10-02 14:27 UTC)

### Facts

- A bounded SSH query using the same configured alias, batch mode, and strict
  host-key verification found no process record for the previously observed
  PID 3081118; the query emitted the explicit `PID_NOT_PRESENT` marker.
- A process-name-only inventory (`PID`, `UID`, `PPID`, `comm`; no command-line
  arguments) returned `NO_QEMU_PROCESS_MATCHED` at the same check. No QMP
  endpoint, guest, image, or former operator was inspected.
- No process was signaled or launched. No build, transfer, or cleanup ran.

### Decision / UNKNOWN

- The earlier QEMU observation is stale, but this bounded match does not prove
  the Mini is globally idle or identify the prior run/image. Recheck ownership
  immediately before any future start; do not infer availability from PID
  absence alone.
- The five `BUILD_*` roles remain unset and the ignored remote-role config's
  expected revision remains invalid. Do not transfer/build/start QEMU until
  those exact roles and the current repository/receiver state are verified.
- Production Sequoia, HUD composition, input/repaint stability, five-minute
  present, and two independent boots remain NOT MET.

## Mini remote-project identity check (2026-10-02)

### Facts

- Using the already configured SSH alias and the ignored remote-MCP project
  path, a bounded read-only query passed `scripts/assert-canonical-repository.sh`.
- That configured project is on branch
  `feature-flr-0019-qemu-build-iteration-final`, revision
  `6e4ccf125ddccac941a2be74612a4d8bb3d37582`, and its tracked/untracked
  worktree check is not clean.
- The command did not print dirty paths or read file contents. This remote-MCP
  project is not established as `BUILD_RECEIVER`; the five fixed `BUILD_*`
  roles remain unset.

### Decision

- Do not update or use this dirty remote-MCP project as the build receiver.
  Do not infer its intended revision from the local feature HEAD. The required
  Mini receiver/build/TMPDIR roles must come from their authoritative local
  role source, then be verified read-only before transfer or build.
- No source, receiver, build directory, cache, or process was changed.

## Authorized fixed-receiver handoff (2026-10-03)

### Facts

- The approved local build-role tuple was recovered only from the historical
  successful handoff invocation whose receiver revision was
  `9db57cfe92deddf4bc2037e53c871ac7acdb0657`; values are not stored here or
  printed. The dirty remote-MCP project was not used.
- Before replacement, the local active bundle and fixed inbox bundle each
  advertised only `54c02bdcddbf80be579c4fd7d493f5bd24f6df6c`, matching the
  then-current clean Mini receiver and an ancestor of this local feature tip.
  They contained no unique pending receiver revision.
- A read-only process/cgroup check identified the remaining Python process as
  belonging to the existing IVI bridge/gateway container, not a BitBake or
  QEMU owner. Its actual cwd was not readable and remains UNKNOWN. No named
  QEMU/runqemu/Flutter/BitBake owner or reserved-port listener was found.
- The fixed receiver was clean at `54c02bd`; retained `TOPDIR`/`TMPDIR`
  snapshots were stale, so only the documented bounded live metadata check
  could establish the current effective paths.
- One invocation of
  `scripts/handoff-fluorite-bundle.sh 5770cec617bf9d59b11216e9aba762b66efa4cbe 9fb2d8c63bda212d4c17ad8f24698226869a2a37`
  completed successfully. Bundle SHA-256 was
  `9bad41bf0ada8f59722cb56d348e4cd00328c79b85b9fb12c359b5d6ce0ec752` on
  local and remote; effective `TOPDIR` and `TMPDIR` checks passed; the fixed
  receiver is exact tip `9fb2d8c63bda212d4c17ad8f24698226869a2a37` and clean.
- No `do_patch`, compile, image build, QEMU start, process signal, or change to
  the dirty remote-MCP project occurred.

### Decision / next check

- The obsolete active bundle was replaced only after its unique advertised tip
  was proved present as the receiver's current revision; the one canonical
  handoff helper remained the only transfer/update mechanism.
- FLR-0406 stays In Progress until the transferred focused tests pass on Mini
  and the modified serial gate is exercised on the real serial endpoint in a
  fresh, single-owner FLR-0405 run. Product rendering acceptance remains open.

## Closeout — Mini serial endpoint verification (2026-10-03)

### Check

- On the exact transferred receiver tip `9fb2d8c63bda212d4c17ad8f24698226869a2a37`,
  `python3 -B tests/test_qemu_runtime_harness.py` passed 16/16.
- In one exact-0334 FLR-0405-0002 runtime, all serial-exec commands returned
  `rc=0` without the previous echo/prompt-gate failure or a command timeout;
  GDB returned successfully with zero stopped threads.
- The shared 0405 observation remained inconclusive for rendering: the QMP
  stills preceded the first present, no Oops was recorded, and the present
  return/order details belong to FLR-0405. The remote MP4 encoder failed, but
  this does not invalidate the serial-gate result.
- App stop, negotiated QMP quit, wrapper/process cleanup, port release, and
  unchanged 0334 artifact hashes passed.

### Outcome

- Mark this ticket Done for its bounded harness deliverable: the deterministic
  setup/nonce gate has local unit coverage and has operated against the real
  Mini QEMU serial endpoint. No product code, Yocto recipe, image, or runtime
  rendering defect was fixed or declared successful here.
- Remaining 3D/display work stays open in FLR-0405 and its follow-up runtime
  evidence.
