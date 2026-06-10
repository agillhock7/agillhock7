#!/usr/bin/env python3
"""Regressions for generated featured project profile content."""

from __future__ import annotations

import struct
import sys
import unittest
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import generate_featured_content as featured  # noqa: E402


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_chunk(kind: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(kind)
    checksum = zlib.crc32(data, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)


def solid_rgb_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = bytes(rgb) * width
    raw = b"".join(b"\x00" + row for _ in range(height))
    return PNG_SIGNATURE + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(raw)) + png_chunk(b"IEND", b"")


def rgba_pixels(image_bytes: bytes) -> tuple[int, int, bytes]:
    offset = len(PNG_SIGNATURE)
    width = height = color_type = 0
    compressed = bytearray()
    while offset < len(image_bytes):
        length = struct.unpack(">I", image_bytes[offset : offset + 4])[0]
        kind = image_bytes[offset + 4 : offset + 8]
        data = image_bytes[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", data)
            assert bit_depth == 8
        elif kind == b"IDAT":
            compressed.extend(data)
        elif kind == b"IEND":
            break

    assert color_type == 6
    raw = zlib.decompress(bytes(compressed))
    row_size = width * 4
    rows = []
    cursor = 0
    for _ in range(height):
        assert raw[cursor] == 0
        cursor += 1
        rows.append(raw[cursor : cursor + row_size])
        cursor += row_size
    return width, height, b"".join(rows)


class PreviewThumbnailTest(unittest.TestCase):
    def test_rounds_preview_png_corners_with_transparency(self) -> None:
        rounded = featured.round_preview_corners(solid_rgb_png(8, 8, (10, 20, 30)), radius=3)

        width, height, pixels = rgba_pixels(rounded)

        self.assertEqual((8, 8), (width, height))
        self.assertEqual(0, pixels[3])
        center_index = ((height // 2) * width + (width // 2)) * 4
        self.assertEqual(bytes((10, 20, 30, 255)), pixels[center_index : center_index + 4])


if __name__ == "__main__":
    unittest.main()
