# Apply only for agl-driver login shells.
[ "${USER}" = "agl-driver" ] || return 0

export XDG_RUNTIME_DIR=/run/user/1001
export WAYLAND_DISPLAY=wayland-0
export BUNDLE=/usr/share/flutter/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/3.38.3/release/
