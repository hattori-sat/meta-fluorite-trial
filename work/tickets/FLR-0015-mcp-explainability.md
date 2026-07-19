# FLR-0015 — Make MCP evidence explainable

- Status: In Progress — Do
- Priority: High
- Depends on: FLR-0001
- Context: [evidence and handoff contract](../../docs/architecture/evidence-handoff-contract.md)

## Problem

MCP safety annotations explain whether a tool is read-only or state-changing, but
they do not explain why an observation can be trusted, what it does not prove, or
what the next bounded query should be.

## Success criteria

- Every envelope exposes transport-level explainability metadata.
- Evidence basis, non-causal boundary, limitations, and next actions are explicit.
- Domain payload vocabulary remains owned by each bounded context.
- Unit tests reject accidental omission or causal overclaiming.
- `make verify` passes and a small PR is opened against `dev-foundation`.

## Minimal countermeasure

Add an `explainability` block derived from the existing evidence ID, unknowns,
warnings, truncation state, and next-query contract. Do not add unsupported
numeric confidence or infer root causes in the MCP kernel.

## Out of scope

- A causal inference engine.
- Automatic hypothesis generation.
- Changes to AGL, Yocto, Flutter, Filament, Vulkan, or target execution.
