#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SCRIPT="$ROOT/scripts/run-mini-recipe-patch-gate.sh"

test -x "$SCRIPT"
bash -n "$SCRIPT"
grep -Fq 'BUILD_HOST BUILD_RECEIVER BUILD_DIR BUILD_TMPDIR' "$SCRIPT"
grep -Fq 'BUILD_AGL_ROOT' "$SCRIPT"
grep -Fq 'assert-canonical-repository.sh' "$SCRIPT"
grep -Fq 'fixed receiver has non-evidence changes' "$SCRIPT"
grep -Fq 'TMPDIR = \"$tmpdir\"' "$SCRIPT"
grep -Fq 'an existing BitBake process is active' "$SCRIPT"
grep -Fq 'bitbake -e "$recipe"' "$SCRIPT"
grep -Fq 'bitbake -f -c clean "$recipe"' "$SCRIPT"
grep -Fq 'bitbake -f -c do_patch "$recipe"' "$SCRIPT"
grep -Fq 'workdir-reset=PASS mode=recipe-clean' "$SCRIPT"
grep -Fq 'workdir-reset=FAIL rc=$clean_rc' "$SCRIPT"
grep -Fq '^Applying patch |^patching file |^Hunk ' "$SCRIPT"
grep -Fq 'ERROR: Logfile of failure stored in:' "$SCRIPT"
grep -Fq 'failing-patch=' "$SCRIPT"
grep -Fq 'path "*/$recipe/*"' "$SCRIPT"
! grep -Fq 'find "$tmpdir/work" -type f -name '\''log.do_patch.*'\'' -print' "$SCRIPT"
grep -Fq 'do_patch=FAIL rc=$patch_rc' "$SCRIPT"
grep -Fq 'task-log=UNKNOWN' "$SCRIPT"
grep -Fq 'shown >= 80' "$SCRIPT"
grep -Fq 'agl-ivi-image-*|core-image-*' "$SCRIPT"
grep -Fq 'exit "$patch_rc"' "$SCRIPT"
echo 'PASS: Mini recipe patch gate contract'
