#!/usr/bin/env python3
"""Convert SDL's 24/32-bit BMP screenshots to PNG without third-party modules."""
import struct
import sys
import zlib
from pathlib import Path


def convert(source, destination):
    bmp = Path(source).read_bytes()
    if bmp[:2] != b'BM':
        raise ValueError('Not a BMP')
    offset = struct.unpack_from('<I', bmp, 10)[0]
    width, height, planes, bits, compression = struct.unpack_from('<iiHHI', bmp, 18)
    if bits not in (24, 32) or compression not in (0, 3) or width <= 0:
        raise ValueError('Unsupported BMP layout')
    stride = ((width * bits + 31) // 32) * 4
    rows = []
    for y in range(abs(height)):
        row = (abs(height) - 1 - y) if height > 0 else y
        data = bmp[offset + row * stride:offset + (row + 1) * stride]
        output = bytearray([0])
        for x in range(width):
            i = x * (bits // 8)
            output.extend((data[i + 2], data[i + 1], data[i]))
        rows.append(output)
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, abs(height), 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b'')
    Path(destination).write_bytes(png)


if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2])
