# FLR-0370 — trace native fixture material-color dataflow

- Status: Done
- Priority: High
- Owner: Filament fixture source / Yocto patch-stack / material API roles
- Created: 2026-09-30
- Predecessor: [FLR-0369 LIT constant-color runtime control](FLR-0369-lit-hardcoded-material-control.md)
- Branch: `feature-flr-0370-trace-fixture-material-color-dataflow` (local continuation of the verified runtime baseline; no push)
- Working log: [FLR-0370 working log](../logs/2026-09-30-flr0370.md)

## Objective

Explain the measured mode interaction: `materialParams.color` is visible in
UNLIT (FLR-0368), black in LIT/SUN (FLR-0367), while constant blue is visible
in LIT/SUN (FLR-0369). Trace the actual source/API and recipe patch ordering,
including the active MaterialInstance setter and coupled LIT/SUN switch, using
the existing Devtool/Filament source already available. This is a read-only
diagnosis: no source, recipe, patch, image, or launch script changes; no build
or QEMU run.

## Facts

- FLR-0367 current-image LIT used `hardcoded=false source=parameter` and
  produced zero native ROI pixels despite HUD and successful draw/present.
- FLR-0369 held the current rootfs, LIT/SUN fixture, geometry, camera, and
  launch profile fixed; adding only
  `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR=1` selected
  `hardcoded=true shading=lit source=constant` and produced 119,716 chromatic
  native pixels plus 2,845 chromatic HUD pixels.
- FLR-0368 showed `hardcoded=false shading=unlit source=parameter` with
  119,716 visible native chromatic pixels and the same HUD pixel count. The
  parameter setter is therefore not globally absent or ineffective.
- The current `flutter-auto_2.0.bbappend` orders patches 0248, 0249, 0250,
  0251, and later 0295. Patch 0248 changes assignment to the created active
  MaterialInstance; 0249 adds the constant/parameter source split; 0295 couples
  LIT shading and SUN creation behind one environment flag.
- FLR-0153/0154 record older setter/constant-source trials; they must be
  interpreted with their older camera/source/image revisions. In particular,
  the later 0251 camera-projection correction is applied after 0249 in the
  current recipe stack.
- Patch 0167 declares `color` as `FLOAT3`, sets a default value on the Material,
  then creates an instance. Patch 0248 changes that order to create the active
  `MaterialInstance` first and call its `setParameter("color", LINEAR, float3)`;
  the Renderable binds that same instance. The runtime UNLIT positive control
  confirms this parameter route can produce visible pixels on the current
  image.
- Patch 0249 changes two things between branches: the constant source writes
  `material.baseColor.rgb = vec3(0.05, 0.45, 1.0)`, while the parameter source
  writes `material.baseColor = vec4(materialParams.color, 1.0)`. The parameter
  declaration remains `FLOAT3`. Therefore FLR-0369 changed both source and
  assignment form relative to FLR-0367; the exact assignment form was not yet
  isolated.
- Patch 0251 restores the local fixture camera projection. Patch 0295 uses one
  `FLUORITE_NATIVE_FIXTURE_LIGHT` flag for both LIT material shading and SUN
  creation, so the current LIT/SUN controls do not isolate those two effects.
- The FLR-0369 app exited before its intentional PID stop. Its QMP evidence is
  valid, but the exit cause remains UNKNOWN and is not part of this source
  trace.
- Read-only inspection of the existing Podman container showed it is running,
  but the persistent source directories currently have no `view_target.cc`;
  `fluorite-plugins/.git/HEAD` is absent, and no matching file was found in the
  existing source or attic trees. No state was repaired or recreated. This
  conflicts with the complete-source checkpoint recorded by FLR-0208; the
  reason for the current missing worktree contents is UNKNOWN.

## Hypotheses

1. The differing GLSL assignment form is decisive: RGB-only assignment with
   the parameter may render under LIT/SUN. Prediction: changing only the
   parameter branch to `.baseColor.rgb = materialParams.color` makes the
   native ROI visible. This is untested, not a root-cause claim.
2. LIT-specific parameter binding or generated shader behavior is the cause.
   Prediction: RGB-only parameter assignment remains black while the existing
   constant-color LIT control remains visible.
3. The light itself contributes to the failure. Prediction: separating
   `Shading::LIT` from SUN creation changes the result; current controls cannot
   test this because patch 0295 couples them.

## Procedure / success criteria

- Reconfirm canonical repository and sole active ticket; preserve the current
  committed patch stack.
- Read the `flutter-auto` recipe/bbappend patch ordering and inspect the
  relevant hunks in 0167, 0248–0251, and 0295 plus FLR-0153/0154 history.
- Locate the current persistent Devtool source if already mounted, then trace
  in order: `MaterialBuilder` source and parameter declaration → material build
  result → material instance creation → color setter/default value → renderable
  binding. Compare function/API signatures with the Filament source present in
  that checkout; do not fetch new source or start a build.
- Report exact file/patch lines, the parameter-source behavior across
  UNLIT/LIT, the coupled shading/light behavior, revisions of earlier tests,
  and the first proven mismatch (or UNKNOWN if source cannot prove it).
- Do not edit source, recipes, patches, scripts, image, or evidence in this
  diagnostic ticket. If a concrete code fix is justified, open a separate
  implementation ticket using the existing Mac Devtool workflow.

## Impact

- Build-time, packaging, and runtime: none; read-only.
- Integration risk: none in this ticket.

## Plan / Do / Check / Act

### Plan

Use the three current-image runtime controls as the outcome boundary; trace
source ownership before another QEMU loop or any patch. Compare the LIT-specific
parameter interaction and the coupled LIT/SUN behavior against the actual patch
stack and API source.

### Do

- Read the `flutter-auto_2.0.bbappend` registrations and patches 0167,
  0248–0251, and 0295. Confirmed the active-instance setter, the two distinct
  shader assignments, the projection correction, and the combined LIT/SUN
  flag.
- Checked the existing Podman container and its persistent `sources` and
  `attic` paths read-only. The container was running; no `view_target.cc` was
  present, and the `fluorite-plugins/.git` directory had no `HEAD`. No Devtool,
  source, build, or QEMU operation was performed.
- Requested judgment-only review from Astra; recommendation was to isolate
  the parameter branch's RGB-only assignment before changing the light,
  setter, camera, geometry, or runtime launcher.

### Check

| Gate | Actual | Result |
| --- | --- | --- |
| Canonical repository / one active ticket | Canonical guard passed in the FLR worktree; FLR-0370 was the sole active ticket | PASS |
| Recipe patch order | 0248–0251 and 0295 registration confirmed in `flutter-auto_2.0.bbappend` | PASS |
| Parameter declaration → value → instance → renderable | Layer history identifies the current patch contract; current persistent source checkout is absent, so current API signature revalidation is UNKNOWN | PARTIAL — limitation recorded |
| Evidence-backed next action | 0249 changes source and assignment form together; RGB-only parameter assignment is the smallest next discriminator | PASS |
| Scope / mutation boundary | No source, recipe, patch, image, build, or QEMU mutation | PASS |

### Act

- Close this bounded static diagnosis without claiming the runtime root cause.
  FLR-0371 owns one Devtool-generated change to the parameter expression's
  assignment form, followed by a Mini build and direct-SSH/manual-Flutter QMP
  evaluation. Recreate the source only through official Devtool using the
  current recipe patch stack; do not handcraft or repair a source Git history.
- Keep LIT/SUN, setter, parameter value, geometry, camera, and manual launch
  fixed in FLR-0371. Do not edit the app/QEMU launch script.
- Production Sequoia same-frame acceptance remains open.

## UNKNOWN

- Exact current-source/API reason the parameter-source LIT/SUN variant is black;
  the source checkout is currently unavailable for direct API validation.
- Whether RGB-only parameter assignment restores LIT pixels.
- Why the FLR-0369 app process exited before the intentional stop.
- Whether production Sequoia is correctly visible in the same frame as HUD.

## Visual evidence

- [FLR-0367 QMP frame](../evidence/FLR-0367-qmp-run-0001.png): HUD visible;
  LIT/SUN plus parameter-source native ROI black.
- [FLR-0368 QMP frame](../evidence/FLR-0368-qmp-run-0001.png): HUD and blue
  UNLIT parameter-source geometry visible together.
- [FLR-0369 QMP frame](../evidence/FLR-0369-qmp-run-0001.png): HUD and dark-blue
  LIT/SUN constant-source geometry visible together.
- Whether the Devtool source and Mini image revisions match the expected
  patches unless manifests and source commits verify it.
