# FLR-0100 evidence — present return and userspace fault boundary

Date: 2026-09-12  
Image: fixed Mini authoritative qemux86-64 image from the FLR-0099 evidence
chain  
Capture contract: one QEMU, serial runtime evidence, QMP-only frames, QMP
quit, residual-process check

## Result

The recovered production run entered the Vulkan present path but did not
return from it because the guest reported a userspace page fault in
`FEngine::loop`. This closes the “present is merely delayed” question, but it
does not identify the original production input that caused the invalid state.

## Evidence

- First bounded GDB collection: `$RECEIVER/evidence/flr0100-present-return/production/gdb.txt`.
  It is retained, but the harness result is FAIL because the serial window did
  not observe the completion marker. The file recorded `GDB_RC=0`.
- Retry runtime/Oops: `$RECEIVER/evidence/flr0100-present-return/retry/wait-present.txt`.
  SHA-256: `b4be379444a46513e3c5181069710c42024af73753b8c99697ebf853129d3717`.
- Retry harness result:
  `$RECEIVER/evidence/flr0100-present-return/retry/wait-present-result.txt`.
  SHA-256: `45eaa60fa2d90da29121b939e8c4f8b1b9531ec2d2aa704fde7d3bf08bb55eb6`.
- Present-entry order in the retry was:
  `FLUORITE_VK_PRESENT_ENTER` → `FLUORITE_VK_PRESENT_CALL_BEGIN` →
  `FLUORITE_VK_QUEUE_PRESENT_ENTER wait=true` →
  `FLR0026_VK_QUEUE_PRESENT_BEGIN` → guest Oops. No queue-present return,
  outer present return, or serial completion marker followed.
- Current rootfs symbol evidence: Mini `nm -D` reports
  `llvm::CmpInst::isOrdered` at `libLLVM.so.18.1+0xb1d540`; retry RIP
  arithmetic places the reported instruction pointer at `+0xb1d541`.
  FLR-0030 directly mapped this same offset through `/proc/<pid>/maps` and
  `eu-addr2line`; the retry itself did not retain a maps snapshot.
- Retry QMP before SHA-256:
  `2617e8773e7bf65962467a54d212e36715ea674fbe3b7d05dc322c0dec209dc6`.
- Retry QMP early SHA-256:
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- QMP teardown: `capabilities=negotiated quit=accepted`; residual check:
  `cleanup=PASS residual_targets=0 residual_qmp=0`.

## Classification

- Fact: the guest reported a user-space fault in `FEngine::loop` after the
  queue-present entry marker.
- Inference: the absent present-return marker is a consequence of the fault,
  not a QMP or Wayland capture failure.
- Hypothesis: a production scene/resource/pipeline input causes invalid state
  before or during the software-Vulkan present path.
- UNKNOWN: the original producer and the exact current-run stack/map at the
  instant of the fault.

The next observation is owned by FLR-0101. No product behavior was changed by
this evidence unit.
