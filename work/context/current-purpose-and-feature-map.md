# Current purpose and feature map

Last updated: 2026-09-29

> Historical snapshot: this map records the QEMU validation feature state as of 2026-07-19. `TASKS.md` is the current source of truth for active work; statuses below are retained as historical context and normalized to Waiting where no completion evidence exists.

## Purpose at snapshot date

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

## Feature boundary at snapshot date

The feature at the snapshot date was `feature-flr-0018-qemu-launch-runbook`, owning only FLR-0018, the fixed Execution runbook, target-mutation approval boundary, bounded timeout/snapshot contract, and session-output handoff. FLR-0017 was then held under Check; neither status is current.

It does not own BitBake image rebuilds, cache mutation, Raspberry Pi writes, Flutter/Filament/Vulkan source fixes, LLVM root-cause claims, or arbitrary SSH/QEMU execution.

## Ticket state at snapshot date

- `FLR-0015`: Waiting. Implementation, full verification, and delivery evidence are not recorded.
- `FLR-0017`: Waiting. Historical launch/readiness/crash observation is retained; closeout and persistent evidence contract remain incomplete.
- `FLR-0018`: Waiting. Runbook execution was not started; session-bundle persistence remains a gap.
- `FLR-0025`: Waiting. Local implementation is recorded; live Mini process-topology and end-to-end acceptance remain unverified.
- `FLR-0016`: Waiting. BitBake metadata observation succeeded, but full manifest/source provenance remains UNKNOWN.
- `FLR-0008`: Next — Plan at the snapshot date. Scene acceptance was a downstream handoff, not that feature's execution scope.

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
