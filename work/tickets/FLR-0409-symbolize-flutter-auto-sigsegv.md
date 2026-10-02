# FLR-0409 — resolve exact flutter-auto SIGSEGV symbols

- Status: In Progress
- Priority: High
- Created: 2026-10-03
- Owner: existing Yocto package/debug artifacts / Mini evidence role / GDB-symbolization role
- Branch: `feature-flr-0409-symbolize-flutter-auto-sigsegv`
- Depends on: [FLR-0408](FLR-0408-replay-known-positive-sequoia-profile-on-0334.md), evidence run `flr0408-0001`, checkpoint `6bc260c`
- Plan: [FLR-0409 bounded symbol-recovery plan](../../docs/superpowers/plans/2026-10-03-flr0409-symbol-recovery.md)
- Working log: [FLR-0409 working log](../logs/2026-10-03-flr0409.md)

## Objective and boundary

Use only already-existing image/package/debug/link/install artifacts to find
symbols that exactly match the crashed `flutter-auto` executable from the 0334
image. If an exact match exists, resolve the faulting instruction and caller
chain far enough to identify the first defensible source boundary. If none
exists in the bounded approved search scope, record the checked locations and
stop with symbols unavailable. Do not regenerate artifacts in this ticket.

This is crash-boundary symbolization, not a rendering verdict or a product fix.
It does not reopen the FLR-0408 QEMU run: that process has exited and no live
QMP frame exists. Sequoia/HUD pixels remain UNKNOWN.

## Facts

- FLR-0408 used the exact 0334 rootfs SHA-256
  `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`, with
  the matching kernel and qemuboot hashes documented in its ticket.
- `flutter-auto` PID 765 / UID 1001 / start token 239895 ended with SIGSEGV at
  `2026-10-02T22:35:52Z`. Its core is retained at
  `$EVIDENCE_ROOT/flr0408-0001/qemu/core-pid765.elf.zst` on the Mini, SHA-256
  `9961abd4e8adc9fb69298e43772fd7674e486df0a85617fe8ff8f18a865548b0`.
- The mapped executable was stripped `/usr/bin/flutter-auto`, Build-ID
  `529c5d321d81192f82f146d9d23736722aec2208`; no matching guest
  `/usr/lib/debug/.build-id` file was found during FLR-0408.
- GDB recorded signal thread LWP 812, `SEGV_MAPERR`,
  `si_addr=RAX=0x7f0a79cbc1c4`, and RIP `0x56032183498d`. The decoded instruction was
  `mov (%rax),%rax`. The instruction lies in the mapped executable at the
  currently recorded mapping-relative offset `0xd5198d`.
- The mapped GDB transcript is retained at
  `$EVIDENCE_ROOT/flr0408-0001/qemu/gdb-core-pid765-mapped.out`, SHA-256
  `5fa2e889fbe4101db4217e0a1a052c83575aa9ed3ac190067be1afead1b626a7`.
- The transcript contains unresolved application frames. The core and original
  image were not copied to the Mac or committed. FLR-0408 captured no QMP
  screenshot or video.

## Inferences

- The immediate invalid read occurred while executing a mapped instruction
  belonging to the stripped main executable. This does not prove the app code
  created the invalid pointer; a caller, library, or earlier state corruption
  may have supplied it.
- `0xd5198d` is not automatically the address accepted by `addr2line`; the
  exact ELF, program headers, core mapping, and PIE load bias must be correlated
  before symbolization.
- A function name or successful backtrace would locate a failure boundary but
  would not alone establish the pointer's origin or the product root cause.

## UNKNOWN

- Whether any already-existing package/debug/link artifact contains exact
  symbols for Build-ID `529c5d321d81192f82f146d9d23736722aec2208`.
- Which function and caller chain contain the fault; the existing stack is
  stripped and its pointer origin is unresolved.
- Whether the immediate invalid read originated in Flutter, Filament, Mesa/
  LLVM, another library, an API/lifetime boundary, or prior memory corruption.
- Whether this crash is related to scene construction, the unmatched present,
  rendering, or display output. FLR-0408 has no live QMP pixels, so Sequoia/HUD
  visibility is UNKNOWN.

## Ranked hypotheses and falsifiers

1. **The faulting component formed or retained a stale/invalid pointer.**
   Support would require exact symbols and surrounding code showing the value
   is derived/used inside that path without an invalid incoming argument.
   Falsify or weaken it if a resolved caller demonstrably supplies the invalid
   value across a defined API boundary.
2. **An upstream caller/API/lifetime boundary supplied the invalid pointer.**
   Support would be a resolved frame/argument path showing the value arrives
   from a caller or resource handle before the faulting dereference. Weaken it
   if the incoming value is valid at the call boundary and becomes invalid
   within the faulting routine (not yet observable from this core alone).
3. **Earlier memory corruption or optimized/incomplete unwind obscures the
   pointer's origin.** Support would be inconsistent/corrupted saved state or
   an unusable caller chain even with matching symbols. Falsify only with
   stronger independent runtime evidence; absence of such evidence here is
   not proof that corruption did not occur.

## Search and execution boundary

Follow this order, using paths established from the exact image manifest and
existing environment documentation:

1. Read the exact image's package manifest and existing package metadata; look
   for already-produced `flutter-auto` debug packages, split debug files, or
   deployed debug artifacts. The ELF Build-ID must match exactly.
2. If absent, inspect only the identified recipe's existing link/install
   outputs for the final unstripped executable or separate debug file. Do not
   run a task to regenerate an output.
3. If exact executable symbols are absent, inspect only directly associated
   existing maps/objects/source and report them as partial leads, not exact
   symbolization.
4. For any candidate, verify Build-ID, architecture, executable sections, and
   PIE load bias using the saved core mapping and ELF program headers before
   resolving RIP and frames. Preserve the input artifact in place.

No BitBake task, build, QEMU start, guest package installation, cache cleanup,
source mutation, Devtool action, branch change in another worktree, or copying
the raw core/image to the Mac is in scope. Do not inspect unrelated caches or
other tasks' build outputs. Stop if the next step would mutate shared state or
needs an artifact-owner handoff.

## Success criteria

- Revalidate the recorded core/transcript identities without moving the large
  artifacts; record commands, role paths, hashes, and access result.
- Identify the exact image/package/recipe metadata and inspect only the
  corresponding existing package/debug and link/install paths.
- If a matching symbol file exists, verify its Build-ID and ELF mapping, then
  produce a bounded symbolized instruction/caller report for LWP 812 and state
  what the surrounding source does and does not prove.
- If none exists, record the specific metadata and artifact paths checked,
  conclude `EXACT_SYMBOLS=UNAVAILABLE`, leave caller/component/root cause
  UNKNOWN, and stop without recreating symbols.
- Keep pixel state UNKNOWN. Do not claim any Sequoia, HUD, renderer, present,
  or final product acceptance from this ticket.
- Record clean read-only completion, evidence hashes, and the next separate
  ticket needed to obtain symbols or resume live visual validation.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | exact Build-ID symbol availability and faulting instruction/caller |
| Where | existing 0334 image/package/debug/link/install outputs and preserved core |
| When | after the FLR-0408 process exited and before any new runtime replay |
| Who | image/package owner role, Mini evidence role, symbolization role |
| How | read-only manifest-to-recipe-to-existing-artifact search; GDB/ELF mapping check |

## Plan / Do / Check / Act

### Plan

- Reuse only the exact run/image identity and Mini-resident core from FLR-0408.
- Compare the existing packaged-debug route with the existing link/install
  output route; prefer the package tied to the image manifest.
- Verify Build-ID, architecture, ELF segments, and load bias before any
  symbolizer invocation.
- Stop if exact symbols are not already present; do not trigger a rebuild.

### Do

- Pending. No package/build-output search has run in FLR-0409 yet.

### Check

- Pending. Exact symbolization and caller/root-cause state are UNKNOWN.
- No runtime pixels are available from FLR-0408; do not treat post-exit state
  or the missing QMP capture as a visual result.

### UNKNOWN

- Exact symbol-file availability, the symbolized caller chain, pointer
  provenance, component ownership, and relationship to presentation are all
  UNKNOWN until the bounded existing-artifact search is completed.
- Sequoia/HUD pixel state remains UNKNOWN because no live QMP frame was
  captured in FLR-0408.

### Act

- If exact caller symbols are recovered, create a separate ticket for the
  narrow source/runtime discriminator selected from that evidence.
- If exact symbols are absent, stop and create a bounded follow-up only if
  generating exact debug symbols is necessary and approved. Keep the
  production visual goal open; the next runtime attempt must capture QMP
  immediately after confirming the live app identity.
