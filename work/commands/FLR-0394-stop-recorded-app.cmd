set -eu
identity=/run/user/1001/flr0394-0001-app.identity
read pid saved_uid saved_start wrapper < "$identity"
apps=$(pgrep -u 1001 -x flutter-auto || true)
set -- $apps
count=$#
if [ -r "/proc/$pid/status" ]; then
  uid=$(awk '/^Uid:/{print $2; exit}' "/proc/$pid/status")
  start=$(awk '{print $22}' "/proc/$pid/stat")
else
  uid=none
  start=none
fi
if [ "$uid" = "$saved_uid" ] && [ "$start" = "$saved_start" ] && [ "$count" -eq 1 ] && [ "$1" = "$pid" ]; then
  kill -TERM "$pid"
  echo FLR0394_APP_STOP=SIGTERM_SENT
  sleep 2
else
  echo FLR0394_APP_STOP=NO_SIGNAL_identity_or_count_changed
fi
apps=$(pgrep -u 1001 -x flutter-auto || true)
set -- $apps
printf 'FLR0394_APP_RESIDUAL=%s\n' "$#"
