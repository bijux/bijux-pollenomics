"""Authenticate a complete pure-xlrd cache entry without importing its package."""

from __future__ import annotations

import base64
import csv
from email.parser import Parser
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
from typing import Any


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def safe_member(name: str) -> str:
    require(
        bool(name)
        and not name.startswith("/")
        and "\\" not in name
        and all(part not in ("", ".", "..") for part in name.split("/"))
        and PurePosixPath(name).as_posix() == name,
        "Unsafe cache RECORD path",
    )
    return name


def inventory(root: Path) -> list[dict[str, Any]]:
    require(
        root.is_dir()
        and root.absolute() == root.resolve()
        and not any(p.is_symlink() for p in (root, *root.parents)),
        "Physical cache root required",
    )
    rows = []
    for current, directories, names in os.walk(root, followlinks=False):
        for name in directories + names:
            path = Path(current) / name
            require(
                not path.is_symlink() and (path.is_file() or path.is_dir()),
                "Cache alias or special entry",
            )
            row: dict[str, Any] = {
                "path": path.relative_to(root).as_posix(),
                "kind": "directory" if path.is_dir() else "file",
            }
            if path.is_file():
                raw = path.read_bytes()
                row.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            rows.append(row)
    return sorted(rows, key=lambda row: row["path"])


def validate_cache(root: Path, expected: dict[str, Any]) -> list[dict[str, Any]]:
    """Bind every resource/directory and every RECORD claim, including unused scripts."""
    actual = inventory(root)
    require(
        actual == expected["entries"], "Full xlrd cache namespace or payload differs"
    )
    metadata = Parser().parsestr((root / "xlrd-2.0.2.dist-info/METADATA").read_text())
    wheel = Parser().parsestr((root / "xlrd-2.0.2.dist-info/WHEEL").read_text())
    require(
        metadata["Name"] == "xlrd"
        and metadata["Version"] == "2.0.2"
        and metadata["Requires-Python"]
        == ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*",
        "Selected xlrd distribution identity differs",
    )
    require(
        all("extra == '" in item for item in metadata.get_all("Requires-Dist", [])),
        "Undeclared runtime dependency",
    )
    require(
        wheel["Wheel-Version"] == "1.0"
        and wheel["Root-Is-Purelib"] == "true"
        and wheel.get_all("Tag") == ["py2-none-any", "py3-none-any"],
        "Pure compatible xlrd WHEEL identity differs",
    )
    rows = list(
        csv.reader(io.StringIO((root / "xlrd-2.0.2.dist-info/RECORD").read_text()))
    )
    names = [safe_member(row[0]) for row in rows if len(row) == 3]
    require(
        len(names) == len(rows) == 16 and len(set(names)) == 16,
        "Complete sixteen-member RECORD required",
    )
    files = {row["path"] for row in actual if row["kind"] == "file"}
    require(files == set(names), "RECORD/file membership differs")
    for name, digest, size in rows:
        raw = (root / name).read_bytes()
        if name == "xlrd-2.0.2.dist-info/RECORD":
            require(
                digest == size == "", "Only RECORD self-row may have absent hash/size"
            )
        else:
            require(
                digest.startswith("sha256=") and size.isascii() and size.isdigit(),
                "RECORD hash/size schema differs",
            )
            observed = (
                base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
                .decode()
                .rstrip("=")
            )
            require(
                digest == "sha256=" + observed and str(len(raw)) == size,
                "RECORD payload hash or size differs",
            )
        require(
            raw[:4]
            not in (
                b"\x7fELF",
                b"\xcf\xfa\xed\xfe",
                b"\xfe\xed\xfa\xcf",
                b"\xca\xfe\xba\xbe",
                b"\xbe\xba\xfe\xca",
            ),
            "Native payload is outside pure-xlrd scope",
        )
    require(
        (root / "xlrd-2.0.2.dist-info/top_level.txt").read_text() == "xlrd\n",
        "xlrd top-level namespace differs",
    )
    return [
        {
            "path": str(root / row["path"]),
            "sha256": row["sha256"],
            "bytes": row["bytes"],
        }
        for row in actual
        if row["kind"] == "file"
    ]
