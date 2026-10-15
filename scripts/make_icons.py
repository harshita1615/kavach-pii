"""Draw the Kavach icon (a shield with a check mark) as PNGs, with no image library.

    python scripts/make_icons.py

Writes extension/icons/icon{16,32,48,128}.png. Shapes are defined in a
0..1 coordinate space and rendered with 4x4 supersampling for antialiasing.
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "extension" / "icons"

SHIELD_TOP = (29, 78, 216)  # #1d4ed8
SHIELD_BOTTOM = (30, 58, 138)  # #1e3a8a
CHECK = (255, 255, 255)


def bezier(p0, p1, p2, steps):
    """Points along a quadratic Bezier curve, excluding p0."""
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        out.append(
            (
                (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1],
            )
        )
    return out


def shield_outline(steps: int = 48) -> list[tuple[float, float]]:
    """Peaked top, straight sides, curved sides meeting at a pointed bottom."""
    right = [(0.5, 0.05), (0.88, 0.17), (0.88, 0.45)]
    right += bezier((0.88, 0.45), (0.88, 0.76), (0.5, 0.95), steps)  # down to the tip
    left = [(1 - x, y) for x, y in reversed(right[1:-1])]  # mirror, tip excluded
    return right + left


def inside(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    result = False
    j = len(poly) - 1
    for i, (xi, yi) in enumerate(poly):
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            result = not result
        j = i
    return result


def segment_distance(px, py, ax, ay, bx, by) -> float:
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


CHECK_POINTS = [(0.31, 0.50), (0.45, 0.64), (0.71, 0.36)]


def on_check(x: float, y: float, width: float) -> bool:
    return any(
        segment_distance(x, y, *CHECK_POINTS[i], *CHECK_POINTS[i + 1]) <= width / 2
        for i in range(len(CHECK_POINTS) - 1)
    )


def render(size: int) -> bytes:
    poly = shield_outline()
    check_width = 0.11 if size >= 32 else 0.15
    samples = 4
    rows = []
    for py in range(size):
        row = bytearray([0])  # filter type 0
        for px in range(size):
            shield = check = 0
            for sy in range(samples):
                for sx in range(samples):
                    x = (px + (sx + 0.5) / samples) / size
                    y = (py + (sy + 0.5) / samples) / size
                    if inside(x, y, poly):
                        shield += 1
                        if on_check(x, y, check_width):
                            check += 1
            n = samples * samples
            alpha = shield / n
            mix = check / shield if shield else 0
            t = py / max(1, size - 1)
            base = [round(SHIELD_TOP[i] * (1 - t) + SHIELD_BOTTOM[i] * t) for i in range(3)]
            rgb = [round(base[i] * (1 - mix) + CHECK[i] * mix) for i in range(3)]
            row += bytes([*rgb, round(alpha * 255)])
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 48, 128):
        (OUT / f"icon{size}.png").write_bytes(render(size))
        print(f"wrote icons/icon{size}.png")


if __name__ == "__main__":
    main()
