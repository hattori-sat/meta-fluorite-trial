# FLR-0112 — distinguish black geometry from no native draw

- Status: Waiting
- Priority: High
- Owner: target-validation + rendering-diagnostics roles
- Created: 2026-09-12
- Updated: 2026-09-12
- Work unit: QMP-only画像の色・輪郭・領域分析で、黒い3Dオブジェクトと無描画を判定する
- Links: [FLR-0049](FLR-0049-production-model-render-boundary.md), [FLR-0111](FLR-0111-compare-pure-fixture-present-wait.md)
- Next source investigation: [FLR-0113](FLR-0113-isolate-explicit-light-contribution-boundary.md)

## Problem

### Purpose

現在のnative pixel metricは背景との差分を主に数えるため、黒い車体が黒背景に重なる場合に「無描画」と誤分類する可能性がある。QMP-only画像の見た目、輪郭、色分布を同じ入力から再現可能に判定し、production 3Dの未描画と黒色geometryを分離する。

### Success measure

- 同一image identity・同一QEMU profileでproduction、model-only、pure fixtureを比較できる。
- 各QMP frameについて、背景色、色分布、エッジ画素、対象領域のbounding box、SHA-256を記録する。
- 次の4状態を明示的に分類できる。
  1. native drawなし
  2. 黒色を含むnative geometryが存在
  3. native surfaceには描画されるが最終合成で隠れる
  4. HUDのみが表示される
- 判定ができるまで、source patchを作成しない。

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | production QMPはHUD-onlyに見え、model-only QMPは黒い車と赤色灯を表示する | FLR-0049 QMP画像、FLR-0109/0111 evidence |
| Where | build host上のQEMU、native surface領域とFlutter HUD領域 | 固定QMP capture contract |
| When | production scene setup後およびpresent境界で発生 | FLR-0109/0111 marker logs |
| Who | Flutter/Filament render path、QMP observer、pixel analyzer | role-based runtime evidence |
| How | 背景との差分pixel countだけでは黒色geometryを十分に識別できない | 既存 `qemu-pixel-capture.py` と過去画像の目視比較 |

### Priority selection

- Compared strata: renderer未描画、黒色geometry、Wayland合成隠蔽、pixel analyzer誤分類。
- Selected focus: まず観測分類を改善し、無描画と黒色geometryを同じQMP証拠で分離する。
- Selection evidence: model-only画像は黒い車体でも輪郭・赤色灯・wireframeが確認できる一方、production画像はHUD以外の輪郭が確認できない。

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| QMP capture | running QEMU | authoritative PPM | PASS on historical runs | FLR-0049, FLR-0111 |
| background comparison | PPM + background/reference | changed pixel count | black-on-black can be ambiguous | existing analyzer |
| visual classification | PPM | geometry/HUD distinction | model-only and production differ visually | FLR-0049 images |
| render/present marker correlation | stderr | draw→submit→present relationship | production present return remains incomplete in FLR-0109 | FLR-0109 |

### Problem point

QMP画像の分類stepが、黒色geometryの輪郭・色アクセント・エッジを独立した証拠として扱っていない。native drawが無いことと、黒いgeometryが背景に近いことの差が最初の未分離点である。

### Ideal condition

QMP-only captureを入力すると、背景比較だけでなく、色ヒストグラム、局所コントラスト、エッジ、HUD除外領域を使ってnative geometryの有無を再現可能に判定できる。

### Current condition — Facts

- 既存metricは背景との差分pixel数とbounding boxを出力する。
- 過去のmodel-only QMP画像では、黒い車体、赤い灯、wireframeが視認できる。
- 過去のproduction QMP画像では、HUDとボタンは見えるが、車体の輪郭は確認できない。
- FLR-0111 pure fixtureはnative pixel countが非zeroで、queue-present return/doneも得られている。
- FLR-0077の同一rootfs `87043b0e099eca442a39f4d7b104d4bcfbc79e7f8a54851df78bb5dd93697ed7`
  では、自作fixture＋HUDが`41750/223200`、Sequoia model-onlyが
  `140034/223200`、full productionが`0/223200`だった。3つの表示条件を
  別imageの記憶で混同してはいけない。
- 同じproduction-stage系の固定条件では、FLR-0067のlight-skippedが
  `4905/223200`、explicit lights enabledが`0/223200`だった。FLR-0068/0069
  では異なる単一POINT light（GUID 126、128）も`0/223200`だった。
- FLR-0070ではnative light stateが有効でSceneにも存在したが、operation
  trace付きだけ`5510/223200`になった。FLR-0071ではtraceと遅延を含む同様の
  条件を再現できず、traceは修正ではなくタイミングを含む未解決の観測である。

### Gap

色が背景と近いgeometryを、無描画と自動的に区別する指標と判定基準が不足している。

### Impact

誤分類したままsurface、alpha、light、presentのsource patchを作ると、原因層を誤る可能性がある。

### Point of occurrence

QMP画像からnative geometryの存在を判定する観測工程。renderer内部の真因はこのticketでは扱わない。

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| 黒色geometryが黒背景に埋もれている | 輪郭・局所edge・赤色灯は残る | edge/color-accent analysisと目視を比較 | UNKNOWN | 次回QMP comparison |
| native draw自体がない | HUDだけで、対象領域のedge/color-accentがない | 同一条件のmodel-only/pure fixtureを比較 | productionでは有力だが未確定 | FLR-0109/0111 |
| native surfaceは描画済みだが合成で隠れる | native captureにはgeometry、最終QMPにはない | native readbackとQMPを同一runで比較 | UNKNOWN | 要追加証拠 |

### Confirmed root cause

UNKNOWN。現段階では、production QMPの見た目はHUD-onlyであり、present境界のproduction-specific wait候補があるが、pixel分類の不確実性を完全には除けない。

### Minimal countermeasure

既存のQMP captureとmarker収集を維持し、analyzerに色分布・エッジ・HUD除外領域の補助指標を追加する。判定後にのみ、必要ならruntime source patchへ進む。

## Scope

### In scope

- QMP-only PPMの機械的分類
- model-only / pure fixture / productionの同一条件比較
- native readbackと最終QMPの差分分類

### Out of scope

- このticket単独でのFilament、Vulkan、Waylandの動作変更
- production 3Dの修正断定
- 新しいQEMU/TMPDIRの増設

## Success criteria

- [x] Analyzer reports edge, chromatic, luminance, color-bin, and bounding-box
  evidence in addition to the existing background/reference metric.
- [x] Synthetic black-on-black, black-on-white, and red-accent controls pass.
- [x] Historical model-only and full-production QMP PPMs are analyzed with
  recorded hashes and role-based artifact paths.
- [x] Historical pure-fixture + Flutter-HUD QMP composition control is
  analyzed separately from the native candidate region.
- [x] QMP-only画像3種を同一image identityで取得
- [x] 色分布、edge、HUD除外領域、bbox、SHA-256を記録
- [ ] 4状態のうち各画像を一意に分類
- [x] 分類結果を根拠に、次のsource investigation ticketを切る

## Visual evidence

- QMP-only screenshotまたは承認済み実機capture: FLR-0049 historical QMP imagesをcontrolとして使用。新規画像はDo開始後に追加。
- 画像で見える内容 / 見えない内容: model-onlyは黒い車体・赤色灯・wireframe、productionはnative候補領域がHUD-only、pure fixture + HUDは同一QMP画面に2Dと3Dが見える。全画面metricはHUDを含むためnative判定には使わない。
- Run ID / image identity / captured at: FLR-0049 historical runs、FLR-0111 fixed debug image。新規run IDは未定。
- Pixel count / bounding box / SHA-256 / evidence ID: 既存ticket/evidenceに記録済み。追加分析値は新規evidenceへ記録。
- Artifact attachment or role-based link: `work/tickets/FLR-0049-production-model-render-boundary.md`、`work/logs/2026-09-08-flr0049.md`、`work/evidence/FLR-0111-pure-fixture-present-2026-09-12.md`

## Hypotheses

1. productionにはgeometryが存在するが、背景・alpha・light条件により黒く見えている。
2. productionはfixtureと異なり、native drawまたはpresent完了へ到達していない。
3. native surfaceでは描画されているが、Flutter/Wayland最終合成で隠れている。

## PDCA

### Plan

- Verification sequence: QMP capture → HUD除外 → background/color histogram → edge/contrast → marker alignment → native readback comparison。
- Expected observations: model-only/pure fixtureはgeometry指標positive、productionは指標の有無で無描画と黒色geometryを分離する。
- Stop conditions: QMP-onlyでない画面、複数QEMU、image identity不一致、またはQMP teardown未確認。
- Risks: 画像分析だけではnative surfaceと最終合成を分離できない。必要なら別ticketへ分割する。

### Do

- 既存QMP PPMを変更せず、analyzerへedge、chromatic、luminance、dominant
  color-bin、補助classification hintを追加した。
- 合成black-on-black、black-on-white、red-accentの6 focused testsがPASS。
- 過去のmodel-only、full-production、model2 clear-control、pure fixture +
  Flutter HUD PPMを解析し、
  結果を`work/evidence/FLR-0112-qmp-black-pixel-classification-2026-09-12.md`
  に記録した。

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| historical visual control | model-onlyとproductionの見た目の差が確認できる | 黒い車体とHUD-onlyを目視確認 | FLR-0049 historical QMP images | PASS |
| analyzer geometry indicators | edge/chromatic/color summaryを出力する | 6 testsと3 historical PPMで確認 | FLR-0112 evidence | PASS |
| diagnostic 2D+3D composition control | fixtureとHUDが同じQMP画面に存在する | upper regionにgeometry indicatorsを確認 | FLR-0112 evidence | PASS |
| repository verification | 全体の安全ゲートが通る | `make verify` PASS | FLR-0112 evidence | PASS |
| automated 4-state classifier | 一意に分類できる | RGB-onlyでuniform blackは判定不能 | 本ticket | UNKNOWN |

### Act

- FLR-0111のremote残件とは独立して、本ticketでは画像分類の再現性を固める。
- 分類結果がnative draw不足なら、present/render ownerの新規ticketへ分割する。
- 分類結果が合成隠蔽なら、surface/alpha/compositorの新規ticketへ分割する。

## Decision log

- 2026-09-12: 既存non-background countだけでproductionの無描画を断定しない。過去のmodel-only画像が黒色車体を実画素として示すため、画像分類を独立ticket化した。

## Unknowns

- production native surfaceに黒色geometryが存在するか。
- native readbackとQMP最終画面の差分。
- edge/contrast指標の閾値をどこに置くか。

## Current condition summary

The current evidence answers the operational question “under which conditions
do 2D, 3D, camera, and light succeed or fail?” as follows:

| Condition | 2D/HUD | Native 3D | Camera | Result |
| --- | --- | --- | --- | --- |
| Full production, explicit lights enabled | visible | `0/223200` | applied/valid markers present | 3D FAIL at the production shaded-light boundary |
| Same production stage, explicit lights skipped | visible | `4905/223200` | same camera/present path | 2D+3D PASS control |
| Sequoia model-only | visible/controlled | `140034/223200` | `(5,0,-5)`, target `(0,0,0)`, near `0.05`, far `1000` | model/camera/output PASS |
| Self-made pure fixture | visible | `41750/223200` | fixed fixture camera | native fixture/output PASS |

These values are from the reconciled current-image records in FLR-0077 and the
fixed light A/B in FLR-0067. They are not a claim that all four rows came from
one process; each row retains its recorded image identity.

Camera is not the current first stable failure: the black full-production
cases still apply a valid camera and reach frame/present markers, while the
model-only control renders with that camera. A separate historical fixture
failure came from dereferencing the old production camera graph before native
scene creation; the camera-isolated fixture corrected that route.

The explicit-light path is the current first stable difference. One selected
POINT light (GUID 126 or GUID 128) also remained black, and a trace-visible
one-off was not reproducible. Therefore the exact light construction,
Scene-attachment, material/resource, target, or readback operation remains
UNKNOWN; no one of them is promoted to root cause yet.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings:
