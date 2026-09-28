#!/usr/bin/env python3
"""Capture a bounded no-input QMP window for FLR-0232."""

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


def wait_for_output(output: Path, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if output.is_file() and output.stat().st_size > 0:
            return
        time.sleep(0.05)
    raise RuntimeError(f"QMP screendump missing after {timeout:.1f}s: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qmp", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=25)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()
    if args.frames < 1 or args.interval < 0:
        raise SystemExit("frames must be positive and interval must be non-negative")
    args.root.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(10)
        sock.connect(str(args.qmp))
        print(f"greeting={receive(sock)}")
        print(f"capabilities={command(sock, 'qmp_capabilities')}")

        for index in range(args.frames):
            output = args.root / f"no-input-{index:02d}.ppm"
            reply = command(
                sock,
                "human-monitor-command",
                {"command-line": f"screendump {output}"},
            )
            wait_for_output(output)
            print(f"frame={index:02d} reply={reply}")
            if index + 1 < args.frames:
                time.sleep(args.interval)


if __name__ == "__main__":
    main()
