# FLR-0413 — resolve the FEngine page-fault instruction/address boundary

- Status: In Progress
- Priority: Critical
- Created: 2026-10-03
- Owner: guest kernel page-fault evidence / `FEngine::loop` / ELF mapping roles
- Predecessor: [FLR-0410](FLR-0410-synchronize-event-callback-map.md)
- Historical comparison: [FLR-0366](FLR-0366-capture-fengine-loop-pagefault.md)
- Working log: [FLR-0413 working log](../logs/2026-10-03-flr0413.md)
- Runtime evidence: [FLR-0410-0001](../evidence/FLR-0410-0001.md)

## Work unit

Using existing FLR-0410-0001 runtime artifacts and the exact candidate image,
reconcile kernel RIP/CR2 with the mapped libLLVM bytes and the exact QEMU 8.2.7
IRET helper. This was a read-only discriminator: no product/source edit,
BitBake, cache operation, or QEMU run occurred in this ticket.

## Outcome required

Recompute RIP → mapping offset → ELF VMA; verify the exact deployed QEMU and
source version; trace opcode `CF` through the translator and IRET helper; and
decide whether the saved CR2/error code are mechanically consistent. Do not
infer why control reached the byte or assign renderer/present causality.

## Known facts

- FLR-0410-0001 used the ordinary Example Demo profile on candidate rootfs
  SHA-256 `f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08`.
- The guest logged `BUG: unable to handle page fault for address
  00000000d9486750`, `#PF: supervisor read access in user mode`, Oops `[#1]`,
  CPU 0, PID/TID 758, `Comm: FEngine::loop`, kernel 6.6.111, RIP
  `0x7f1c3bd22541`, CR2 `0x00000000d9486750`, and RSP
  `0x00007f1bd9486750`.
- Four focused Mini artifacts were freshly hashed and matched their recorded
  evidence: kernel Oops `aebaae48…`, symbol/map record `876985be…`, first-fault
  snapshot `c3f1a5fc…`, and thread lifecycle `4b8dc09f…`.
- The exact candidate rootfs file is libLLVM.so.18.1 inode 5719, size
  107,835,552 bytes, Build-ID `359c1108040bc6bc1af64bb639d0b25385858051`.
  Its ELF `PT_LOAD` layout and the recorded executable mapping agree. Mapping
  start `0x7f1c3ba3d000` with file offset `0x838000` gives RIP-relative
  `0x2e5541` and ELF VMA `0xb1d541`; the exact rootfs ELF bytes and Oops bytes
  agree. Wrong ELF selection and load/file-offset arithmetic are falsified for
  these supplied artifacts.
- At ELF VMA `0xb1d540`, the bytes are `ff cf`: the historical `isOrdered`
  symbol starts with `dec %edi`. The Oops RIP is VMA `0xb1d541`, the second
  byte `cf`, followed by `83 ff 07`. If executed in 64-bit mode, bare `CF` is
  IRETD (32-bit operand size); Intel documents that `REX.W + CF` is required
  for IRETQ.
- The Oops also records CS selector `0x33`, SS selector `0x2b`, RFLAGS
  `0x217`, R10 equal to RIP `0x7f1c3bd22541`, RSP
  `0x00007f1bd9486750`, and CR2 `0x00000000d9486750`.
- The saved launch command used the exact QEMU 8.2.7 binary
  (SHA-256 `8cb2c6f4…`), `-machine q35`, and omitted both `-accel` and
  `-enable-kvm`. The QEMU 8.2.7 source available under the existing native
  recipe workdir reports `VERSION=8.2.7`; `target/i386/tcg/seg_helper.c` has
  SHA-256 `36afbc28…`. Its translator passes `dflag-1` for opcode `CF` to
  `helper_iret_protected`; `shift==1` takes `POPL_RA`, whose `SEG_ADDL`
  effective address is explicitly cast to `uint32_t` and read using
  `cpu_ldl_kernel_ra`. `get_sp_mask` returns `0xffffffff` for SS flags with
  `DESC_B_MASK` (and `0xffff` without it; `DESC_L_MASK` returns zero).
- The kernel Oops states supervisor read access in user mode, error code
  `0x0000` (not-present read), CR2 `0xd9486750`, and RSP whose low 32 bits are
  exactly `0xd9486750`.
- QEMU's saved command does not name an accelerator. QEMU 8.2.10 official
  invocation documentation states TCG is the default; for this 8.2.7 run the
  active backend remains inferred, not explicitly logged.
- GPT-6.1 Sol independently reviewed the exact source and register facts. Its
  judgment is advisory: the QEMU IRETD explanation is a strong conditional
  match, but it does not establish how control reached `isOrdered+1`.
- The faulting LWP had vanished before the later bounded GDB capture. The
  parent app remained, and `coredumpctl` found no core. There is no post-fault
  register/memory snapshot from the faulting TID.
- Present began twice, returned once, and succeeded once; the second begin is
  unmatched. This is concurrent evidence, not proof that present caused the
  page fault.
- GPT-6.1 Sol's judgment-only review recommends this instruction-boundary
  reconciliation before scene changes or another renderer run. The review is
  advisory; raw evidence and ELF checks decide the result.

## Problem stratification — 4W1H (Why excluded)

| Dimension | Current observation | Evidence |
| --- | --- | --- |
| What | Kernel page fault is attributed to a RIP whose prior ELF symbolization is register-only, while CR2 names an unmapped data address | FLR-0410-0001 Oops excerpt, registers, instruction bytes |
| Where | Guest `FEngine::loop`; mapped libLLVM; exact candidate rootfs | Runtime map/Build-ID record and candidate identity |
| When | Guest uptime 376.161, after one successful present and during the next unmatched present interval | App log, dmesg, present counters |
| Who | Renderer thread, guest kernel, ELF/runtime-observer roles | TID 758, `FEngine::loop`, kernel Oops |
| How | Kernel reports supervisor read access in user mode; faulting LWP disappeared before GDB | Raw dmesg and post-fault thread snapshot |

## Process analysis

| Step | Expected | Observed | Boundary |
| --- | --- | --- | --- |
| app launch / READY | Same PID/UID/start identity and scene readiness | Launch passed; READY markers existed | Not the first known gap |
| present | Every begin eventually has a return and successful completion | 2 begins, 1 return, 1 success | One begin unmatched; causal order UNKNOWN |
| runtime map → ELF | Saved RIP resolves to exact candidate file bytes | Rootfs Build-ID, PT_LOAD, map offset, calculated VMA, and Oops bytes agree | Mapping and wrong-image hypotheses falsified for these artifacts |
| instruction decode | Saved instruction can explain the kernel access | RIP lands on bare `CF` one byte after `dec %edi`; in 64-bit mode this decodes as IRETD, not IRETQ | Prior control transfer into `isOrdered+1` remains unexplained |
| QEMU guest memory helper | Fault address can be derived from IRETD stack reads | Exact 8.2.7 TCG helper has a 32-bit stack-address path; low 32 bits of RSP equal CR2 under stated segment assumptions | Strong conditional immediate mechanism; runtime conditions not yet captured |
| post-fault observation | GDB can inspect the faulting LWP/core | TID absent; no coredump | Existing run cannot reveal caller or segment-cache state |

## Competing hypotheses

1. **The immediate page fault is caused by QEMU's TCG IRETD stack-read path.**
   The saved IP entered the second byte of `dec %edi`, where bare `CF` is
   IRETD. In exact QEMU 8.2.7, the `shift==1` helper path reads a 32-bit stack
   address. If the active backend is TCG, CS.L=1, and the cached SS is flat
   with B=1, the observed RSP truncates to exactly CR2. Prediction: a live
   breakpoint/fault capture shows those mode/segment facts and the helper's
   effective stack read at `0xd9486750`. Falsifier: a different backend,
   segment state, faulting operand, or CR2 derivation.
2. **An upstream invalid control transfer enters `isOrdered+1`; IRETD is only
   the first visible consequence.** R10 equals saved RIP, which is compatible
   with an indirect transfer but is not proof. Prediction: a pre-instruction
   breakpoint captures a caller/branch or corrupted return path targeting
   `RIP`, with the expected bytes. Falsifier: a legitimate control-flow path
   or a different faulting instruction/context.
3. **The preserved Oops register/context record is incomplete or belongs to a
   different execution boundary.** Prediction: a same-run, identity-bracketed
   capture fails to reproduce the exact IP/CR2 relation or maps the TID to a
   different image/thread. Falsifier: one live capture ties process identity,
   exact image, breakpoint registers, and the subsequent Oops together.

The wrong-ELF and mapping-arithmetic explanations are no longer live
hypotheses for the supplied FLR-0410 artifacts: the exact rootfs bytes and
recorded mapping independently agree. The immediate QEMU mechanism remains a
conditional inference, not a proven product or emulator root cause.

## Scope and impact

- In scope: bounded reads of the Mini raw run evidence, exact candidate
  libLLVM package/rootfs file identity, Build-ID, ELF program headers, runtime
  map arithmetic, exact QEMU 8.2.7 translator/helper source, saved bytes, and
  FLR-0366 comparison.
- Out of scope: source patches, scene/material/light/camera edits, build,
  QEMU boot, input/repaint, or present workaround. FLR-0414 owns the separate
  fault-time capture because this static record cannot reveal the control
  transfer or cached segment state.
- Build-time/runtime/packaging impact: none; this ticket is read-only.
- Integration risk: low if exact candidate and run identities are preserved;
  high risk of false causality if ELF symbol names or present counts are used
  without instruction/mapping reconciliation.

## Success criteria

- [x] Read the minimal existing raw Oops, maps, thread-lifecycle, and GDB
  records from the exact `flr0410-0001` evidence directory; verify their
  recorded hashes before interpreting them.
- [x] Identify the exact deployed libLLVM file for the candidate rootfs and
  independently verify its Build-ID, `PT_LOAD` layout, file offsets, and bytes
  at the calculated fault address.
- [x] Recompute runtime RIP → mapping offset → ELF VMA from recorded mapping
  data; compare saved Oops instruction bytes with the exact file bytes and
  FLR-0366's calculation.
- [x] Classify each claim as Fact, Inference, Hypothesis, or UNKNOWN; the
  static address/mapping boundary is resolved, while control transfer and
  fault-time segment state remain UNKNOWN.
- [ ] Open a separate ticket/log for the one live hardware-breakpoint capture
  and activate it after this closeout commit; fault-time context is essential.
- [x] Run canonical/privacy/checkpoint/Markdown-link/diff checks and commit
  only FLR-0413 static records locally. The full link checker reports the same
  11 historical missing targets; no new FLR-0410/0413 link is implicated.

## Plan / Do / Check / Act

### Plan

1. Verify canonical worktree and ticket state; use only FLR-0410-0001's exact
   Mini evidence and candidate image. Do not scan unrelated logs or builds.
2. Read and hash only the Oops, symbol/map, first-fault, and thread-lifecycle
   artifacts before interpreting them.
3. Read the exact candidate libLLVM from the rootfs through a transient
   seekable memfd; verify Build-ID, PT_LOAD, mapping arithmetic, and bytes.
4. Inspect the exact deployed QEMU 8.2.7 translator and segment helper; derive
   the conditional CR2 match without asserting the unrecorded runtime state.
5. Compare two live explanations and define the single next fault-time
   control-transfer capture; opening its ticket is the remaining handoff.

### Do

- Verified exact Mini Oops/map/first-fault/thread-lifecycle hashes and linked
  them to the documented FLR-0410-0001 manifest.
- Extracted the candidate rootfs `libLLVM.so.18.1` stream to a transient
  seekable memfd (no persistent image/file extraction); verified its Build-ID,
  PT_LOAD mapping, and exact instruction bytes. `readelf -n /dev/stdin` failed
  because the pipe is not seekable; the memfd method succeeded. Mini did not
  have `rg`; bounded source searches used standard `grep`.
- Read the exact QEMU 8.2.7 source from its existing native recipe workdir;
  followed opcode `CF` through the translator to `helper_iret_protected` and
  the 32-bit stack-read helper. No source, build, cache, or QEMU state changed.
- Recomputed the conditional low-32-bit stack address and sent the bounded
  hard judgment to GPT-6.1 Sol. Sol agreed it is a strong conditional match,
  while the prior control transfer and runtime CS/SS state remain unresolved.

### Check

- Exact record hashes, rootfs ELF identity/mapping/bytes, and QEMU source path
  are verified for the recorded candidate. Wrong-file and map-arithmetic
  explanations are falsified for this evidence set.
- The conditional IRETD mechanism is an inference only: active accelerator,
  CS.L, SS base/B cache, and fault-time helper operands were not captured.
- Overall goal remains active; this static analysis passes no visual or
  stability acceptance gate.

### Act

- Preserve FLR-0410-0001 exactly; no need to repeat its build or alter product
  code to resolve this static boundary.
- Create one identity-bound live hardware-breakpoint ticket against the same
  candidate; capture the active accelerator before allowing the target
  instruction to continue.
- Keep FLR-0413 In Progress until the successor ticket and TASKS transition
  are committed. Never promote the conditional emulator mechanism to root
  cause without live state.
- Do not mark the overall goal Done from matching a symbol name, process
  readiness, a diagnostic fixture, or present counters alone.

## Unknowns

- Whether TCG was the active accelerator, and the fault-time CS.L, SS base,
  and SS.B cached state.
- Whether the process entered `isOrdered+1` through an invalid indirect jump,
  corrupted return, or another control-flow event.
- Whether the conditional QEMU IRETD path actually made the read at CR2, and
  whether that event is related to the unmatched present.
- Whether this renderer page fault has any causal connection to earlier
  `FEngine::loop` or callback-map faults.

## References

- Intel, *64 and IA-32 Architectures Software Developer's Manual*, Vol. 2A,
  `IRET/IRETD/IRETQ` opcode semantics: [official PDF](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf).
- Exact QEMU tag files inspected from the Mini's existing 8.2.7 source workdir:
  [`translate.c`](https://gitlab.com/qemu-project/qemu/-/blob/v8.2.7/target/i386/tcg/translate.c)
  and [`seg_helper.c`](https://gitlab.com/qemu-project/qemu/-/blob/v8.2.7/target/i386/tcg/seg_helper.c).
- QEMU's adjacent 8.2.10 invocation docs say TCG is the default when no
  accelerator is specified; this is not direct proof of the 8.2.7 runtime
  backend: [official docs](https://qemu.readthedocs.io/en/v8.2.10/system/invocation.html).
