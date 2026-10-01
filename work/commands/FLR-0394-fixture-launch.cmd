set -eu
log=/run/user/1001/flr0394-0001-app.log
identity=/run/user/1001/flr0394-0001-app.identity
test ! -e "$log"
test ! -e "$identity"
test -z "$(pgrep -u 1001 -x flutter-auto || true)"
nohup su -s /bin/sh agl-driver -c '
unset FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE FLR0305_PRODUCTION_SCENE_LIGHT
env XDG_RUNTIME_DIR=/run/user/1001 WAYLAND_DISPLAY=wayland-0 \
  FLUORITE_NATIVE_PURE_FIXTURE=1 \
  FLUORITE_NATIVE_MINIMAL_GEOMETRY=1 \
  FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1 \
  FLUORITE_NATIVE_FIXTURE_LIGHT=1 \
  FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR=1 \
  /usr/bin/timeout 180 /usr/bin/flutter-auto \
  -b /usr/share/flutter/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/3.32.5/release \
  > /run/user/1001/flr0394-0001-app.log 2>&1
rc=$?
printf "\nFLR0394_APP_EXIT_STATUS=%s\n" "$rc" >> /run/user/1001/flr0394-0001-app.log
exit "$rc"
' </dev/null >/dev/null 2>&1 &
wrapper=$!
sleep 1
pids=$(pgrep -u 1001 -x flutter-auto || true)
set -- $pids
test "$#" -eq 1
pid=$1
uid=$(awk '/^Uid:/{print $2; exit}' "/proc/$pid/status")
start=$(awk '{print $22}' "/proc/$pid/stat")
test "$uid" = 1001
printf '%s %s %s %s\n' "$pid" "$uid" "$start" "$wrapper" > "$identity"
printf 'FLR0394_LAUNCH=PASS pid=%s uid=%s start=%s wrapper=%s\n' "$pid" "$uid" "$start" "$wrapper"
