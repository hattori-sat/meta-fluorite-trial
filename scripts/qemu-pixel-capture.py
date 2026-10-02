#!/usr/bin/env python3
"""Capture and analyze a QEMU framebuffer without depending on window geometry."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
import time
from pathlib import Path


def _qmp_message(sock: socket.socket, timeout: float) -> dict:
    sock.settimeout(timeout)
    data = bytearray()
    while b"\r\n" not in data:
        chunk = sock.recv(65536)
        if not chunk:
            raise RuntimeError("QMP socket closed before a complete message")
        data.extend(chunk)
    line, _, _ = data.partition(b"\r\n")
    try:
        value = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("invalid JSON received from QMP") from exc
    if not isinstance(value, dict):
        raise RuntimeError("QMP returned a non-object message")
    return value


def _qmp_command(socket_path: Path, command: str, arguments: dict | None = None) -> dict:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(str(socket_path))
        _qmp_message(sock, 10.0)
        sock.sendall(b'{"execute":"qmp_capabilities"}\r\n')
        capabilities = _qmp_message(sock, 10.0)
        if "error" in capabilities:
            raise RuntimeError(f"QMP capabilities failed: {capabilities['error']}")
        payload: dict[str, object] = {"execute": command}
        if arguments is not None:
            payload["arguments"] = arguments
        sock.sendall((json.dumps(payload, separators=(",", ":")) + "\r\n").encode())
        response = _qmp_message(sock, 30.0)
        if "error" in response:
            raise RuntimeError(f"QMP command failed: {response['error']}")
        return response


def capture(socket_path: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command_line = f"screendump {str(output)}"
    _qmp_command(
        socket_path,
        "human-monitor-command",
        {"command-line": command_line},
    )
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"QEMU did not create a non-empty screendump: {output}")


def capture_video(socket_path: Path, frames_dir: Path, frame_count: int, interval: float) -> None:
    if frame_count < 1:
        raise ValueError("frame count must be positive")
    if interval < 0:
        raise ValueError("interval must not be negative")
    frames_dir.mkdir(parents=True, exist_ok=True)
    if any(frames_dir.iterdir()):
        raise ValueError(f"frame directory is not empty: {frames_dir}")
    for index in range(frame_count):
        output = frames_dir / f"frame-{index:05d}.ppm"
        capture(socket_path, output)
        if index + 1 < frame_count:
            time.sleep(interval)


def _read_ppm(path: Path) -> tuple[int, int, bytes]:
    raw = path.read_bytes()
    if not raw.startswith(b"P6"):
        raise ValueError(f"unsupported PPM format in {path}; expected binary P6")
    index = 2
    tokens: list[bytes] = []
    while len(tokens) < 3:
        while index < len(raw) and raw[index] in b" \t\r\n":
            index += 1
        if index < len(raw) and raw[index] == ord("#"):
            newline = raw.find(b"\n", index)
            if newline < 0:
                raise ValueError("unterminated PPM comment")
            index = newline + 1
            continue
        start = index
        while index < len(raw) and raw[index] not in b" \t\r\n":
            index += 1
        if start == index:
            raise ValueError("incomplete PPM header")
        tokens.append(raw[start:index])
    width, height, max_value = (int(token) for token in tokens)
    if max_value != 255:
        raise ValueError(f"unsupported PPM max value: {max_value}")
    if index >= len(raw) or raw[index] not in b" \t\r\n":
        raise ValueError("PPM header is not separated from pixel payload")
    index += 1
    pixels = raw[index:]
    expected = width * height * 3
    if len(pixels) != expected:
        raise ValueError(f"PPM pixel payload is {len(pixels)} bytes; expected {expected}")
    return width, height, pixels


def _parse_region(value: str, width: int, height: int) -> tuple[int, int, int, int]:
    if value == "full":
        if width <= 0 or height <= 0:
            raise ValueError("PPM dimensions must be positive")
        return 0, 0, width, height
    try:
        x, y, region_width, region_height = (int(part) for part in value.split(","))
    except ValueError as exc:
        raise ValueError("region must be x,y,width,height") from exc
    if x < 0 or y < 0 or region_width <= 0 or region_height <= 0:
        raise ValueError("region coordinates and dimensions must be positive")
    if x + region_width > width or y + region_height > height:
        raise ValueError("region extends outside the PPM image")
    return x, y, region_width, region_height


def _parse_rgb(value: str) -> tuple[int, int, int]:
    try:
        rgb = tuple(int(part) for part in value.split(","))
    except ValueError as exc:
        raise ValueError("RGB must be r,g,b") from exc
    if len(rgb) != 3 or any(channel < 0 or channel > 255 for channel in rgb):
        raise ValueError("RGB channels must be in the range 0..255")
    return rgb  # type: ignore[return-value]


def _pixel_at(pixels: bytes, width: int, column: int, row: int) -> tuple[int, int, int]:
    offset = (row * width + column) * 3
    return pixels[offset], pixels[offset + 1], pixels[offset + 2]


def _color_bin(pixel: tuple[int, int, int], bin_size: int = 32) -> str:
    return ",".join(str((channel // bin_size) * bin_size) for channel in pixel)


def _update_bbox(
    bbox: list[int], column: int, row: int, origin_x: int, origin_y: int
) -> None:
    local_x, local_y = column - origin_x, row - origin_y
    bbox[0] = min(bbox[0], local_x)
    bbox[1] = min(bbox[1], local_y)
    bbox[2] = max(bbox[2], local_x)
    bbox[3] = max(bbox[3], local_y)


def _bbox_or_none(bbox: list[int], origin_x: int, origin_y: int) -> list[int] | None:
    if bbox[2] < 0:
        return None
    return [origin_x + bbox[0], origin_y + bbox[1], bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1]


def analyze(
    path: Path,
    region_value: str,
    reference: Path | None,
    background: str,
    threshold: int,
    edge_threshold: int = 16,
    chroma_threshold: int = 24,
) -> dict:
    width, height, pixels = _read_ppm(path)
    x, y, region_width, region_height = _parse_region(region_value, width, height)
    reference_pixels: bytes | None = None
    if reference is not None:
        reference_width, reference_height, reference_pixels = _read_ppm(reference)
        if (reference_width, reference_height) != (width, height):
            raise ValueError("reference image dimensions differ from the sample")
    background_rgb = _parse_rgb(background)
    changed = 0
    min_x, min_y = region_width, region_height
    max_x = max_y = -1
    edge_pixels = 0
    chromatic_pixels = 0
    max_chroma = 0
    min_luma = 255
    max_luma = 0
    color_bins: dict[str, int] = {}
    edge_bbox = [region_width, region_height, -1, -1]
    chromatic_bbox = [region_width, region_height, -1, -1]
    region_bytes = bytearray()
    for row in range(y, y + region_height):
        for column in range(x, x + region_width):
            offset = (row * width + column) * 3
            pixel = pixels[offset : offset + 3]
            region_bytes.extend(pixel)
            pixel_tuple = (pixel[0], pixel[1], pixel[2])
            color_bins[_color_bin(pixel_tuple)] = color_bins.get(_color_bin(pixel_tuple), 0) + 1
            luma = (299 * pixel_tuple[0] + 587 * pixel_tuple[1] + 114 * pixel_tuple[2]) // 1000
            min_luma = min(min_luma, luma)
            max_luma = max(max_luma, luma)
            chroma = max(pixel_tuple) - min(pixel_tuple)
            max_chroma = max(max_chroma, chroma)
            if chroma >= chroma_threshold:
                chromatic_pixels += 1
                _update_bbox(chromatic_bbox, column, row, x, y)
            if reference_pixels is None:
                different = max(abs(pixel[channel] - background_rgb[channel]) for channel in range(3)) > threshold
            else:
                different = max(
                    abs(pixel[channel] - reference_pixels[offset + channel]) for channel in range(3)
                ) > threshold
            if different:
                changed += 1
                local_x, local_y = column - x, row - y
                min_x, min_y = min(min_x, local_x), min(min_y, local_y)
                max_x, max_y = max(max_x, local_x), max(max_y, local_y)
            neighboring_pixels = []
            if column > x:
                neighboring_pixels.append(_pixel_at(pixels, width, column - 1, row))
            if column + 1 < x + region_width:
                neighboring_pixels.append(_pixel_at(pixels, width, column + 1, row))
            if row > y:
                neighboring_pixels.append(_pixel_at(pixels, width, column, row - 1))
            if row + 1 < y + region_height:
                neighboring_pixels.append(_pixel_at(pixels, width, column, row + 1))
            if any(
                max(abs(pixel_tuple[channel] - neighbor[channel]) for channel in range(3))
                >= edge_threshold
                for neighbor in neighboring_pixels
            ):
                edge_pixels += 1
                _update_bbox(edge_bbox, column, row, x, y)
    region_size = region_width * region_height
    changed_bbox = None if max_x < 0 else [x + min_x, y + min_y, max_x - min_x + 1, max_y - min_y + 1]
    indicators_present = edge_pixels > 0 or chromatic_pixels > 0
    result = {
        "path": str(path),
        "width": width,
        "height": height,
        "region": [x, y, region_width, region_height],
        "ppm_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "region_sha256": hashlib.sha256(region_bytes).hexdigest(),
        "changed_pixels": changed,
        "changed_ratio": changed / region_size,
        "threshold": threshold,
        "comparison": "reference" if reference is not None else "background",
        "bounding_box": changed_bbox,
        "edge_pixels": edge_pixels,
        "edge_ratio": edge_pixels / region_size,
        "edge_threshold": edge_threshold,
        "edge_bounding_box": _bbox_or_none(edge_bbox, x, y),
        "chromatic_pixels": chromatic_pixels,
        "chromatic_ratio": chromatic_pixels / region_size,
        "chroma_threshold": chroma_threshold,
        "chromatic_bounding_box": _bbox_or_none(chromatic_bbox, x, y),
        "max_chroma": max_chroma,
        "luma_range": [min_luma, max_luma],
        "dominant_color_bins": [
            {"rgb": key, "pixels": count}
            for key, count in sorted(color_bins.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
        "geometry_indicator": "present" if indicators_present else "absent-or-undetectable",
        "classification_hint": (
            "geometry-indicators-present"
            if indicators_present
            else "uniform-or-undetectable"
        ),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--socket", type=Path, required=True)
    capture_parser.add_argument("--output", type=Path, required=True)
    video_parser = subparsers.add_parser("video")
    video_parser.add_argument("--socket", type=Path, required=True)
    video_parser.add_argument("--frames-dir", type=Path, required=True)
    video_parser.add_argument("--frames", type=int, required=True)
    video_parser.add_argument("--interval", type=float, default=1.0)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--input", type=Path, required=True)
    analyze_parser.add_argument("--region", required=True)
    analyze_parser.add_argument("--reference", type=Path)
    analyze_parser.add_argument("--background", default="0,0,0")
    analyze_parser.add_argument("--threshold", type=int, default=8)
    analyze_parser.add_argument(
        "--edge-threshold",
        type=int,
        default=16,
        help="minimum per-channel difference to count a local 4-neighbor edge",
    )
    analyze_parser.add_argument(
        "--chroma-threshold",
        type=int,
        default=24,
        help="minimum max(channel)-min(channel) to count a chromatic pixel",
    )
    args = parser.parse_args()
    try:
        if args.operation == "capture":
            capture(args.socket, args.output)
            print(json.dumps({"output": str(args.output), "bytes": args.output.stat().st_size}))
        elif args.operation == "video":
            capture_video(args.socket, args.frames_dir, args.frames, args.interval)
            print(json.dumps({"frames_dir": str(args.frames_dir), "frames": args.frames}))
        else:
            if args.threshold < 0 or args.threshold > 255:
                raise ValueError("threshold must be in the range 0..255")
            if args.edge_threshold < 0 or args.edge_threshold > 255:
                raise ValueError("edge threshold must be in the range 0..255")
            if args.chroma_threshold < 0 or args.chroma_threshold > 255:
                raise ValueError("chroma threshold must be in the range 0..255")
            print(json.dumps(analyze(
                args.input,
                args.region,
                args.reference,
                args.background,
                args.threshold,
                args.edge_threshold,
                args.chroma_threshold,
            )))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"qemu-pixel-capture: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
