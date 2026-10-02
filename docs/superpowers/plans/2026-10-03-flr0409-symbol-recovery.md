# FLR-0409 Plan — bounded exact-Build-ID symbol recovery

## Outcome

Resolve the existing FLR-0408 SIGSEGV to a defensible symbolized instruction
and caller boundary using only exact-build artifacts that already exist; if
those artifacts are absent, prove the bounded search result and stop.

## Evidence baseline

- Predecessor run: `flr0408-0001`, exact 0334 rootfs
  `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`.
- Executable: `/usr/bin/flutter-auto`, Build-ID
  `529c5d321d81192f82f146d9d23736722aec2208`.
- Fault: LWP 812, SIGSEGV / `SEGV_MAPERR`, `RIP=0x56032183498d`,
  `RAX=si_addr=0x7f0a79cbc1c4`, instruction `mov (%rax),%rax`.
- Core and bounded GDB transcript remain on Mini under the FLR-0408 evidence
  role; hashes are in [the ticket manifest](../../../work/evidence/FLR-0408-0001.md).
- No QMP pixels were captured; visual result remains UNKNOWN.

## Hypotheses to test

1. The faulting code formed or retained a stale/invalid pointer. Prediction:
   exact symbols and nearby source show the value derived within that path
   without an invalid incoming pointer.
2. An upstream caller/API/lifetime boundary supplied the invalid pointer.
   Prediction: the resolved stack and arguments expose an incoming resource or
   pointer value before the dereference.
3. Earlier memory corruption or an optimized/incomplete unwind obscures the
   origin. Prediction: the exact symbols still leave saved state or caller
   provenance inconsistent/indeterminate.

## Two-path comparison

| Path | Test | Interpretation |
| --- | --- | --- |
| Existing image package metadata/debug split | Identify the package from the image manifest, then inspect only its already-generated debug/deploy files | Highest provenance; exact Build-ID match is required |
| Existing recipe link/install output | Resolve recipe/workdir from the image provenance and inspect existing outputs without running tasks | Useful fallback; stale or different-build objects are rejected by Build-ID |

The package/debug and existing link/install routes test whether exact symbols
are available; the three pointer-origin hypotheses require interpreting the
resulting symbolized boundary. Source/maps/objects are a last partial-evidence
route only. Do not scan all caches. Build-ID, architecture, ELF program
headers and saved core mapping must agree. Derive load bias before symbolizing;
do not assume the recorded `0xd5198d` mapping offset is a valid `addr2line` PC.

## Execution boundary

- Read-only commands only; preserve the existing core and all shared outputs.
- No BitBake, Devtool, QEMU, package installation, source edits, cache cleanup,
  image transfer, or second runtime.
- No raw core/image copy to Mac and no root-cause attribution from a function
  name alone.
- Stop if exact outputs are absent or owned by another active task; record the
  exact checked paths and leave the result UNKNOWN/UNAVAILABLE.

## Checks

1. Reconfirm the FLR-0408 core and GDB transcript hashes in place.
2. Use image manifest → effective recipe/package metadata → exact existing
   artifact paths; record package and recipe identity.
3. Verify any candidate Build-ID, architecture, executable sections, and
   PIE load bias before symbolizing LWP 812.
4. Compare the resolved stack and nearby source against the three hypotheses;
   state supporting/refuting evidence without overclaiming causality.
5. Record exact commands, bounded output paths/hashes, and whether the search
   ended in exact symbols found or exact symbols unavailable.
