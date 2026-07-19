# FLR-0018 — Registered QEMU launch runbook

- Status: In Progress — Do
- Priority: High
- Depends on: FLR-0017
- Context: Execution

## Purpose

FLR-0017で確認したqemux86-64 QEMU profileを、任意shellではなく、承認・timeout・snapshot・session evidence outputを持つ固定`command_runner` runbookへ移す。

## Scope boundary

- Owns only the registered QEMU launch/stop process and bounded log ownership.
- Does not interpret Fluorite scene meaning, Vulkan root cause, or LLVM responsibility.
- Does not copy or rebuild kernel/rootfs; it consumes the existing artifact identity supplied by the target role.

## Success criteria

- Fixed runbook manifest and code allowlist accept only finite target/profile choices.
- `-snapshot` is mandatory; timeout and process ownership are recorded.
- Output is a role-local session bundle containing serial log, launch parameters, and optional screen/coredump locators.
- Execution remains disabled by default and requires ticket-bound plan, confirmation, and MCP host approval.
- Target Validation MCP can consume the resulting session bundle without arbitrary command access.

## Current implementation state

- Fixed manifest `qemux86-64-fluorite` is installed and catalog allowlisted.
- The command is target-mutation, but execution remains disabled by default and no real runbook execution has been requested through `command_runner`.
- Current executor retains bounded output in run log/audit; role-local session bundle persistence is still a gap and must be resolved before declaring this ticket Done.
- `describe_runbook` and `plan_runbook` were exercised with image identity `qemux86-artifact-20260405160535`; the plan reported `execution_enabled=false`, `risk=target_mutation`, `qemu_artifact` root, exact fixed argv, mandatory `-snapshot`, and 120-second timeout.
- No `execute_runbook` or `start_runbook` call was made.

## Current evidence

- FLR-0017 current session reached explicit Fluorite app launch, Vulkan/llvmpipe initialization, native readiness, event-channel creation, and then SIGSEGV in `libLLVM.so.18.1` after approximately 74 seconds.
- The session log remains outside Git in the current QEMU artifact directory; only its role locator and hash are recorded in FLR-0017/log.

## Smallest next action

Implement and test the fixed runbook in Execution context. Do not enable real execution until its dry-run, privacy, process-cancellation, and artifact-output tests pass.
