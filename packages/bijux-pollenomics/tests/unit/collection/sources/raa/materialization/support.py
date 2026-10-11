"""Explicit raw-fixture identities and byte helpers shared by RAÄ tests."""

from hashlib import sha256
from pathlib import Path
import struct

A = "00000000-0000-0000-0000-000000000001"


def blob(srs: int = 3006) -> bytes:
    return b"GP\x00\x01" + struct.pack("<i", srs) + struct.pack("<BIdd", 1, 1, 0.0, 0.0)


def identity(path: Path) -> tuple[str, int]:
    content = path.read_bytes()
    return sha256(content).hexdigest(), len(content)
