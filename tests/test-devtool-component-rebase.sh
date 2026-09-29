#!/usr/bin/env bash
set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
helper="$repo_root/scripts/rebase-fluorite-devtool-component.sh"
wrapper="$repo_root/scripts/run-podman-devtool.sh"
refresh="$repo_root/scripts/refresh-project-layer-baseline.py"

test -x "$helper"
test -x "$wrapper"
test -x "$refresh"
bash -n "$helper"
bash -n "$wrapper"
python3 -c 'import ast, pathlib, sys; ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))' "$refresh"

rg -q --fixed-strings 'component-reset' "$helper"
rg -q --fixed-strings 'source-git-ensure-branch' "$helper"
rg -q --fixed-strings 'update-recipe' "$helper"
! rg -q --fixed-strings -- '--force-patch-refresh' "$helper"
rg -q --fixed-strings 'From $source_commit ' "$helper"
rg -q --fixed-strings 'canonical patch copy is not byte-identical' "$helper"
rg -q --fixed-strings -- '--replace-canonical' "$helper"
rg -q --fixed-strings 'canonical-replaced=PASS' "$helper"
rg -q --fixed-strings 'registration_line=' "$helper"
rg -q --fixed-strings 'assert_unique_registration_lines' "$helper"
rg -q --fixed-strings 'canonical patch registration has duplicate lines' "$helper"
rg -q --fixed-strings 'baseline-lock=REFRESHED' "$helper"
rg -q --fixed-strings '/^mkfifo: cannot create fifo /' "$helper"
rg -q --fixed-strings '/^mount-permission=/' "$helper"
rg -q --fixed-strings '/^## /' "$helper"
rg -q --fixed-strings 'component_recipe=fluorite-plugins' "$helper"
rg -q --fixed-strings 'source path has multiple active Devtool recipes' "$helper"
rg -q --fixed-strings 'target component is registered to a different source path' "$helper"
rg -q --fixed-strings 'workspace_bbappend="$state_root/build/workspace/appends/${recipe}.bbappend"' "$helper"
rg -q --fixed-strings '# initial_rev .: $baseline_commit' "$helper"
! rg -q --fixed-strings -- '--force-patch-refresh "$baseline_commit"' "$helper"
rg -q --fixed-strings 'source-git-ensure-branch' "$wrapper"
rg -q --fixed-strings 'source Git branch points at a different revision' "$wrapper"
printf '%s\n' 'devtool component rebase contract: PASS'
