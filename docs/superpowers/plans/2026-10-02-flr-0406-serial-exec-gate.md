# FLR-0406 — deterministic serial-exec setup gate

## Outcome and boundaries

Make the existing serial-exec observation gate deterministic using a local
mock serial endpoint. Do not start QEMU, run BitBake, change product source,
or alter FLR-0405 runtime evidence. Preserve the full Fluorite display goal;
this is only an observation-tool prerequisite.

## Facts

- FLR-0405's two same-boot guest queries failed before guest-command dispatch
  with `echo-off-response-unexpected` and empty command output.
- The second setup capture contained two adjacent prompts after tty echo had
  already been disabled. The first failure's exact rejecting predicate remains
  UNKNOWN.
- The current recognizer accepts only one prompt at the end of the captured
  setup response, with either no preceding text or exactly `stty -echo`.
- An existing test uses a local TCP serial mock. It can assert that no guest
  command is dispatched when setup has not been proven.

## Ranked hypotheses and discriminators

1. **A serial-stream boundary ambiguity is the primary defect.** The serial
   endpoint is persistent while TCP connections are short-lived, so delayed or
   duplicate prompt bytes can be attributed to the new echo-off response.
   Support: replayed duplicate-prompt transcript fails the current exactly-one
   predicate, and a unique setup marker gives a deterministic boundary.
   Refute: a chunk-faithful mock shows that duplicate bytes cannot cross the
   setup-command boundary and another exact predicate is responsible.
2. **The gate overfits echo-enabled output.** A shell already in no-echo mode
   may not emit the command text and can produce a different valid response.
   Support: a no-echo mock fails before command dispatch while the equivalent
   echo-enabled mock passes. Refute: both fail only when duplicate/stale bytes
   are introduced.
3. **The failure is later in command framing, not setup.** This is lower
   likelihood because both recorded attempts had zero guest-command output and
   returned the setup-gate error. Refute/confirm by separately asserting that
   the requested command is sent exactly once only after setup acceptance and
   that its completion marker/status are parsed exactly.

Compare two implementation paths:

- Tolerate multiple prompt-shaped lines. This is a smaller parser change but
  risks treating stale output as proof that the shell is synchronized.
- Send a controlled echo-off setup command that emits a per-session unique
  marker, then require that marker and the final prompt before dispatch. This
  establishes a boundary independent of command echo and tolerates earlier
  prompt residue without using it as readiness evidence. Prefer this path if
  mock tests support it.

## Execution plan

1. Move FLR-0405 to Waiting with the explicit dependency on FLR-0406; promote
   FLR-0406 to the sole In Progress ticket. Update the 0405/0406 PDCA and
   working log, and locally commit the transition without pushing.
2. Create a local `dev-flr-0405-first-fault` transition checkpoint at the
   recorded 0405 tip, then create `feature-flr-0406-serial-exec-gate` from that
   checkpoint. Re-run the canonical guard before implementation.
3. Extend the existing loopback TCP fixture to model prompt chunks, echo-on,
   already-no-echo, duplicate prompt residue, missing marker, command dispatch
   count, command output, and nonzero status. Add the smallest regression first
   and run it against the unchanged implementation to record RED.
4. Implement only the serial-exec setup gate needed by the failing test. Keep
   failures fail-closed: no guest command before the unique setup marker and
   final prompt are both observed. Preserve bounded I/O and transcript output.
5. Run focused serial-exec tests, the complete Python harness tests, relevant
   shell/static/contract checks, privacy/checkpoint/markdown/whitespace gates,
   and inspect the final diff. Report unrelated baseline failures separately.
6. Update FLR-0406 Plan/Do/Check/Act and working log with exact commands,
   results, and test counts; update FLR-0405 as blocked only by the observation
   gate and retain its runtime UNKNOWN. Locally commit the ticket-scoped change;
   do not push.
7. Stop before another QEMU run. Resume FLR-0405 only through its existing
   documented Mini handoff, after verifying the exact transferred harness and
   using a fresh run ID.

## Verification / exit criteria for this ticket

- Regression is observed failing before the implementation change and passing
  afterward.
- Echo-on and already-no-echo sessions each dispatch the requested command
  exactly once and preserve exact output/status.
- Prompt chunking and stale/duplicate prompt residue do not cause premature
  dispatch; missing/invalid marker fails closed with zero guest dispatches.
- Focused and repository-relevant tests pass, or remaining baseline failures
  are isolated and recorded.
- No QEMU, build, product-source, image, or cache state is changed.
- FLR-0405 remains Waiting/UNKNOWN; neither diagnostic gate success nor ticket
  closure is represented as 3D display success.
