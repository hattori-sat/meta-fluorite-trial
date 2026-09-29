#!/usr/bin/env python3
"""Capture the FLR-0226 hover A/B using QMP only.

The script deliberately does not use a host-window screenshot.  It sends the
same absolute pointer sequence used by FLR-0225 and records one PPM per step
under the caller-supplied evidence directory.
"""

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qmp", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(10)
        sock.connect(str(args.qmp))
        greeting = receive(sock)
        print(f"greeting={greeting}")
        print(f"capabilities={command(sock, 'qmp_capabilities')}")
        print(f"mice={command(sock, 'query-mice')}")

        def dump(name: str) -> None:
            output = args.root / f"{name}.ppm"
            reply = command(
                sock,
                "human-monitor-command",
                {"command-line": f"screendump {output}"},
            )
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError(f"QMP screendump missing: {output}")
            print(f"{name}={reply}")

        dump("initial")
        steps = [
            ("move-x", {"type": "abs", "data": {"axis": "x", "value": 30463}}),
            ("move-y", {"type": "abs", "data": {"axis": "y", "value": 1638}}),
            ("down", {"type": "btn", "data": {"button": "left", "down": True}}),
            ("up", {"type": "btn", "data": {"button": "left", "down": False}}),
        ]
        for name, event in steps:
            print(f"input-{name}={command(sock, 'input-send-event', {'events': [event]})}")
            time.sleep(1)
            dump(name)


if __name__ == "__main__":
    main()
