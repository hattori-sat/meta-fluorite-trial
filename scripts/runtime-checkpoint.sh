#!/bin/sh
set -eu

usage() {
  cat >&2 <<'EOF'
usage:
  runtime-checkpoint.sh new --ticket FLR-NNNN --log work/logs/file.md \
    --iteration N --title TITLE --facts TEXT --inferences TEXT \
    --hypotheses TEXT --unknowns TEXT --decision TEXT --next TEXT [--dry-run]
  runtime-checkpoint.sh verify --ticket FLR-NNNN --log work/logs/file.md
EOF
  exit 2
}

fail() {
  echo "runtime-checkpoint: $*" >&2
  exit 1
}

command_name=${1:-}
[ -n "$command_name" ] || usage
shift

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ticket_id=
log_path=
iteration=
title=checkpoint
facts=
inferences=
hypotheses=
unknowns=
decision=
next_action=
dry_run=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --ticket) ticket_id=${2:-}; shift 2 ;;
    --log) log_path=${2:-}; shift 2 ;;
    --iteration) iteration=${2:-}; shift 2 ;;
    --title) title=${2:-}; shift 2 ;;
    --facts) facts=${2:-}; shift 2 ;;
    --inferences) inferences=${2:-}; shift 2 ;;
    --hypotheses) hypotheses=${2:-}; shift 2 ;;
    --unknowns) unknowns=${2:-}; shift 2 ;;
    --decision) decision=${2:-}; shift 2 ;;
    --next) next_action=${2:-}; shift 2 ;;
    --dry-run) dry_run=true; shift ;;
    *) usage ;;
  esac
done

[ -n "$ticket_id" ] || fail "--ticket is required"
[ -n "$log_path" ] || fail "--log is required"
case "$ticket_id" in
  FLR-[0-9][0-9][0-9][0-9]) ;;
  *) fail "ticket must match FLR-NNNN: $ticket_id" ;;
esac
case "$log_path" in
  work/logs/*.md) ;;
  *) fail "log must be under work/logs and end in .md: $log_path" ;;
esac

ticket_file=$(find "$repo_root/work/tickets" -maxdepth 1 -type f -name "${ticket_id}-*.md" -print | sed -n '1p')
[ -n "$ticket_file" ] || fail "ticket file not found: $ticket_id"
log_file=$repo_root/$log_path
[ -f "$log_file" ] || fail "working log not found: $log_path"

status=$(sed -n 's/^- Status: //p' "$ticket_file" | sed -n '1p')
active_files=$(rg -l --glob 'FLR-*.md' '^- Status: In Progress$' "$repo_root/work/tickets" 2>/dev/null || true)
active_count=$(printf '%s\n' "$active_files" | awk 'NF { count++ } END { print count + 0 }')
[ "$active_count" -eq 1 ] || fail "expected exactly one In Progress ticket, found $active_count"

has_heading() {
  rg -q --fixed-strings "$1" "$2"
}

verify_contract() {
  [ "$status" = "In Progress" ] || [ "$status" = "Waiting" ] || [ "$status" = "Done" ] ||
    fail "unsupported ticket status: $status"
  has_heading '### Facts' "$log_file" || fail "working log has no Facts section"
  has_heading '### Hypotheses' "$log_file" || fail "working log has no Hypotheses section"
  if ! has_heading '### UNKNOWN' "$log_file" && ! has_heading '## Unknowns' "$ticket_file"; then
    fail "ticket/log has no UNKNOWN section"
  fi
  if ! has_heading '### Check' "$log_file" && ! has_heading '### Verification' "$log_file"; then
    fail "working log has no Check or Verification section"
  fi
  if ! has_heading '### Act' "$log_file" && ! has_heading '### Next action' "$log_file"; then
    fail "working log has no Act or Next action section"
  fi
  echo "PASS: checkpoint contract ticket=$ticket_id active=$active_count log=$log_path"
}

case "$command_name" in
  verify)
    verify_contract
    ;;
  new)
    [ "$status" = "In Progress" ] || fail "new checkpoint requires In Progress ticket: $ticket_id ($status)"
    [ -n "$iteration" ] || fail "--iteration is required for new"
    case "$iteration" in
      *[!0-9]*|0*) fail "iteration must be a positive integer: $iteration" ;;
    esac
    [ -n "$facts" ] || fail "--facts is required for new"
    [ -n "$inferences" ] || fail "--inferences is required for new"
    [ -n "$hypotheses" ] || fail "--hypotheses is required for new"
    [ -n "$unknowns" ] || fail "--unknowns is required for new"
    [ -n "$decision" ] || fail "--decision is required for new"
    [ -n "$next_action" ] || fail "--next is required for new"
    if rg -q "^## Iteration ${iteration}[[:space:]]" "$log_file"; then
      fail "iteration already exists in $log_path: $iteration"
    fi
    recorded_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    if git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      branch=$(git -C "$repo_root" branch --show-current)
      head=$(git -C "$repo_root" rev-parse --short HEAD)
    else
      branch=UNKNOWN
      head=UNKNOWN
    fi
    block=$(cat <<EOF
## Iteration ${iteration} — ${title} (${recorded_at})

### Facts

- ${facts}
- checkpoint branch: ${branch}; repository HEAD: ${head}

### Inferences

- ${inferences}

### Hypotheses

- ${hypotheses}

### UNKNOWN

- ${unknowns}

### Evidence / command result

- Record the exact command, exit status, artifact role path, and SHA-256 here.

### Decision

- ${decision}

### Next action

- ${next_action}
EOF
)
    if [ "$dry_run" = true ]; then
      printf '%s\n' "$block"
    else
      printf '\n%s\n' "$block" >> "$log_file"
      echo "PASS: checkpoint appended ticket=$ticket_id iteration=$iteration log=$log_path"
    fi
    ;;
  *)
    usage
    ;;
esac
