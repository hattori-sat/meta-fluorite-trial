#!/usr/bin/env python3
"""Capture the combined x-then-y motion with a bounded hold."""

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
    parser.add_argument("--hold-after-x", type=float, default=4.0)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()
    if args.hold_after_x < 0 or args.repeats < 1 or args.interval < 0:
        raise SystemExit("hold and interval must be non-negative; repeats must be positive")
    args.root.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(10)
        sock.connect(str(args.qmp))
        print(f"greeting={receive(sock)}")
        print(f"capabilities={command(sock, 'qmp_capabilities')}")
        dump(sock, args.root, "initial")
        x_event = {"type": "abs", "data": {"axis": "x", "value": 30463}}
        y_event = {"type": "abs", "data": {"axis": "y", "value": 1638}}
        print(f"input=x reply={command(sock, 'input-send-event', {'events': [x_event]})}")
        time.sleep(1)
        dump(sock, args.root, "move-x")
        print(f"hold-after-x={args.hold_after_x}")
        time.sleep(args.hold_after_x)
        print(f"input=y reply={command(sock, 'input-send-event', {'events': [y_event]})}")
        time.sleep(1)
        dump(sock, args.root, "move-y")
        for index in range(args.repeats):
            time.sleep(args.interval)
            dump(sock, args.root, f"post-move-y-{index:02d}")


if __name__ == "__main__":
    main()
