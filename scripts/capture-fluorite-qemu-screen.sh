#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)

usage() {
    cat <<'EOF'
Usage:
  capture-fluorite-qemu-screen.sh capture --socket SOCKET --output PPM
  capture-fluorite-qemu-screen.sh analyze --input PPM --region X,Y,W,H [options]

Capture uses QEMU QMP/HMP screendump, so it does not depend on macOS window
coordinates. Analyze reports image and region hashes, changed-pixel ratio,
bounding boxes, local edge pixels, chromatic pixels, and dominant color bins.
With --reference it compares two same-sized PPM files; otherwise it compares
against --background (default 0,0,0). The edge/chroma metrics are supporting
evidence; a uniform black region remains inherently undetectable from RGB alone.
EOF
}

if [ "$#" -eq 0 ]; then
    usage >&2
    exit 2
fi

case "$1" in
    capture|analyze)
        operation=$1
        shift
        exec python3 "${script_dir}/qemu-pixel-capture.py" "$operation" "$@"
        ;;
    -h|--help)
        usage
        ;;
    *)
        echo "capture-fluorite-qemu-screen: unknown operation: $1" >&2
        usage >&2
        exit 2
        ;;
esac
