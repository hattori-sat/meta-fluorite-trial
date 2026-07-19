# FLR-0025 — Bounded BitBake monitor MCP

Status: In Progress (Do)

## Outcome

Provide a context-efficient, read-only monitor for bounded BitBake runs on the Mini PC. The monitor must expose status, elapsed time, current task, exit code, and a capped log tail without accepting arbitrary SSH, shell, or BitBake arguments.

## Success criteria

- Only the three fixed BitBake target/task profiles are executable; arbitrary shell, argv, SSH input, clean tasks and cache deletion remain rejected.
- `running`, `completed`, `failed`, `timed_out`, `cancelled` and restart-time `unknown` are durable and recoverable by evidence ID.
- Wall-clock and inactivity bounds are independent; capped output and the selected activity source are visible while running.
- A live gate records the BitBake client PID/PGID and classifies observed server/worker PID/PGID topology. A worker outside the owned group blocks a long compile until shutdown handling is revised.
- qemux86-64 effective identity passes before compile, compile exits zero before image, and image exits zero before artifact transfer.
- Kernel/rootfs size and SHA-256 match across build role and Mac before snapshot QEMU starts.
- Fluorite reaches readiness, visible stable render and interaction without crash during the bounded session.

## 4W1H stratification and selected stratum

| Dimension | Stratum |
| --- | --- |
| What | fixed metadata, demo compile, image, artifact transfer, QEMU, explicit Fluorite launch |
| When | one predecessor gate at a time; no image before compile and no QEMU before artifact identity |
| Where | build execution on Linux build role; artifact/QEMU validation on Mac role |
| Who | command supervisor owns launch/evidence; build role executes; target validator judges runtime |
| How | plan confirmation, durable status, bounded tail, PID/PGID and hash evidence |

The selected first stratum is supervisor lifecycle because an ambiguous timeout invalidates every downstream build verdict.

## Process and latest first problem point

`fixed plan -> client launch -> live PID/output/task activity -> terminal record -> compile -> image -> hash transfer -> snapshot boot -> explicit app launch -> verdict`

The latest first problem point is between client launch and trustworthy task activity: task-log changes can prove progress, but the current evidence does not yet prove whether BitBake server/workers share the client PGID.

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
3. The server and active worker remain in the launched client PGID, so group termination is sufficient. A differing PGID refutes this and blocks the long run.
4. A fixed Flutter Engine task-log directory is a valid supplemental signal only during demo compile. Treating it as image-wide activity would allow unrelated/stale writes to mask image inactivity, so the image profile uses combined stdout only.

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

### Live I/O correction

- `run-4013109fd45b4221` proved PID/PGID were live, but output remained at zero until cancellation because buffered `read(4096)` waited for a full buffer or EOF.
- The run was cancelled through MCP after 84.491 seconds; status persisted `cancelled` and exit `-15`.
- Replace buffered reads with `os.read` so available BitBake progress bytes update activity and the bounded tail immediately.
- `run-626abb9801e942d6` then proved live output streaming, but also confirmed a long Flutter engine task needs its fixed `log.do_compile` as a second activity source. The run was cancelled through MCP after 124.471 seconds before changing the monitor.
- Add the manifest-fixed `yocto_compile_logs` root. Changes to bounded `log.do_*`/`run.do_*` markers reset task inactivity without accepting a path from the caller.

## Multi-agent Check — 2026-07-20

### Facts

- PDCA, patch, Yocto and target-validation reviewers independently checked the monitor and downstream loop.
- Fixed commands and destructive-operation rejection passed review.
- Four FLR-0025 commits had non-role Git metadata; values were not recorded. The local feature segment was rewritten to the approved integration role and a metadata privacy regression gate was added.
- The image profile incorrectly reused a recipe-specific activity root; it is removed from that profile.

### Inferences

- Compile task-log activity is useful evidence but is not ownership evidence.
- A short live metadata gate is the smallest safe way to observe actual BitBake topology before allowing a long compile.

### UNKNOWN

- Live client/server/worker PGID topology at the corrected revision.
- Whether the fixed engine task root exists and advances on the build role.
- Compile, image, artifact and runtime outcomes.

### Decision rule

- Standardize the monitor only when local gates pass, effective qemux identity is confirmed, and live topology/activity/terminal persistence match expectations.
- Revise the supervisor before long execution if server/worker ownership or activity association is ambiguous.
- Cancel and roll back only the latest monitor countermeasure if it suppresses real inactivity or cannot terminate its verified scope; never clean caches to force a result.

### Smallest next action

Run local verify/privacy checks, update the remote feature ref with lease protection, fast-forward the build role, then execute the short metadata topology gate.

## Live topology gate — 2026-07-20

### Facts

- Corrected revision metadata run `run-85975b1d8f0146db` completed in 6.987 seconds with exit 0 and durable bounded evidence.
- Compile topology run `run-f950f77adf4a44f5` observed live task-log activity, but the client and Cooker/Worker used different SID/PGID values.
- MCP cancellation persisted `cancelled`, exit `-15`, and 37.269 seconds for the client while Cooker/Worker briefly remained. They subsequently exited; no cache cleanup was used.
- The supervisor now baselines pre-existing BitBake processes, records newly created client/server/worker PID, PPID, PGID and SID, terminates all newly observed owned groups on cancel/timeout, and persists any remaining server processes.
- Local `make verify` passes with 71 Python tests and 52 MCP focused tests.

### Inference

The earlier timeout ambiguity was caused by BitBake daemon lifecycle crossing the client process-group boundary, not by an observed compiler failure.

### Check rule

The next compile may continue only if status shows the new Cooker/Worker group and a deliberate early cancellation proves `remaining_server_processes` is empty. Otherwise revise again before a long run.

### Smallest next action

Commit/push/synchronize the topology fix, run one early cancellation acceptance, then restart the incremental compile for completion.
