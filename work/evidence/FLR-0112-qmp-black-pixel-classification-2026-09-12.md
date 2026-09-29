# FLR-0112 evidence — QMP black-pixel classification (2026-09-12)

## Outcome

The analyzer now reports local edge pixels, chromatic pixels, color-bin
summary, luminance range, and separate bounding boxes in addition to the
existing background/reference difference. It correctly identifies historical
model-only geometry indicators and retains an explicit indeterminate result for
a uniform black production region. This improves observation quality but does
not by itself distinguish native draw absence from a hidden surface.

## Facts

All inputs below are historical QMP-only PPM artifacts. The paths are expressed
by role and relative artifact name; no display-window screenshot was used.

| Control | Region / background | changed | edge | chromatic | luma range | classification hint |
| --- | --- | ---: | ---: | ---: | --- | --- |
| production model-only | `[200,100,400,250]` / `255,255,255` | 36659 | 4243 | 1077 | `[0,255]` | `geometry-indicators-present` |
| full production HUD-only | `[300,80,620,360]` / `0,0,0` | 0 | 0 | 0 | `[0,0]` | `uniform-or-undetectable` |
| model2 no-shapes clear control | `[200,100,400,250]` / `0,0,0` | 100000 | 0 | 0 | `[255,255]` | `uniform-or-undetectable` |
| pure fixture + Flutter HUD | `[0,0,400,250]` / `0,0,0` | 39864 | 5003 | 16773 | `[0,255]` | `geometry-indicators-present` |

### Artifact identities

- production model-only: `$HISTORICAL_QMP_ROOT/work/latest-mac/flr0049-ccb81ec/model-only-20260908/qmp-final.ppm`; PPM SHA-256 `61d1c910b7bdc39893b00812ce94b25c917f603d139773aae71c935c1e04e9a2`; region SHA-256 `6b7f6a4470702adc5c885e72162f671017b14826986663770fd6d8b7052b2c19`.
- full production HUD-only: `$HISTORICAL_QMP_ROOT/work/latest-mac/flr0049-ccb81ec/fluorite-agl-owner-qmp-final.ppm`; PPM SHA-256 `f17dce32b20db927c39d6fae60f8eca83bc40f995076a95775bf96d839dd044f`; region SHA-256 `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- model2 no-shapes clear control: `$HISTORICAL_QMP_ROOT/work/evidence/flr0049-model2/model2-no-shapes-10s.ppm`; PPM SHA-256 `2097d8f3aa89cb4083d5414e2636bbd9cf88d6a261844a2d8b9a947554376311`; region SHA-256 `76b0aeaa517d0aafaa054a563434429a184a7f7e10c6403136c9daf1ed281024`.
- pure fixture + Flutter HUD: `$HISTORICAL_QMP_ROOT/work/latest-mac/flr0049-ccb81ec/fluorite-mock-above-qmp-final.ppm`; PPM SHA-256 `1c036b946854fb8b37f85ec238504981516bb4191ab2927529fbf95f37da3414`; region SHA-256 `b4b537f6d5b29a1ae5593cd553e986169f60f412e0707a4fc9f7834418d8d7bd`.

## Interpretation

- The model-only control contains edge and chromatic indicators consistent
  with the historically observed black vehicle, red lamps, and wireframe.
- The full production control is exactly uniform black in the selected native
  region. The result is compatible with no native draw, a black object with no
  visible boundary, or a later hidden/composited surface; it is not sufficient
  to choose among them.
- The model2 no-shapes control demonstrates why changed-pixel count alone is
  insufficient: a uniform clear surface can change every pixel while having
  no geometry indicators.
- The pure fixture + Flutter HUD control has geometry indicators in the upper
  native candidate region and visibly proves a diagnostic 2D+3D composition.
- Analyzing the entire full-production frame is invalid for a native-3D
  verdict: HUD text, charts, and controls contribute edges and chromatic
  pixels. The native candidate region must be analyzed separately from HUD.

## Verification

- Focused unit tests: `python3 -m unittest tests.test_qemu_pixel_capture` — 6
  tests passed.
- CLI help exposes `--edge-threshold` and `--chroma-threshold`.
- `git diff --check`: PASS before commit.
- Full repository gate: `make verify` — PASS. This included 84 Python unit
  tests, 52 MCP smoke tests, 389 internal Markdown links, 31 shell syntax
  files, privacy checks, file-size checks, and the QEMU/runtime harness.
- No QEMU, remote target, image build, or source checkout was created for this
  analysis.

## Limitations

- RGB-only analysis cannot detect a fully black object on an exactly black
  background.
- Native readback and final QMP capture are still required to separate target
  rendering from final Wayland/Flutter composition.

## Current-image triad reconciliation

FLR-0077 supplies the stronger same-image evidence that the earlier wording
called merely historical. The fixed rootfs SHA-256 was
`87043b0e099eca442a39f4d7b104d4bcfbc79e7f8a54851df78bb5dd93697ed7`.

| Condition | Native candidate | HUD | Interpretation |
| --- | ---: | ---: | --- |
| self-made fixture + Flutter HUD | `41750/223200` | `6291/100000` | geometry indicators present; combined diagnostic path |
| Sequoia model-only | `140034/223200` | parent HUD masked | geometry indicators present; native 3D-only positive |
| full production | `0/223200` | nonzero | final frame is HUD-only in the native candidate region |

The stage matrix narrows the next boundary further: with `DEFAULT` indirect
light and skybox skipped, explicit-light setup changes the candidate from
`4905/223200` when skipped to `0/223200` when enabled. Two different single
POINT lights also remain at zero. A later native-light operation trace once
produced `5510/223200`, but the following timing/reproducibility ticket did
not reproduce that effect. This establishes a stable production-stage
boundary, but not the exact light/material/resource operation.

The fourth requested state—native pixels present before composition but absent
from final QMP—remains unproven because a synchronized native readback and
final QMP frame from the same run has not yet been retained.

## Static patch-stack audit

- The canonical `flutter-auto_2.0.bbappend` currently lists 130 patch entries.
- Unconditional behavior includes the Vulkan/transparent/above-parent base,
  software frame scheduling and registration ordering, plus model/asset
  lifetime corrections and the camera point-target correction.
- Most later surface probes, native readback, scene/light isolation, camera
  tracing, and fixture controls are environment-gated. In the normal no-probe
  configuration, the extra diagnostic surface commits and synchronous waits
  are disabled.
- This audit is a confounder inventory, not a root-cause verdict. Historical
  fixture and model-only positive controls show that the native path can emit
  visible geometry, while the full-production native candidate remains
  uniform black/HUD-only. A same-image triad is still required.
