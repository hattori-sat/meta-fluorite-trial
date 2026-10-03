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
reconcile the kernel page-fault RIP/CR2, process mapping, and loaded libLLVM
instruction bytes. Determine the earliest proven mismatch in address-to-ELF
resolution, or establish precisely why the vanished faulting LWP leaves that
boundary UNKNOWN. This is a read-only discriminator: no product/source edit,
BitBake, cache operation, or QEMU run in this ticket.

## Outcome required

Produce a reproducible mapping calculation from runtime RIP through the
recorded `/proc/<pid>/maps` file offset and ELF `PT_LOAD` segments to the exact
candidate libLLVM bytes, compare those bytes with the saved Oops instruction
bytes and FLR-0366, then identify the first faulting instruction/access if the
evidence permits. If not, specify the minimum fault-time capture needed in a
separate ticket. Do not blame callback synchronization, Vulkan present,
Filament, Mesa/LLVM, QEMU, or lighting by correlation alone.

## Known facts

- FLR-0410-0001 used the ordinary Example Demo profile on candidate rootfs
  SHA-256 `f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08`.
- The guest logged `BUG: unable to handle page fault for address
  00000000d9486750`, `#PF: supervisor read access in user mode`, Oops `[#1]`,
  CPU 0, PID/TID 758, `Comm: FEngine::loop`, kernel 6.6.111, RIP
  `0x7f1c3bd22541`, CR2 `0x00000000d9486750`, and RSP
  `0x00007f1bd9486750`.
- The saved runtime mapping calculation maps RIP to ELF VMA `0xb1d541` in
  libLLVM.so.18.1, Build-ID
  `359c1108040bc6bc1af64bb639d0b25385858051`. Saved instruction bytes start
  `ff cf 83 ff 07`.
- FLR-0366 reports this same Build-ID and ELF VMA as
  `llvm::CmpInst::isOrdered`, disassembled there as `dec %edi; cmp $7,%edi;
  setb %al; ret`. This register-only sequence contains no memory read and
  cannot, by itself, explain the logged CR2 page fault.
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
| kernel fault | RIP instruction performs an access to CR2 | Reported RIP maps to a register-only function in historical symbolization | First inconsistency to resolve |
| post-fault observation | GDB can inspect the faulting LWP/core | TID absent; no coredump | Fault-time context unavailable |

## Competing hypotheses

1. **Runtime-to-ELF address resolution is wrong or incomplete.** Load bias,
   mapping file offset, selected ELF, segment alignment, or symbol version may
   have been misapplied, so VMA `0xb1d541` is not the actual faulting bytes.
   Prediction: exact maps/PT_LOAD arithmetic and exact candidate library bytes
   map RIP to a different instruction or Build-ID than previously recorded.
   Falsifier: independently reproduced mapping selects the same Build-ID,
   VMA, and register-only bytes from the exact candidate ELF.
2. **The saved fault context/artifact pair is insufficient or inconsistent.**
   The faulting instruction, process mapping, and CR2 cannot be reconciled from
   the preserved post-fault record because the LWP vanished and no core exists.
   Prediction: exact static ELF/map reconstruction still yields register-only
   bytes, while no saved data identifies the fault-time mapped bytes or
   instruction that accessed CR2. Falsifier: an existing independent artifact
   (such as a same-run core, exact fault-time code bytes, or matching kernel
   trace) identifies a memory-access instruction and its operand.

## Scope and impact

- In scope: bounded reads of the Mini raw run evidence, exact candidate
  libLLVM package/rootfs file identity, Build-ID, ELF program headers, runtime
  map arithmetic, saved bytes, and FLR-0366 comparison.
- Out of scope: source patches, scene/material/light/camera edits, new build,
  QEMU boot, input/repaint, or present workaround. If static evidence cannot
  resolve the contradiction, create a separate ticket for fault-time capture.
- Build-time/runtime/packaging impact: none; this ticket is read-only.
- Integration risk: low if exact candidate and run identities are preserved;
  high risk of false causality if ELF symbol names or present counts are used
  without instruction/mapping reconciliation.

## Success criteria

- [ ] Read the minimal existing raw Oops, maps, thread-lifecycle, and GDB
  records from the exact `flr0410-0001` evidence directory; verify their
  recorded hashes before interpreting them.
- [ ] Identify the exact deployed libLLVM file for the candidate rootfs and
  independently verify its Build-ID, `PT_LOAD` layout, file offsets, and bytes
  at the calculated fault address.
- [ ] Recompute runtime RIP → mapping offset → ELF VMA from recorded mapping
  data; compare saved Oops instruction bytes with the exact file bytes and
  FLR-0366's calculation.
- [ ] Classify each claim as Fact, Inference, Hypothesis, or UNKNOWN; determine
  whether the first address/mapping boundary is resolved or remains unknown.
- [ ] Define the smallest next evidence action in a separate ticket if fault-
  time context is essential. Run canonical guard, privacy/checkpoint, focused
  Markdown and diff checks; commit only ticket/log/dashboard updates locally,
  with no push.

## Plan / Do / Check / Act

### Plan

1. Verify canonical worktree and ticket state; use only FLR-0410-0001's exact
   Mini evidence and candidate image. Do not scan unrelated logs or builds.
2. Read the minimal run files (fault excerpt, mappings, raw dmesg, thread
   lifecycle, GDB result) and verify the manifest hashes.
3. Read the exact candidate libLLVM file without extraction or mutation if a
   bounded image/package path is available; verify Build-ID and PT_LOAD data.
4. Independently calculate RIP-to-ELF mapping and compare file bytes with the
   saved kernel instruction bytes and FLR-0366.
5. Decide between a mapping discrepancy and an evidence/context gap. If static
   records cannot reveal the faulting operand, stop and create a new,
   single-purpose fault-time capture ticket rather than starting QEMU here.

### Do

- Not started. Ticket creation and log initialization only; no runtime or build
  action has been taken under FLR-0413.

### Check

- Pending exact Mini record hash verification and candidate ELF reconstruction.
- Overall goal remains active; this static analysis cannot pass any visual or
  stability acceptance gate.

### Act

- Preserve FLR-0410-0001 exactly; do not repeat its QEMU or alter the product
  while the RIP/CR2 contradiction is unresolved.
- If an ELF/mapping error is proven, correct only the observer interpretation
  and reassess the existing evidence before proposing runtime work.
- If saved evidence is intrinsically insufficient, create a separate ticket
  for one fault-time capture method and have GPT-6.1 Sol review the decision.
- Do not mark FLR-0413 or the overall goal Done from matching a symbol name,
  process readiness, or present counters alone.

## Unknowns

- Whether the guest loaded exactly the same libLLVM file/build as the one used
  in the previous symbol mapping.
- Whether the recorded load-bias/file-offset arithmetic is correct.
- Which instruction actually accessed CR2, and whether it is related to the
  unmatched present.
- Whether this renderer page fault has any causal connection to earlier
  `FEngine::loop` or callback-map faults.
