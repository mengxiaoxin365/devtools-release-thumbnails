import os
import struct
import zlib

from src.thumbnail_service import InfraiClient, ThumbnailRequest, generate_thumbnail


def sample_image() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload))

    width, height = 640, 360
    scanline = b"\x00" + b"\x18\x72\xa4" * width
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanline * height))
        + chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    if not os.environ.get("INFRAI_API_KEY"):
        raise SystemExit("Set INFRAI_API_KEY before running this example")
    result = generate_thumbnail(ThumbnailRequest("release-screen.png", sample_image()), InfraiClient())
    print(result)
