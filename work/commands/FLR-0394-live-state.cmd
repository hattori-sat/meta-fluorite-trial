set -eu
log=/run/user/1001/flr0394-0001-app.log
identity=/run/user/1001/flr0394-0001-app.identity
read pid saved_uid saved_start wrapper < "$identity"
if [ -r "/proc/$pid/status" ]; then
  uid=$(awk '/^Uid:/{print $2; exit}' "/proc/$pid/status")
  start=$(awk '{print $22}' "/proc/$pid/stat")
else
  uid=none
  start=none
fi
apps=$(pgrep -u 1001 -x flutter-auto || true)
set -- $apps
begins=$(grep -c -F 'FLR0026_VK_QUEUE_PRESENT_BEGIN' "$log" || true)
returns=$(grep -c -F 'FLR0026_VK_QUEUE_PRESENT result=0' "$log" || true)
done_count=$(grep -c -F 'FLR0026_VK_PRESENT_BOUNDARY_DONE' "$log" || true)
printf 'FLR0394_LIVE pid=%s uid=%s start=%s saved_start=%s app_count=%s PRESENT_BEGIN=%s PRESENT_RETURN=%s PRESENT_DONE=%s wrapper=%s\n' "$pid" "$uid" "$start" "$saved_start" "$#" "$begins" "$returns" "$done_count" "$wrapper"
test "$uid" = "$saved_uid"
test "$start" = "$saved_start"
test "$#" -eq 1
test "$1" = "$pid"
echo FLR0394_PID_GATE=PASS
