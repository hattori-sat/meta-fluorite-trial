#!/usr/bin/env bash
set -euo pipefail

# This is a pre-commit gate: every non-ignored candidate must already be in the
# index so the command checks the exact snapshot that will be committed.
if test -n "$(git ls-files --others --exclude-standard)"; then
    echo "staged whitespace check: FAIL (non-ignored untracked candidates remain)" >&2
    exit 1
fi

# Check tracked edits that have not reached the index as well as the index
# snapshot. Captured baseline artifacts are byte-locked to their recorded source
# hashes and are validated separately by tests/test_baseline_artifacts.py.
git diff --check
git diff --cached --check -- . \
    ':(glob,exclude)conf/*/*.template' \
    ':(glob,exclude)layers/meta-fluorite-trial/**' \
    ':(exclude)manifests/agl-trout-fixed.xml' \
    ':(glob,exclude)manifests/local-changes/**'

echo "staged whitespace check: PASS (authored files; byte-locked baseline hash-gated)"
