set -eu
log=/run/user/1001/flr0394-0001-app.log
identity=/run/user/1001/flr0394-0001-app.identity
read pid saved_uid saved_start wrapper < "$identity"
branch=$(grep -m 1 -F 'FLUORITE_NATIVE_MATERIAL_BRANCH hardcoded=true shading=lit source=constant' "$log")
printf 'FLR0394_BRANCH=%s\n' "$branch"
timeout 165 sh -c 'tail -n 0 -f "$1" | grep -m 1 -F "FLR0026_VK_QUEUE_PRESENT result=0"' sh "$log" >/dev/null
geometry=$(grep -m 1 -F 'FLUORITE_NATIVE_MINIMAL_GEOMETRY_CONTRACT' "$log")
printf 'FLR0394_GEOMETRY=%s\n' "$geometry"
if [ -r "/proc/$pid/status" ]; then
  uid=$(awk '/^Uid:/{print $2; exit}' "/proc/$pid/status")
  start=$(awk '{print $22}' "/proc/$pid/stat")
else
  uid=none
  start=none
fi
apps=$(pgrep -u 1001 -x flutter-auto || true)
set -- $apps
printf 'FLR0394_FIRST_PRESENT pid=%s uid=%s start=%s saved_start=%s app_count=%s wrapper=%s\n' "$pid" "$uid" "$start" "$saved_start" "$#" "$wrapper"
test "$uid" = "$saved_uid"
test "$start" = "$saved_start"
test "$#" -eq 1
test "$1" = "$pid"
echo FLR0394_FIRST_PRESENT_GATE=PASS
