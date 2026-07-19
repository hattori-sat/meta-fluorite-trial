#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Usage: scripts/run-remote-mcp.sh <agl|yocto|command_runner>" >&2
    exit 2
}

fail() {
    echo "Remote MCP startup: $1" >&2
    exit 1
}

test "$#" -eq 1 || usage
server_id=$1
case "$server_id" in
    agl|yocto|command_runner) ;;
    *) usage ;;
esac

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
role_config=${FLUORITE_MCP_REMOTE_ROLE_CONFIG:-$repository_root/.fluorite-mcp/remote-role.conf}

test -f "$role_config" || fail "local role config is missing"
test ! -L "$role_config" || fail "local role config must not be a symlink"

ssh_alias=
remote_repository=
expected_project_revision=
allow_command_execution=0
seen_ssh_alias=0
seen_remote_repository=0
seen_expected_project_revision=0
seen_allow_command_execution=0

while IFS= read -r line || test -n "$line"; do
    case "$line" in
        ''|'#'*) continue ;;
        *=*) ;;
        *) fail "local role config contains a malformed line" ;;
    esac

    key=${line%%=*}
    value=${line#*=}
    case "$key" in
        ssh_alias)
            test "$seen_ssh_alias" -eq 0 || fail "ssh_alias is duplicated"
            ssh_alias=$value
            seen_ssh_alias=1
            ;;
        remote_repository)
            test "$seen_remote_repository" -eq 0 || fail "remote_repository is duplicated"
            remote_repository=$value
            seen_remote_repository=1
            ;;
        expected_project_revision)
            test "$seen_expected_project_revision" -eq 0 || fail "expected_project_revision is duplicated"
            expected_project_revision=$value
            seen_expected_project_revision=1
            ;;
        allow_command_execution)
            test "$seen_allow_command_execution" -eq 0 || fail "allow_command_execution is duplicated"
            allow_command_execution=$value
            seen_allow_command_execution=1
            ;;
        *) fail "local role config contains an unsupported key" ;;
    esac
done < "$role_config"

test "$seen_ssh_alias" -eq 1 || fail "ssh_alias is required"
test "$seen_remote_repository" -eq 1 || fail "remote_repository is required"
test "$seen_expected_project_revision" -eq 1 || fail "expected_project_revision is required"

if ! [[ "$ssh_alias" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]; then
    fail "ssh_alias must be an SSH config role alias without account or address syntax"
fi

if ! [[ "$remote_repository" =~ ^/[A-Za-z0-9._/-]+$ ]]; then
    fail "remote_repository must be an absolute path using only safe path characters"
fi
case "/$remote_repository/" in
    *'/../'*|*'/./'*) fail "remote_repository must not contain dot traversal" ;;
esac

if ! [[ "$expected_project_revision" =~ ^[0-9a-f]{40}$ ]]; then
    fail "expected_project_revision must be a full lowercase Git commit"
fi

case "$allow_command_execution" in
    0|1) ;;
    *) fail "allow_command_execution must be 0 or 1" ;;
esac
if test "$server_id" != command_runner; then
    allow_command_execution=0
fi

remote_config=$remote_repository/.fluorite-mcp/config.json
remote_command="cd $remote_repository && { test -r $remote_config || { echo 'Remote MCP startup: runtime role config is missing' >&2; exit 1; }; } && bash scripts/assert-canonical-repository.sh >&2 && { test \"\$(git rev-parse HEAD 2>/dev/null)\" = $expected_project_revision || { echo 'Remote MCP startup: project revision mismatch' >&2; exit 1; }; } && { git diff --quiet -- . && git diff --cached --quiet -- . && test -z \"\$(git ls-files --others --exclude-standard)\" || { echo 'Remote MCP startup: project worktree is not clean' >&2; exit 1; }; } && { test -z \"\$(git ls-files --others --ignored --exclude-standard -- 'mcp/**' 'scripts/**' 'runbooks/**' '*.py' '*.pyc' '*.pyo' '*.pyd' '*.so' '*.dylib')\" || { echo 'Remote MCP startup: ignored runtime surface is not clean' >&2; exit 1; }; } && BASH_ENV=/dev/null ENV=/dev/null PYTHON= FLUORITE_MCP_CONFIG=$remote_config PYTHONDONTWRITEBYTECODE=1 FLUORITE_MCP_ALLOW_EXECUTION=$allow_command_execution exec bash scripts/run-mcp.sh $server_id"

exec ssh -T \
    -o BatchMode=yes \
    -o ClearAllForwardings=yes \
    -o PermitLocalCommand=no \
    -o StrictHostKeyChecking=yes \
    -- "$ssh_alias" "$remote_command"
