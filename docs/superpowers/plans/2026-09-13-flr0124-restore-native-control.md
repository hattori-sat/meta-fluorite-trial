# Restore the native 3D control through Devtool

## Goal

Restore a reproducible C++ native cube control in the current effective
`flutter-auto` source, then prove it with the fixed Mini build and QMP-only
evidence before comparing the Dart Example Demo cube.

## Constraints

- One active ticket: FLR-0124.
- Reuse the fixed Podman Devtool container, bind-mounted canonical repository,
  Mini receiver, build directory, TMPDIR, QEMU profile, and evidence root.
- Do not hand-author a generated patch. Edit the persistent Devtool source,
  commit it in its local Git, and use official `devtool finish --mode patch`.
- Do not launch QEMU until source identity and the patch/build gates pass.
- Do not claim Dart or production-scene success from the control result.

## Steps

1. Record the Mini effective native source identity and applied patch order.
2. Align the persistent Mac Devtool local-Git baseline with that source using
   the existing repository procedure.
3. Edit only the minimal native control and commit it in Devtool.
4. Generate the unchanged patch with official Devtool and register it in the
   canonical layer.
5. Run the Mac recipe gate, commit the canonical layer, bundle it, and hand it
   to the fixed Mini receiver.
6. Run Mini `do_patch`, targeted compile, and full image gates using the fixed
   build/TMPDIR.
7. Run one official QEMU native control, capture QMP early/late PPM plus
   bounded runtime markers, quit through QMP, and analyze the fixed region.

## Decision gates

- If the Devtool baseline cannot be made identical, stop before editing and
  record UNKNOWN.
- If the patch does not apply to the current Mini source, do not hand-edit the
  patch; revise the Devtool source baseline or split a new source-reconcile
  ticket.
- If the control has nonzero 3D pixels, split the Dart comparison into a new
  ticket.
- If the control remains black, split native frame/present diagnosis into a
  new ticket and leave Dart out of scope.
