# FLR-0055 — TPS bounded QEMU/runtime harness

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + build-host roles
- Created: 2026-09-09
- Updated: 2026-09-11
- Work unit: QEMU起動・QMP・serial login・最小ログ抽出・teardownを自動化し、同じ手順ミスを再発させない
- Working log: `work/logs/2026-09-09-flr0055.md`
- Related: [FLR-0050](FLR-0050-flutter-parent-alpha-frame-loop.md), [FLR-0054](FLR-0054-podman-bundle-handoff-simplification.md)

## Problem

QEMU検証で、QMP引数形式、SDLバックエンド、転送ポート衝突、serial login
タイミング、capability交渉前のquitを手作業で誤り、失敗ログを読む範囲も広がった。
これは個別の注意力ではなく、起動前検査・実行・証跡・終了の工程設計の問題である。

## TPS / 4S policy

- **整理**: QEMU raw image、PPM/video、serial全文、coreはGit外へ置き、ticketには選択したmarker、統計、hashだけを残す。不要な複製は作らない。
- **整頓**: canonical source、固定build/TMPDIR、固定cache、固定evidence rootを役割別に1つへ固定する。runごとにQMP socket名だけを分ける。
- **清掃**: 起動前・終了後にQEMU、runqemu、flutter-auto、socket、転送portを自動検査する。失敗時も最初の原因とcleanup状態を残す。
- **清潔**: 成功条件、失敗条件、UNKNOWNを機械判定可能な短いsummaryへ揃える。
- **標準化**: QMPは`qmp_capabilities`後に操作し、serialはexact prompt後にloginし、QMP framebufferを主画面証拠とする。
- **自働化**: preflight、起動引数生成、selected marker抽出、QMP quit、残留検査を1つのallowlisted harnessから呼ぶ。

## Stratification — 4W1H excluding Why

| Dimension | Contract |
| --- | --- |
| What | one QEMU, one QMP socket, one serial channel, selected runtime markers and QMP pixels |
| Where | `$BUILD_HOST`または`$MAC_VALIDATION_HOST`の固定role paths |
| When | preflight → launch → guest prompt → marker window → QMP capture → negotiated quit → residual check |
| Who | harness owner、Yocto build owner、runtime validation ownerの責務を分離 |
| How | fixed profile + fail-fast checks + bounded output + role-only evidence |

## Success criteria

- [ ] 起動前にQEMU/process/socket/port/image identityを自動検査し、失敗理由を1つに絞る。
- [ ] runqemuのSDL依存を避けるQMP headless profileと、必要なserial/login同期を標準化する。
- [ ] QMP操作はcapability交渉を必須にし、quit後のprocess/socket検査を自動化する。
- [ ] raw全文を毎回読まず、selected marker・first actionable error・pixel summaryだけを出す。
- [ ] QMP-only画像/動画、runtime log、失敗ログを1 runの固定role directoryへ格納し、ticketへhashを記録できる。
- [ ] static contract tests、shell syntax、privacy、checkpoint verificationが通る。
- [ ] guest SSH banner readiness and QMP teardown are live-verified on the
  current Mini PC image, with every failed attempt and residual check retained.

## Hypotheses

1. 起動前の機械的なsocket/port/process検査で、SDL・port・stale socket系の再試行を減らせる。
2. serial prompt同期をharnessに移せば、login失敗をruntime failureと誤認しなくなる。
3. marker whitelistとbounded tailで、原因特定に必要なログ量を減らしても診断精度を保てる。

## Plan

1. 現行FLR-0050の失敗例をfailure taxonomyへ固定する。
2. preflight、QMP negotiation/quit、marker summaryの最小harnessをテスト先行で追加する。
3. 既存の公式runqemu runbookへharnessを接続し、同じimageでdry-runと実runを比較する。
4. 成功・失敗・UNKNOWNと削除対象をworking logへ記録し、ローカルcommitする。

## Implementation note

The start mode invokes the Yocto `runqemu` script with its documented `qmp=`,
`snapshot`, `slirp`, `nographic`, and `qemuparams=` options. The serial
`qemuparams` adds a server endpoint for exact prompt synchronization. It does
not replace runqemu with a second QEMU launcher.

## Unknowns

- harnessで、frame-loop停止そのものが解決するかはUNKNOWN。これは運用改善であり、Flutter修正ではない。
- すべてのtargetで同じserial login contractが使えるかはUNKNOWN。
- 動画の必要フレーム数とmarker whitelistの最小集合は実runで調整する。

## Current checkpoint

Core runqemu startup, exact serial prompt synchronization, negotiated QMP
teardown, residual cleanup, and bounded summary are verified. Keep this ticket
Waiting until a QMP pixel/video capture subcommand is separately implemented
and live-verified; use the existing runbook capture step for FLR-0050 meanwhile.

## Continuation checkpoint — 2026-09-11

### Facts

- The FLR-0078 runtime loop retained three QEMU attempts under the existing
  evidence root. p3 reached the guest and launched the self-made native
  fixture, but its QMP-only candidate region was `0/223200` despite fixture,
  submit, present, and commit markers. p4 and p5 reached QMP socket creation
  but never exposed a guest SSH port or serial output; neither was used as a
  rendering verdict.
- The first p3 teardown through the committed harness timed out. Inspection
  showed the pixel-capture client frames QMP commands with CRLF while the
  harness teardown sent LF. Exact QEMU parent/child PIDs were then TERM'd and
  verified absent; no broad kill or socket deletion was used.
- p4 and p5 were each stopped using their exact QEMU/runqemu PIDs. The Mini
  host has no remaining `qemu-system-x86_64` or `runqemu` process and the p4
  evidence directory has no QMP socket. Their start logs and empty serial
  logs remain on the Mini under `$QEMU_EVIDENCE_ROOT/flr0078/p4` and `p5`.

### Inferences

- QMP socket readiness alone is insufficient to call a runtime ready. The
  workflow needs a bounded guest SSH-banner gate before app launch, so a boot
  stall is classified separately from Flutter/rendering.
- QMP teardown must use the same CRLF framing as the capture client; otherwise
  a live QEMU can be mistaken for an unresponsive or uncleanly terminated run.

### Hypotheses

1. The teardown timeout is explained by the harness framing mismatch; a live
   QMP test after the correction should negotiate capabilities and quit.
2. The p4/p5 guest boot stalls are a separate image/QEMU readiness issue. The
   cause is UNKNOWN until the new bounded readiness result and minimal boot
   logs are collected; they must not be merged into the 3D diagnosis.

### Do / Check / Act

- Do: add `guest-ready --ssh-port` with a bounded timeout and SSH-banner
  validation, change only the harness QMP teardown messages to CRLF, and add
  static regression tests.
- Check: run syntax/unit/repository gates, transfer the committed correction
  through the fixed bundle receiver, then live-verify one QEMU start, the
  guest-ready gate, QMP-only capture as applicable, and negotiated teardown.
- Act: on a clean live gate, return the sole `In Progress` focus to FLR-0078;
  otherwise retain the first actionable readiness failure and open a separate
  image/boot ticket rather than changing the Flutter source.

## Live correction result — 2026-09-11

- Commit `b71dce6` passed repository verification and was transferred through
  the existing fixed receiver. The same current rootfs, build directory,
  TMPDIR, and QEMU profile were reused.
- Mini p6 passed `start=PASS`, then
  `guest-ready=PASS ssh_port=... attempt=4` using the new bounded SSH-banner
  gate. One QMP-only framebuffer was saved at
  `$QEMU_EVIDENCE_ROOT/flr0055/p6/qmp-smoke.ppm`; it is 1280x800, 3072016
  bytes, SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- The corrected teardown returned `qmp=PASS capabilities=negotiated
  quit=accepted` and `cleanup=PASS residual_targets=0 residual_qmp=0`.
  Follow-up process and socket inspection found no QEMU/runqemu/flutter-auto
  residual. The black p6 frame is a boot/control capture and is not a 3D
  verdict.

### Decision

The operational gate is complete and this ticket returns to Waiting. FLR-0078
is the sole active ticket again. The next run must use `guest-ready` before
launching the app, use serial fallback when SSH is refused, and end through the
corrected `qmp-quit`; the historical fixture profile must include both
`FLR0026_SYNC_TRACE=1` and `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1` before
comparing pixels.

## Post-readiness loss checkpoint — 2026-09-11

### Facts

- In p7, `guest-ready` passed on attempt 3, but the next guest SSH operation
  was refused. QMP capture remained responsive and the QEMU process remained
  a single live target, so this is a guest/service readiness loss rather than
  a QMP-start failure. The app was not launched and no 3D verdict was taken.
- The p7 QEMU was ended by corrected QMP quit with
  `cleanup=PASS residual_targets=0 residual_qmp=0`. The short-lived guest SSH
  state and the p7 QMP/start evidence remain in the existing evidence root.

### Inferences / UNKNOWN

- The readiness gate correctly detected an SSH banner, but a single probe is
  not sufficient to guarantee that the guest remains usable for app launch.
- UNKNOWN: whether the guest lost sshd, rebooted, or was affected by a boot
  service race. The previous serial TCP endpoint did not retain early output
  because no client was attached before boot messages were emitted.

### Do / Check / Act

- Do: add a secondary `-serial file:` stream to the existing runqemu command;
  retain the interactive TCP serial channel and the one-QEMU contract.
- Check: run the repository gates, transfer the correction, start one fresh
  QEMU, verify the new boot-serial file is populated, pass guest-ready, and
  perform a second SSH probe before allowing app launch. End through QMP quit.
- Act: if stable, return FLR-0078 to the sole active focus. If the guest
  drops again, use the retained boot serial as the first evidence for a new
  image/boot ticket and do not change Flutter source.

## Serial prompt nudge checkpoint — 2026-09-11

### Facts

- p8 boot-serial evidence contains the AGL banner and
  `qemux86-64 login:`. Sending one newline followed by `root` over the
  existing serial endpoint reached the root shell prompt.
- The previous `serial-login` implementation waited for a prompt without
  first nudging late-attached getty, so it could fail with no useful output
  even though the guest was booted. p8 was ended through corrected QMP quit
  with clean residual checks.

### Inferences / UNKNOWN

- The kernel, QEMU, serial getty, and root shell are reachable in p8. The
  SSH service is not a reliable launch channel for this image; serial should
  be the fallback when the boot serial proves a login prompt.
- UNKNOWN: why the SSH banner disappears after `guest-ready`; this remains a
  separate boot/service issue and is not treated as a Flutter fault.

### Do / Check / Act

- Do: make `serial-login` send one newline immediately after connecting,
  retain the exact prompt synchronization, and keep the bounded boot serial
  capture.
- Check: run repository gates, transfer the correction, start one QEMU, use
  `guest-ready` plus a second readiness probe, then verify serial-login can
  execute one benign command before QMP-only app testing.
- Act: if the serial gate passes, return FLR-0078 to the active fixture run;
  otherwise retain the boot evidence and split the SSH/boot issue.

## Live serial fallback result — 2026-09-11

- Mini p9 passed QMP start, `guest-ready`, and the corrected `serial-login`.
  The boot serial evidence contains the AGL banner and login prompt. The
  second SSH probe was refused, so the image's SSH service is not treated as
  a stable launch channel.
- Five QMP-only frames were captured from the same p9 QEMU. They were all the
  black control frame with SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  The attempted long app command did not produce a confirmed guest app PID,
  so this is not a fixture or 3D verdict.
- Corrected QMP quit returned capability negotiation and cleanup PASS. No
  QEMU/runqemu/flutter-auto process or QMP socket remained.

### Decision

The QEMU orchestration unit is complete for the current image: boot serial and
serial-login are the deterministic fallback; SSH is optional and must be
classified by the bounded readiness gate. FLR-0078 resumes with a short,
PID-confirmed serial fallback launch before any pixel classification.

The later serial command/output capture improvement is implemented under
FLR-0079 and is not mixed into this completed orchestration gate.
