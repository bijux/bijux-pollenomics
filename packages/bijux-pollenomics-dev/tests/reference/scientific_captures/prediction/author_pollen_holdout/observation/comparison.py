"""Separate current code-origin metadata from exact retained author numerical values."""

import hashlib
from pathlib import Path
from typing import Any


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def exact(left: Any, right: Any) -> None:
    if type(left) is not type(right):
        raise ValueError("Original author JSON type changed")
    if isinstance(left, dict):
        if set(left) != set(right):
            raise ValueError("Original author JSON keys changed")
        for key in left:
            exact(left[key], right[key])
    elif isinstance(left, list):
        if len(left) != len(right):
            raise ValueError("Original author JSON length changed")
        for a, b in zip(left, right, strict=True):
            exact(a, b)
    elif left != right:
        raise ValueError("Original author scientific value changed")


def exact_csv(current: bytes, original: bytes) -> None:
    """Match the original replay's declared CSV CRLF-to-LF projection."""
    if current.replace(b"\r\n", b"\n") != original:
        raise ValueError("Original author CSV values or ordering changed")
