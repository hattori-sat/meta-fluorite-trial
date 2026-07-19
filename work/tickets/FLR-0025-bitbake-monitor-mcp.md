# FLR-0025 — Bounded BitBake monitor MCP

Status: Inbox (Next chat)

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
