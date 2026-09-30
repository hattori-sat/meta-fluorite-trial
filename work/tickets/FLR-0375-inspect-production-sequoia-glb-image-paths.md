# FLR-0375 — inspect the production Sequoia GLB image references

- Status: Done
- Priority: High
- Owner: candidate-image package inspection / Filament GLB asset roles
- Created: 2026-09-30
- Predecessor: [FLR-0374 present/Oops evidence](FLR-0374-preserve-manual-present-oops-evidence.md)
- Branch: `feature-flr-0375-sequoia-glb-path-check` (local, no push)
- Working log: [FLR-0375 working log](../logs/2026-09-30-flr0375.md)
- Candidate rootfs SHA-256:
  `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`.

## Objective

Determine whether the exact candidate image's production
`assets/models/sequoia_ngp.glb` contains missing external image paths or
whether the texture inputs are embedded/present. Use read-only inspection of
the existing rootfs and inspect only this model's bounded metadata. This is a
static discriminator before another patch/build/runtime loop; it is not a
rendering fix.

## Facts

- FLR-0374's manual app log shows the installed Example Demo reading
  `assets/models/sequoia_ngp.glb`. Emissive texture index 6 becomes ready and
  is applied, but that does not prove every image reference resolves or any
  texture is sampled.
- The current QMP frame has no recognizable vehicle or HUD; the same candidate
  image previously showed a self-made colored LIT/SUN fixture and HUD in
  FLR-0371. Therefore a global inability to compose 2D+3D is not the leading
  hypothesis.
- FLR-0374 also records 28 informational material-default messages for
  `emissive`, `reflectance`, `uvOffset`, and `uvScale`. Their effect is UNKNOWN.
- FLR-0374 did not transfer a QEMU disk image to Mac. Keep that boundary; the
  only extracted object in this ticket may be the single Sequoia GLB, if
  needed for parsing.
- Candidate rootfs SHA-256 matched exactly. The installed GLB is
  13,671,064 bytes with SHA-256
  `cde9efd067a75c1f5b99b8fb529b5bb4636956193188bd15add3bccc349109ec`.
- GLB v2 declares the exact file length and has JSON+BIN chunks; its one
  buffer and 108 bufferViews are in bounds.
- All 23 images are embedded PNGs referenced through bufferViews. All 23
  passed PNG signature, chunk CRC, IHDR/IDAT/IEND, and deflate checks. There
  are zero external image URIs and zero image/bufferView range errors.
- All 23 texture sources and all 23 material texture references resolve to
  valid image/texture indices; no reference errors were found.

## 4W1H (excluding Why)

| Dimension | Current evidence | Needed discriminator |
| --- | --- | --- |
| What | Top-level Sequoia GLB is read; final pixels are not identifiable | GLB image/texture/material references and their payload form |
| Where | Example Demo 3.32.5 in the exact FLR-0371 candidate rootfs | Exact packaged path and only referenced payloads |
| When | Asset loading occurs before the unmatched second present/Oops | Static package state, independent of the runtime fault |
| Who | Installed Flutter bundle and Filament GLTFIO path | Rootfs file identity and GLB JSON structure |
| How | Read-only `debugfs`/GLB metadata inspection; no mount or rebuild | Bounded report with path-resolution verdict and hashes |

## Hypotheses

1. **External texture-path failure.** The GLB JSON references external image
   URIs absent from the installed bundle. Prediction: at least one URI resolves
   to no packaged file.
2. **Images are embedded/present.** Prediction: image records use GLB buffer
   views or data URIs, with valid bounds and non-empty payloads; this falsifies
   a missing external-path explanation but not runtime binding/sampling.
3. **The GLB is structurally sound but runtime material/camera/render output is
   wrong.** Supported at the static asset boundary: all referenced payloads
   are present, while FLR-0374's no-vehicle/no-HUD QMP result remains. This is
   not proof of which runtime stage fails.

## Scope and success criteria

- Verify the candidate rootfs SHA-256 before reading it. Use the existing
  Mini build artifact and one fresh evidence directory
  `$BUILD_EVIDENCE/flr0375-0001/`; do not create additional temporary roots.
- Use read-only ext4 inspection (for example `debugfs`) to stat the exact
  installed `sequoia_ngp.glb` and, if useful, extract only that single model
  into the run evidence directory. Do not mount the image read-write, modify
  the rootfs, or transfer the rootfs/kernel/QEMU image to Mac.
- Parse the GLB header/JSON chunk and validate buffer lengths, image URI or
  buffer-view source, texture-to-image indices, material texture references,
  and image payload integrity. Do not print or retain image pixel data.
- Record rootfs and GLB hashes, exact package path, bounded parse output, and
  an explicit verdict: external path missing, embedded/present, malformed, or
  UNKNOWN.
- No QEMU, Flutter launch, script edit, source edit, Devtool, BitBake,
  `do_patch`, build, or image change in this ticket.
- This ticket passes when the exact packaged GLB and every referenced image
  source are accounted for, or a precise bounded UNKNOWN/blocker is recorded.
  It does not claim 2D+3D rendering acceptance.

## Impact

- **Build-time:** none.
- **Packaging:** read-only inspection only; no package changes.
- **Runtime:** none.
- **Integration risk:** none if inspection remains read-only; no rootfs mount
  or mutation is allowed.

## Plan / Do / Check / Act

### Plan

1. Run canonical-repository and single-active-ticket checks.
2. On Mini, confirm no build/QEMU activity is needed and verify the candidate
   rootfs hash against this ticket.
3. Read the one installed GLB using a read-only tool; preserve one bounded
   summary under the run evidence directory.
4. Validate its header, JSON length, buffers, image references, texture links,
   and material references. Compare only the relevant facts with FLR-0374's
   `GLTFIO_EMISSIVE` markers.
5. Record which hypothesis the result supports and open a separate next ticket
   only if additional runtime/source work is justified.

### Do

- Verified the exact rootfs hash, then used read-only `debugfs` to extract
  only the installed Sequoia GLB into `$BUILD_EVIDENCE/flr0375-0001/`.
- Validated GLB structure, all 23 embedded PNG payloads, all texture sources,
  and all material texture references. No rootfs mount or mutation, QEMU,
  Flutter, build, Devtool, or script edit occurred.
- An initial `stat` measured the symlink itself (59 bytes); `readlink -f` and
  `stat -L` corrected the measurement to the image target. The first parser
  pass checked PNG signatures and bounds only; a second pass checked CRC and
  deflate for every image. Only the verified second pass is used for verdict.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Canonical repository / active ticket | Guard passes; FLR-0375 sole active | PASS | PASS |
| Candidate identity | Exact rootfs hash matches FLR-0371/0374 | `949921c8…` exact match | PASS |
| GLB structure | Valid header and bounded JSON | GLB2/file length/chunks valid; 108 bufferViews, zero range errors | PASS |
| Image references | Every referenced image is embedded or resolves to a packaged file | 23 embedded PNGs validated; 0 external URIs; all 23 texture/material references valid | PASS |
| Scope | No image/build/runtime mutation | One read-only GLB extraction; no QEMU, build, patch, or script changes | PASS |

### Act

- Missing external texture files are falsified for this exact packaged GLB.
  Do not add a path patch. Runtime sampling remains unproven.
- Open FLR-0376 to replay Flutter manually with the known-good explicit
  `agl-driver` Wayland session environment; FLR-0374 did not record that
  environment contract. Keep all launcher scripts unchanged until the manual
  invocation produces a successful observable screen.

## UNKNOWN

- Whether texture coordinates and material instances sample those images at
  runtime.
- Whether active camera 12 frames the production vehicle; this is outside the
  static asset verdict.
