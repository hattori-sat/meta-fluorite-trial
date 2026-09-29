# FLR-0101 evidence — production selector matrix

Date: 2026-09-12  
Runtime: fixed Mini image and fixed build/TMPDIR; one QEMU at a time; QMP-only
screenshots/video; QMP quit and residual-process/socket checks after each case.

## Verdict

The effective model/resource reductions did not change the current boundary:
the production app reached visible swapchain draw and present entry, retained
the 2D HUD, produced `0/223200` native candidate pixels, and did not retain a
queue-present return marker. The smallest trigger remains UNKNOWN. This is an
evidence-unit result, not a product fix.

The scene-content and scene-render cases are retained but excluded from the
trigger verdict because their requested runtime condition or serial evidence
was not observed.

## Case matrix

All valid cases reported one compositor and one `flutter-auto` process and
completed QMP teardown with zero residual targets/sockets.

| Case | Runtime condition | Internal result | QMP late SHA-256 | Native / HUD | Video result |
| --- | --- | --- | --- | --- | --- |
| `control-r4` | production control | present entry, no return; no selected-output Oops | `a2aa3a8d615e2dc98e6760a1f28db70b79d474796b2977fefe6664bd779a0a35` | `0/223200`, `984/100000` | six identical frames |
| `model-match-sequoia-r1` | match `sequoia`, 17 assets selected | same boundary | `46118f1831458250913c8a7017bcfdac777c4584e61f0adc1c99f211a320e186` | `0/223200`, `1294/100000` | six identical frames |
| `model-limit-1-r1` | one model selected (`sequoia_ngp.glb`) | same boundary | `67b58c380f4f4b4cb4bace90840ce212a6564dfe1a05156219548db8a69f8929` | `0/223200`, `1207/100000` | six identical frames |
| `environment-skip-r1` | environment stage skipped | same boundary | `810268b8dfe3794801b0aa3ef9523ce4591f6966e325b751b5725e0f7c82432a` | `0/223200`, `984/100000` | six identical frames |
| `model-skip-r1` | zero model assets loaded | same boundary | `abc13a6d69560e0e88cde88dcb99bbb211b8458b738cbf69457566391aafd0c4` | `0/223200`, `1234/100000` | six identical frames |

Remote evidence root for the valid cases:
`$RECEIVER/evidence/flr0101-libllvm-trigger/`.

## Invalid and failed attempts

- `control/`: wrong script paths; no QEMU was started.
- `control-r2/`: wrapper omitted the required absolute runqemu binary; the
  preflight rejected `path-not-absolute:` before QEMU startup.
- `control-r3/`: QEMU started, but the serial-login app launch did not start
  `flutter-auto`; the all-black QMP capture is not a product control.
- `scene-content-skip-r1/`: the requested skip marker was absent and the full
  scene state remained, so the selector was ineffective. QMP late SHA-256 was
  `e2a7c210e13be603436fd7ec3fe98a35237127db9d9e98148dd49aaf100f721a`, with
  six non-identical frames; no trigger claim is made.
- `scene-render-skip-r1/`: serial extraction missed its completion marker and
  retained no runtime markers. QMP late SHA-256 was
  `650f19f14bcec091b93e77486b2c1ceea5348198db265eebecdae74d1f28983e`, with
  `0/223200` native and `1294/100000` HUD pixels; QMP teardown still passed.

## Decision

Do not extend the old runtime selector namespace and do not patch present,
fence, semaphore, or compositor semantics from this matrix. The next ticket
is FLR-0102: inspect the active Mac Devtool source and add neutral,
opt-in `FLUORITE_*` markers around the production scene draw/command-recording
seam, then rebuild authoritatively on the Mini and repeat QMP evidence.
