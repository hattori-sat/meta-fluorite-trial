# FLR-0400 — bounded live-observer polling for the exact 0334 image

> Fix the observation boundary exposed by FLR-0399. Each guest serial request
> returns one bounded state snapshot; the host polls against one monotonic
> deadline and captures the first identity-bracketed live frame, including
> while the state is still WAITING. Do not modify the product scene or image.

**Ticket:** `work/tickets/FLR-0400-bounded-live-observer-polling.md`

**Branch:** `feature-flr-0400-snapshot-deadline-polling` (local only; no push)
**Milestone base:** `dev-flr-0396-sequoia-material-parity` at
`b0b7f8ede77178412240475dd582ffa5641c309d`
**Immediate dependency:** FLR-0399 at `9db57cfe92deddf4bc2037e53c871ac7acdb0657`
**Image:** reuse the already-built FLR-0396/patch-0334 candidate; no rebuild.
**Fresh run:** `flr0400-0001`; FLR-0399's consumed `flr0399-0001` is frozen.

## Facts and problem boundary

- FLR-0399's single runtime attempt launched the exact 0334 image and
  `/usr/bin/flutter-auto` as UID 1001. At the sampled state, the exact process
  was live but READY, present-begin, and present-return were all zero.
- Its guest `ready` command can loop 100 times, running several external
  `grep`/`awk` commands plus `sleep 0.2` on every pass. The host serial-exec
  deadline is 40 seconds; the outer observer deadline is 48 seconds.
- The `ready` request timed out at 39.5266 seconds. A later bounded
  `collect.setup.serial.log` contained a late `WAITING` marker, and the next
  request correctly failed closed on `echo-off-response-unexpected`. Evidence
  preservation and exact QEMU teardown then passed. No live Flutter QMP frame
  was captured, so Sequoia pixels remain UNKNOWN.
- The FLR-0399 parser maps syntactically valid `WAITING` to `TIMEOUT` for the
  ready/present stages, and `run_once` does not poll that state.
- No product, material, texture, camera, light, recipe, image, or build input
  is in scope. The local source tree is clean at the FLR-0399 commit; this
  ticket is stacked because it depends on the observer code not yet merged to
  the milestone branch. The review boundary is the diff from that commit.

## Hypotheses and chosen path

1. **Nested guest-loop latency is the immediate orchestration defect.** The
   long command can exceed the enclosing serial request, allowing a late reply
   to contaminate the next protocol phase. This matches the recorded timeout
   and late WAITING bytes. A single-snapshot command followed by bounded host
   polling should falsify this if each request still overruns its short
   per-call budget.
2. **Serial framing or guest responsiveness is an independent alternative.**
   If a one-snapshot command still times out, retain its setup transcript and
   stop; do not weaken the fail-closed echo/response check. That result would
   separate transport/guest responsiveness from the removed in-guest loop.

Compared with simply increasing the serial timeout, one snapshot per request
keeps each protocol transaction bounded, prevents a guest-side polling loop
from outliving its parent request, and allows a live QMP frame before READY.
The host owns one monotonic total deadline (120 seconds), polls every 2 seconds,
and caps each state request at 15 seconds or the remaining budget, whichever is
smaller. WAITING never resets that deadline.

## Tasks (TDD)

### 1. Record the failed attempt and open this unit

- [x] Move FLR-0399 to Waiting without changing its failed-run evidence or
  retrying its consumed run ID.
- [x] Add FLR-0400 as the sole In Progress ticket; record the branch-policy
  exception, fixed-image provenance, task/run IDs, and source-boundary facts.
- [x] Update `TASKS.md` and this ticket's working log; keep runtime artifacts
  outside Git.

### 2. Tests first

- [x] Change the parser contract test so valid WAITING remains WAITING; retain
  rejection tests for malformed, duplicate, and identity-free live markers.
- [x] Prove the guest ready/present command performs one bounded snapshot and
  contains no guest-side polling loop; do not assert its exact shell string.
- [x] Add deterministic `run_once` tests using an injected monotonic clock,
  sleeper, state provider, and capture adapter: first WAITING frame is captured
  once with a stable PID/UID/start identity; WAITING then READY/PRESENT advances
  under the same deadline; repeated WAITING cannot extend that deadline.
- [x] Prove deadline expiry starts no extra state read or capture, evidence is
  preserved before teardown exactly once, and teardown is exactly once.
- [x] Keep localhost serial-exec regressions and strict stale-response rejection.

### 3. Minimal implementation

- [x] Replace the guest-side repeated gate with one short state snapshot that
  emits WAITING/READY/PRESENT/EXITED/FAULT and the exact process identity and
  readiness counters.
- [x] Keep WAITING as a first-class parser result. Poll on the host every
  2 seconds using one absolute monotonic deadline and unique serial evidence
  labels; never issue a read or capture after expiry.
- [x] Capture a full QMP still and one short four-frame video at the first live
  sample (WAITING when that is first, otherwise READY); preserve existing
  identity-bracketed READY and first-PRESENT stills. A WAITING capture is
  evidence only, not a renderer pass.
- [x] Permit the existing ticket-scoped 0399 helper/controller to execute the
  new `flr0400-0001` run in its fresh evidence directory. Keep the 0399 module
  and protocol marker names as implementation provenance; record this
  namespace reuse explicitly. Do not duplicate the runner or alter the QEMU
  image/profile.

### 4. Verify and run once

- [x] Run focused tests, syntax checks, privacy/canonical gates, MCP smoke,
  independent gates, file-size gate, and the relevant full verification. Keep
  the existing FLR-0397 stale-test failure explicitly separate. One working
  log heading-contract miss was detected by checkpoint verification and
  corrected; checkpoint now passes with active=1. Final staged whitespace,
  privacy, and canonical checks also pass.
- [ ] Commit the scoped code/tests and the three task records locally only; do
  not push. Use the official Git-bundle handoff helper, not a hand-built copy.
- [ ] Immediately before QEMU, recheck Mini receiver tip, exact image hashes,
  QEMU/Flutter/BitBake/Devtool/GDB ownership, ports, QMP socket, and fresh
  evidence path. Preserve unrelated processes.
- [ ] Run exactly one QEMU observation with `flr0400-0001`, no BitBake build.
  Inspect the entire full-screen QMP still/video and save bounded runtime
  evidence before teardown. Confirm exact process/socket/port cleanup.

## Impact and boundaries

- **Build-time / packaging:** none; reuse the exact existing image.
- **Runtime:** observation cadence changes only; the first identity-bracketed
  live QMP frame also saves one four-frame/one-second video. Later captures are
  stills. The app's rendering/input behavior is unchanged.
- **Integration risk:** repeated serial labels and run-ID validation must stay
  unique and fail closed. The FLR-0399 protocol labels are retained only for
  shared-helper compatibility and must not be confused with the FLR-0400 run.
- **Visual conclusion:** only an identity-bracketed full-frame screenshot can
  establish what was visible. READY, present markers, a live process, a fixture,
  or a post-exit black frame do not pass the Sequoia gate.
- **Overall goal:** this observer ticket cannot complete the user's product
  acceptance criteria. If it captures no colored production Sequoia, create
  the next focused product/runtime ticket from the first preserved boundary;
  do not reclassify UNKNOWN as failure or success.
