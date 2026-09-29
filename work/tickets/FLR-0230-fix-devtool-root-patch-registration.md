# FLR-0230 — fix Devtool root-vs-plugin patch registration

- Status: Inbox
- Priority: Medium
- Owner: Devtool finish helper and Yocto recipe registration role
- Created: 2026-09-20
- Predecessor: FLR-0229

## Objective

Make the canonical finish helper derive `patchdir` from the official generated
patch path instead of applying `ivi-homescreen-plugins` to every patch under
the Toyota recipe files directory.

## Facts

- FLR-0229 generated a root-level `flutter-auto` patch that changes
  `shell/wayland/window.cc`.
- The helper initially registered that patch with
  `patchdir=ivi-homescreen-plugins`, which would send a root-level patch to the
  wrong apply directory.
- The generated patch bytes were correct; only the recipe registration was
  wrong and was corrected manually for FLR-0229.

## Success criteria

- A generated patch whose paths start at `shell/` receives root-scoped
  `file://...` registration.
- A generated patch whose paths start at `ivi-homescreen-plugins/` retains
  `patchdir=ivi-homescreen-plugins` registration.
- Both cases are contract-tested without changing patch bytes.

## Scope boundary

Do not change FLR-0229 source behavior or rerun its QMP experiment in this
workflow-only ticket.

## Evidence

- Predecessor: [FLR-0229](FLR-0229-isolate-output-enter-pixel-ratio-repaint.md)
