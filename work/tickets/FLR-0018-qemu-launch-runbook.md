# FLR-0018 — Registered QEMU launch runbook

- Status: Next — Plan
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

## Current evidence

- FLR-0017 current session reached explicit Fluorite app launch, Vulkan/llvmpipe initialization, native readiness, event-channel creation, and then SIGSEGV in `libLLVM.so.18.1` after approximately 74 seconds.
- The session log remains outside Git in the current QEMU artifact directory; only its role locator and hash are recorded in FLR-0017/log.

## Smallest next action

Implement and test the fixed runbook in Execution context. Do not enable real execution until its dry-run, privacy, process-cancellation, and artifact-output tests pass.
