#!/usr/bin/env python3
"""Capture repeated QMP frames after one pointer-motion event."""

from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path


def receive(sock: socket.socket) -> dict:
    data = bytearray()
    while b"\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise RuntimeError("QMP closed before a complete response")
        data.extend(chunk)
    line, _, _ = bytes(data).partition(b"\n")
    return json.loads(line.decode("utf-8"))


def command(sock: socket.socket, name: str, arguments: dict | None = None) -> dict:
    payload: dict[str, object] = {"execute": name}
    if arguments is not None:
        payload["arguments"] = arguments
    sock.sendall((json.dumps(payload, separators=(",", ":")) + "\r\n").encode())
    response = receive(sock)
    if "error" in response:
        raise RuntimeError(f"QMP command failed: {response['error']}")
    return response


def dump(sock: socket.socket, root: Path, name: str) -> None:
    output = root / f"{name}.ppm"
    command(sock, "human-monitor-command", {"command-line": f"screendump {output}"})
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if output.is_file() and output.stat().st_size > 0:
            print(f"frame={name} output={output}")
            return
        time.sleep(0.05)
    raise RuntimeError(f"QMP screendump missing after 2.0s: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qmp", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--axis", choices=("x", "y"), required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()
    if args.repeats < 1 or args.interval < 0:
        raise SystemExit("repeats must be positive and interval must be non-negative")
    args.root.mkdir(parents=True, exist_ok=True)
    value = 30463 if args.axis == "x" else 1638

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(10)
        sock.connect(str(args.qmp))
        print(f"greeting={receive(sock)}")
        print(f"capabilities={command(sock, 'qmp_capabilities')}")
        dump(sock, args.root, "initial")
        event = {"type": "abs", "data": {"axis": args.axis, "value": value}}
        print(f"input={args.axis} reply={command(sock, 'input-send-event', {'events': [event]})}")
        time.sleep(1)
        dump(sock, args.root, f"move-{args.axis}")
        for index in range(args.repeats):
            time.sleep(args.interval)
            dump(sock, args.root, f"post-move-{args.axis}-{index:02d}")


if __name__ == "__main__":
    main()
