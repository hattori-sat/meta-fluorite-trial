# Task dashboard

Last updated: 2026-09-29

## Current focus

**FLR-0211 closed the SHM geometry mismatch and falsified the Vulkan clipping discriminator; FLR-0214 proved the RGB-positive WSI buffer reaches the compositor, FLR-0215 identified the native surface-composition boundary, FLR-0216 proved the SHM control, FLR-0217 proved readback completion, FLR-0218 closed the image-identity hypothesis, FLR-0219 proved the native Wayland client lifecycle, FLR-0220 proved real chromatic geometry in the native target, and FLR-0221 proved that the existing SHM bridge displays the geometry while native-only QMP remains black. FLR-0222 is paused on native-only restoration; FLR-0224 closed the input-coverage boundary and FLR-0225 now owns the post-input white-surface/composition boundary.**

**[FLR-0235 — replace Material hover button with static clickable surface](work/tickets/FLR-0235-replace-material-hover-button.md) is Done.** QMP proves simultaneous 2D HUD and native 3D cube through the tested pointer-motion sequence; the FLR-0234 full-white transition did not recur. **[FLR-0236 — activate Planetarium scene from the Scenes control](work/tickets/FLR-0236-activate-planetarium-scene.md) is Done:** the callback marker and input path are proven, but post-tap HUD composition becomes uniform white and Planetarium pixels are not proven. **[FLR-0237 — fix Planetarium route composition and visible scene ownership](work/tickets/FLR-0237-fix-planetarium-route-composition.md) is Done:** removing the route's full-surface gesture build did not remove the white post-tap frame. **[FLR-0238 — isolate route-state mount from parent repaint](work/tickets/FLR-0238-isolate-route-state-mount-repaint.md) is Done:** marker-only parent `setState` reproduced the white HUD while the native fixture stayed visible. **[FLR-0239 — isolate parent setState from the repaint boundary](work/tickets/FLR-0239-isolate-parent-setstate-repaint.md) is Done:** removing parent `setState` preserved both HUD and native 3D through the QMP tap. **[FLR-0240 — mount scene subtree without parent repaint](work/tickets/FLR-0240-mount-scene-subtree-without-parent-repaint.md) is Done:** child-only mounting still whitened the HUD while native 3D stayed visible. **[FLR-0241 — isolate Planetarium lifecycle callbacks](work/tickets/FLR-0241-isolate-planetarium-lifecycle-callbacks.md) is Done:** inert lifecycle bodies produced the same white HUD while native 3D stayed visible. **[FLR-0242 — isolate generic StatefulSceneView mount](work/tickets/FLR-0242-isolate-stateful-sceneview-mount.md) is Done:** a generic inert StatefulSceneView also whitened the HUD after QMP button-up while the native 3D remained visible. **[FLR-0243 — isolate plain child replacement](work/tickets/FLR-0243-isolate-plain-child-replacement.md) is Done:** a plain inert `SizedBox` also whitened the HUD while the native fixture remained visible; FLR-0244 owns the builder-rebuild versus child-identity discriminator. **FLR-0286 now owns reproduction of the historical combined Sequoia/HUD/light condition.**

**Current production boundary:** [FLR-0348](work/tickets/FLR-0348-watch-lavapipe-signal-without-fence-type.md) is Done as a bounded two-predicate diagnostic: both GDB watches armed, neither hit during 8.07 seconds, and both fields remained false/null. QMP showed the HUD and metrics while all 768,000 pixels in the lower 3D ROI remained black; teardown passed. This is not a production 2D+3D success and does not identify the producer or establish causality. [FLR-0345](work/tickets/FLR-0345-retrospective-3d-visibility-checklist.md) and [FLR-0349](work/tickets/FLR-0349-audit-3d-countermeasure-effectiveness.md) retain the historical comparison and intervention audit. FLR-0070 p9 remains unstable evidence; Photo 1 is a static GLB emissive texture, not a QMP runtime frame. FLR-0348 used a diagnostic-only unlinked-fence-ready override, so its stall must not be generalized to neutral production.

**Handoff prerequisite:** [FLR-0351](work/tickets/FLR-0351-validate-mini-handoff-before-receiver-update.md) is Done. A bounded, read-only check independently confirmed the Mini receiver at exact feature tip `5e46a1ecc97cb1e5e0df76ea1cbecceaa83df103`, clean, with BitBake idle and fixed `TOPDIR`/effective `TMPDIR` roles matching. The existing bundle SHA and tip were verified. The original helper's final client marker/exit code is still UNKNOWN, but receiver state is proven; no retransmission is warranted. No build or QEMU run occurred in FLR-0351.

**FLR-0350 is Done as a bounded partial experiment:** its one QEMU attempt failed closed at the pre-exec FIFO gate, before Flutter or GDB started. The QMP still/eight frames and host teardown are recorded; the black frame is not a Flutter render result. Producer correlation and the overall 3D objective remain UNKNOWN/open. The follow-up is a separate runner-gate/cleanup task.

**[FLR-0354 — repair and deterministically test the pre-exec FIFO launch gate](work/tickets/FLR-0354-fix-flr0350-fifo-launch-gate.md) is Done as a harness-only correction.** It adds object-identity validation, early process identity capture, deterministic tests, and fresh-ID enforcement. It does not change the product or establish a rendering result; the 3D objective remains open for a separate fresh runtime ticket.

**[FLR-0355 — relay a fresh run ID and retest the FIFO gate on QEMU](work/tickets/FLR-0355-relay-run-id-and-retest-fifo-gate.md) is Waiting.** Its only run stopped before FIFO observation because the runner omitted that command from staging; its black QMP image is not a render verdict and `flr0355-0001` will never be retried. **[FLR-0356 — stage the FIFO observer before QEMU launch](work/tickets/FLR-0356-stage-fifo-observer-before-qemu.md) is Waiting**; target FIFO identity fields matched, but strict host validation failed at `marker-not-first` before GDB/GO. Its QMP image is pre-GO and cleanup passed. **[FLR-0357 — refresh the 3D visibility retrospective](work/tickets/FLR-0357-refresh-3d-visibility-retrospective.md) is Done** as an evidence-only retrospective; it does not close the rendering goal. **[FLR-0358 — establish a fail-closed serial capture boundary](work/tickets/FLR-0358-clear-serial-buffer-before-command.md) is In Progress pending handoff**; its only Mini attempt used a byte-different FLR-0335 helper copy and stopped before GDB/GO. The QMP black frame is pre-GO, and `flr0358-0001` must not be retried.

WIP limit: 原則`In Progress`は1件。緊急割込みは理由をworking logへ残す。

## Ticket unit policy

- 1つのMarkdown ticketは、1つの独立した検証単位だけを扱う。
- 完了時はPDCA、Facts/Inferences/Hypotheses/UNKNOWN、QMP-only写真または画面証拠、ログ、ハッシュを同じticketへ記録する。
- 次の仮説検証・修正・画面遷移は、前ticketを再利用せず新しいMarkdown ticketへ分割する。
- Jiraへの登録は行わず、リポジトリ内のticketとworking logを正本とする。
- `FLR-0026`と既存の`FLR0026_*`文字列は初期3D検証の履歴専用とし、現行の作業ディレクトリ・受け口・環境変数・証跡名には再利用しない。新規診断は`FLUORITE_*`命名を使う。

## In Progress

| ID | Problem / outcome | Owner | PDCA | Next action |
| --- | --- | --- | --- | --- |
| [FLR-0358](work/tickets/FLR-0358-clear-serial-buffer-before-command.md) | establish a fail-closed fresh serial capture boundary before the FLR-0350 gate | QEMU serial harness / runtime-gate roles | Local capture fix passed its loopback tests, but Mini run `flr0358-0001` selected old helper SHA `339472…` rather than current bundle helper `088e8e…`; FIFO validator stopped at `marker-not-first` before GDB/GO, so the serial fix was not exercised and QMP black is pre-GO only | Complete this bounded attempt record; do not retry the run ID. Hand off the separate exact-helper selection fix to a new ticket |
| [FLR-0356](work/tickets/FLR-0356-stage-fifo-observer-before-qemu.md) | stage every static guest serial command before QEMU start and evaluate the actual-FD FIFO gate once | Mac runner / Mini QEMU / QMP evidence roles | Waiting: 28 tests pass; Mini staged 11/11 commands and captured matching FIFO fields, but official host validation stopped at `marker-not-first`; pre-GO black QMP is not a render verdict; cleanup passed | Resume after FLR-0358 fixes framing and a fresh one-shot gate passes; do not reuse `flr0356-0001` |
| [FLR-0355](work/tickets/FLR-0355-relay-run-id-and-retest-fifo-gate.md) | propagate a fresh ticket run ID through preflight/start, then test the corrected FIFO gate on the pinned QEMU image | Mac runner / Mini QEMU / QMP evidence roles | Waiting: one attempt consumed `flr0355-0001`; staging omitted the FIFO-observer command, so the gate/attach/GO did not run; QMP was uniformly black and teardown passed | FLR-0356 owns the staging fix and a fresh one-shot runtime attempt; never retry `flr0355-0001` |
| [FLR-0348](work/tickets/FLR-0348-watch-lavapipe-signal-without-fence-type.md) | observe both Lavapipe wait-release predicates without unavailable DWARF types | bounded GDB script / Mini runtime / QMP evidence roles | Done: exact image, both hardware watches armed; 8.07-second no-hit with fields false/null; QMP HUD visible and 768,000-pixel 3D ROI black; app/QEMU/QMP teardown passed | FLR-0350 stopped before app launch; FLR-0355 repairs the run-ID handoff before fresh producer-correlation evidence |
| [FLR-0335](work/tickets/FLR-0335-compare-present-without-gdb.md) | compare production present behavior with and without GDB | production Example Demo / FEngine / QMP runtime roles | Done: no-GDB control reproduced the same FEngine/libLLVM `isOrdered+1` fault at 284.16s; QMP remained HUD-only/native-black; the planned 720s was not reached because the fault occurred first | FLR-0338 captures pre-instruction control-flow context |
| [FLR-0332](work/tickets/FLR-0332-trace-native-buffer-publish-trigger.md) | trace native buffer publish trigger after surface creation | native render target publish / Wayland buffer attach roles | Done: current ViewTarget reaches draw and explicit commit A/B, but Vulkan queue-present does not return; child surface has no attach and QMP remains HUD-only/native-black | FLR-0333/0335 classify the recurring fault boundary; FLR-0338 captures pre-fault caller state |
| [FLR-0331](work/tickets/FLR-0331-trace-current-native-wayland-surface-composition.md) | trace current native Wayland surface composition after draw submit | native Wayland surface attach/commit/import and QMP composition | Done: parent surface commits, but native `wl_surface@39` never attaches/damages/commits in the bounded current-image run | FLR-0332 owns native buffer publish trigger |
| [FLR-0330](work/tickets/FLR-0330-replay-production-without-readback-diagnostic.md) | replay the production control without native readback instrumentation | production Sequoia render/present path versus readback diagnostic | Done: no-readback control reaches Scene/draw and remains HUD-only/native-black; readback is observational, not causal | FLR-0331 owns native surface composition |
| [FLR-0329](work/tickets/FLR-0329-classify-readback-fence-timeout.md) | classify native readback fence timeout behavior | Filament Vulkan readback fence / llvmpipe queue completion | Done: bounded probe returns `VK_TIMEOUT`, cleanup completes, and QMP remains HUD-only/native-black | FLR-0330 owns no-readback causality A/B |
| [FLR-0328](work/tickets/FLR-0328-trace-readback-completion-boundary.md) | trace native readback completion boundary after command recording | Filament Vulkan readback queue / fence / callback roles | Done: static mapping and one QMP-first run identify the first missing event after `FENCE_WAIT_BEGIN`; no source patch or Light/camera change | FLR-0329 owns bounded fence-timeout classification |
| [FLR-0271](work/tickets/FLR-0271-trace-readback-child-surface-visibility.md) | trace readback child-surface visibility in composed output | readback child-surface visibility / compositor import | Done: continuous QMP control proves self-made 3D plus 2D pixels; QMP omission is falsified, readback surface/import remains unresolved | FLR-0252 owns production-scene verification |
| [FLR-0272](work/tickets/FLR-0272-diagnose-production-asset-loading-oom.md) | diagnose production asset/Scene loading OOM before stable 3D and input transition | production asset lifecycle / Scene ownership | Done: bounded model loading removes the guest-OOM loop; Run 0303 proves camera selection and isolates the remaining post-activation render/surface boundary | FLR-0273 owns the controlled fixture-versus-production comparison |
| [FLR-0273](work/tickets/FLR-0273-isolate-post-activation-render-surface-visibility.md) | isolate post-activation render content from Wayland child-surface visibility | runtime render content / surface composition | Done: same-image fixture produces colored QMP 3D while production remains zero-chroma; shared QEMU/Wayland/QMP black-path hypothesis is falsified | FLR-0274 owns production model/material/lighting visibility |
| [FLR-0274](work/tickets/FLR-0274-diagnose-production-model-material-visibility.md) | diagnose production model/material/lighting visibility after camera activation | production scene asset / material / lighting runtime roles | Done: 0091 changes effective camera to Playground; authoritative QMP remains zero-chroma, so camera was necessary but insufficient | FLR-0275 owns production payload isolation |
| [FLR-0307](work/tickets/FLR-0307-probe-production-fragment-output-target.md) | probe production fragment output versus target handoff | production Sequoia fragment/output and target-boundary roles | Waiting: official patch/build/QMP gates pass, but the production engine fault occurs before the emissive/material seam | resume after the runtime fault boundary is separated |
| [FLR-0275](work/tickets/FLR-0275-isolate-production-payload-visibility.md) | isolate production payload visibility after camera correction | production model / shape / material / native scene attachment roles | Done: the attempted A/B was invalid because current source ignored the stale model-skip control and OOM-killed flutter-auto before visual verdict | FLR-0276 owns bounded current-source model loading |
| [FLR-0276](work/tickets/FLR-0276-restore-bounded-production-model-control.md) | validate bounded production model-payload control | production asset loading / current scene-stage diagnostic controls | Done: current controls selected one model at 4096MiB without OOM; production then SIGSEGVed in `CallEvent`, while the same-QEMU pure fixture produced colored QMP geometry | FLR-0277 owns the production `CallEvent`/render crash boundary |
| [FLR-0277](work/tickets/FLR-0277-isolate-production-call-event-segv.md) | isolate production `CallEvent` SIGSEGV after bounded model load | production frame-event lifecycle / render-thread safety | Done: normal and frame-event-skip production both survived without a core; skip did not restore chromatic pixels, so the direct-cause hypothesis is not proven | FLR-0278 owns production grayscale/no-chroma render content |
| [FLR-0278](work/tickets/FLR-0278-isolate-production-grayscale-render-content.md) | isolate production grayscale render content after frame-event A/B | production model/material/lighting and target-content state | Done: 4096 MiB is healthy; lights-on and shape-skip did not sustain chroma, and delayed SIGSEGV is in CallEvent/DrawFrame | FLR-0279 owns the opaque surface-composition discriminator |
| [FLR-0279](work/tickets/FLR-0279-isolate-production-opaque-surface-composition.md) | isolate production opaque surface composition | production View blend mode / Flutter-Wayland surface composition | Done: opaque mode was effective (`blend=0`) but late QMP remained zero-chroma; no coredump and teardown passed | FLR-0280 owns production model content binding |
| [FLR-0280](work/tickets/FLR-0280-trace-production-model-content-binding.md) | trace production model content binding | production model transform/material binding and default-scene content | Done: model limit 1 selects primary mode, which current source intentionally does not add to scene; QMP stayed black | FLR-0281 validates the secondary model instance |
| [FLR-0281](work/tickets/FLR-0281-validate-secondary-production-model-instance.md) | validate secondary production model instance | production model selection and secondary scene attachment | Done: model limit 2 loaded Sequoia and Fox, but both dispatched as primary; no secondary scene/material path was reached and QMP remained zero-chroma | FLR-0282 owns primary scene attachment |
| [FLR-0282](work/tickets/FLR-0282-attach-primary-production-model-to-scene.md) | attach the primary production model to the scene | primary production model scene attachment | Done: official 0286, Mini do_patch/compile/image, scene-add/material/draw evidence passed; QMP remained black with lighting skipped | FLR-0283 owns production lighting A/B |
| [FLR-0283](work/tickets/FLR-0283-restore-production-lighting-ab.md) | restore production lighting for the attached model | production lighting and material visibility | Done: indirect light restored, but QMP SHA/chroma remained unchanged and direct lights were still skipped | FLR-0284 owns direct-light A/B |
| [FLR-0284](work/tickets/FLR-0284-restore-production-direct-lights-ab.md) | restore direct production lights for the attached model | production direct-light contribution | Done: direct lights restored without fault, but QMP remained zero-chroma; scene-pass command count changed to 1 | FLR-0285 owns render-queue/draw-command tracing |
| [FLR-0285](work/tickets/FLR-0285-trace-production-draw-command-boundary.md) | trace the production draw-command boundary | production render queue and target draw boundary | Waiting: model/3D pixels and the HUD-only split are recorded; historical combined-condition reproduction moved to FLR-0286 | resume only after FLR-0286 establishes the current positive baseline |
| [FLR-0286](work/tickets/FLR-0286-reproduce-known-good-combined-sequoia-hud.md) | reproduce historical combined Sequoia/HUD/light pixels | runtime validation and composition baseline | Waiting: self-made lit Filament fixture plus HUD is a positive control; Sequoia acceptance remains open | FLR-0287 owns production Sequoia camera/material/light comparison |
| [FLR-0287](work/tickets/FLR-0287-compare-production-sequoia-light-material.md) | compare production Sequoia camera/material/light visibility against the lit fixture control | production scene camera, asset/material, and light attachment roles | Waiting: camera/model/material/scene draw pass, native ROI remains completely black | FLR-0288 owns the single native diagnostic-scene light-attachment A/B |
| [FLR-0288](work/tickets/FLR-0288-test-production-light-attachment-in-diagnostic-scene.md) | test production light attachment in the native diagnostic scene | production light ownership and render-target visibility | Waiting: 13-light attachment reached, but diagnostic scene forced opaque blend and hid HUD; light-only verdict invalid | FLR-0289 owns the opt-in translucent diagnostic-surface probe |
| [FLR-0289](work/tickets/FLR-0289-add-opt-in-translucent-diagnostic-surface.md) | add an opt-in translucent diagnostic surface for the production light A/B | diagnostic surface blend contract | Waiting: opt-in blend=translucent and 13-light attachment pass, but QMP becomes full white with only 2 colored native pixels | FLR-0290 owns diagnostic native-surface alpha/Wayland stacking observation |
| [FLR-0290](work/tickets/FLR-0290-observe-diagnostic-surface-alpha-stacking.md) | observe diagnostic native-surface alpha and Wayland stacking | native surface alpha / compositor ownership | Waiting: attach/damage/commit/release and place_above pass with no protocol error, but beginFrame is false almost continuously | FLR-0291 owns the Filament beginFrame failure after native-surface attach |
| [FLR-0291](work/tickets/FLR-0291-isolate-begin-frame-failure-after-native-attach.md) | isolate Filament beginFrame failure after native-surface attach | renderer beginFrame / swapchain lifecycle | Waiting: fixed image/runtime proves beginFrame false after native attach; QMP is uniform and not a light verdict | FLR-0292 owns the one-variable swapchain configuration A/B |
| [FLR-0292](work/tickets/FLR-0292-ab-swapchain-configuration-before-begin-frame.md) | A/B transparent versus opaque native swapchain before beginFrame | Filament swapchain configuration / Vulkan acquire lifecycle | Waiting: opaque mode logged and produced the exact FLR-0291 beginFrame/QMP result; swapchain alpha is falsified | FLR-0293 owns bounded GDB inspection of the beginFrame return path |
| [FLR-0293](work/tickets/FLR-0293-inspect-begin-frame-return-path.md) | inspect Filament beginFrame return path with target GDB | Filament renderer / Vulkan acquire diagnostics | Waiting: GDB attach passed but release binary has no beginFrame symbols; bounded backtrace retained | FLR-0294 owns existing FrameSkipper/fence sync trace |
| [FLR-0294](work/tickets/FLR-0294-trace-frame-skip-fence-status.md) | trace FrameSkipper fence status behind beginFrame=false | Filament FrameSkipper / Vulkan fence lifecycle | Waiting: status=1 is TIMEOUT_EXPIRED and the false-heavy loop follows linked=false; transient linked recovery prevents a sole-root-cause claim | FLR-0295 owns the existing unlinked-fence-ready A/B |
| [FLR-0295](work/tickets/FLR-0295-ab-unlinked-fence-ready.md) | A/B unlinked FrameSkipper fence readiness | Filament FrameSkipper / Vulkan fence lifecycle | Waiting: forcing unlinked fences ready restores beginFrame/draw/present, but QMP is byte-identical uniform gray | FLR-0296 owns production Sequoia under recovered frame loop |
| [FLR-0296](work/tickets/FLR-0296-production-sequoia-after-frame-recovery.md) | replay production Sequoia after frame-loop recovery | production Sequoia content/material/light/composition | Waiting: frame/draw/present recover and HUD is visible, but production native ROI remains black; scene_default is expected | FLR-0297 owns current-image model-only control |
| [FLR-0297](work/tickets/FLR-0297-reproduce-current-model-only-control.md) | reproduce current-image Sequoia model-only control | production Sequoia camera/culling/material baseline | Waiting: wide-camera model-only run is black despite model/draw/present/HUD; historical default-camera silhouette exists | FLR-0298 owns default-camera replay |
| [FLR-0298](work/tickets/FLR-0298-replay-default-camera-sequoia.md) | replay default-camera Sequoia model-only condition | production Sequoia camera/framing runtime | Waiting: default camera produces the same HUD-only frame as wide camera; no vehicle silhouette | FLR-0299 owns one-variable asset selector comparison |
| [FLR-0299](work/tickets/FLR-0299-compare-sequoia-asset-selection.md) | compare Sequoia asset selection for model-only visibility | production model selection/asset visibility | Waiting: both selectors resolve to sequoia_ngp and produce identical HUD-only frame | FLR-0300 owns existing culling-disable A/B |
| [FLR-0300](work/tickets/FLR-0300-ab-production-culling.md) | A/B production culling for Sequoia model-only visibility | production Sequoia culling/frustum visibility | Waiting: diagnostic culling switch does not reach production path; frame unchanged, materials/bounds present | FLR-0301 owns primary model transform/scene boundary |
| [FLR-0301](work/tickets/FLR-0301-inspect-production-primary-model-transform.md) | inspect production primary-model transform and scene ownership | production ModelSystem transform/scene boundary | Waiting: source-backed classification complete; FLR-0302 owns the bounded runtime probe | FLR-0302 owns world transform/root attachment probe |
| [FLR-0302](work/tickets/FLR-0302-probe-production-world-transform.md) | probe production Sequoia world transform and root attachment | production ModelSystem transform/scene boundary | Waiting: valid root/child/world transform and materials, but native ROI remains black; FLR-0304 owns camera/culling boundary | inspect effective camera/frustum/culling |
| [FLR-0303](work/tickets/FLR-0303-fix-transform-probe-compile.md) | fix production transform probe compile contract | production ModelSystem transform/scene boundary | Done: Mini do_patch, component compile, full image, and QEMU probe all passed | FLR-0304 owns next runtime boundary |
| [FLR-0304](work/tickets/FLR-0304-probe-production-camera-culling-visibility.md) | probe production camera, frustum, and culling visibility | production ViewTarget camera/renderable visibility | Done: effective camera matrices observed; 108-renderable production culling A/B left native ROI at 0/144000 while HUD remained 2845 chromatic | FLR-0305 owns production default-Scene light |
| [FLR-0305](work/tickets/FLR-0305-probe-production-default-scene-light.md) | probe a self-made light in the production default Scene | production default Scene lighting/material evaluation | Done: default-Scene SUN attached and logged; native ROI remained 0/144000 while HUD remained 2845 chromatic | FLR-0306 owns material/output |
| [FLR-0306](work/tickets/FLR-0306-probe-production-material-output.md) | probe production material and fragment output | production Sequoia material/fragment output | Waiting: material metadata, Scene draw, and present are positive but native ROI remains 0/144000; FLR-0307 owns fragment/target boundary | inspect one-variable fragment output |
| [FLR-0308](work/tickets/FLR-0308-diagnose-fengine-loop-page-fault.md) | diagnose FEngine loop page fault during production load | Flutter engine loop / production asset-load runtime | Waiting: one-model A/B classifies non-zero SUN as the trigger candidate; zero-intensity discriminator is split out | resume after FLR-0309 separates light creation from lighting contribution |
| [FLR-0309](work/tickets/FLR-0309-probe-zero-intensity-production-light.md) | separate production light creation from non-zero lighting contribution | production default-Scene SUN / LLVM-llvmpipe runtime boundary | Done: zero-intensity SUN still reaches present and reproduces the FEngine/libLLVM page fault; native ROI remains 0/144000 and all QMP video frames are identical | FLR-0310 owns light-registration versus renderer-present boundary |
| [FLR-0310](work/tickets/FLR-0310-isolate-production-light-registration-present-boundary.md) | isolate production light registration from the renderer-present fault boundary | production light entity registration / renderer queue-present lifecycle | Done: moving the opt-in SUN before ECS update leaves the same FEngine/libLLVM fault and identical black native ROI | FLR-0311 owns production GLTF/material/asset fault versus the known-good LIT fixture |
| [FLR-0311](work/tickets/FLR-0311-compare-production-gltf-material-fault-with-lit-fixture.md) | compare production GLTF/material asset fault with the known-good LIT fixture | production asset/material shader path versus direct Filament fixture | Done: zero and normal light A/B both reach asset create/async load/present but native ROI remains 0/144000; light intensity is falsified as the distinguishing variable | FLR-0312 owns post-load renderable/material boundary |
| [FLR-0312](work/tickets/FLR-0312-trace-production-post-load-renderable-material.md) | trace production post-load renderable and material setup | production async resource completion / Scene attachment / renderable-material roles | Done: corrected scene-stage trace proves asset loaded, Scene add completed, 12 renderables and 21 materials; native ROI remains 0/144000 | FLR-0313 owns camera/culling/target visibility |
| [FLR-0313](work/tickets/FLR-0313-trace-production-camera-culling-target.md) | trace production camera, culling, and target visibility | production camera/frustum/culling / render-target visibility roles | Done: camera/transform/target metadata valid, but beginFrame false=45141 and native ROI remains 0/144000 | FLR-0314 owns emissive-output visibility control |
| [FLR-0314](work/tickets/FLR-0314-test-production-emissive-output.md) | test production Sequoia emissive output visibility | production material output / camera and target visibility roles | Done: frame recovery and Glass emissive override pass, but native ROI remains 0/144000; override did not target PaintColor | FLR-0315 owns body-material emissive control |
| [FLR-0315](work/tickets/FLR-0315-target-production-body-emissive-control.md) | target the production body emissive control | Mac Devtool source / PaintColor material / Mini runtime roles | Done: official patch/build/runtime pass; PaintColor has no emissiveFactor, so native ROI remains 0/144000 while HUD remains 2845 chromatic | FLR-0316 owns actual PaintColor parameters and self-made emissive/light control |
| [FLR-0316](work/tickets/FLR-0316-inspect-paintcolor-material-and-selfmade-light.md) | inspect PaintColor parameter contract and self-made light/emissive control | Filament material parameters / self-made control / production comparison | Done: actual PaintColor parameters and FLR-0316 QMP result recorded; Light/asset/draw/HUD pass but production ROI remains 0/144000 and baseColor branch did not fire | FLR-0317 owns predicate-level PaintColor override trace |
| [FLR-0317](work/tickets/FLR-0317-trace-paintcolor-override-predicate.md) | reproduce the historical tail-light positive baseline | production Sequoia resource/material / runtime profile / QMP roles | Waiting: frame-ready and wide-camera conditions pass, but the vehicle ROI remains 0/144000; source comparison found a primary+secondary scene-attachment difference | FLR-0318 owns the primary/secondary duplicate-attachment A/B |
| [FLR-0318](work/tickets/FLR-0318-ab-primary-secondary-scene-attachment.md) | A/B the primary production model scene attachment against the historical tail-light-positive path | production model instancing / Scene attachment / depth and material visibility roles | Done: primary-attach skip leaves native ROI 0/144000 with HUD unchanged; duplicate attachment is rejected | FLR-0319 owns production GLB material/texture/sampler binding |
| [FLR-0319](work/tickets/FLR-0319-trace-production-material-texture-binding.md) | trace production GLB material, texture, and sampler binding against the red-tail-light baseline | GLB resource loader / Filament material parameter and texture binding roles | Done: source/deployed asset match; HeadLights and emissiveIndex are present; QMP native ROI remains 0/144000, so the next boundary is gltfio texture readiness/binding | FLR-0320 owns gltfio texture readiness and binding completion |
| [FLR-0320](work/tickets/FLR-0320-trace-gltfio-texture-readiness-binding.md) | trace production gltfio texture readiness and emissiveMap binding completion | Filament gltfio ResourceLoader / TextureProvider / dependency graph roles | Done: texture readiness queues and reapplies emissiveMap; QMP native ROI remains black, so binding is not the missing edge | FLR-0321 owns post-binding vehicle visibility/draw-to-surface boundary |
| [FLR-0321](work/tickets/FLR-0321-trace-post-binding-vehicle-visibility.md) | trace post-binding vehicle visibility and draw-to-surface output | Filament renderable visibility / camera-frustum / Vulkan-Wayland surface roles | Done: fixture pixels, production scene/material/bind/draw/present markers, and camera/attachment A/B place the first missing boundary in production material/fragment output; texture preview is not runtime evidence | FLR-0322 owns the existing PaintColor predicate trace |
| [FLR-0322](work/tickets/FLR-0322-trace-paintcolor-runtime-predicate.md) | trace the existing PaintColor runtime predicate without a new source edit | Devtool source Git / production PaintColor material predicate / Mini QMP roles | Done: official registration, Mini do_patch/compile/image, and QMP pass; marker absent because the diagnostic was gated by the same `material_match` it was meant to measure | FLR-0323 owns an unconditional predicate trace |
| [FLR-0323](work/tickets/FLR-0323-trace-paintcolor-predicate-operands.md) | trace all PaintColor predicate operands without hiding false values | persistent Devtool source Git / production material predicate / Mini QMP roles | Done: official patch/build/QMP pass; asset and base-color predicates are true, but `material_name=PaintColor` reports `material_match=false` because the source compares a `const char*` with a literal by pointer identity | FLR-0324 owns the minimal string-content comparison fix |
| [FLR-0324](work/tickets/FLR-0324-fix-paintcolor-string-comparison.md) | fix PaintColor string-content comparison and retest Sequoia pixels | persistent Devtool source Git / production material predicate / Mini QMP roles | Done: official patch/build/QMP pass; PaintColor comparison and baseColor override now fire, but native ROI remains 0/144000 | FLR-0325 owns post-override material/fragment output |
| [FLR-0325](work/tickets/FLR-0325-trace-post-override-material-output.md) | trace post-override material state and renderable binding | persistent Devtool source Git / Filament material output / Mini QMP roles | Done: post-override value is `(1,0,1,1)`, same bound MaterialInstance is `PaintColor`, and QMP proves HUD-only/native-black | FLR-0326 owns fragment-output versus native-target boundary |
| [FLR-0326](work/tickets/FLR-0326-probe-production-fragment-target-boundary.md) | probe production fragment output versus native target | Filament production material/fragment output and native target roles | Done: fixed-color replacement, Scene/draw/present, driver readback entry/command recording/exit passed; completion/result/callback absent and QMP native ROI remained 0/144000 | FLR-0328 owns the readback completion boundary |
| [FLR-0307](work/tickets/FLR-0307-probe-production-fragment-output-target.md) | probe production fragment output versus target handoff | production Sequoia fragment emission and visible target handoff | Waiting: official patch/build/QMP gates pass, but FEngine::loop page-faults before the emissive/material seam | FLR-0308/0309 own the first runtime fault boundary |

## Inbox

| [FLR-0327](work/tickets/FLR-0327-align-mac-mini-source-baseline.md) | align Mac Devtool and Mini flutter-auto source baseline | Mac Devtool / authoritative Yocto source identity | Done: Mac effective revisions and do_patch plus Mini bundle/do_patch now match | keep the project-layer pins as the deterministic source contract |

| [FLR-0253](work/tickets/FLR-0253-restore-production-frame-event-registration.md) | restore production frame-event registration order | Done: official 0084 is applied through Mini rootfs and libapp.so, but runtime proves PlanetariumSceneView starts readiness polling before onPlatformViewCreated; QMP 2D HUD remains visible and production 3D remains black | FLR-0255 owns the pre-Platform-View readiness poll |
| [FLR-0255](work/tickets/FLR-0255-defer-readiness-poll-until-platform-view.md) | defer readiness polling until Platform View creation | Done: official 0085 reached native registration, model selection, draw/present, and Wayland attach; QMP HUD `2845` remains visible but production ROI has `0` chromatic pixels and onCreated/readiness completion is absent | FLR-0256 owns the PlatformView callback boundary |
| [FLR-0256](work/tickets/FLR-0256-trace-platform-view-created-callback.md) | trace PlatformView-created callback reachability | Done: official 0086 and QMP probe show all app callback markers absent while native registration/draw/present/Wayland markers pass; 2D HUD `2845`, production ROI `0` chromatic | FLR-0257 owns native create-result delivery |
| [FLR-0257](work/tickets/FLR-0257-trace-platform-view-create-result.md) | trace native PlatformView create result delivery | Done: official 0275 is present in the guest binary; C API return and 2D HUD pass, but both result markers and app callback markers remain absent, so the caller/handler boundary is split to FLR-0258 | FLR-0258 owns the handler return boundary |
| [FLR-0258](work/tickets/FLR-0258-trace-platform-view-handler-return.md) | trace PlatformView handler return boundary | Done: official 0276 passed Mini patch/compile/image/QMP; handler entry and call begin occur, call return/end and downstream result/callback markers do not, while HUD is visible and production 3D remains black | FLR-0259 owns native call-stack and wait/fault classification |
| [FLR-0259](work/tickets/FLR-0259-trace-platform-view-create-block.md) | trace PlatformView create call non-return | Done: official 0277 passed Mini patch/compile/image/QMP; bounded gdb/eu-stack proved cyclic future waits, and the async drain repair made handler/result/callback/drain markers return; QMP now shows a black PlatformView trapezoid over 2D | FLR-0260 owns black production render content |
| [FLR-0254](work/tickets/FLR-0254-repair-mac-app-recipe-gate.md) | repair Mac app recipe do_patch gate dependency profile | Done: focused extraction preserves provider metadata; official `modify --no-extract` registered the existing clean app source in the fixed Podman container | FLR-0272 resumes camera-contract source correction |

| [FLR-0250](work/tickets/FLR-0250-repair-mac-devtool-parser-response.md) | repair Mac Devtool parser response path | Done: tracked response shim plus focused recipe profile; official wrapper modify/finish-source passed with one generated patch and no stale process | FLR-0249 resumed Mini build/runtime |

| [FLR-0224](work/tickets/FLR-0224-clear-native-input-coverage-for-flutter-route.md) | clear native input coverage for Flutter route | Done: official current-source patch 0272 applied on Mini; QMP click entered the Flutter parent surface, but no Scenes marker appeared and HUD became uniform white; clean teardown | FLR-0225 owns post-input composition |

| [FLR-0225](work/tickets/FLR-0225-diagnose-post-input-white-composition.md) | diagnose post-input white surface and route composition | Done: stepwise QMP isolated the first white transition to Flutter-parent repaint after pointer motion into the Scenes area; native cube ROI stayed unchanged, no native reattach followed, neutral move was unchanged, and both QEMU teardowns passed | FLR-0226 owns the transparent-parent/hover correction |

| [FLR-0226](work/tickets/FLR-0226-fix-flutter-parent-hover-composition.md) | fix Flutter-parent hover composition | Done: official transparency patch passed Mini do_patch/do_compile/image, but QMP reproduced the same uniform parent/HUD white frame while the native ROI stayed unchanged; QMP quit/cleanup passed | FLR-0227 owns MenuAnchor/hover-layer isolation |

| [FLR-0227](work/tickets/FLR-0227-isolate-menuanchor-hover-composition.md) | isolate MenuAnchor hover composition | Done: official MenuAnchor-removal A/B passed Mini do_patch/do_compile/image and reproduced the same parent/HUD white frame with unchanged native ROI; QMP quit/cleanup passed | FLR-0228 owns Flutter embedder/parent repaint |
| [FLR-0228](work/tickets/FLR-0228-isolate-flutter-parent-repaint-composition.md) | isolate Flutter-parent repaint composition | Done: runtime parent-alpha probe kept native 3D unchanged but reproduced parent/HUD white after input; static source narrowed the next discriminator to output-enter `SetPixelRatio` metrics resend | FLR-0229 owns the single A/B |
| [FLR-0229](work/tickets/FLR-0229-isolate-output-enter-pixel-ratio-repaint.md) | isolate output-enter pixel-ratio repaint | Done: official root-level Devtool patch passed Mini do_patch/do_compile/image; skipping output-enter SetPixelRatio preserved HUD through move-y with native 3D unchanged, but button up still whitened HUD | FLR-0231 owns button-release repaint |
| [FLR-0231](work/tickets/FLR-0231-isolate-button-release-repaint.md) | isolate button-release repaint | Done: official button-up gate passed Mini do_patch/do_compile/image; QMP control and button-up-skip had identical `up.ppm` and uniform-white HUD, while native 3D stayed at `24178` chromatic pixels; button-up delivery was falsified | FLR-0232 owns input-independent parent repaint |
| [FLR-0232](work/tickets/FLR-0232-isolate-input-independent-parent-repaint.md) | isolate input-independent parent repaint | Done: no-input and single-axis controls stayed chromatic; combined x→4s→y produced a persistent white HUD at the first `wl_pointer.motion`, while native 3D stayed at `24178`; FLR-0233 owns motion delivery A/B | FLR-0233 owns pointer-motion repaint |
| [FLR-0233](work/tickets/FLR-0233-isolate-pointer-motion-repaint.md) | isolate pointer-motion repaint | Done: official motion-only gate passed Mini do_patch/do_compile/image; control whitened HUD at motion while motion-skip preserved HUD `2801` and native 3D `24178`; FLR-0234 owns the product-safe repair | FLR-0234 owns parent repaint repair |
| [FLR-0234](work/tickets/FLR-0234-repair-pointer-motion-parent-repaint.md) | repair pointer-motion parent repaint | Done: transparent `FilledButton` overlay patch built successfully but QMP hover produced a uniform-white full frame; native present stayed successful and teardown passed | FLR-0235 owns static clickable surface |
| [FLR-0235](work/tickets/FLR-0235-replace-material-hover-button.md) | replace Material hover button with static clickable surface | Done: official patch, Mini do_patch/do_compile/image, QMP 2D+3D visual evidence, motion sequence, and clean teardown all passed; HUD `2845` and native ROI `24178` remained chromatic | New ticket required for route activation or production-scene lighting/camera validation |
| [FLR-0236](work/tickets/FLR-0236-activate-planetarium-scene.md) | activate Planetarium scene from the Scenes control | Done: official patch, Mini do_patch/do_compile/image, QMP tap marker, and clean teardown passed; callback is proven but post-tap HUD became uniform white and native ROI stayed at fixture baseline | FLR-0237 owns route composition and scene ownership |
| [FLR-0237](work/tickets/FLR-0237-fix-planetarium-route-composition.md) | fix Planetarium route composition and visible scene ownership | Done: official patch, Mini do_patch/do_compile/image, QMP initial/post screenshots, bounded guest log, and clean teardown passed; removing the full-surface gesture build did not remove post-tap HUD white | FLR-0238 owns route-state mount vs parent repaint |
| [FLR-0238](work/tickets/FLR-0238-isolate-route-state-mount-repaint.md) | isolate route-state mount from parent repaint | Done: marker-only parent `setState` reproduced HUD `0`/uniform white after tap while native ROI stayed `24178`; route-state mounting is not required, and Mini/QMP/evidence/cleanup gates passed | FLR-0239 owns the parent `setState` repaint discriminator |
| [FLR-0239](work/tickets/FLR-0239-isolate-parent-setstate-repaint.md) | isolate parent setState from the repaint boundary | Done: no-`setState` callback retained HUD `2845` and native ROI `24178` through QMP tap; the same control with parent `setState` produced HUD `0`/uniform white | FLR-0240 owns scene-subtree-only mounting |
| [FLR-0240](work/tickets/FLR-0240-mount-scene-subtree-without-parent-repaint.md) | mount scene subtree without parent repaint | Done: ValueNotifier child-only update mounted Planetarium; HUD still became `0`/uniform white after activation while native ROI stayed `24178`; scene lifecycle callbacks are the next discriminator | FLR-0241 owns Planetarium lifecycle callback isolation |
| [FLR-0241](work/tickets/FLR-0241-isolate-planetarium-lifecycle-callbacks.md) | isolate Planetarium lifecycle callbacks | Done: official patch/Mini gates/QMP passed; inert callbacks still produced HUD `0`/uniform white after tap while native ROI stayed `24178`; callback bodies are not sufficient cause | FLR-0242 owns generic-versus-Planetarium mount |
| [FLR-0242](work/tickets/FLR-0242-isolate-stateful-sceneview-mount.md) | isolate generic StatefulSceneView mount from Planetarium mount | Done: official patch/Mini do_patch/compile/image/QMP passed; generic inert child produced HUD `0`/uniform white after button-up while native fixture ROI stayed `100800`; FLR-0243 owns plain child replacement |
| [FLR-0243](work/tickets/FLR-0243-isolate-plain-child-replacement.md) | isolate plain child replacement from StatefulSceneView mount | Done: official patch/Mini do_patch/compile/image/QMP passed; plain `SizedBox` produced HUD `0`/uniform white after button-up while native fixture ROI stayed `100800`; FLR-0244 owns builder-rebuild versus child identity |
| [FLR-0244](work/tickets/FLR-0244-isolate-builder-rebuild-from-child-identity.md) | isolate builder rebuild from child identity replacement | Done: official patch/Mini do_patch/compile/image/QMP passed; stable child Builder rebuild produced HUD `0`/uniform white after button-up while native fixture ROI stayed `100800`; FLR-0245 owns Builder removal versus platform-view/Wayland composition |
| [FLR-0245](work/tickets/FLR-0245-isolate-builder-from-platform-view-composition.md) | isolate Builder from platform-view composition | Done: official patch/Mini do_patch/compile/image/QMP passed; direct stable child preserved HUD `2883` and native ROI `100800` through button-up; FLR-0246 owns direct Planetarium lifecycle mounting |
| [FLR-0246](work/tickets/FLR-0246-mount-planetarium-directly-without-builder.md) | mount Planetarium directly without Builder rebuild | Done: official patch/Mini do_patch/compile/image/QMP passed; direct Planetarium mount preserved HUD `2883` and native ROI `100800`, but lifecycle onCreate count was 0 and production geometry remains UNKNOWN; FLR-0247 owns readiness callback tracing |
| [FLR-0247](work/tickets/FLR-0247-trace-planetarium-readiness-callback.md) | trace Planetarium readiness callback reachability | Done: readiness registration and first false were observed; no ready/dispatch/onCreate marker appeared in the bounded run, while HUD/native pixels stayed chromatic and cleanup was zero | FLR-0248 owns MethodChannel call/response tracing |
| [FLR-0248](work/tickets/FLR-0248-trace-readiness-method-channel-boundary.md) | trace readiness MethodChannel call/response boundary | Done: Mini source contains both diagnostics; runtime produced two MissingPluginException results, then 345 bounded timeouts and zero native handler receives, while HUD/native pixels stayed chromatic and cleanup was zero | FLR-0249 owns registration-order/lifetime correction |
| [FLR-0249](work/tickets/FLR-0249-fix-readiness-method-channel-registration.md) | fix readiness MethodChannel registration boundary | Done: official `0081` generated from source HEAD `8832428`; Mini do_patch/compile/image passed; QMP reached `FLR0249_READINESS_START_AFTER_PLATFORM_VIEW`, `READY`, and `CALLBACK_DISPATCHED`, but display evidence is handed to FLR-0251 | FLR-0251 owns simultaneous 2D+3D restoration |
| [FLR-0251](work/tickets/FLR-0251-restore-known-good-2d-3d-display.md) | restore the known-good simultaneous 2D HUD and native 3D display after FLR-0249 | Done: official Devtool reverse patch `0082`; Mini do_patch/compile/image passed; QMP restored HUD `2883` and native fixture `100800` with known-good SHA; cleanup passed | FLR-0252 owns production Planetarium/Sequoia visibility |
| [FLR-0230](work/tickets/FLR-0230-fix-devtool-root-patch-registration.md) | fix Devtool root-vs-plugin patch registration | Workflow defect found during FLR-0229; not started | Devtool workflow role | Inbox | make finish helper infer patchdir from generated patch paths |

| [FLR-0210](work/tickets/FLR-0210-podman-tmpfs-work-ownership.md) | repair fixed Podman tmpfs work ownership after container restart | Podman Devtool harness | Inbox | Re-run the Mac do_patch gate after the wrapper repair |
| [FLR-0212](work/tickets/FLR-0212-qmp-socket-path-preflight.md) | preflight QMP socket path length | QEMU evidence harness role | Inbox | Add a deterministic socket-path length check before runqemu |
| [FLR-0214](work/tickets/FLR-0214-trace-wayland-wsi-buffer-transfer.md) | trace Wayland WSI buffer transfer after positive native readback | Done: bounded strace and live mapping evidence proved RGB-positive content in both app and compositor; native QMP remained black; no source patch | FLR-0215 owns native surface visibility/selection |
| [FLR-0215](work/tickets/FLR-0215-trace-native-surface-compositor-visibility.md) | trace native surface compositor visibility and selection | Done: runtime markers and Wayland attach/commit proved the native surface role and buffer commit; QMP still omitted the RGB-positive surface | FLR-0216 owns readback-to-visible-SHM discrimination |
| [FLR-0216](work/tickets/FLR-0216-diagnostic-readback-visible-shm-bridge.md) | prove native readback through the visible SHM path | Done: SHM control cube is visible in QMP; bridge changes composition but readback payload is uniform white, so native geometry is not proven | FLR-0217 owns payload identity/timing |
| [FLR-0217](work/tickets/FLR-0217-trace-native-readback-payload-identity.md) | trace native readback payload identity and timing | Done: swapchain target/readback/present all return success, but existing markers do not expose the exact readback image index; QMP native ROI remains black | FLR-0218 owns image-index correlation |
| [FLR-0213](work/tickets/FLR-0213-rebuild-filament-devtool-baseline.md) | rebuild a complete Filament Devtool source baseline | Devtool source-history role | Done | child-edit official patch criterion passed in FLR-0211 |

| [FLR-0218](work/tickets/FLR-0218-trace-swapchain-image-index-identity.md) | trace swapchain image-index identity across readback and present | Done: current-color, draw, readback, and present correlate to the same swapchain image; driver readback is RGB-positive, but QMP native ROI is black while HUD is visible; Mini patch/compile/image and QMP teardown passed | FLR-0220 owns render-target shape content |

| [FLR-0219](work/tickets/FLR-0219-trace-final-native-wayland-composition.md) | trace final native Wayland composition after RGB-positive readback | Done: same-run Wayland attach/damage/frame/commit and Vulkan present returned 0; compositor was active with shared mappings and no bounded journal error, but QMP native ROI stayed black and the native readback ROI was uniform white (`chromatic_pixels=0`), so 3D geometry was not proven | FLR-0220 owns render-target shape content |

| [FLR-0220](work/tickets/FLR-0220-trace-native-render-target-shape-content.md) | trace native render-target shape content before Wayland composition | Done: minimal fixture contract, camera, indexed draw, same-image correlation, and `111758` chromatic native pixels passed; paired QMP native ROI remained black | FLR-0221 owns final composition/import/display |

| [FLR-0221](work/tickets/FLR-0221-trace-composition-of-native-geometry-buffer.md) | trace composition of native geometry buffer after verified native pixels | Done: same-QEMU A/B showed native-only QMP `0` chromatic pixels while the existing SHM bridge showed `100800`; QMP/cleanup passed | FLR-0222 owns native-only restoration |

| [FLR-0223](work/tickets/FLR-0223-validate-production-scene-and-input-transition.md) | validate production scene and QEMU input transition | Done: production native readback was uniform (`chromatic_pixels=0`); scaled QMP click entered native `wl_surface` and lost the HUD without a route marker; QMP evidence and teardown passed | FLR-0224 owns input-coverage A/B |
| [FLR-0222](work/tickets/FLR-0222-restore-native-wsi-3d-display.md) | restore native WSI 3D display without diagnostic bridge | Waiting: extent-only A/B changed `1280x720` to `1280x800` but native pixels outside the SHM child remained zero; FLR-0223 validated production behavior independently | Resume after FLR-0224 input unit |

| ID | Problem / outcome | Owner | PDCA | Next action |
| --- | --- | --- | --- | --- |
| [FLR-0195](work/tickets/FLR-0195-fix-devtool-initial-revision-flow.md) | fix deterministic Devtool initial-revision flow | Done: helper now verifies the workspace baseline and invokes official update-recipe without conflicting CLI initial-rev; contract test and official FLR-0194 patch generation passed; local commits `b93dcfb`, `7c63e9e` | FLR-0194 resumes Mini build/runtime |
| [FLR-0197](work/tickets/FLR-0197-squash-devtool-source-history.md) | make complete Devtool patch baseline deterministic | Done: source was squashed to one baseline-to-final commit; official single patch, whitespace gate, Mini do_patch, and do_compile passed; local commit `2dfaee6` | FLR-0194 resumes image/runtime |
| [FLR-0196](work/tickets/FLR-0196-fix-readback-callback-api.md) | fix readback callback API compatibility | Done: pinned Filament function-pointer callback with user context compiled on Mini; official patch and Mini do_patch/do_compile passed; local commit `2dfaee6` | FLR-0194 resumes image/runtime |
| [FLR-0194](work/tickets/FLR-0194-readback-direct-fixture-swapchain.md) | read back direct fixture swapchain pixels | Waiting: image built and QMP shows HUD plus uniformly black 3D region; Vulkan readback reaches map/reshape/work-complete, but app callback result is not emitted; FLR-0198 owns driver-completion payload tracing | Resume after FLR-0198 payload result |
| [FLR-0198](work/tickets/FLR-0198-trace-vulkan-readback-payload.md) | trace Vulkan readback payload at driver completion | Done: official Filament patch generated from source commit `608c1c4`, Mac/Mini do_patch, do_compile, image, QMP capture, driver payload trace, and QMP teardown passed; total driver payload is non-zero while the 3D candidate remains black | FLR-0199 owns ROI and surface-composition split |
| [FLR-0199](work/tickets/FLR-0199-isolate-wayland-native-surface-composition.md) | isolate Wayland/native surface composition after non-zero driver payload | Done: corrected official patch, Mini do_patch/do_compile/image, one QEMU run, driver ROI (`nonzero_rgb=111758`, `nonzero_alpha=111758`), QMP HUD/black-3D split, one flutter-auto process, and clean teardown passed; first missing boundary is after driver content and before QMP parent-frame visibility; 74 pre-existing zero-byte tracked HEAD files were restored exactly and are outside the patch | FLR-0200 owns child-surface visibility/compositor evidence |
| [FLR-0201](work/tickets/FLR-0201-reproduce-known-good-native-fixture-stack.md) | reproduce the known-good native fixture after the current patch stack | Done: current image shows 2D HUD and non-zero native driver ROI, while the QMP 3D ROI is uniformly black; escaped app-id launch and View-only opaque A/B were recorded, and QEMU teardown passed | FLR-0202 owns the swapchain-alpha discriminator |
| [FLR-0202](work/tickets/FLR-0202-test-opaque-native-swapchain-composition.md) | test opaque native swapchain composition after non-zero driver readback | Done: official 0264 patch built and runtime-tested; composite alpha changed to opaque, driver ROI stayed non-zero, but QMP HUD stayed visible while the central and wide 3D ROIs remained uniformly black; QMP/video evidence and clean teardown retained | FLR-0203 owns child-surface composition analysis |
| [FLR-0203](work/tickets/FLR-0203-isolate-wayland-child-surface-after-opaque-ab.md) | isolate Wayland child-surface composition after opaque A/B | Done: official 0265 commit/flush probe built and runtime-tested; driver ROI stayed non-zero, `wl_display_flush` returned 8, and QMP central/wide 3D ROIs stayed uniformly black; clean teardown retained | FLR-0204 owns stacking direction A/B |
| [FLR-0204](work/tickets/FLR-0204-test-wayland-child-surface-stacking-direction.md) | test Wayland child-surface stacking direction after commit/flush falsification | Done: official 0266 gated `place_below` A/B built and runtime-tested; stacking marker was `below=true`, driver ROI stayed non-zero, QMP frame SHA matched control, and central/wide 3D ROIs stayed uniformly black; clean teardown retained | FLR-0205 owns protocol/import-release observation |
| [FLR-0205](work/tickets/FLR-0205-observe-wayland-native-buffer-import-release.md) | observe Wayland native buffer import and release after stacking A/B | Done: one runtime with `WAYLAND_DEBUG=client` proved native surface buffer attach → damage → frame → commit and Vulkan present result 0; compositor journal had no matching error, while QMP central/wide 3D ROIs remained zero; clean teardown retained | FLR-0206 owns SHM buffer content trace |
| [FLR-0206](work/tickets/FLR-0206-trace-vulkan-wayland-shm-buffer-content.md) | trace Vulkan to Wayland SHM buffer content after positive protocol attach/commit | Done: one bounded strace captured five 4096000-byte `mesa-shared` pools and `MAP_SHARED` mappings; QMP remained central/wide zero, but mmap contents were not directly readable through syscall tracing | FLR-0207 owns live gdb memory inspection |
| [FLR-0207](work/tickets/FLR-0207-inspect-live-wayland-shm-buffer-bytes.md) | inspect live Wayland SHM buffer bytes after syscall trace | Done: gdb sampled ten live `memfd:mesa-shared` mappings after present; eight were zero and two alpha-only, while paired QMP central/wide ROIs stayed black; clean teardown passed | FLR-0208 owns fixed Devtool baseline repair |
| [FLR-0208](work/tickets/FLR-0208-repair-devtool-full-source-baseline.md) | repair the fixed Devtool full-source baseline | Done: Mini effective source and missing Git objects were restored into the same fixed Mac source; baseline commit `95dc7cef4`, source tree/index both 478, official Devtool registration and finish lifecycle passed | FLR-0209 owns visible SHM fallback |
| [FLR-0209](work/tickets/FLR-0209-visible-shm-cube-fallback.md) | show a visible 3D cube through current Wayland SHM fallback | Done: official 0267, Mini do_patch/do_compile/image, one QMP run, stable 12-frame QMP video, visible three-face cube and 2D Scenes button in one frame, clean teardown; native Vulkan RGB remains open in FLR-0211 | FLR-0211 owns geometry and native WSI |
| [FLR-0200](work/tickets/FLR-0200-isolate-native-surface-compositor-visibility.md) | isolate native surface compositor visibility after non-zero driver ROI | Waiting: `set_position(0,0)` executes and driver readback is non-zero, but paired QMP 3D ROI remains black; exact post-readback composition field is UNKNOWN; QEMU teardown is clean | FLR-0201 owns current-vs-known-good stack comparison |
| [FLR-0193](work/tickets/FLR-0193-trace-post-create-native-draw-content.md) | trace post-create native draw content | Waiting: direct opaque fixture renders into the 1280x800 swapchain and emits TARGET_DRAW2/present=0, but existing intermediate-target probe does not apply; QMP 3D region remains uniformly black | FLR-0194 owns direct swapchain readback |
| [FLR-0192](work/tickets/FLR-0192-defer-viewtarget-create-until-ecs-init.md) | defer ViewTarget creation until ECS initialization | Done: official 0257+0258 patch stack applied cleanly; Mini do_patch/do_compile/image passed; runtime reached create handler and start count=1, but fixed 3D region remained black after Vulkan present; local commits `5258506`, `0aeae3b`; no push | FLR-0193 owns post-create draw-content boundary |
| [FLR-0191](work/tickets/FLR-0191-isolate-native-readiness-3d-draw.md) | isolate native readiness and 3D draw boundary | Done: 0256 do_patch/do_compile/image passed; explicit 3.38.3 fixture launch showed 2D HUD and Vulkan submit but 3D region remained uniformly black; first missing boundary was ViewTarget create handler with start count=0; canonical commits `b85068f`, `10c0b0c`; no push | FLR-0192 owns message ordering fix |
| [FLR-0183](work/tickets/FLR-0183-rebase-wayland-child-surface-flush.md) | rebase Wayland child-surface flush patch | Done: current source made 0240 obsolete; active registration removed and clean Mini advanced to 0241; local commit `47911d5`; no push | FLR-0184 owns 0241 |
| [FLR-0185](work/tickets/FLR-0185-current-fixture-camera-lookat.md) | restore current fixture camera projection and lookAt | Done: official 0251 replacement applied on Mac and Mini, clean gate advanced to the next boundary 0227; local commit `51100aa`; no push | FLR-0186 owns 0227 fuzz |
| [FLR-0186](work/tickets/FLR-0186-rebase-0227-current-plugin-source.md) | rebase 0227 on current plugin source | Done: corrected effective-source 0227 generated through Mac Devtool, Mini applied 0227 with zero fuzz and stopped at 0232 fuzz; local commits `b4a3006`, `013d02b`; no push | FLR-0187 owns 0232 fuzz |
| [FLR-0187](work/tickets/FLR-0187-rebase-0232-current-plugin-source.md) | rebase 0232 on current plugin source | Done: current-source official 0232 patch applied on Mac and Mini with clean do_patch; local commit `42689fd`; bundle `12955023...`; no push | FLR-0188 owns compile/runtime |
| [FLR-0188](work/tickets/FLR-0188-compile-and-validate-clean-3d-runtime.md) | compile and validate the clean 3D runtime image | Waiting: image boots and reaches flutter-auto, but MaterialParameter COLOR aborts before first frame; FLR-0190 owns the contract correction | Resume after FLR-0190 |
| [FLR-0190](work/tickets/FLR-0190-align-material-color-wire-format.md) | align MaterialParameter COLOR wire format with current native API | Done: retired stale 0052 active registration; corrected image built and QMP proved app survival/2D HUD while 3D remained black; local commits `de3f352`, `2ddab09`; no push | FLR-0191 owns readiness/3D |
| [FLR-0189](work/tickets/FLR-0189-reconcile-stale-0235-0236-apis.md) | reconcile stale 0235/0236 ECS APIs before compile | Done: retired obsolete active registrations; Mini do_patch and do_compile PASS at `44c88ec`; bundle `900600b8...`; no push | FLR-0188 resumes image/QEMU |
| [FLR-0184](work/tickets/FLR-0184-rebase-native-fixture-local-camera.md) | rebase native fixture local-camera patch | Done: 0241 was obsolete after current direct-camera API inspection; active registration removed and clean Mini advanced to 0242; local commit `dddd214`; no push | FLR-0185 owns current 0242 lookAt |
| [FLR-0156](work/tickets/FLR-0156-restore-pure-fixture-camera-projection.md) | restore pure-fixture camera projection | Waiting: Mini do_patch advanced through 0222 and is now blocked by 0223/current-plugin mismatch; FLR-0167 owns reconciliation | Resume after FLR-0158/0167 make the existing patch stack apply |
| [FLR-0158](work/tickets/FLR-0158-reconcile-current-flutter-auto-patch-stack.md) | reconcile current flutter-auto patch stack baseline | Waiting: 0002 was removed and 0220/0222 were reconciled; FLR-0167 owns the next 0223 boundary | Resume after the remaining patch stack is clean |
| [FLR-0179](work/tickets/FLR-0179-retire-obsolete-0239-patch.md) | retire obsolete 0239 recipe patch | Done: 0239 was removed from active SRC_URI after clean-gate reproduction; the next boundary is 0228; local commit `8ac4589`; no push | FLR-0180 owns 0228 |
| [FLR-0178](work/tickets/FLR-0178-deterministic-mini-recipe-workdir.md) | make the Mini recipe patch gate deterministic | Done: recipe-scoped clean reset passed and the same 0239 failure reproduced from a clean workdir; local commit `5962776`; no push | FLR-0179 owns obsolete 0239 retirement |
| [FLR-0177](work/tickets/FLR-0177-rebase-0239-effective-plugin-source.md) | rebase 0239 on the effective plugin source | Waiting: Mini S is not the 0239 predecessor source; resolve deterministic workdir provenance first | Resume after FLR-0178 proves a clean patch baseline |
| [FLR-0181](work/tickets/FLR-0181-devtool-registration-override-scope.md) | allow valid QEMU override patch registrations | Done: distinct QEMU override lines pass and exact duplicate lines remain rejected; local helper change is included in the 0228 checkpoint; no push | FLR-0180 resumes |
| [FLR-0180](work/tickets/FLR-0180-rebase-0228-effective-plugin-source.md) | rebase QEMU quality patch 0228 | Done: official current-source 0228 patch replaced and clean Mini do_patch advanced to the next boundary; local checkpoint `1688e28`; no push | FLR-0182 owns the next patch |
| [FLR-0182](work/tickets/FLR-0182-rebase-effective-viewtarget-frame-boundary.md) | rebase effective ViewTarget frame boundary patch | Done: current DrawFrame diagnostics generated officially and clean Mini do_patch advanced to 0240; local checkpoint `e958aa0`; no push | FLR-0183 owns 0240 |
| [FLR-0159](work/tickets/FLR-0159-rebase-0220-current-source.md) | rebase 0220 against the resolved current source | Done: current-source Devtool patch replaced 0220 and the Mini do_patch gate advanced past 0220; 0221 is split to FLR-0160 | Resume FLR-0158 after the remaining patch stack is reconciled |
| [FLR-0160](work/tickets/FLR-0160-rebase-0221-current-plugin-source.md) | rebase 0221 against the resolved current plugin source | Done: corrected effective-source Devtool baseline made 0222 apply; Mini do_patch advanced through 0222 and stopped at 0223; local layer commit `c789dc4`; no push | FLR-0167 owns 0223 |
| [FLR-0167](work/tickets/FLR-0167-rebase-0223-effective-plugin-source.md) | rebase 0223 on the effective post-0222 plugin source | Done: corrected official Devtool patch applied on Mini and do_patch advanced to 0226; FLR-0168 owns the next boundary | FLR-0168 owns 0226 |
| [FLR-0168](work/tickets/FLR-0168-rebase-0226-effective-plugin-source.md) | rebase 0226 on the effective post-0225 plugin source | Done: corrected official Devtool patch applied on Mini and do_patch advanced to 0224; FLR-0169 owns the next boundary | FLR-0169 owns 0224 |
| [FLR-0169](work/tickets/FLR-0169-rebase-0224-effective-plugin-source.md) | rebase 0224 on the effective post-0226 plugin source | Done: corrected official Devtool patch applied on Mini and do_patch advanced to 0229; the next 0229 source boundary is split after the workflow gate | FLR-0171 owns 0229 |
| [FLR-0170](work/tickets/FLR-0170-deterministic-mini-recipe-patch-gate.md) | deterministic Mini recipe patch gate | Done: fixed-receiver recipe gate passed preflight, bounded the output, and reproduced 0229 hunk 2 with the correct task log; local commits `6f08bc6`, `6f79907`, `11a2c01`; no push | FLR-0171 owns 0229 |
| [FLR-0171](work/tickets/FLR-0171-rebase-0229-effective-plugin-source.md) | rebase 0229 on the effective plugin source | Done: official Devtool rebase applied 0229 on Mini and do_patch advanced to 0231; local commits `0ce6670`, `5993e70`; no push | FLR-0172 owns 0231 |
| [FLR-0172](work/tickets/FLR-0172-rebase-0231-effective-plugin-source.md) | rebase 0231 on the effective plugin source | Done: official Devtool rebase applied 0231 on Mini and do_patch advanced to 0233; local commit `e9876c4`; no push | FLR-0173 owns 0233 |
| [FLR-0173](work/tickets/FLR-0173-rebase-0233-effective-plugin-source.md) | rebase 0233 on the effective plugin source | Done: official Devtool rebase generated a byte-identical canonical patch, Mini applied 0233, and do_patch advanced to 0234; local commit `be6ab09`; no push | FLR-0174 owns 0234 |
| [FLR-0174](work/tickets/FLR-0174-rebase-0234-effective-plugin-source.md) | rebase 0234 on the effective plugin source | Done: official Devtool rebase generated a byte-identical canonical patch, Mini applied 0234, and do_patch advanced to 0235; local commit `63bbf78`; no push | FLR-0175 owns 0235 |
| [FLR-0175](work/tickets/FLR-0175-rebase-0235-effective-plugin-source.md) | rebase 0235 on the effective plugin source | Done: official Devtool rebase generated a byte-identical canonical patch, Mini applied 0235, and do_patch advanced to 0236; local commit `d4c8f4f`; no push | FLR-0176 owns 0236 |
| [FLR-0176](work/tickets/FLR-0176-rebase-0236-effective-plugin-source.md) | rebase 0236 on the effective plugin source | Done: official Devtool rebase generated a byte-identical canonical patch, Mini applied 0236 and advanced through 0238; local commit `4667dc5`; no push | FLR-0177 owns 0239 |
| [FLR-0166](work/tickets/FLR-0166-validate-registration-before-replacement.md) | validate registration before canonical patch replacement | Done: registration-before-copy and explicit-replacement replay passed with old/new SHA evidence and full verification; local commit `cb8b90b` was created; no push | Resume FLR-0160 |
| [FLR-0165](work/tickets/FLR-0165-explicit-canonical-patch-replacement.md) | allow explicit canonical patch replacement during rebase | Done: default refusal and explicit replacement contract passed full verification; local commit `5629e5c` was created; no push | Resume FLR-0160 |
| [FLR-0164](work/tickets/FLR-0164-standard-devtool-update-recipe.md) | use the standard Devtool update-recipe path | Done: standard update-recipe generated one patch and full verification passed; local commit `7c6ad06` was created; no push | Resume FLR-0160 |
| [FLR-0163](work/tickets/FLR-0163-reject-wrong-devtool-recipe.md) | reject wrong recipe before split-component Devtool reset | Done: source-path/component-role guard passed the wrong-recipe replay and full verification; local commit `5145eae` was created; no push | Resume FLR-0160 with `fluorite-plugins` |
| [FLR-0162](work/tickets/FLR-0162-fix-devtool-helper-dirty-detection.md) | fix false dirty detection in the one-shot Devtool helper | Done: whole-line status parsing passed full verification and local commit `974cefe` was created; no push | Resume FLR-0160 after the next helper guard |
| [FLR-0161](work/tickets/FLR-0161-one-shot-devtool-component-rebase.md) | make split-component Devtool rebase one-shot and bounded | Done: contract/full verification passed and local commit `9012626` created; no push | Resume FLR-0160 with the fixed helper |
| [FLR-0157](work/tickets/FLR-0157-determinize-devtool-runtime-loop.md) | make Devtool patch generation and runtime log selection deterministic | Done: fail-closed Devtool finish, bounded runtime log slicer, tests, and local commit `b6f7e3c` | FLR-0156 resumes after patch-stack baseline reconciliation |
| [FLR-0140](work/tickets/FLR-0140-reconcile-2d-hud-with-recovered-dart-3d.md) | reconcile 2D HUD with recovered Dart 3D | Flutter surface/compositor + Fluorite ViewTarget roles | Waiting | Await separate alpha/composite follow-up after API alignment |
| [FLR-0147](work/tickets/FLR-0147-restore-current-native-fixture-camera-contract.md) | restore current native fixture camera contract | ViewTarget camera + native fixture runtime roles | Waiting | Explicit local camera did not restore QMP native pixels; continue under FLR-0148 |
| [FLR-0151](work/tickets/FLR-0151-repair-podman-tmpfs-ownership-after-restart.md) | repair Podman tmpfs ownership after restart | Mac Podman Devtool container lifecycle role | Inbox | Remove the manual ownership-repair step after container restart |

## Recently completed

| ID | Problem / outcome | Result |
| --- | --- | --- |
| [FLR-0350](work/tickets/FLR-0350-correlate-lavapipe-sync-release-producer.md) | correlate the exact Lavapipe Present-wait sync object with its release producer | Done as a bounded partial experiment: the only run failed at `FLR0350_FIFO_READ_GATE` before app/GDB start. QMP AGL splash/black post-run still and 8-frame video saved; producer correlation UNKNOWN. Host QEMU/QMP cleanup verified; guest stop reported unknown process identity. FLR-0354 owns runner gate/cleanup correction; 3D objective remains open |
| [FLR-0351](work/tickets/FLR-0351-validate-mini-handoff-before-receiver-update.md) | validate effective TMPDIR and Mini handoff preconditions before receiver update | Done: read-only Mini evidence independently confirmed exact requested receiver tip, clean worktree, idle BitBake, effective `TOPDIR`/`TMPDIR` role agreement, and matching existing bundle SHA. Original helper terminal marker remains UNKNOWN; receiver state is proven, so no retransfer was made. No build/QEMU side effect |
| [FLR-0354](work/tickets/FLR-0354-fix-flr0350-fifo-launch-gate.md) | prove the blocked `read` FD references the run-owned FIFO and make failed-launch cleanup identity-safe | Done as a Mac-side harness correction: strict parser compares actual FD target and gate type/device/inode; wrapper identity is captured before evaluation; 23 focused tests and runner `--check` pass; consumed ID is rejected. Full `make verify` remains blocked by 9 pre-existing FLR-0338/0339 evidence links. No QEMU/build/Mini action; 3D remains UNKNOWN |
| [FLR-0345](work/tickets/FLR-0345-retrospective-3d-visibility-checklist.md) | consolidate 3D visibility interventions, effects, and regression risk | Done as an evidence-indexed retrospective: fixture + HUD composition is proven, production Sequoia + HUD is historical but unstable, current QMP is HUD-only with black 3D ROI, and regression is plausible but unproven. Photo 1 is a static texture atlas; exact-current HUD-off Sequoia is untested. FLR-0344 ran and isolated an arm-wait helper failure; local commit `fe85290` |
| [FLR-0346](work/tickets/FLR-0346-tolerate-empty-gdb-log-during-arm-poll.md) | distinguish a fresh empty GDB transcript from missing state | Done: actual helper red/green regression proves the old guard rejects an existing empty log; corrected helper waits for a delayed marker and reports missing PID/log independently. 86 Python tests, 51 shell syntax checks, privacy, 1,051 links, canonical/checkpoint gates pass. Does not determine FLR-0344's exact false predicate or renderer cause; FLR-0347 owns the exact-image retest |
| [FLR-0347](work/tickets/FLR-0347-retest-empty-log-arm-poll-on-exact-image.md) | verify corrected arm-poll and capture exact-image GDB/QMP evidence | Done: one exact-image run; corrected wait polled 44 times and persisted initial `signaled=false`, `fence=0`, then specific GDB error `No struct type named pipe_fence_handle`. QMP HUD remained visible; lower 768,000-pixel ROI was uniformly black across still/eight frames; app/QEMU/socket teardown passed |
| [FLR-0349](work/tickets/FLR-0349-audit-3d-countermeasure-effectiveness.md) | audit 3D countermeasure effects, regressions, and the next bounded discriminator | Done: the fixture+HUD control is proven; the readback-mode regression is proven only for that path; historical Sequoia-to-current regression remains plausible, not proven. Updated FLR-0348 to observe both Lavapipe wait-release predicates |
| [FLR-0348](work/tickets/FLR-0348-watch-lavapipe-signal-without-fence-type.md) | observe both Lavapipe wait-release predicates without unavailable DWARF types | Done: exact-image watches armed on `signaled` and raw fence storage; 8.07-second bounded no-hit, both values false/null. QMP shows HUD/metrics but the 768,000-pixel 3D ROI is black; teardown passed. FLR-0350 owns exact sync-to-producer correlation |
| [FLR-0339](work/tickets/FLR-0339-capture-vulkan-present-stall-stack.md) | capture the production Present-stall thread context | Done as a bounded partial result: Present-enter/no-return recurred with 19 draw-end/native commits; the 20-second GDB command listed 38 threads but stopped during LWP 718's Mesa `lvp_pipe_sync_wait` stack. QMP showed HUD/metrics/Scenes and a uniformly black lower 768,000-pixel ROI; screenshot/video hashes and clean app/QMP teardown are recorded. Exact Present caller and semaphore-to-sync-object identity remain UNKNOWN; FLR-0340 owns static source mapping |
| [FLR-0341](work/tickets/FLR-0341-capture-lavapipe-present-wait-runtime.md) | capture the Lavapipe wait caller and submit-to-Present handle continuity | Done: exact-image run captured FEngine thread 25 at `lvp_pipe_sync_wait` → `wsi_common_queue_present`; the later submit's signal handle matched Present's wait handle but Present did not return. QMP showed the HUD and a uniformly black 768,000-pixel 3D ROI in the screenshot and all eight frames. GDB reached the 20-second limit after detaching; app/QEMU/socket cleanup passed. FLR-0343 observes the exact wait object's fields and writer |
| [FLR-0342](work/tickets/FLR-0342-inspect-mesa-pending-wait-binary.md) | inspect the exact Mesa pending-wait implementation | Done as a bounded static correction: exact runtime ELF/disassembly and Mesa 24.0.7 archive agree that `cnd_wait` precedes the pending-flag test. The exact downstream patch set and the sync object's field values remain UNKNOWN; FLR-0343 observes the runtime producer |
| [FLR-0339](work/tickets/FLR-0339-capture-vulkan-present-stall-stack.md) | capture the production Present-stall thread context | Done as a bounded partial result: Present-enter/no-return recurred with 19 draw-end/native commits; the 20-second GDB command listed 38 threads but stopped during LWP 718's Mesa `lvp_pipe_sync_wait` stack. QMP showed HUD/metrics/Scenes and a uniformly black lower 768,000-pixel ROI; screenshot/video hashes and clean app/QMP teardown are recorded. Exact Present caller and semaphore-to-sync-object identity remain UNKNOWN; FLR-0340 owns static source mapping |
| [FLR-0340](work/tickets/FLR-0340-map-present-wait-semaphore-source.md) | map the present wait to the exact semaphore/source path | Done as a bounded read-only map: exact FLR-0335 image hashes and Filament submit→Present source chain were recorded. The later FLR-0342 correction establishes that Lavapipe reaches `cnd_wait` before the pending-flag test; downstream Mesa patches remain UNKNOWN. FLR-0341 captured the runtime caller and matching handle |
| [FLR-0339](work/tickets/FLR-0339-capture-vulkan-present-stall-stack.md) | capture the production Present-stall thread context | Done as a bounded partial result: Present-enter/no-return recurred with 19 draw-end/native commits; the 20-second GDB command listed 38 threads but stopped during LWP 718's Mesa `lvp_pipe_sync_wait` stack. QMP showed HUD/metrics/Scenes and a uniformly black lower 768,000-pixel ROI; screenshot/video hashes and clean app/QMP teardown are recorded. Exact Present caller and semaphore-to-sync-object identity remain UNKNOWN; FLR-0340 owns static source mapping |
| [FLR-0338](work/tickets/FLR-0338-capture-isordered-offset-context.md) | capture control-flow context at the recurring `isOrdered+1` boundary | Done: GDB armed a hardware execution breakpoint at the exact ASLR-adjusted address but no target stop occurred within 45 seconds. This is a valid bounded no-hit result, not proof that the thread never reaches the address. QMP run 0003 shows HUD/metrics/Scenes and 768,000 uniformly black lower-ROI pixels; Sequoia asset/emissive binding and magenta-unlit override markers ran, but shader sampling remains UNKNOWN. App/QMP cleanup passed; no source patch/build. FLR-0339 owns the present-stall stack snapshot |
| [FLR-0337](work/tickets/FLR-0337-capture-user-and-kernel-fault-trace.md) | capture both user and kernel page-fault context for the recurring FEngine worker | Done: same-TID `page_fault_user` event matched the Oops IP/address 418 µs earlier; 19 draws/commits, one present begin and no return; Sequoia asset/emissive binding reached ready/applied; QMP HUD visible and lower 768,000-pixel 3D ROI black; app/QMP cleanup passed. Root cause, perf-loss status, and fault/present causality remain UNKNOWN; FLR-0338 owns a hardware-breakpoint context capture |
| [FLR-0335](work/tickets/FLR-0335-compare-present-without-gdb.md) | compare production present behavior with and without GDB | Done: same-image no-GDB run reproduced the recurring `libLLVM.so.18.1` / `isOrdered+1` FEngine fault at 284.16s; QMP HUD stayed visible and native ROI remained 0/144000. App/QMP cleanup passed; GDB timing effect is plausible, not proven; FLR-0338 owns pre-instruction context |
| [FLR-0333](work/tickets/FLR-0333-trace-vulkan-present-return-page-fault.md) | trace Vulkan queue-present return and FEngine page fault before native buffer attach | Done: same-image production diagnostic run reached scene insertion and magenta-unlit override, yet native ROI remained 0/144000; queue-present had no return, one FEngine worker faulted, and eight QMP frames were identical. Root cause remains UNKNOWN; FLR-0334 owns fault symbolication |
| [FLR-0267](work/tickets/FLR-0267-fix-readback-shm-buffer-release.md) | fix readback SHM buffer release ownership | Done: official 0281 passed Mini patch/compile/full image; two distinct SHM buffers published and released, but ten live QMP frames were fully black, so release ownership was not sufficient; FLR-0268 owns readback-mode whole-frame regression versus capture timing |
| [FLR-0268](work/tickets/FLR-0268-isolate-readback-composition-regression.md) | isolate readback-mode composition regression | Done: same-image SHM-only control restored 2D plus self-made 3D in ten QMP frames; delayed readback remained full black, so timing was rejected and FLR-0269 owns protocol tracing |
| [FLR-0269](work/tickets/FLR-0269-trace-readback-wayland-protocol.md) | trace readback Wayland protocol divergence | Done: readback and parent surface requests were accepted with no protocol error; QMP transitioned from 2D-visible to full black during readback mode; FLR-0270 owned pool separation |
| [FLR-0270](work/tickets/FLR-0270-separate-readback-shm-pool.md) | separate readback SHM pool from control surface | Done: early ten-frame window was 2D-stable but readback ROI stayed black; later same-image run returned to full black, so pool separation is not a durable fix; FLR-0271 owns visibility/import and timing |
| [FLR-0260](work/tickets/FLR-0260-diagnose-black-production-render-content.md) | diagnose black production render content after PlatformView return | Done: current-source stage-isolation A/B built and runtime-tested; model selection and Present were positive, but ten QMP frames remained zero-chroma. FLR-0261 owns the missing scene-stage boundary |
| [FLR-0261](work/tickets/FLR-0261-trace-current-production-scene-stages.md) | trace current production scene stages after model selection | Done: 0279 passed Mini patch/compile/image; production asset load, Scene insertion, Draw submit/end, active default Scene, and Present were positive, while ten QMP frames remained effectively black/grayscale. FLR-0262 owns native readback vs composition |
| [FLR-0262](work/tickets/FLR-0262-split-native-readback-from-qmp-composition.md) | split native swapchain readback from QMP composition | Done: native readback completed with nonzero full-buffer content while ten paired QMP frames were identical and completely black in the 3D ROI; FLR-0263 owns readback-to-SHM visibility |
| [FLR-0263](work/tickets/FLR-0263-verify-native-readback-visible-surface.md) | verify native readback reaches the visible surface | Done: readback-to-SHM published twice with zero skips, but paired QMP remained fully black; FLR-0264 owns surface/QMP correlation |
| [FLR-0265](work/tickets/FLR-0265-repair-privacy-wayland-false-positive.md) | repair privacy checker false positives and personal paths | Done: Wayland protocol tokens no longer trigger email detection; three historical personal paths were replaced with role placeholders; regression test added |
| [FLR-0264](work/tickets/FLR-0264-reconcile-readback-shm-runtime-patch.md) | reconcile published SHM surface with QMP pixels | Done: Wayland child-surface parent/position/stacking/attach/commit/flush passed and live QMP still omitted only the readback update; same-image SHM control displayed 24,178 chromatic cube pixels; FLR-0266 owns buffer lifecycle |
| [FLR-0266](work/tickets/FLR-0266-fix-readback-shm-buffer-lifecycle.md) | fix readback SHM buffer lifecycle | Done: official 0280 passed Mini patch/compile/image; setup, callback, and publish used the same thread and same buffer, while ten live QMP frames kept the readback ROI black; FLR-0267 owns release/fresh-buffer implementation |
| [FLR-0142](work/tickets/FLR-0142-flush-wayland-child-surface.md) | flush Wayland child surface after Filament present | Done: flush-only probe was falsified; the stable Cube-only QMP frame remained unchanged |
| [FLR-0141](work/tickets/FLR-0141-align-dart-native-scene-camera-api.md) | align Dart/native scene and camera update API | Done: target-relative Native camera eye restored QMP-visible Planetarium geometry; remaining black lighting is split to FLR-0143 |
| [FLR-0143](work/tickets/FLR-0143-align-planetarium-light-material-contract.md) | align Planetarium light/material world-space contract | Done: world-space light-position patch did not restore color and correlated with an FEngine loop page fault; next boundary is FLR-0144 |
| [FLR-0144](work/tickets/FLR-0144-isolate-planetarium-light-native-fault.md) | isolate Planetarium light native fault boundary | Done: direct light contribution correlates with the FEngine/libLLVM fault; disabling contribution keeps geometry/present stable but black, so the next material API test is FLR-0145 |
| [FLR-0146](work/tickets/FLR-0146-restore-devtool-workspace-layer.md) | restore Devtool workspace layer after Podman restart | Done: tracked Yocto workspace-layer metadata restores `modify --no-extract` after restart without selecting the legacy control workspace |
| [FLR-0145](work/tickets/FLR-0145-test-planetarium-unlit-material.md) | test Planetarium unlit material API contract | Done: official `baseMap`-satisfied unlit material patch built and runtime-tested; Planetarium remained black, normal direct-light run faulted at queue-present, and the current fixture comparison exposed a camera-frame mismatch split to FLR-0147 |
| [FLR-0148](work/tickets/FLR-0148-reconcile-effective-viewtarget-api-contract.md) | reconcile effective ViewTarget scene/render API contract | Done: 0244 proved the native Scene, camera, viewport, opaque View, Wayland child, Renderable, primitive, material, and buffers are valid; QMP remained uniformly black, so the next boundary is Filament draw-to-target |
| [FLR-0149](work/tickets/FLR-0149-trace-filament-draw-to-target-contract.md) | trace Filament draw-to-target contract | Done: existing diagnostics proved the native Renderable emits `draw2` into a valid 1280×800 swapchain target and RenderPass returns; QMP remained black, so swapchain pixel content is the next boundary |
| [FLR-0150](work/tickets/FLR-0150-read-native-swapchain-pixels.md) | read native swapchain pixels before Wayland | Done: swapchain readback and paired QMP were both zero despite valid draw/present/Wayland markers; the first zero boundary is narrowed to Vulkan pixel generation/content/readback semantics, with exact state owner split to FLR-0152 |
| [FLR-0152](work/tickets/FLR-0152-trace-vulkan-pipeline-state-contract.md) | trace Vulkan pipeline state contract for the native fixture | Done: viewport/scissor, color-write mask, program handles, vertex input, draw2, present, and Wayland commit were valid; the API mismatch is the color being set on Material's default instance while the Renderable uses a separate created instance |
| [FLR-0153](work/tickets/FLR-0153-align-native-material-instance-api.md) | align native fixture MaterialInstance parameter API | Done: explicit color on the Renderable-bound MaterialInstance produced the same all-black 3D candidate; Filament source shows `createInstance()` copies the default instance, so the API-mismatch hypothesis is falsified |
| [FLR-0154](work/tickets/FLR-0154-isolate-native-materialbuilder-color-output.md) | isolate native MaterialBuilder color output | Done: fixed Mini image ran the hardcoded-color attempt; QMP showed the same all-black 3D candidate across the screenshot and six video frames while the 2D HUD remained visible. The result moves attention past dynamic color, but missing branch-entry logging keeps shader-constant execution UNKNOWN; FLR-0155 owns that boundary |
| [FLR-0155](work/tickets/FLR-0155-trace-native-vertex-upload-and-clip-contract.md) | trace native vertex upload and clip contract | Done: fixture entry, exact vertex/index bytes and checksums, non-null Vulkan upload/bind handles, indexed draw, present, and Wayland commit all passed. Static camera/source analysis identifies the first zero boundary as an unset identity projection in the fixture-local early-return path; the implementation is split to FLR-0156 |

## Active loop state

| Phase | State | Evidence / next gate |
| --- | --- | --- |
| Baseline and ticket scope | Completed | FLR-0027でshape/light分離の独立gateを完了し、FLR-0028へ分割 |
| QEMU / Fluorite | FLR-0358 Mini attempt stopped before GO | FLR-0358 staged 11/11 commands and booted the pinned image, but the orchestrator selected the FLR-0335 helper copy; the pre-GO black QMP image is not a render result. Next discriminator is exact helper provenance under FLR-0359 |
| Native render path | Production acceptance still open | The retrospective confirms positive same-frame fixture+HUD evidence, historical Sequoia candidates, and later post-GO production black ROIs as separate evidence classes. Return to production QMP only after the strict FIFO gate reaches GO |
| Wayland composition | Completed for diagnostic path | FLR-0042でSHM child attachとQMP visible pixelsを確認 |
| Mac → mini PC build | Completed | c1252c4のbundle、固定receiver、既存build/TMPDIR、do_patch/do_compile/full imageが成功 |

## Next

**Current next gate (2026-09-29):** FLR-0357's retrospective is committed as `6b43802` and Done; FLR-0356 remains Waiting after its pre-GO marker rejection. FLR-0358's loopback test and OE receiver preflight corrections are committed and transferred, but its sole Mini run `flr0358-0001` selected an older helper from FLR-0335 evidence (`339472…`) instead of the exact bundle helper (`088e8e…`). The strict FIFO validator correctly failed closed before GDB/GO; the black QMP image is pre-GO and says nothing new about rendering. The run was cleaned up and its ID is consumed. The next independent ticket must bind runner and starter to one run-scoped copy of the current committed helper, verify provenance in the fast local check, then use a new ID once. Historical FLR-0286 fixture+HUD pixels remain the positive composition control; FLR-0287 production Sequoia remains a separate unresolved render boundary.

The diagnostic narrative below is retained as historical context; current ticket status and next action are recorded above and in the linked tickets.

FLR-0348 ran once on the exact pinned image. Both wait-predicate watches armed;
neither hit in 8.07 seconds, and `signaled=false` / `fence=NULL` persisted.
Present entered and did not return. QMP showed the HUD/metrics/Scenes control;
the fixed lower ROI `[0,200,1280,600]` was 768,000/768,000 black pixels in the
still and all eight frames. Cleanup passed; no image build or product patch was
made. This does not show production Sequoia or prove that the sync wait causes
the black ROI. FLR-0350 later failed its pre-exec gate before Flutter/GDB
launch; no producer or rendering conclusion can be drawn from its black QMP
frame. FLR-0354 owns correcting the FIFO descriptor check and safe cleanup.
After deterministic repair tests pass, create a new one-shot producer
correlation run ticket. No speculative scene/light/camera/HUD change is in
scope.
FLR-0326 reached the fixed-color production replacement, Scene draw/present,
and Vulkan readback command-recording boundary, but no completion/result/
callback marker appeared and the QMP native ROI remained zero while the HUD
remained visible. Camera, culling, and Light are not first-cause candidates.
FLR-0328 then located the first missing event at the fence wait itself, and
FLR-0329 proved the bounded result is `VK_TIMEOUT`. FLR-0330 removed the
readback observer without changing the black native ROI. FLR-0331 then showed
native surface creation without native buffer attach/commit. The current gate
is to identify the fault event and its relation to the missing present return;
historical HUD-plus-Sequoia/color evidence remains the acceptance target.
FLR-0261
closed its diagnostic
stage-isolation A/B: the current-source controls reached model selection and
Present, and the current-source scene trace reached asset load, Scene
insertion, Draw submit/end, and active default Scene, but ten QMP frames
remained effectively black/grayscale. The first zero is now split to native
readback versus composition in FLR-0262. FLR-0262 found nonzero native
readback against a black QMP ROI; FLR-0263 published readback through SHM
twice but QMP stayed fully black. FLR-0264 then proved the child-surface
protocol and live-QMP timing while a same-image SHM control displayed the cube.
FLR-0266 falsified thread ownership and FLR-0267 proved that distinct
readback buffers are published and released, but the QMP frame became fully
black. FLR-0268 then proved the same image renders 2D plus a self-made 3D
through SHM-only control and rejected startup timing. FLR-0269 confirmed the
Wayland requests were accepted but the QMP frame transitioned to black;
FLR-0270 separated the readback pool and produced an early stable window, but
the readback ROI remained black and a later same-image run returned to full
black; FLR-0271 owns the child-surface visibility/import and timing boundary.
FLR-0259 closed the PlatformView create deadlock: official
0277 passed Mini patch/compile/image/QMP; bounded
stacks proved the handler's drain wait cycled with the ECS thread's synchronous
Flutter frame-event send, and the asynchronous value-captured drain made all
handler/result/callback/drain markers return. QMP now shows a black
PlatformView trapezoid over the white 2D surface, so FLR-0261 owns the
remaining current-source scene-stage boundary. FLR-0258 closed the handler-return
boundary: official 0276 passed Mini patch/compile/image/QMP; the handler enters
and starts `PluginsAoiPlatformViewCreate`, but no return/end or downstream
result/callback marker occurs while the 2D HUD remains visible. FLR-0259 now
owns native call-stack and wait/fault classification. FLR-0257 closed the native create-result
diagnostic: the patch is in the guest binary, but its two result markers remain
absent while the C API return and 2D HUD pass; the next boundary is the
platform-views handler return. FLR-0233 closed the
pointer-motion discriminator: the official motion-only gate passed Mini
do_patch/do_compile/image; control whitened HUD at the logged motion while
motion-skip preserved HUD `2801` and native `24178`. The diagnostic gate is not
the product fix; FLR-0234 owns the parent repaint repair. FLR-0232 closed the
input-independent-parent classification: no-input and single-axis controls
stayed at HUD `2801`/native `24178`, while x→4s→y produced
`wl_pointer.motion` and a persistent HUD `0`/native `24178`. FLR-0231 closed
the button-release
discriminator: the official button-up gate passed Mini do_patch/do_compile/image,
but control and button-up-skip QMP runs produced the same uniform-white HUD
after `up` while the native ROI stayed at `24178` chromatic pixels. The
button-up delivery hypothesis is therefore falsified. FLR-0229 closed the
output-enter
metrics discriminator: the official root-level patch passed Mini
do_patch/do_compile/image; skipping output-enter `SetPixelRatio` preserved HUD
through `move-y` with native 3D unchanged, but button `up` still whitened HUD.
FLR-0228 closed the parent-alpha
boundary classification: its runtime-only probe kept the diagnostic 3D ROI
unchanged but reproduced the uniform white parent after pointer movement, and
static inspection narrowed the next discriminator to output-enter
`SetPixelRatio` metrics resend. FLR-0227 closed the MenuAnchor
widget-layer hypothesis: the official A/B patch passed Mini do_patch/
do_compile/image, but QMP reproduced the white parent/HUD frame with an
unchanged native ROI and clean teardown. FLR-0226 closed its parent-level
transparency hypothesis. FLR-0220 closed its geometry and
clipping work unit, and FLR-0213 closed after the child-edit official patch
criterion passed. FLR-0194, FLR-0195, FLR-0196, FLR-0197,
FLR-0198, and FLR-0199
are Done: the deterministic update-recipe flow, Filament callback correction,
and complete baseline-to-final patch history all passed their contract and Mini
gates. FLR-0194's image build and QMP run passed the existing boundaries, but
the application callback did not emit a result after driver readback completed.
FLR-0214 then proved that the native WSI buffer is RGB-positive in both the
producer and compositor mappings while the final QMP native ROI remains black;
FLR-0215 owned the surface visibility/selection boundary, and FLR-0216 showed
that the visible SHM control works while the readback bridge receives a
uniform-white payload. FLR-0217 proved readback completion but not image
identity. FLR-0218 then correlated the same swapchain image through draw,
readback, and present, falsifying image-index mismatch. FLR-0219 proved the
native Wayland client lifecycle but found uniform-white native readback rather
than geometry; FLR-0220 proved the render-target shape-content boundary before
the final composition question was reopened. FLR-0221 then proved the SHM
bridge/native-only split. FLR-0222 is paused on native-only restoration while
FLR-0224 closed input coverage; FLR-0225 isolated the post-input
surface/composition boundary; FLR-0226 owns the minimal Flutter-parent
transparent-composition correction.
FLR-0198 then proved that the driver-completion buffer contains non-zero bytes,
but did not prove that the 3D candidate ROI contains them; the QMP 3D candidate
remains uniformly black. FLR-0199 proved that the driver ROI is non-zero while
the paired QMP ROI is black. FLR-0200 owns the native-surface visibility and
compositor split. FLR-0193 is Waiting: the opaque
fixture reaches a direct 1280x800 swapchain draw and present, but the existing
intermediate-target probe does not run and QMP remains uniformly black;
FLR-0194 resumes direct swapchain readback after FLR-0195. FLR-0192 is Done: the ECS ordering
fix reached create handler count=1 but the fixed 3D QMP region remained black.
FLR-0189 is Done: obsolete active
0235/0236 registrations were retired, and Mini do_patch/do_compile PASS at
`44c88ec`. FLR-0188 resumes image/QEMU. FLR-0187 is Done: the clean
patch stack reached compilation, but stale 0235/0236 APIs fail against the
current source. FLR-0187 is Done: current-source
official 0232 was generated through Mac Devtool, applied on Mac and Mini with
clean do_patch, and the stack reached the compile boundary. FLR-0186 is Done: corrected
effective-source 0227 was generated through Mac Devtool, applied on Mini with
zero fuzz, and the clean gate stopped at 0232 fuzz. FLR-0185 is Done: 0251
applied on Mac and Mini and the clean gate advanced to 0227. FLR-0184 is Done: 0241 was
obsolete after current direct-camera API inspection and clean Mini advanced to
0242. FLR-0183 is Done: current source
made 0240 obsolete and clean Mini advanced to 0241. FLR-0182 is Done: current
DrawFrame diagnostics generated officially and clean Mini do_patch advanced to
0240. FLR-0180 is Done: official
current-source 0228 replaced the stale patch and clean Mini do_patch advanced
to the next boundary. FLR-0181 is Done: valid QEMU
override registrations are accepted and exact duplicate lines remain rejected.
FLR-0179 is Done: 0239 was
retired after a clean-gate reproduction and the next boundary is 0228.
FLR-0178 is Done: the recipe-scoped
clean reset passed and reproduced the same 0239 boundary from a clean workdir.
FLR-0177 is Waiting because the
Mini workdir provenance must be made deterministic before regenerating 0239.
FLR-0176 is Done: official Devtool
rebase applied 0236 on Mini and do_patch advanced through 0238. FLR-0175 is Done: official Devtool
rebase applied 0235 on Mini and do_patch advanced to 0236. FLR-0174 is Done: official Devtool
rebase applied 0234 on Mini and do_patch advanced to 0235. FLR-0173 is Done: official Devtool
rebase applied 0233 on Mini and do_patch advanced to 0234. FLR-0172 is Done: official Devtool
rebase applied 0231 on Mini and do_patch advanced to 0233. FLR-0171 is Done:
official Devtool rebase applied 0229 on Mini and do_patch advanced to 0231. FLR-0170 is Done: its fixed-receiver
recipe gate passed preflight, bounded failure output, and reproduced 0229 hunk 2
with the correct `flutter-auto` task log. FLR-0169 is Done: corrected 0224
applied on Mini and do_patch advanced to 0229. FLR-0168 is Done: corrected
effective-source Devtool generation made 0226 apply and Mini do_patch advanced
to 0224. FLR-0167 is Done: corrected 0223 applied as well. FLR-0166 is Done: registration was
validated before explicit replacement, old/new SHA evidence was produced, and
full verification passed. FLR-0165 is Done: default refusal
and explicit replacement are contract-tested and full verification passed.
FLR-0164 is Done: the standard
update-recipe path generated one patch in the fixed workspace and full
verification passed. FLR-0163 is Done: the
source-path/component-role guard rejected the outer `flutter-auto` before
reset/add, and full verification passed. FLR-0162 is Done: its whole-line
status parsing passed full verification and was committed locally as `974cefe`.
FLR-0161 is Done: the one-shot
split-component Devtool rebase helper, bounded failure output, contract tests,
and automatic baseline-lock refresh passed `make verify` and were committed
locally as `9012626`. FLR-0160 resumes after the
`do_patch` gate advanced past 0220 and stopped at the 0221/current-plugin
boundary; FLR-0158 is Waiting after its minimal 0002 metadata correction;
FLR-0159 is Done because its 0220 boundary advanced successfully with the
current-source Devtool patch;
FLR-0157 is Done with the deterministic
handoff/runtime-evidence helper committed. FLR-0155 is Done as a completed
boundary classification: exact fixture vertex/index upload checksums and
Vulkan bind handles match the source data, while the fixture-local camera
branch skips the only projection update and leaves Filament's identity
projection active. With eye `(0,0,5)` and cube z range `[-1,1]`, the view-space
z range is `[-6,-4]`, outside the identity clip range, so all geometry is
clipped before fragment output. FLR-0156 owns the minimal repair: preserve the
fixture-local look-at but apply the deserialized camera configuration first.
FLR-0154 is Done as a completed
runtime discriminator attempt with a recorded limitation: the hardcoded-color
launch remained black, but the source did not emit a branch-entry marker, so
execution of that exact shader-source branch is UNKNOWN. FLR-0153 is Done as a falsified API
discriminator: explicit color on the Renderable-bound MaterialInstance did not
change the all-black native 3D candidate, and the checked Filament source shows
that `createInstance()` duplicates the default instance's uniform buffer. The
next unit hardcodes the shader output color under an environment-gated
diagnostic switch to separate dynamic material/uniform behavior from a later
Vulkan attachment/content boundary. FLR-0152 is Done as a state
classification unit: Mini/QEMU state traces show valid render area, viewport,
scissor, color-write mask, shader handles, vertex input, indexed draw, queue
present, and Wayland child commits.
FLR-0150 is Done as a boundary
evidence unit: the actual swapchain readback and paired QMP region were both
zero even though native draw2 admission, valid swapchain target identity,
render-pass return, queue present, and Wayland child commit were positive. The
first zero boundary is therefore narrowed to Vulkan pixel generation,
attachment/content, or readback semantics; the exact API owner is split to
FLR-0152. FLR-0149 is Done as a boundary
evidence unit: existing Filament diagnostics proved native draw2 admission,
valid swapchain target identity, and render-pass return, while QMP remained
black. FLR-0148 is Done as a boundary
evidence unit: the effective ViewTarget and native resource contracts were
valid, but the QMP native region remained black; existing Filament draw and
render-pass diagnostics are enabled next. FLR-0147 is Waiting because its
explicit local-camera discriminator reached the runtime but did not restore
native QMP pixels; the effective scene/render/composition contract is now
tracked separately. FLR-0146 is Done: after a Podman
restart, the tracked Yocto-standard workspace layer restored `modify
--no-extract` in the same container and mount without using the obsolete control
copy. The 3D test now uses the packaged unlit shader's `baseMap` contract; the
old color-only helper is not valid for this asset.
FLR-0142 is
Done: the official Devtool-generated Wayland flush patch applied
and the Mini/QMP loop passed, but the stable post-launch frame remained the
same Cube-only frame as FLR-0139; flush is not the composition fix. FLR-0141
and the camera/API unit FLR-0141 is Done. FLR-0140 remains Waiting for the separate
alpha/composite follow-up after API alignment. FLR-0139 owns the Dart unlit `baseMap` contract after FLR-0138 showed that
culling was confounded by an unsatisfied shader input and an incomplete
swapchain observation window. It is Done: the official 0059 patch was built
into one Mini image, and a single normal-Dart QEMU showed the self-made Cube
in QMP. FLR-0140 is Waiting on the separate alpha/composite follow-up after
API alignment; its same-run evidence showed early HUD and late Cube frames.
FLR-0141 remains the separate Dart/native scene and camera API-alignment
ticket. Do not
reopen FLR-0139 or alter its 0059 patch.
FLR-0138 owned the self-made Dart Cube culling A/B after
FLR-0137 proved that switching the same fixture from lit to unlit material did
not change the black 3D
region. FLR-0136 is Done as an opacity classification. FLR-0135 is Done as an
API correction and negative visual classification. FLR-0134
is Done as a diagnostic classification: the normal Dart run reaches
`beginFrame`, `render`, `endFrame`, target draw, and present, but its fixed 3D
region is black; the same QEMU native fixture is visibly blue. The Light
mismatch was corrected and classified in FLR-0135 without a visual change.
FLR-0137 is Done: its official unlit-material patch and all Mini build/runtime
gates passed, but the self-made Dart Cube remained absent in QMP while
draw/present markers stayed active. The next source-owned difference is
culling: the visible native fixture explicitly disables culling, while Dart
Shape defaults `cullingEnabled` to true and native BaseShape forwards it.
FLR-0136 now tests the ViewTarget opacity boundary. FLR-0133 is Waiting: the
diagnostic
ready override changed frame status from skip to admitted, but the fixed 3D
QMP region remained black; the reason ViewTarget still does not produce 3D
pixels is UNKNOWN. FLR-0132 is Waiting: the official
Devtool-generated camera-mode patch applied and all Mini build gates passed,
and a clean single-process QEMU run reached Dart scene pass, Shape readiness,
and camera receive/apply, but the fixed 3D region remained uniformly black.
The first missing boundary was `FrameSkipper`/Vulkan fence linkage:
`linked=false` led to `TIMEOUT_EXPIRED`, `Renderer::beginFrame=false`, and no
ViewTarget target-draw/present markers. The reason the command fence is
unlinked remains UNKNOWN and is owned by FLR-0133. FLR-0131 is Waiting: its launch
guard allowed a duplicate `flutter-auto`, causing an `agl_shell` collision and
guard allowed a duplicate `flutter-auto`, causing an `agl_shell` collision and
frame skips, so its Shape-to-Filament Draw boundary is UNKNOWN. FLR-0130 is
Waiting: the actual Mini API
already had the camera receiver, and the default-primary guard was removed by
the official Devtool patch, but the camera markers did not produce visible 3D
pixels. FLR-0129 is Waiting: the lit Dart fixture remained
black with forced-opaque ViewTarget, so the translucent-only hypothesis is not
supported. FLR-0127 is Waiting: the A/B changed the full
frame from black to uniform white but did not produce geometry or HUD pixels;
the material/surface owner remains UNKNOWN. FLR-0126 is Waiting: Shape/Camera/
submit/present markers passed, but the normal Dart fixture remained uniformly
black in QMP. FLR-0125 is Done: the native fixture now
reaches visible QMP pixels through the Devtool-generated patch, canonical layer,
Mini build, and one-QEMU control. FLR-0124 is Waiting because its Devtool, canonical layer, Mini
build, and teardown gates passed but the runtime never reached native geometry
setup; its QMP region remained uniform black. FLR-0123 is Waiting
because its source preflight found that the current Mini image lacks the
historical native-control implementation, so a variable-only QEMU run would be
a no-op. FLR-0122 is Waiting because its source/marker map and one accepted
QMP run completed, but the exact first source-owned divergence remains UNKNOWN.
FLR-0121 cleared the Dart/native camera API-generation and
payload-placement mismatch. FLR-0121 is Waiting because its camera errors
disappeared but its QMP central 3D region remained uniform black. FLR-0120 is
Waiting because its native registration reorder was falsified by the unchanged
camera channel errors. FLR-0119 is Waiting because its bounded ECS retry
stopped the pre-present crash and reached shape/Vulkan submit, but the QMP
central 3D region remained black; FLR-0118 is Waiting because its source and
build gates passed but the fixture crashed before present; FLR-0113 resumes
the explicit-light contribution A/B only after a valid fixture QMP-positive
control. FLR-0116 removed the current-image Example Demo pre-frame
`std::bad_variant_access` boundary; FLR-0115 closed the
reproducible Example Demo pub-cache lock flow. FLR-0114 reconciled the inherited flutter-auto
patch baseline;
FLR-0114 is Done as the deterministic Mac recipe gate;
FLR-0112 is Waiting after completing the QMP color/edge classification and
splitting the next source investigation;
FLR-0111 remains Waiting for the already-started second-run cleanup and deep
stack collection. FLR-0111 compares the pure fixture against FLR-0109's
lavapipe wait candidate. FLR-0109 resumes isolating the blocked present/WSI
owner after the independent fixture-control result; FLR-0108 proved production
pipeline creation returns successfully.
FLR-0108 is Done as a boundary-evidence unit: the six production pipeline
creates returned success and selected RenderPass begin/end markers were
paired, but queue-present had no bounded return and QMP native pixels remained
zero. Its GDB, QMP, marker, kernel, hash, and clean-teardown evidence is in
the ticket and evidence file.
FLR-0104 is Done as a separate image/tooling unit; it did not claim a
production 3D fix.
FLR-0105 is Done as a bounded debugger unit: the normal
`llvm::CmpInst::isOrdered` entry and its LLVM InstCombine chain were captured,
while the later OOPS landed at `isOrdered+1` in another `FEngine::loop` thread.
FLR-0106 resolved the outer producer as Mesa `gallivm_compile_module()` at
`lp_bld_init.c:620`; FLR-0107 then showed that the observed call is shared
`lvp_CreateDevice` initialization, both LLVM passes return normally, and input
validity/fault causality remain UNKNOWN. FLR-0108 owns the production-specific
pipeline boundary.
FLR-0103 is Done as a boundary-evidence unit: the production QMP frame stayed
HUD-only, the guest OOPS mapped to `llvm::CmpInst::isOrdered` at file offset
`0xb1d541`, and QMP teardown was clean. FLR-0106 later identified the first
non-LLVM producer as Mesa `gallivm_compile_module()`; the later guest
`addr2line` OOM is recorded as a separate failed observation.
FLR-0102 is closed as a diagnostic evidence unit: the fixture reached visible
native 3D while production remained native-black and faulted at the
post-scene/present boundary. The official Devtool patch, Mini build, QMP
captures, logs, hashes, and teardown are recorded in its ticket and evidence
file.
FLR-0101 is closed as an evidence unit: the smallest production trigger
remains UNKNOWN, while model/resource reductions consistently retained the
same native-black/present-entry boundary. The scene-content and scene-render
selector cases were invalid and are explicitly excluded from the conclusion.
FLR-0100 closed the present-return ambiguity: the recovered production run
entered queue-present and then the guest reported a userspace page fault in
`FEngine::loop` at the already-known `libLLVM.so.18.1` /
`llvm::CmpInst::isOrdered` offset boundary. The exact producer remains
UNKNOWN; no synchronization or present patch was made.
FLR-0099 isolated the first observed draw-to-native divergence: the fixture
returned from `vkQueuePresentKHR` and produced `41,750/223,200` native pixels,
while recovered production reached a visible swapchain draw but had no queue
present return and remained at `0/223,200`. FLR-0100 owns thread/backtrace and
syscall timing analysis; no source patch is justified yet.
FLR-0098 rechecked current-image frame-skip recovery: the existing ready
control restored frame begin/end and draw-target setup, but production native
pixels remained zero. FLR-0097 isolated the post-pipeline render boundary: production scene,
camera, view, renderable, and material state were valid, but
`FRAME_BEGIN started=false` prevented native draw/submit/present while the
fixture reached native pixels. FLR-0096 captured bounded runtime state during the fourth production pipeline
create and is Done: the fourth create eventually returned success after about
21.4 seconds, but the production native region remained black. FLR-0095
captured live startup markers and
complete fixture/production pipeline records and is Done as an evidence unit;
the fourth create cause remains UNKNOWN. FLR-0094 compared the self-made
fixture and production pipeline inputs using neutral controls and is Waiting
because the fixture startup marker was not retained. FLR-0093 isolated the production
graphics-pipeline create boundary identified by FLR-0091. FLR-0091 closed the first unfinished Vulkan
command unit after FLR-0090 identified the llvmpipe worker wait. FLR-0089 closed the semaphore
completion/pixel correlation, and FLR-0088 closed the signal/wait mapping
boundary after FLR-0086 isolated
the first missing `vkQueuePresentKHR` return boundary. FLR-0086 isolates the
present-call completion boundary after
FLR-0083 proved that producer-side queue flush runs but the consumer does not
reach `waitForCommands()`/`FEngine::execute()`. FLR-0082 bounded the Podman `status`
probe so the existing machine/container/bind contract is reused without a
downloads-tree scan on every check. FLR-0081 is Waiting after the current
minimal geometry remained black and stopped before command execution/present.
FLR-0079 reproduces the current-image forced-fixture present
boundary before the explicit-light A/B in FLR-0078. FLR-0078 isolates explicit-light Scene attachment after
FLR-0077 proved that default indirect-light attachment alone does not restore
the full-production shaded output. The current image proves a self-made cube and Sequoia model-only
pixels. FLR-0076 is Done as the surface/composition boundary unit. FLR-0075 is
Done as the source/build
restoration unit: the official Mac Devtool patch was generated and Mini
`do_patch`/compile/full-image passed, but QMP did not show an accepted visible
3D object or HUD. FLR-0074 is closed with QMP evidence: the forced matrix was cleanly
captured but its runtime log showed `INDIRECT_LIGHT_TYPE=HDR`, not the
`DEFAULT` condition used by p6; the source-stack comparison then identified
the removed recipe patch. FLR-0073 is closed with
QMP evidence: the 0206-free `a0ddaf3` image and current image are both black,
so 0206 is not the cause. FLR-0072 is closed with QMP evidence; the old p9
rootfs and complete launch identity are missing. FLR-0071 is closed with QMP
evidence; delay-only and native-state trace did not restore pixels, so neither
is a product fix. FLR-0070 is closed with QMP evidence; it found a historical
trace-visible condition but did not establish a product fix.
FLR-0067 separates the first production scene stage that
turns the visible model-only baseline into a zero target. FLR-0065 completed
the bounded current-image target comparison and is Waiting; FLR-0066 completed
the historical controlled-path comparison. FLR-0064 completed
the non-blocking observation through the fixed Mini/QEMU flow. FLR-0062 is
Waiting after identifying the queue-idle boundary.
FLR-0053 is Waiting with the one-machine/one-container provider gate passed;
its source-dependent `modify`/`finish` acceptance is owned by FLR-0062.
FLR-0058's frame/fence gate,
FLR-0059's surface-placement gate, FLR-0060's shape/light plus owner
reconciliation, and FLR-0061's draw/pipeline boundary are complete and Waiting;
route/input remains a later independent gate. FLR-0052's canonical receiver
and progressive BitBake gates are complete. FLR-0054's Podman mount and bundle
handoff simplification is complete. FLR-0053's Podman runtime is available
through one operator-managed machine; this project wrapper does not manage
machine lifecycle.

FLR-0026は、0197/0198/0199の証拠済み範囲を固定した履歴ticketとしてWaitingのまま保持する。旧receiver成果物の現行受け口からの退避はFLR-0085で完了し、今後はFLR-0086以降のticketと中立な`FLUORITE_*`命名を使用する。FLR-0084はdriver-thread lifecycleの観測を完了し、present-call境界をFLR-0086へ分割した。FLR-0027のshape/light分離gate、FLR-0028のco-enabled境界特定、FLR-0029の再現性・診断ツール経路確認、FLR-0030のfault symbol mapping、FLR-0039のselected判定静的確認、FLR-0040のselected GUID134 runtime比較は独立ticketとして完了した。次はFLR-0041でGUID134/GUID136のnative entity/resource/render-list状態を直接記録する。FLR-0023はfixtureのpackage/AOT inclusion、mini PC image build、full-scene比較まで完了したが、production sceneの可視3D到達は継続中である。devへの通常mergeはFluorite動作確認まで行わない。

| ID | Problem / outcome | Depends on |
| --- | --- | --- |
| [FLR-0002](work/tickets/FLR-0002-mac-qemu-baseline.md) | Macで既存qemux86-64の再現可能な起動baselineを採る | FLR-0001 |
| [FLR-0003](work/tickets/FLR-0003-qemuarm64-hvf.md) | qemuarm64 + HVFがMac検証の主経路になるか判定する | FLR-0002 |
| [FLR-0004](work/tickets/FLR-0004-yocto-observer-mcp.md) | build hostのYocto状態を安全に観測するread-only MCPを作る | FLR-0001 |
| [FLR-0005](work/tickets/FLR-0005-target-validation-mcp.md) | QEMU/実機の証拠収集を標準化するvalidation MCPを作る | FLR-0002 |
| [FLR-0006](work/tickets/FLR-0006-raspberrypi-build.md) | 固定baselineからRaspberry Pi 4 imageを再build・検証する | FLR-0003, FLR-0004 |
| [FLR-0007](work/tickets/FLR-0007-agl-architecture.md) | AGLがimage、compositor、launcher、appを組み立てるprocessを固定revisionから理解する | FLR-0001 |
| [FLR-0009](work/tickets/FLR-0009-flutter-engine-embedder.md) | Flutter Engineとivi launcherの描画・thread・surface契約を理解する | FLR-0007, FLR-0008 |
| [FLR-0010](work/tickets/FLR-0010-filament-bridge.md) | Dart APIからnative filament_viewとFilamentまでのcall pathを特定する | FLR-0008 |
| [FLR-0011](work/tickets/FLR-0011-vulkan-gpu-stack.md) | Filament/FlutterからVulkan、Mesa、GPUまでの実効経路をtarget別に特定する | FLR-0009, FLR-0010 |
| [FLR-0012](work/tickets/FLR-0012-source-knowledge-mcp.md) | component別MCPのshared contractを固定する | FLR-0007, FLR-0008 |
| [FLR-0013](work/tickets/FLR-0013-agl-observer-mcp.md) | AGLのmanifest、feature、image組立をYoctoから分離して観測する | FLR-0001 |
| [FLR-0014](work/tickets/FLR-0014-command-runner-mcp.md) | allowlist runbookだけを実行するcommand MCPを作る | FLR-0001, FLR-0004, FLR-0013 |
| [FLR-0008](work/tickets/FLR-0008-fluorite-demo.md) | Fluorite 3D demoの成功状態とscene/native境界を固定する | FLR-0001, FLR-0015 |
| [FLR-0016](work/tickets/FLR-0016-bitbake-preflight.md) | 既存 AGL checkout/cache を再利用する BitBake preflight を固定する | FLR-0001, FLR-0006, FLR-0007 |
| [FLR-0017](work/tickets/FLR-0017-qemu-evidence-mcp.md) | legacy QEMU contractをbounded evidence observerへ落とし込む | FLR-0002, FLR-0005, FLR-0008, FLR-0016 |
| [FLR-0018](work/tickets/FLR-0018-qemu-launch-runbook.md) | QEMU launchをregistered Execution runbookへ固定する | FLR-0017 |
| [FLR-0019](work/tickets/FLR-0019-qemu-build-iteration.md) | BitBake成果物からQEMU stable-render verdictまでを反復する | FLR-0018 |
| [FLR-0020](work/tickets/FLR-0020-self-contained-build-workspace.md) | meta-fluorite-trialだけでAGL/Yocto build workspaceを再構成する | FLR-0019 |
| [FLR-0023](work/tickets/FLR-0023-project-owned-fluorite-layer.md) | meta-fluorite-trial layerをFluorite固有実装のsource of truthとしてBitBake入力を再構成する | FLR-0021, FLR-0022 |
| [FLR-0024](work/tickets/FLR-0024-project-layer-naming.md) | legacy meta-localをmeta-fluorite-trial layerへ置き換える | FLR-0023 |
| [FLR-0025](work/tickets/FLR-0025-bitbake-monitor-mcp.md) | bounded BitBake監視MCPを追加する | FLR-0024 |
| [FLR-0023](work/tickets/FLR-0023-flutter-engine-3d-fixture.md) | fixtureのnative crash boundaryからentity/renderable/frame/child surfaceの未達を切り分ける | FLR-0019, FLR-0021 |

## Waiting

- [FLR-0344](work/tickets/FLR-0344-capture-lavapipe-watch-failure-deterministically.md):
  One exact-image run reproduced Present-enter/no-return and a HUD-only QMP
  frame with all 768,000 lower-ROI pixels black. GDB launch succeeded, but
  `missing-gdb-state` skipped the arm poll; later transcript showed GDB alive
  and thread-creation lines. App/QEMU/QMP teardown passed. FLR-0346 corrected
  the helper locally; FLR-0347 performs the separately ticketed same-image
  retest. Do not repeat the original FLR-0344 run.

- [FLR-0343](work/tickets/FLR-0343-observe-lavapipe-sync-producer.md):
  Waiting after one exact-image run reproduced Present-enter/no-return and
  saved QMP evidence of visible HUD with a uniformly black lower 3D ROI. GDB
  never emitted the armed marker within 10 seconds; only its log SHA was
  retained, so sync fields and writer remain UNKNOWN. FLR-0344 separates
  attach/arm/watch and persists selected GDB output before teardown.

- [FLR-0336](work/tickets/FLR-0336-capture-kernel-context-of-fengine-page-fault.md):
  Waiting after one bounded kernel-only trace. Both guest page-fault events
  and perf callchains are supported; the recurring Oops reproduced at guest
  monotonic `422.495545`, but no kernel-event sample matched TID 710 or the
  Oops time. QMP remained HUD-only with a uniformly black lower 3D ROI. Root
  cause is UNKNOWN; FLR-0337 completed the user+kernel event discriminator.

- [FLR-0334](work/tickets/FLR-0334-symbolize-production-fengine-render-fault.md):
  Waiting. Same-image diagnostic run under GDB lasted 11m07 and exceeded the
  predecessor's 598-second page-fault point, but no SIGSEGV occurred. A manual
  SIGINT captured main-thread `nanosleep`, Wayland poll, and FEngine/llvmpipe
  wait stacks; QMP stayed byte-identical and present-return markers remained
  absent. FLR-0335 later reproduced a page fault without GDB; the post-fault
  RIP mapped to the known `isOrdered+1` boundary, but the faulting TID was gone
  before GDB attach. FLR-0337 captured the matching user-fault event;
  FLR-0338 completed a bounded hardware-breakpoint no-hit capture. FLR-0339
  then captured a partial Lavapipe pending-wait stack during Present-enter/no-return;
  FLR-0340 owns static source mapping. Do not repeat the `isOrdered+1`
  breakpoint or the all-thread GDB dump without new evidence.
- [FLR-0130](work/tickets/FLR-0130-restore-deserialized-camera-handoff.md):
  Waiting. The initial API-generation diagnosis was corrected. The official
  current-source Devtool patch removed the default-primary skip, and Mini
  `do_patch`, `do_compile`, full image, camera handoff markers, QMP capture/video,
  and negotiated teardown passed. The fixed QMP 3D region remained uniform
  black; FLR-0131 owns the next Draw boundary.

- [FLR-0129](work/tickets/FLR-0129-compare-dart-opaque-translucent-surface.md):
  Waiting. The lit Dart fixture with a current-source forced-opaque ViewTarget
  still had a black 3D region while its 2D HUD, Shape/submit/present markers,
  and opaque probe were present. The translucent-surface-only hypothesis is
  not supported; FLR-0130 owns the missing deserialized-camera handoff.

- [FLR-0116](work/tickets/FLR-0116-flutter-auto-material-variant-crash.md):
  Done. The official Mac Devtool COLOR compatibility patch was built on Mini,
  and one QMP-only run proved the repaired app stays alive and shows its 2D
  HUD. Production 3D remains open; the invalid environment-only fixture
  attempt is preserved and handed to FLR-0118.

- [FLR-0118](work/tickets/FLR-0118-devtool-fixture-3d-pixel-control.md):
  Waiting. The official Devtool fixture patch and Mini full image passed, but
  the corrected Wayland launch crashed before present in
  `ECSystem::vSetupMessageChannels(this=0x0)`; FLR-0119 owns the initialization
  race repair.

- [FLR-0119](work/tickets/FLR-0119-fix-ecs-platform-channel-init-race.md):
  Waiting. The bounded retry patch was generated by official Devtool,
  registered, bundled, built on Mini, and ran without a coredump through
  `SHAPE_READY` and Vulkan submit. The central QMP 3D region stayed black;
  FLR-0120 tested and falsified the camera API registration-order boundary;
  FLR-0121 owns the Dart/native API-generation mismatch.

- [FLR-0120](work/tickets/FLR-0120-register-filament-camera-api-before-fixture-init.md):
  Waiting. Commit `81caadc` passed bundle, Mini build, and no-coredump QEMU
  health, but `setCameraDolly`/`setCameraTarget` remained unhandled and the
  central QMP region stayed uniform black. FLR-0121 owns the next adapter.

- [FLR-0115](work/tickets/FLR-0115-flutter-pub-cache-lock-order.md): Done.
  Commit `5136925` fixed the lock-before-archive ordering and marker identity
  refresh. The corrected archive, Example Demo compile, full image, current
  manifest, and QMP-only guest debug-tool probe passed on the existing Mini
  roles. The production launch aborted before a comparable first frame and is
  tracked independently by FLR-0116.
- [FLR-0113](work/tickets/FLR-0113-isolate-explicit-light-contribution-boundary.md): Waiting. Current-tip `flutter-auto` `do_patch`, `do_compile`, full image, and current-image debug-tool probe now pass; the first production launch aborts in MaterialParameter deserialization before the 3D A/B, which FLR-0116 owns.
- [FLR-0111](work/tickets/FLR-0111-compare-pure-fixture-present-wait.md): Waiting. The first pure-fixture control passed native QMP pixels, queue-present return/done, low-memory GDB, and teardown. The already-started second run needs one bounded deep-GDB/QMP/cleanup collection when the remote execution gate is available; no third QEMU is permitted.
- [FLR-0104](work/tickets/FLR-0104-runtime-debug-tools.md): Done. The project-owned runtime-debug packagegroup was built into exact image `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`; guest GDB, coredumpctl, LLVM symbolizer, syscall/profiling tools, targeted debug files, QMP capture, and zero-residual teardown all passed. FLR-0103 resumes the production fault diagnosis.
- [FLR-0105](work/tickets/FLR-0105-gdb-breakpoint-ownership.md): Done. One-QEMU bounded GDB captured normal entry into `llvm::CmpInst::isOrdered` and an LLVM InstCombine caller chain; the later `FEngine::loop` OOPS landed at the next byte in another thread. QMP remained HUD-only (`0/223200` native), teardown passed, and no source fix was claimed. FLR-0106 owns the outer-producer capture.
- [FLR-0106](work/tickets/FLR-0106-capture-llvm-outer-producer.md): Done. One-QEMU bounded `bt 16` reached Mesa `gallivm_compile_module()` at `lp_bld_init.c:620` above LLVM; QMP remained HUD-only (`0/223200` native), teardown passed, and no source fix was claimed. FLR-0107 owns the Gallivm/LLVM input correlation.
- [FLR-0107](work/tickets/FLR-0107-correlate-gallivm-llvm-input.md): Done. Static Mesa 24.0.7 source and one-QEMU GDB evidence showed the Gallivm call occurs under shared `lvp_CreateDevice` texture-handle setup; both LLVM pass calls returned, while the later OOPS remained causally UNKNOWN. QMP stayed HUD-only (`0/223200` native), teardown passed, and no source fix was claimed. FLR-0108 owns the production pipeline boundary.
- [FLR-0103](work/tickets/FLR-0103-trace-post-scene-vulkan-present-boundary.md): Done. The fixed debug-image production run kept the 2D HUD visible, retained a black native region, and mapped the `FEngine::loop` OOPS to `libLLVM.so.18.1` / `llvm::CmpInst::isOrdered` at file offset `0xb1d541`. The exact caller/producer remains UNKNOWN; FLR-0106 owns the deeper bounded caller capture.
- [FLR-0058](work/tickets/FLR-0058-restore-native-frame-loop.md): current-image control/`TREAT_UNLINKED_FENCE_READY` A/B proved that unlinked Fence state causes repeated frame skips, but ready treatment alone did not produce QMP native 3D pixels. Surface visibility is split to FLR-0059.
- [FLR-0059](work/tickets/FLR-0059-native-surface-visibility-ab.md): current-image default/below-parent surface A/B reached Sequoia model/camera/frame/present markers but both arrangements retained the same black native candidate region. Shaded draw/resource separation is split to FLR-0060.
- [FLR-0060](work/tickets/FLR-0060-production-shaded-draw-resource-boundary.md): current-image shape/light probes were black under the normal grpc owner; snapshot-only owner isolation reproduced HUD plus diagnostic native pixels, while full shaded production remained black. The remaining production draw/resource boundary is split to FLR-0061.
- [FLR-0057](work/tickets/FLR-0057-production-lit-3d-and-route.md): current-image light-count matrix 1/5/6/13 is complete; all cases reached model/camera/present markers but the production 3D candidate region remained black. Frame-loop, composition, and route/input are split to FLR-0058 and later tickets.
- [FLR-0050](work/tickets/FLR-0050-flutter-parent-alpha-frame-loop.md): combined diagnostic composition is evidenced; direct alpha, full shaded vehicle, and route/input are split to FLR-0057.
- [FLR-0053](work/tickets/FLR-0053-podman-devtool-runtime.md): one rootful Podman machine, one bind-mounted container, OCI image, and `status` twice are PASS; source-dependent `modify`/`finish` are owned by FLR-0062.
- [FLR-0062](work/tickets/FLR-0062-production-shaded-output-target-boundary.md): corrected 49089ba removes redundant 0025/0026 while retaining 0027; Mini app `do_patch` 104/104 and full image 11748/11748 pass. One QMP run proves single-process ownership and clean teardown, but 0175 stops at `TARGET_PROBE_QUEUE_IDLE_BEGIN`; the ticket is Waiting and hands off to FLR-0064.
- [FLR-0064](work/tickets/FLR-0064-nonblocking-target-content-probe.md): Waiting. Mac Devtool 0176 was applied by Mini do_patch, compile, and full image; one QEMU completed the probe with target `nonzero_pixels=0` while the same QMP frame showed the 2D HUD. No latest-patch regression was proven.
- [FLR-0065](work/tickets/FLR-0065-production-target-zero-resource-boundary.md): Waiting. Current model-only and controlled combined paths are visible; full-shaded production remains black and is split to FLR-0067.
- [FLR-0066](work/tickets/FLR-0066-compare-historical-production-3d-stack.md): Done. Current image reproduces both the historical model-only result and the controlled combined diagnostic result; no generic latest-patch regression was found.
- [FLR-0067](work/tickets/FLR-0067-reintroduce-production-scene-stages.md): Waiting. p6 fixed `DEFAULT` indirect light and skipped skybox, then isolated explicit lights as the first zero boundary; the one-light cut is split to FLR-0068.
- [FLR-0071](work/tickets/FLR-0071-separate-trace-timing-side-effect.md): Done. Same-image trace-disabled, delay-only, and native-state-trace QMP comparison remained black in the 3D region; Mini build and cleanup passed.
- [FLR-0072](work/tickets/FLR-0072-reproduce-p9-trace-visible-condition.md): Done. Current-image trace replay remained black twice; p9 old rootfs and complete launch identity are unavailable.
- [FLR-0073](work/tickets/FLR-0073-compare-pre-0206-image-stack.md): Done. 0206-free and current images were both black under the same QMP profile; 0206 is not the cause.
- [FLR-0074](work/tickets/FLR-0074-isolate-explicit-light-render-target.md): Done. The forced matrix was captured and cleaned up; source/image provenance then showed the current black image uses HDR indirect light because the DEFAULT-restoring recipe patch was removed.
- [FLR-0075](work/tickets/FLR-0075-restore-production-default-indirect-light.md): Done as a restoration unit. Mac Devtool generated the DEFAULT indirect-light patch; Mini applied and built it, but the QMP control showed `1280x800` native surface versus `1280x720` app config and no accepted visible 3D/HUD.
- [FLR-0076](work/tickets/FLR-0076-isolate-surface-extent-composition.md): Done. The current fixed image rendered the self-made cube with the 2D HUD and rendered the production Sequoia model alone; the `1280x800` native extent versus `1280x720` Flutter view is not sufficient to explain the full-scene black result. The remaining boundary is the full production shaded path, split to FLR-0077.
- [FLR-0077](work/tickets/FLR-0077-isolate-full-production-shaded-boundary.md): Done. Official Mac Devtool patch 0207 and Mini build gates passed; opt-in default indirect-light Scene attachment did not change the full-production 3D region from zero. FLR-0078 isolates explicit-light attachment/resource behavior.
- [FLR-0063](work/tickets/FLR-0063-qmp-socket-path-contract.md): a valid long evidence directory caused QMP timeout because the Unix socket path exceeded the AF_UNIX limit; add fail-fast short-path preflight without mixing the harness fix into FLR-0062.
- [FLR-0079](work/tickets/FLR-0079-reproduce-current-fixture-present-boundary.md): Waiting. p13 classifies the current control's first observed divergence at the frame/fence-to-present boundary; it does not establish a product fix.
- [FLR-0080](work/tickets/FLR-0080-current-image-frame-recovery.md): Waiting. Ready-fence changed `FRAME_SKIP_STATUS` to 0 but produced no queue-present marker or QMP pixels; it is not a 3D fix.
- [FLR-0081](work/tickets/FLR-0081-current-image-minimal-geometry.md): Waiting. p15/p16 reached current minimal-geometry frame begin and enqueue, but produced zero command-execution/present markers and black QMP frames; FLR-0083 owns the source boundary.
- [FLR-0083](work/tickets/FLR-0083-current-image-command-stream-boundary.md): Done. p17 proved 62 producer-side queue flushes but zero consumer wait/engine-execute/present markers; FLR-0084 owns driver-thread lifecycle evidence.
- [FLR-0084](work/tickets/FLR-0084-driver-thread-lifecycle.md): Done. The authoritative Mini gates passed; neutral lifecycle markers proved driver-thread startup and queue-wait return, while QMP showed 2D HUD pixels but zero native 3D pixels. The first missing boundary is after `VK_QUEUE_PRESENT_BEGIN`; FLR-0086 owns the present-call diagnosis.
- [FLR-0086](work/tickets/FLR-0086-present-call-boundary.md): Done. The authoritative image build and QMP-only runtime passed; the first remaining boundary is `FLUORITE_VK_QUEUE_PRESENT_ENTER` without a return, while the HUD is visible and native 3D remains `0/223200`.
- [FLR-0093](work/tickets/FLR-0093-isolate-production-pipeline-create.md): Done as a diagnostic unit. Mac Devtool patch, Mini metadata/`do_patch`/`do_compile`/full-image gates, and one QMP-only production run passed; six pipeline creates returned `result=0`, while native pixels stayed `0/223200` and the HUD remained visible. The fixture-versus-production comparison is split to FLR-0094.
- [FLR-0090](work/tickets/FLR-0090-fence-completion-boundary.md): Done. Current-image GDB showed `FEngine::loop` and llvmpipe workers waiting in `libvulkan_lvp.so`; QMP showed HUD pixels and zero native pixels.
- [FLR-0089](work/tickets/FLR-0089-semaphore-completion-and-native-pixels.md): Done. Neutral Devtool fence trace built authoritatively on Mini; submit returned success, the fence was `VK_NOT_READY`, HUD pixels were visible, native pixels remained zero, and QMP cleanup passed.
- [FLR-0088](work/tickets/FLR-0088-vkqueue-present-wait-owner.md): Done. Corrected Devtool patch and authoritative Mini gates passed; submit returned success and the same semaphore handle was passed to present, while QMP kept the HUD visible and native pixels at zero.
- [FLR-0087](work/tickets/FLR-0087-serial-exec-completion-marker.md): Done. The serial completion record now places `rc=<number>` before the terminal marker; the fixed Mini receiver passed both zero and deliberate non-zero command checks on the active QEMU.
- [FLR-0078](work/tickets/FLR-0078-isolate-light-scene-attachment-boundary.md): Waiting. Its one-light Scene-add A/B is blocked until the current-image forced fixture control is reproduced or classified.
- [FLR-0055](work/tickets/FLR-0055-tps-bounded-qemu-harness.md): Waiting. Commits b71dce6/da341db/4cb84bd provide bounded guest readiness, boot serial evidence, CRLF QMP teardown, and serial prompt wake; p9 live gates passed, while SSH remains unreliable.
- [FLR-0056](work/tickets/FLR-0056-runtime-preflight-false-cleanup.md): residual detection corrected and orphaned QEMUs stopped; serial late-attach prompt recovery remains Waiting. Current-image guest SSH is available.
- [FLR-0022](work/tickets/FLR-0022-devtool-docker-bundle.md): bundle workflow implementation exists, but the clean receiver + completed recipe-scoped Devtool/BitBake gate remains open.
- [FLR-0023](work/tickets/FLR-0023-flutter-engine-3d-fixture.md): fixture package/static gates are complete; runtime child-surface acceptance is superseded by the smaller FLR-0042/FLR-0050 boundaries.

- [FLR-0001](work/tickets/FLR-0001-canonical-repository-baseline.md): foundation deliveryとCIはPASS。PR review/merge、Linux build roleの同一revision checkout、remote MCP、branch policyのacceptance待ち。
- push後、canonical cloneをproject rootにしたfresh Codex taskでcustom-agent/MCP routingをsmokeする。
- 実機検証条件（Raspberry Pi 4、display、input、network）の詳細はUNKNOWN。
- GitHub repository settingsで`Branch policy / validate-branch-flow`をrequired status checkにする。

## Inbox

- [FLR-0114](work/tickets/FLR-0114-reconcile-flutter-auto-patch-stack-baseline.md): Done. Reconciled the current-source `flutter-auto` patch stack, including the QEMU-only quality patch; the bounded Mac `do_patch` gate passed 104/104 tasks without patch-fuzz QA failure.

- FLR-0112: QMP-only画像の色・輪郭・領域分析で、黒い3D geometryと無描画を分離する。
- FLR-0016: BitBake preflight中のMACHINE/conf/cache identityを確認する（Waiting、manifest provenance UNKNOWN）。
- FLR-0017: legacy `docs/mac-qemu.md`のexplicit launch/readiness/crash evidenceをQEMU observerへ移す。
- FLR-0018: current QEMU app-launch evidenceを固定Execution runbookへ移す。
- FLR-0019: pseudo/tar packagecopy failureを切り分け、成果物ができた場合のみscp/QEMUへ進む。
- FLR-0030: symbol mappingは完了。core/debug-lineが無い理由と、faultがLLVMへの不正な着地かどうかはFLR-0031以降で必要に応じて追跡する。
- FLR-0031: ライト1/2個ではQMP実3D、13個ではHUD-only。3〜12個の閾値探索をFLR-0032へ分割。
- FLR-0032: prefix 1〜5個ではQMP実3D、6〜13個ではHUD-only。GUID `136` 固有か集約resourceかの比較をFLR-0033へ分割。
- FLR-0033: 同じ6灯でGUID136をGUID138へ置換するとHUD-onlyからQMP実3Dへ戻ることを確認。原因フィールド／下流操作の特定をFLR-0034へ分割。
- FLR-0034: GUID136/138の実効Light値を比較し、type・強度・flags等は一致、positionのみ差分と確認。position対identityの比較をFLR-0035へ分割。
- FLR-0035: 両方のposition overrideでQMP実3Dに戻ることを確認し、position値単独では説明できないためsetter/timing比較をFLR-0036へ分割。
- FLR-0036: same-value setterはHUD-only、未変更baselineの18秒/43秒も同一HUD-only。setter単独・単純なcapture timingを棄却し、重複位置の一般化をFLR-0037へ分割。
- FLR-0037: GUID136をGUID138位置、GUID134位置、非重複の新規位置へ変更した3 variantが同一のQMP 3D pixelsを示し、重複自体を棄却。changed-position setterのidentity比較をFLR-0038へ分割。
- FLR-0038: GUID138だけを新規位置へ変更したvariantは、Present成功・faultなしでもHUD-only。GUID136固有のchanged-position経路のnative operation追跡をFLR-0039へ分割。
 - FLR-0039: static source traceでGUID138がlight limit 6の未選択項目であることを特定。selected GUID134とGUID136を比較するFLR-0040へ分割。
 - FLR-0040: selected GUID134を新規positionへ変更してもHUD-only。native entity/resource/render-list traceをFLR-0041へ分割。
 - FLR-0041: GUID134/GUID136ともFilament native state・Scene登録は正常だがQMPはHUD-only。render/frame/present/Wayland境界をFLR-0042へ分割。
 - FLR-0042: 自作Filament cubeのnative render/present/QMP画素と、SHM mockのWayland child composition/QMP画素を確認。production scene setupの切り分けをFLR-0043へ分割。
- FLR-0043: production Sceneでshape setupをskipすると自作cubeがQMP実画素で表示されることを確認し、実GLB/shape経路をFLR-0044へ分割。
- FLR-0044: 過去成功条件のshape-onlyでproduction shape群をQMP実画素化し、full model/light/environmentをFLR-0045へ分割。
- FLR-0045: `sequoia_ngp.glb`をmodel limit=1で選択し、environment/lights skip条件のQMP実画素を確認。model+lights共存をFLR-0046へ分割。
- FLR-0046: model=1・environment skipでlight prefixを比較し、8灯はGLB画素、9灯（GUID 162追加）はHUD-only。GUID identity分離をFLR-0047へ分割。
- FLR-0047: GUID 162を除外してGUID 164で9灯枠を埋めてもHUD-only。GUID 162単独原因を棄却し、count/native state比較をFLR-0048へ分割。
- FLR-0048: 9灯境界をnative light stateで比較し、shadow-caster無効化でもHUD-onlyだったため、shadow単独仮説を棄却。production modelの描画境界とscene遷移をFLR-0049へ分割。
- FLR-0049: production model-only QMPでSequoiaの実3D画素とscene-addを確認。Flutter親alphaとframe-loopは別境界としてFLR-0050へ分割。
- FLR-0052: canonical clone・linked worktree・artifact境界を整理し、meta-fluorite-trialだけから同じ検証入力を再現できるか確認する。
- FLR-0057: production lit 3Dのlight count/identity boundaryとRadar/Planetarium route/inputをFLR-0050から分割する。
- FLR-0058: FLR-0057でlight count単独を棄却したため、model追加後のFRAME_BEGIN停止と未リンクFenceの因果を、現行イメージのQMP証拠で切り分ける。
- FLR-0059: FLR-0058で回復したframe条件を使い、current imageのnative surface placementとFlutter親の可視性をQMPで分離する。
- FLR-0060: FLR-0059でsurface placement単独を棄却したため、既存のshape/light suppression controlsを使ってproduction shaded draw/resourceの最初の発散をQMPで分離する。
- FLR-0061: owner-isolated shape-positive/full-negativeを再現し、full shadedがpipeline/draw/submit/presentまで進む一方QMP/readback結果が黒または未発生であることを記録。出力ターゲット境界をFLR-0062へ分割。
- FLR-0062: FLR-0061でdraw/pipeline/submit/present到達を確認し、最新QMPで2D HUD＋中央3D黒とtarget traceを記録。corrected 49089baの重複toggle整理はMini app do_patch/full imageを通過したが、0175は`TARGET_PROBE_QUEUE_IDLE_BEGIN`で停止し、gdbでもlavapipe/llvmpipe待機を確認。light単独のデグレとは断定せず、次はMac Devtoolで非ブロッキング診断を作る。
- FLR-0063: FLR-0062のQMP再実行で、証拠ディレクトリ名が長い場合にsocket path長制限でstart/qmp-quitが失敗した。短いrun directoryを使えば同じQEMUは起動・QMP capture・cleanupできるため、再発防止を独立ticket化する。
- FLR-0034: GUID136/138の実効Light値を比較し、type・強度・flags等は一致、positionのみ差分と確認。position対identityの比較をFLR-0035へ分割。
- FLR-0020: `/AGL/trout` に依存しない fixed-manifest workspace bootstrap を設計する。
- FLR-0021: `meta-vulkan` add-layer有無ではなく、fixed manifestとactive meta-flutter layer topologyの不一致を比較する。

- MCP explainability contractをdomain payloadと混ぜずに運用する。

- `meta-agl/scripts/aglsetup.sh`のlocal変更の必要性を特定する。
- qemux86-64の`libLLVM.so.18.1` SIGSEGVを再現し、TCG/LLVM/threadingの仮説を比較する。
- qemuarm64のMesa/Vulkan/virtio-gpu package構成を確認する。
- Flutter EngineとFilamentが同一window、別surface、external textureのどれで合成されるか特定する。

## Done

- 2026-09-28: [FLR-0342](work/tickets/FLR-0342-inspect-mesa-pending-wait-binary.md) — bounded static correction: exact runtime ELF/disassembly and the Mesa 24.0.7 archive place `cnd_wait` before the `VK_SYNC_WAIT_PENDING` test. Downstream patch provenance and actual sync field values remain UNKNOWN; FLR-0343 owns the one-run producer-state observation.
- 2026-09-28: [FLR-0339](work/tickets/FLR-0339-capture-vulkan-present-stall-stack.md) — same-image production run reproduced Present-enter/no-return and recorded 19 draw-end/native commits. QMP-only screenshot and eight-frame replay show HUD/metrics/Scenes with 768,000 uniformly black lower-ROI pixels. A 20-second GDB attach listed 38 threads and partially captured LWP 718 in Mesa `lvp_pipe_sync_wait`; caller frames and semaphore identity remain UNKNOWN. App/QMP teardown passed; no patch/build.
- 2026-09-28: [FLR-0338](work/tickets/FLR-0338-capture-isordered-offset-context.md) — exact-image GDB hardware breakpoint armed at the runtime address for `libLLVM.so.18.1+0xb1d541`, with no hit during the bounded 45-second window. QMP run 0003 shows HUD/metrics/Scenes and a uniformly black lower 768,000-pixel ROI; 19 draw-end/native commits and one Present-enter/no-return were logged. The 8-frame QMP replay is retained; exact app/QMP cleanup passed. Root cause and link between this address and the Present stall remain UNKNOWN; FLR-0339 owns the present-stall stack snapshot.
- 2026-09-28: [FLR-0337](work/tickets/FLR-0337-capture-user-and-kernel-fault-trace.md) — combined user/kernel fault trace matched TID 703, IP, and address between `page_fault_user` and the following FEngine Oops. QMP proves 2D HUD visible and the lower 3D ROI uniformly black; Sequoia asset/emissive binding reached ready/applied. App/QMP cleanup passed. Root cause and relation to missing present return remain UNKNOWN; FLR-0338 owns the pre-instruction hardware-breakpoint test.

- 2026-09-13: [FLR-0125](work/tickets/FLR-0125-trace-viewtarget-entry-path.md) —
  identified and fixed the request-before-ECS-initialization race through the
  official Mac Devtool path. The canonical patch, bundle, Mini build, native
  geometry/present markers, early/late QMP captures, eight-frame QMP sample,
  and negotiated clean teardown all passed. The fixed central region contained
  `111758` visible blue-geometry pixels; Dart and production-scene validation
  remain separate.

- 2026-09-13: [FLR-0116](work/tickets/FLR-0116-flutter-auto-material-variant-crash.md) —
  official Mac Devtool COLOR compatibility patch was built through the fixed
  Mini bundle flow; one QMP-only run proved that `flutter-auto` survives and
  the 2D HUD is visible. The HUD-excluded central 3D region remained uniform
  black, and the environment-only fixture attempt was rejected as invalid;
  FLR-0118 owns the valid Dart fixture control.

- 2026-09-13: [FLR-0117](work/tickets/FLR-0117-bundle-linked-worktree-receiver.md) — fixed the
  bundle receiver helper to validate Git worktrees through `rev-parse`, so the
  fixed Mini linked worktree is accepted. The already-transferred bundle was
  replayed successfully with full SHA validation and the receiver reached the
  exact `93b91ea2` tip; short SHAs now fail fast before remote access.

- 2026-09-12: [FLR-0099](work/tickets/FLR-0099-draw-to-native-output-boundary.md) — paired fixture/production QMP evidence isolated the first observed divergence to the production `vkQueuePresentKHR` return boundary. Fixture returned `result=0` and produced native pixels; production reached visible-target draw and present enter but remained HUD-only without a return. QMP teardown and residual checks passed; runtime ownership is split to FLR-0100.

- 2026-09-12: [FLR-0100](work/tickets/FLR-0100-vk-present-return-boundary.md) — current-image retry reproduced a userspace page fault in `FEngine::loop` after queue-present entry, consistent with the directly mapped `libLLVM.so.18.1` / `llvm::CmpInst::isOrdered` boundary. The first oversized GDB collection and a local extraction typo were retained as failed invocations; QMP teardown and residual cleanup passed. FLR-0101 owns one-variable production-input isolation; no source fix was claimed.

- 2026-09-12: [FLR-0103](work/tickets/FLR-0103-trace-post-scene-vulkan-present-boundary.md) — one-QEMU production GDB evidence on the FLR-0104 debug image kept the 2D HUD visible and native 3D black, reproduced the `FEngine::loop` kernel OOPS, and mapped RIP to `libLLVM.so.18.1` / `llvm::CmpInst::isOrdered` at file offset `0xb1d541`. The standard batch client did not receive a normal signal stop; a later guest `addr2line` caused a separate OOM/SIGKILL. QMP teardown and residual checks passed. FLR-0106 owns the deeper bounded caller capture; no source fix was claimed.

- 2026-09-12: [FLR-0105](work/tickets/FLR-0105-gdb-breakpoint-ownership.md) — one-QEMU breakpoint-only GDB evidence captured a normal `isOrdered` entry and the LLVM InstCombine chain through `InstCombinePass::run`; a later OOPS landed at `isOrdered+1` in another `FEngine::loop` thread. QMP showed HUD-only output (`0/223200` native, `1250/100000` HUD), QMP teardown and residual checks passed, and FLR-0106 owns the outer-producer capture.

- 2026-09-12: [FLR-0098](work/tickets/FLR-0098-current-image-frame-skip-ab.md) — current-image A/B proved the existing unlinked-fence-ready control changes production from repeated `FRAME_BEGIN started=false`/timeout to successful frame begin/end and draw-target setup, but native pixels remain `0/223200` while HUD remains active. QMP evidence and cleanup passed; draw-to-native-output is split to FLR-0099.

- 2026-09-12: [FLR-0097](work/tickets/FLR-0097-post-pipeline-render-boundary.md) — paired current-image QMP evidence showed the fixture reached `TARGET_DRAW2`/submit/present and changed `41,750/223,200` native pixels, while production had valid scene/resource state but stopped at `FRAME_BEGIN started=false` with `0/223,200` native pixels. The initial host/guest log-summary invocation error was corrected and QMP cleanup passed. FLR-0098 rechecks the existing frame-skip recovery control.

- 2026-09-12: [FLR-0096](work/tickets/FLR-0096-production-pipeline-runtime-snapshot.md) — bounded production runtime evidence proved that the fourth software-Vulkan pipeline create eventually returned `result=0` after about 21.4 seconds, followed by successful creates 5 and 6; GDB/strace showed llvmpipe/futex/epoll waits, while late QMP remained HUD-only (`0/223200` native). QMP teardown and residual cleanup passed. Post-pipeline render/resource state is split to FLR-0097.

- 2026-09-12: [FLR-0091](work/tickets/FLR-0091-isolate-first-unfinished-command.md) — valid production and self-made fixture QMP traces isolated the production-only stop to `vkCreateGraphicsPipelines`; fixture reached native pixels, and QMP teardown/cleanup passed. FLR-0093 owns pipeline-input and blocked-worker diagnosis.

- 2026-09-12: [FLR-0093](work/tickets/FLR-0093-isolate-production-pipeline-create.md) — Mac Devtool-generated neutral pipeline-input tracing was built into the authoritative Mini image; six production pipeline creates returned successfully, but QMP still showed HUD-only output (`0/223200` native, `1236/100000` HUD). The permanent-create-stall hypothesis is rejected; the later fence/present boundary remains open.

- 2026-09-12: [FLR-0092](work/tickets/FLR-0092-retire-stale-legacy-worktree.md) — pruned four stale local Git worktree registrations pointing to deleted temporary directories; historical FLR-0026 source branches and records remain read-only provenance.

- 2026-09-11: [FLR-0085](work/tickets/FLR-0085-retire-legacy-receiver-artifacts.md) — 旧`FLR0026` receiver証拠ディレクトリとbundleを中立アーカイブへ退避し、固定receiver/inboxを現行の受け口として明文化した。履歴ticket・旧パッチは再現性のため変更していない。
- 2026-09-11: [FLR-0082](work/tickets/FLR-0082-podman-bounded-status.md) — bounded the Podman status probe; two calls reused one existing container and bind contract without scanning the persistent downloads tree.
- 2026-09-11: [FLR-0083](work/tickets/FLR-0083-current-image-command-stream-boundary.md) — current-image p17 isolated the first observed boundary to producer queue flush versus driver-thread consumer entry; no product fix was claimed.

- 2026-09-09: [FLR-0052](work/tickets/FLR-0052-canonical-repository-reproducibility.md) — canonical receiver handoff, flutter-auto do_patch/do_compile, full agl-ivi-image-flutter build, and fresh QMP 2D baseline completed; native 3D remains in FLR-0050.
- 2026-09-09: [FLR-0054](work/tickets/FLR-0054-podman-bundle-handoff-simplification.md) — canonical Podman mount permission checks and one-command self-contained active bundle handoff were implemented and verified twice with stable SHA-256 and fixed receiver reuse.
- 2026-09-09: [FLR-0055](work/tickets/FLR-0055-tps-bounded-qemu-harness.md) — opened to automate bounded QEMU startup, QMP teardown, serial synchronization, and minimal evidence summaries after repeated manual-loop failures.
- 2026-09-11: [FLR-0066](work/tickets/FLR-0066-compare-historical-production-3d-stack.md) — current image reproduced the historical model-only Sequoia pixels and the controlled 2D+diagnostic-3D path; no generic latest-patch regression was found.
- 2026-09-11: [FLR-0068](work/tickets/FLR-0068-isolate-explicit-light-count.md) — one selected explicit light (`guid=126`, `POINT`) reproduced the black production 3D target under fixed default-indirect/skybox-skipped conditions; QMP and cleanup evidence passed. Identity-specific behavior is split to FLR-0069.
- 2026-09-11: [FLR-0069](work/tickets/FLR-0069-compare-alternate-single-light.md) — excluding `guid=126` and selecting `guid=128` alone reproduced the same black target, so the first-light identity hypothesis was falsified. Operation tracing is split to FLR-0070.
- 2026-09-11: [FLR-0070](work/tickets/FLR-0070-trace-explicit-light-operation.md) — native light state was valid after `BuildLightAndAddToScene`; the same one-light profile was black without the trace and QMP-visible with it, so trace timing/side effect is the next boundary. QMP teardown was clean.
- 2026-09-11: [FLR-0076](work/tickets/FLR-0076-isolate-surface-extent-composition.md) — current-image QMP controls proved that the self-made cube and 2D HUD can render together and that the production Sequoia model can render alone; surface extent mismatch is not the sole cause of the full-scene black result. FLR-0077 owns the remaining shaded resource/light boundary.
- 2026-09-06: [FLR-0027](work/tickets/FLR-0027-shape-light-rendering-separation.md) — shape-onlyでQMP実3D pixel、light-onlyでpresent/commit境界を確認し、production共存をFLR-0028へ分割。
- 2026-09-06: [FLR-0028](work/tickets/FLR-0028-production-shape-light-coenabled.md) — shape+light共存で37 shapeのrenderableとpresent直前まで確認し、FEngine page faultをFLR-0029へ分割。
- 2026-09-06: [FLR-0029](work/tickets/FLR-0029-present-boundary-page-fault.md) — 同じFEngine page faultを再現し、guestのGDB/eu-stack/coredumpctl経路を確認。symbol/core採取をFLR-0030へ分割。
- 2026-09-06: [FLR-0030](work/tickets/FLR-0030-present-boundary-fault-capture.md) — attach前後のmaps、GDB、`eu-addr2line`、Mini PC側の`nm/objdump`でfault RIPを`libLLVM.so.18.1`の`llvm::CmpInst::isOrdered`付近へ写像。QMP画面はHUD-onlyで3D未達。次の最小trigger検証をFLR-0031へ分割。
- 2026-09-06: [FLR-0031](work/tickets/FLR-0031-isolate-lit-light-trigger.md) — Mac Devtool由来の診断selectorをMini PCでbuildし、ライト1/2個のQMP実3Dと13個のHUD-onlyを同一rootfsで比較。未検証3〜12個の探索をFLR-0032へ分割。
- 2026-09-06: [FLR-0032](work/tickets/FLR-0032-locate-light-count-divergence.md) — ライト4/5個のQMP実3Dと6/7個のHUD-onlyを比較し、prefix境界を5→6へ確定。同数別選択の比較をFLR-0033へ分割。
- 2026-09-06: [FLR-0033](work/tickets/FLR-0033-isolate-sixth-light.md) — 同じ6灯でGUID136選択時はHUD-only、GUID136除外・GUID138選択時はQMP実3Dとなることを確認。恒久修正の特定をFLR-0034へ分割。
- 2026-09-06: [FLR-0035](work/tickets/FLR-0035-isolate-light-position-vs-identity.md) — GUID136/138のpositionを相互に揃えた両variantでQMP実3Dを確認。setter/timingの比較をFLR-0036へ分割。
- 2026-09-06: [FLR-0036](work/tickets/FLR-0036-isolate-light-setter-timing.md) — same-value setterと未変更baselineの遅延QMPを比較し、いずれもHUD-only。setter単独・単純なcapture timingを切り分け、重複位置の一般化をFLR-0037へ分割。
- 2026-09-06: [FLR-0037](work/tickets/FLR-0037-isolate-duplicate-light-position.md) — duplicate 2種とchanged-but-nonduplicate 1種が同一QMP 3D pixelsを示し、重複自体ではなくchanged position mutationを特定。GUID別比較をFLR-0038へ分割。
- 2026-09-07: [FLR-0038](work/tickets/FLR-0038-isolate-changed-light-position-setter.md) — GUID138変更variantを同一profileで比較し、GUID136固有のchanged-position経路を示唆。native operation/entity/resource追跡をFLR-0039へ分割。
 - 2026-09-07: [FLR-0039](work/tickets/FLR-0039-trace-changed-light-native-operation.md) — GUID138が未選択だったことをstatic source traceで特定。正しいselected GUID比較をFLR-0040へ分割。
 - 2026-09-07: [FLR-0040](work/tickets/FLR-0040-compare-selected-changed-light-setter.md) — selected GUID134を新規positionへ変更してもHUD-onlyであることをQMP写真とruntime logで確認。native entity/resource/render-list traceをFLR-0041へ分割。
 - 2026-09-07: [FLR-0041](work/tickets/FLR-0041-trace-selected-light-native-resource.md) — GUID134/GUID136のFilament native state・Scene登録をQMP写真とruntime logで確認。render/frame/present/Wayland境界をFLR-0042へ分割。
 - 2026-09-07: [FLR-0042](work/tickets/FLR-0042-trace-render-frame-present-boundary.md) — 自作Filament cubeの実画素、Vulkan present result、SHM child compositionをQMP写真とruntime markerで確認。production scene setupをFLR-0043へ分割。
 - 2026-09-07: [FLR-0043](work/tickets/FLR-0043-production-scene-visible-3d.md) — production Scene内の自作cubeをshape skip条件でQMP実画素化し、shape/render pathをFLR-0044へ分割。
- 2026-09-07: [FLR-0044](work/tickets/FLR-0044-production-shapes-visible-3d.md) — 過去成功条件でproduction shape群をQMP実画素化し、full model/light/environmentをFLR-0045へ分割。
- 2026-09-08: [FLR-0048](work/tickets/FLR-0048-isolate-light-count-vs-identity.md) — 8灯/9灯のnative stateとreplacementを比較し、shadow-caster無効化でも復帰しないことをQMPで確認。production modelのscene追加後境界をFLR-0049へ分割。
- 2026-09-06: [FLR-0034](work/tickets/FLR-0034-identify-light136-production-fix.md) — GUID136/138のruntime Light値を比較し、type・強度・flags等は一致、positionのみ差分と確認。position対identityの比較をFLR-0035へ分割。

- 2026-07-19: mini PCの読み取り専用baseline調査。
- 2026-07-19: Macとmini PCのclone location/origin/HEAD確認。
- 2026-07-19: foundationをrole metadata commitへ固定し、fresh clone gate後にdev/feature refsをremoteへ配布。

## Someday / Maybe

- build開始・停止を扱うwrite-capable MCP。read-only MCPが安定してから検討する。
- Raspberry Pi実機の自動電源制御、serial console、screen capture連携。
| [FLR-0252](work/tickets/FLR-0252-verify-production-planetarium-3d.md) | verify production Planetarium/Sequoia 3D visibility from the restored control image | Done: current e876 baseline reaches production asset/Scene/draw/present markers but guest OOM kills flutter-auto before stable 3D or input | FLR-0272 owns production asset/Scene OOM diagnosis |
