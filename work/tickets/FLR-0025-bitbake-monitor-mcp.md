# FLR-0025 — Bounded BitBake monitor MCP

Status: In Progress (Do)

## Outcome

Provide a context-efficient, read-only monitor for bounded BitBake runs on the Mini PC. The monitor must expose status, elapsed time, current task, exit code, and a capped log tail without accepting arbitrary SSH, shell, or BitBake arguments.

## Facts

- The existing `yocto` MCP can list/read bounded task logs and the `command_runner` MCP owns fixed asynchronous runbooks.
- SSH does not disable MCP. `scripts/run-remote-mcp.sh` runs the fixed `agl`, `yocto`, and `command_runner` servers on the build role with validated role configuration.
- Current `command_runner` run status is process-local and does not survive MCP restart.
- The recent demo compile was launched outside the MCP, so its timeout marker was not reliably persisted; task logs remained available for evidence.

## Design constraints

- Use a fixed ticket-bound runbook for one of a finite set of BitBake targets/tasks.
- Start asynchronously, poll with `get_run_status`, and read capped logs with `read_run_log`.
- Persist a redacted completion record under the configured build-role audit root so a new chat can resume from an evidence ID.
- Reject arbitrary command, target, cache path, clean task, and SSH parameters.
- Keep build execution disabled by default and require the existing dual approval gates.

## Smallest next action

Implement a fixed `yocto-demo-compile` monitor manifest plus lifecycle persistence, then add protocol/unit tests before using it for the next incremental compile.

## Design decision — 2026-07-20

### Facts

- `mcp/runbook.py` already owns fixed manifest resolution, execution gates, asynchronous threads, `start_new_session=True`, bounded output capture, and `os.killpg` cancellation.
- Existing completion audit events are redacted JSONL, but status lookup was process-local and successful runs were labelled `succeeded`.
- `make verify` passed before and after the implementation change.

### Inferences

- Extending the existing supervisor preserves the fixed target/task and dual approval boundary with less integration risk than adding a second daemon.
- A durable audit reader can resume completed evidence after MCP restart without replaying a build or exposing arbitrary paths.

### Hypotheses

1. Persisting PID/PGID and distinguishing `timed_out` from `failed` will make timeout evidence sufficient to avoid treating an external client timeout as a BitBake failure. This remains to be checked on a live Mini PC run.
2. Combined BitBake task output is a sufficient first inactivity signal for the bounded compile. If a live engine build updates only `log.do_compile` and not client output for 1800 seconds, this hypothesis is refuted and the activity source must be narrowed to the fixed task log.

### UNKNOWN

- Mini PC branch/status is synchronized at `3d124ae` before the monitor commit; the target build directory exists and has no current deploy artifact.
- BitBake server/worker PID discovery and task-output inactivity behavior have not yet been validated on the build host.

### Evidence IDs

- `EV-FLR-0025-local-verify-20260720`: canonical guard, privacy, 66 unit tests, 48 MCP focused tests, protocol smoke, links and file-size checks all PASS.
- `EV-FLR-0025-local-lifecycle-20260720`: implementation records child PID/PGID, emits `completed`/`timed_out` lifecycle states, and exposes `read_completion`.

### Smallest next action

Commit/push the fixed monitor, fast-forward the Mini PC, configure the Git-ignored build-role roots, then run the metadata gate before the bounded demo compile.

## Implementation — 2026-07-20

### Facts

- Production allowlists three new manifests: `yocto-metadata-gate`, `yocto-demo-compile`, and `yocto-image-build`.
- No manifest accepts parameters; target, task, build root and environment profile are fixed.
- Wall-clock and task-output inactivity limits are independent and persist `timeout_kind`.
- The supervisor starts a new session, records PID/PGID and bounded `/proc` process-group membership, and terminates only its owned PGID.
- Redacted `fluorite.run-status/v1` JSON is atomically persisted under the audit root and is readable by run/evidence ID after restart.
- `cleanall`, `cleansstate`, cache deletion, arbitrary shell/argv/path/SSH inputs remain absent.
- Local `make verify` passes with 67 unit tests and 49 MCP focused tests.

### Smallest next action

Commit/push and synchronize the build role, then execute `yocto-metadata-gate` for FLR-0025.

## Live Check — 2026-07-20

### Facts

- Commit `7547631` was pushed and both Mac and Mini PC were synchronized cleanly.
- Metadata gate `run-55876289c4b14770` completed with exit 0 in 7.192 seconds; its output digest and durable record were persisted.
- Three earlier metadata attempts failed before BitBake startup while narrowing the Git-ignored environment wrapper contract. No build/cache cleanup occurred.
- Demo compile `run-54a3d817112d4cdd` started, but `running` status exposed no active step until completion. It was cancelled through MCP after 107.726 seconds; the owned process group exited with signal 15 and status `cancelled`.

### Problem point

The first implementation appended a step record only after `_capture` returned. Therefore PID/PGID and log data existed at completion but were unavailable during the interval when monitoring mattered.

### Countermeasure

Create the active step before process launch, update its PID/PGID, bounded process membership and capped output tail every two seconds, and atomically persist each snapshot. Retain full-stream byte count and digest while storing only the tail.

### Smallest next action

Verify, commit/push the live-status correction, synchronize the Mini PC, and restart the same incremental demo compile.
