# FLR-0196 — fix readback callback API compatibility

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Mini compile role
- Created: 2026-09-15
- Predecessor: [FLR-0194](FLR-0194-readback-direct-fixture-swapchain.md)
- Working log: `work/logs/2026-09-15-flr0193.md`

## Work unit

Make the fixture-gated swapchain readback diagnostic compile against the
pinned Filament API without changing production behavior or hand-editing the
generated Yocto patch.

## Facts

- Mini `do_patch` passed at receiver revision `7c63e9e3853f...`.
- Mini `do_compile` failed at `view_target.cc:874` in the new diagnostic.
- The pinned `filament::backend::BufferDescriptor::Callback` is
  `void(*)(void* buffer, size_t size, void* user)`.
- The diagnostic passed a capturing lambda, which cannot convert to that
  function-pointer type.
- Existing source uses a non-capturing callback plus the `user` argument for
  buffer ownership, so that is the compatible implementation path.

## Hypotheses

1. **Leading:** a non-capturing Filament callback with a heap-owned context
   will compile and preserve the readback statistics.
2. **Alternative:** the pinned Filament header differs between the Mac source
   environment and the Mini recipe sysroot; a Mini header probe will falsify
   this if the signatures are not the same.

## Success criteria

- [x] Edit the existing Mac Devtool source workspace only.
- [x] Regenerate the official patch through the corrected Devtool helper and
  commit the canonical layer change locally.
- [x] Mini `do_patch` and `flutter-auto:do_compile` pass on the fixed
  build/TMPDIR.
- [x] Return ownership of the runtime readback result to FLR-0194 without
  starting QEMU from this compile-only ticket.

## Plan / Do / Check / Act

### Plan

Replace the capturing callback with a non-capturing function-pointer callback
and pass width/height/pixel count through the descriptor `user` context. Keep
the environment-variable gate and callback statistics unchanged.

### Do

FLR-0194's Mini do_patch passed, then do_compile failed with the exact API
boundary recorded above. The source was corrected through the persistent Mac
Devtool workspace, and the complete patch was regenerated and bundled. No
QEMU run was started from this compile-only ticket.

### Check

Mac Devtool regeneration, Mini do_patch, and Mini do_compile passed at receiver
revision `2dfaee6ae21a...`. The complete patch SHA256 is
`880f7979eaa8325d1e928911d6259f7fc4fa7b2ec646d51002470341f8160ec7`.

### Act

Resume FLR-0194 for the image and QMP/readback comparison.
