# Current purpose and feature map

Last updated: 2026-07-19

## Current purpose

この作業区切りの目的は、既存のqemux86-64 artifactを変更せず、Mac QEMU上でのFluorite validationを再現可能な証拠へ変換すること。対象は描画不具合の修正ではなく、boot、explicit app launch、graphics capability、Fluorite readiness/render、crashを別caseとして観測できるTarget Validation基盤である。

## Bounded context and ownership

| Context | Owns | Does not own | Current output |
| --- | --- | --- | --- |
| Target Validation | QEMU target role、session identity、boot/app/render evidence、case verdict | QEMU起動、source root cause | FLR-0017、target_validation MCP |
| Execution | approved QEMU launch/stop runbook、timeout、side effects | render meaning、root cause | 次のrunbook design |
| Fluorite demo | scene/readiness/interaction acceptance | launcher、Vulkan、QEMU command | FLR-0008 handoff |
| Flutter runtime | flutter-auto、engine、surface、thread、app launch contract | scene semantics、GPU diagnosis | FLR-0009 handoff |
| Graphics | Vulkan/Wayland/Mesa/LLVM signal meaning | app launch ownership | FLR-0011 handoff |
| Yocto/AGL | image/source/cache/package provenance | Mac QEMU runtime verdict | FLR-0016 evidence |

## Feature boundary

Current feature is `feature-flr-0017-qemu-evidence-mcp` and owns only FLR-0017, the read-only `target_validation` app-launch/render summarizers, evidence locator/session schema, QEMU runbook input contract, and its working log/handoff summaries.

It does not own BitBake image rebuilds, cache mutation, Raspberry Pi writes, Flutter/Filament/Vulkan source fixes, LLVM root-cause claims, or arbitrary SSH/QEMU execution.

## Ticket state

- `FLR-0017`: In Progress — Plan. Active feature and current WIP.
- `FLR-0016`: Waiting. BitBake metadata observation succeeded, but full manifest/source provenance remains UNKNOWN.
- `FLR-0008`: Next — Plan. Scene acceptance is a downstream handoff, not the current execution scope.

## Work documents

- This purpose/feature map.
- Domain contract: `domains/target-validation/README.md`.
- Feature ticket: `work/tickets/FLR-0017-qemu-evidence-mcp.md`.
- Rendering map: `work/context/fluorite-rendering-stack.md`.
- Evidence transport: `docs/architecture/evidence-handoff-contract.md`.
- Execution boundary: `domains/execution/README.md`.
- Chronological evidence: `work/logs/2026-07-19.md`.
- Evidence index: `work/evidence/FLR-0017-qemu-session.md`.

## Smallest next action

Define one approved QEMU launch profile and one bounded session evidence bundle. Execute at most one short app-launch observation, then hand off app/readiness/render signals to the bounded contexts above.
