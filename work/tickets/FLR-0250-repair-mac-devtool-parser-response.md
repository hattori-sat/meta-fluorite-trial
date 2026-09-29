# FLR-0250 — repair Mac Devtool parser response path

- Status: Done
- Priority: High
- Owner: Mac Podman Devtool/BitBake control
- Created: 2026-09-21
- Predecessor: [FLR-0249](FLR-0249-fix-readiness-method-channel-registration.md)

## Objective

Make the fixed Mac Devtool container complete recipe registration and official
`devtool finish` reliably on the current AGL source layout, without creating a
second container, source workspace, or TMPDIR. Preserve the source commit and
resume FLR-0249 once the gate is green.

## Facts

- The fixed container is `fluorite-mac-devtool`; its AGL, project, and state
  paths are virtiofs mounts.
- BitBake's `ServerCommunicator.runCommand()` in the pinned Poky version has a
  hard-coded 60-second response wait for a command reply.
- `parseFiles` for the app recipe has taken more than five minutes on the
  current virtiofs-mounted AGL tree and returns no reply during that interval.
- The outer Devtool timeout was corrected to 900 seconds for one retry; this
  did not change the 60-second BitBake client timeout.
- `BB_NUMBER_THREADS=4` and `PARALLEL_MAKE=-j4` did not make the parse finish
  within the client wait.
- A disposable minimal layer/local.conf probe still exceeded the normal wait,
  while the same probe with an opt-in client-response shim completed in about
  97 seconds. It parsed 2719 recipes and then reported two expected missing
  base recipes for unrelated bbappends; it did not hit the response timeout.
- The tracked shim reached the official `devtool modify --no-extract` client:
  the full parse remained CPU-active for 900 seconds and the outer Devtool
  timeout expired before registration completed. The exact residual BitBake
  PIDs were then cleaned. Extending the client wait is necessary but not
  sufficient for the full virtiofs-mounted AGL parse.
- A tracked focused recipe profile using the existing `/workspace/agl` mount
  parsed 20 recipes in about 2 seconds and completed official `devtool modify`
  and `finish-source` in about 8 seconds. It keeps the one fixed container and
  `/workspace/tmp`; no metadata mirror is required for normal operation.
- The official finish output for source HEAD
  `88324284058b89b1bfce230636e8329ac4eab246` generated one matching FLR-0249
  patch with SHA256
  `c2b3af70705b7c2132eb6f4691897803b9e408c56c846bc9d5dba1974d4a4b75`.
- The failure leaves only the recorded BitBake server PIDs; they can be
  cleaned by PID after the run. No QEMU or Mini process is involved.

## Hypotheses

1. Virtiofs metadata latency makes the full AGL parse exceed the BitBake
   client response wait.
2. The fixed parser/control cache is incomplete or invalidated after the
   workspace-layer/source registration changes.
3. The selected AGL layer set causes an unexpectedly broad parse; a minimal
   recipe-scoped metadata configuration may reduce the parse below 60 seconds.
4. The fixed 60-second client response boundary explains the first failure,
   and a recipe-scoped metadata profile removes the remaining unnecessary
   parse work without changing the canonical layer.

## Scope

- Inspect the pinned BitBake client/server contract and fixed container mount
  performance.
- Use one bounded, read-only parse probe per hypothesis.
- Prefer a deterministic wrapper/configuration fix that keeps one container,
  one source workspace, one state path, and the normal Yocto Devtool lifecycle.
- The Mac wrapper may inject the tracked opt-in BitBake response-time shim via
  `PYTHONPATH`; it must not edit the read-only AGL checkout or hand-author a
  generated recipe patch.
- The focused profile is selected automatically for this app recipe and can be
  disabled with `FLUORITE_MAC_DEVTOOL_RECIPE_PROFILE=full`.
- Do not hand-author the FLR-0249 patch or edit the Mini build tree.

## Success criteria

- [x] A bounded parse probe completes without the 60-second parser response
  timeout when the tracked shim is injected.
- [x] The tracked response-time shim passes its wrapper contract test and the
  normal fixed-container status gate.
- [x] Full official recipe registration completes within the outer Devtool
  timeout using the focused profile.
- [x] `devtool status` shows the app recipe at the fixed source path.
- [x] FLR-0249 official `devtool finish --mode patch` generates one patch for
  source HEAD `88324284058b89b1bfce230636e8329ac4eab246`.
- [ ] No stale Devtool/BitBake process remains after success or failure.
- [x] The FLR-0249 patch is then registered in
  `meta-fluorite-trial`; Mini/QEMU validation remains FLR-0249 scope.

## Unknowns

- Whether a container-local AGL metadata mirror is required; the focused
  mounted-tree profile falsified that requirement for this app recipe.
- Whether the pinned BitBake client can be configured without modifying the
  upstream AGL/Poky source.

## Evidence

- Working log: [2026-09-21-flr0250.md](../logs/2026-09-21-flr0250.md)
- Prior source commit: `88324284058b89b1bfce230636e8329ac4eab246`
- Official generated patch SHA256:
  `c2b3af70705b7c2132eb6f4691897803b9e408c56c846bc9d5dba1974d4a4b75`
