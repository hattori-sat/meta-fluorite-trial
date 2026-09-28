#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
checkpoint="$repo_root/scripts/runtime-checkpoint.sh"

if [ ! -x "$checkpoint" ]; then
  echo "RED: runtime-checkpoint.sh is not implemented or executable" >&2
  exit 1
fi

ticket_id=$(sed -n 's/^\*\*\[\(FLR-[0-9][0-9][0-9][0-9]\) .*/\1/p' "$repo_root/TASKS.md" | sed -n '1p')
[ -n "$ticket_id" ] || { echo "RED: current ticket is not listed in TASKS.md" >&2; exit 1; }
ticket_file=$(find "$repo_root/work/tickets" -maxdepth 1 -type f -name "${ticket_id}-*.md" -print | sed -n '1p')
[ -n "$ticket_file" ] || { echo "RED: current ticket file not found: $ticket_id" >&2; exit 1; }
log_path=$(sed -n 's/^- Working log: `\(.*\)`/\1/p' "$ticket_file" | sed -n '1p')
[ -n "$log_path" ] || { echo "RED: current ticket has no working log: $ticket_id" >&2; exit 1; }

"$checkpoint" verify \
  --ticket "$ticket_id" \
  --log "$log_path"

output=$("$checkpoint" new \
  --ticket "$ticket_id" \
  --log "$log_path" \
  --iteration 999 \
  --title "test-only checkpoint" \
  --facts "test fact" \
  --inferences "test inference" \
  --hypotheses "test hypothesis" \
  --unknowns "test unknown" \
  --decision "test decision" \
  --next "test next action" \
  --dry-run)

printf '%s\n' "$output" | grep -Fq '## Iteration 999 — test-only checkpoint'
printf '%s\n' "$output" | grep -Fq '### Facts'
printf '%s\n' "$output" | grep -Fq '### UNKNOWN'
printf '%s\n' "$output" | grep -Fq '### Next action'

echo "PASS: runtime checkpoint contract"
