# FLR-0389 plan — correct-marker LIT fixture replay

## Goal

Determine whether the known self-created parameterized LIT/SUN geometry and
CPU/GPU HUD render together on the exact FLR-0385 image, using patch-emitted
readiness markers and a healthy live QMP capture.

## Evidence-led plan

1. Reconcile FLR-0387's incorrect geometry selector against patches 0234/0244;
   preserve the old commands as executed and classify the old geometry result
   UNKNOWN. Record the actual FLR-0388 unhealthy Sequoia attempt and evidence.
2. Verify the canonical repository, active-ticket checkpoint, exact image and
   helper hashes, Mini process/port idle state, and fixed run/evidence paths.
3. Start one official runqemu instance with the same hash-pinned image and
   6144-MiB profile. Manually launch Example Demo 3.32.5 once as UID 1001 with
   the exact known fixture flags. Keep the process/exit and selected log
   evidence in the fixed Mini evidence root.
4. Query exact `FLUORITE_NATIVE_MINIMAL_GEOMETRY_*` strings from the active
   layer patches. Treat up to three 15-second `PENDING` samples as nonterminal;
   stop on a classified fault, process exit, or 45-second limit.
5. Capture one QMP full still/eight-frame video. It is positive only if
   geometry contract + at least eight successful presents + no fault/unmatched
   present + unchanged app PID/UID/start token before and after all capture,
   with both native fixture and HUD visible.
6. QMP quit, independent postflight, compare image/helper hashes, review the
   full-frame evidence, and update ticket/working log/TASKS. No source, patch,
   image, build, cache, or camera/light/texture/composition changes.

## Competing paths

- Re-run the known fixture with corrected, source-verified markers first.
- Continue changing Sequoia material/light/camera now.

Choose the first because it isolates the shared image/runtime contract and
avoids interpreting the unhealthy FLR-0388 capture as a material result.

## Verification

- Exact image/harness identity and zero-residual preflight.
- Manual one-app launch and persisted child exit/selected markers.
- Exact geometry ENABLED/CONTRACT/READY or a clearly recorded earlier fault.
- Healthy present count and PID-bracketed full QMP still/video.
- Teardown and candidate artifact hashes unchanged.
