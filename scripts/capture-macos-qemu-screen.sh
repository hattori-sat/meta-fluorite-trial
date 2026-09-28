#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  capture-macos-qemu-screen.sh OUTPUT.png
  capture-macos-qemu-screen.sh --window-id ID OUTPUT.png
  capture-macos-qemu-screen.sh --interactive-window OUTPUT.png

The default captures the current macOS display. --window-id captures one
window when its CoreGraphics window number is already known. The interactive
form asks screencapture to wait for the QEMU window to be selected. The
resulting image is intentionally kept outside Git because a full desktop
capture can contain unrelated user content.
EOF
}

window_id=
interactive_window=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --window-id)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            window_id=$2
            shift 2
            ;;
        --interactive-window)
            interactive_window=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

[ "$#" -eq 1 ] || { usage >&2; exit 2; }
output=$1
case "$output" in
    /*) ;;
    *) echo "capture-macos-qemu-screen: OUTPUT must be an absolute path" >&2; exit 2 ;;
esac

mkdir -p "$(dirname "$output")"
if [ -n "$window_id" ]; then
    exec /usr/sbin/screencapture -x -o -l "$window_id" "$output"
fi
if [ "$interactive_window" -eq 1 ]; then
    exec /usr/sbin/screencapture -x -o -w "$output"
fi
exec /usr/sbin/screencapture -x -o "$output"
