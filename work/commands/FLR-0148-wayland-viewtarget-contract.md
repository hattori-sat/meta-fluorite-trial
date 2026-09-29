# FLR-0148 bounded ViewTarget/Wayland contract observation

Use this as the single-line command passed to the existing
`qemu-runtime-harness.sh serial-exec` operation. It launches exactly one
installed Example Demo process with the current native fixture controls,
enables the client-side Wayland protocol trace, waits for a bounded window,
and prints only selected scene/view/present and surface markers.

```sh
rm -f /tmp/flr0148-runtime.log /tmp/flr0148-app.pid; su -s /bin/sh agl-driver -c 'env XDG_RUNTIME_DIR=/run/user/1001 WAYLAND_DISPLAY=wayland-0 WAYLAND_DEBUG=client FLUORITE_NATIVE_PURE_FIXTURE=1 FLUORITE_NATIVE_MINIMAL_GEOMETRY=1 FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1 FLR0026_SYNC_TRACE=1 FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1 FLUORITE_VIEWTARGET_FRAME_TRACE=1 nohup /usr/bin/flutter-auto -b /usr/share/flutter/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/3.32.5/release >/tmp/flr0148-runtime.log 2>&1 & echo $! >/tmp/flr0148-app.pid'; sleep 15; printf '%s\n' APP_PID; cat /tmp/flr0148-app.pid; printf '%s\n' SELECTED_MARKERS; grep -E 'FLUORITE_NATIVE|FLUORITE_VIEWTARGET|FLR0026_VK_(WAYLAND|QUEUE_PRESENT|PRESENT_BOUNDARY)|wl_subsurface|wl_surface' /tmp/flr0148-runtime.log | tail -n 180
```

The complete runtime log remains guest-side under `/tmp` during the run. The
harness output and QMP-only PPM/video are the retained evidence; the protocol
trace is used only to classify the child-surface mapping/commit boundary.
