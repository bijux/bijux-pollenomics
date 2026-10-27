"""Literal JSON and bounded file inventories without host or engine readers."""

from __future__ import annotations

import csv
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import stat
from typing import Any

from .lineage import digest
from .scalar import require


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        require(key not in value, "duplicate JSON member")
        value[key] = item
    return value


def _nonfinite(token: str) -> None:
    raise ValueError("Independent KRAG coupled: nonfinite JSON constant " + token)


def decode(body: bytes) -> Any:
    return json.loads(body, object_pairs_hook=_pairs, parse_constant=_nonfinite)


def exact(actual: Any, expected: Any) -> None:
    require(type(actual) is type(expected), "exact native JSON type differs")
    if isinstance(expected, dict):
        require(set(actual) == set(expected), "exact native JSON object members differ")
        for key in expected:
            exact(actual[key], expected[key])
    elif isinstance(expected, list):
        require(len(actual) == len(expected), "exact native JSON population differs")
        for left, right in zip(actual, expected, strict=True):
            exact(left, right)
    else:
        require(actual == expected, "exact native scalar differs")


def read_file(path: Path, limit: int, expected: str | None = None) -> bytes:
    require(
        path.is_absolute()
        and ".." not in path.parts
        and not any(parent.is_symlink() for parent in (path, *path.parents)),
        "unaliased absolute source path required",
    )
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 < before.st_size <= limit,
            "bounded single-link regular file required",
        )
        body = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    final = path.stat()
    require(
        all(
            getattr(before, key) == getattr(after, key) == getattr(final, key)
            for key in (
                "st_dev",
                "st_ino",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
                "st_mode",
                "st_nlink",
            )
        ),
        "file mutated while being read",
    )
    require(
        len(body) <= limit
        and (expected is None or sha256(body).hexdigest() == expected),
        "bounded file byte identity differs",
    )
    return body


def relative_file(root: Path, relative: str) -> Path:
    path = Path(relative)
    require(
        not path.is_absolute() and ".." not in path.parts,
        "relative governed member required",
    )
    target = root / path
    require(
        target.resolve().is_relative_to(root.resolve()), "governed file escaped owner"
    )
    return target


def owned_artifact_path(repository: Path, locator: str, owner: Path) -> Path:
    """Interpret a retained locator without changing its spelling or study owner."""
    require(type(locator) is str and bool(locator), "literal artifact locator required")
    declared = Path(locator)
    require(".." not in declared.parts, "parent traversal in artifact locator")
    if not declared.is_absolute():
        require(
            declared.parts[0] == "artifacts",
            "repository-relative artifacts locator required",
        )
    path = declared if declared.is_absolute() else repository / declared
    require(
        owner.is_absolute()
        and ".." not in owner.parts
        and owner.is_relative_to(repository / "artifacts")
        and path.is_relative_to(owner),
        "artifact locator escaped its original study owner",
    )
    require(
        not any(node.is_symlink() for node in (path, *path.parents)),
        "symlink artifact locator ancestry",
    )
    return path


def pinned(root: Path, pin: dict[str, Any], limit: int) -> tuple[bytes, Any]:
    require(
        type(pin["bytes"]) is int and 0 < pin["bytes"] <= limit,
        "source byte count exceeds budget",
    )
    body = read_file(relative_file(root, pin["path"]), limit, pin["sha256"])
    require(len(body) == pin["bytes"], "source byte count changed")
    return body, decode(body)


def product(
    directory: Path, expected_manifest_sha256: str
) -> tuple[dict[str, Any], dict[str, bytes]]:
    manifest_body = read_file(
        directory / "manifest.json", 16 * 1024**2, expected_manifest_sha256
    )
    manifest = decode(manifest_body)
    require(
        type(manifest) is dict and type(manifest.get("files")) is dict,
        "literal product inventory required",
    )
    files: dict[str, bytes] = {}
    actual = {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file() and path != directory / "manifest.json"
    }
    require(actual == set(manifest["files"]), "product file population differs")
    total = 0
    for name, pin in manifest["files"].items():
        expected = pin if type(pin) is str else pin["sha256"]
        body = read_file(relative_file(directory, name), 16 * 1024**2, expected)
        total += len(body)
        require(
            total <= 128 * 1024**2, "product inventory exceeds independent read bound"
        )
        if type(pin) is dict and "bytes" in pin:
            require(pin["bytes"] == len(body), "product member byte count differs")
        files[name] = body
    require(
        read_file(directory / "manifest.json", 16 * 1024**2) == manifest_body,
        "product manifest changed",
    )
    if "scientific_payload" in manifest:
        require(
            manifest["scientific_content_sha256"]
            == digest(manifest["scientific_payload"]),
            "scientific payload digest differs",
        )
    if "scientific_identity" in manifest:
        canonical = (
            json.dumps(
                manifest["scientific_identity"],
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        )
        require(
            manifest["scientific_content_sha256"]
            == sha256(canonical.encode()).hexdigest(),
            "native scientific identity differs",
        )
    return manifest, files


def csv_rows(body: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(body.decode("utf-8-sig")))
    require(
        reader.fieldnames is not None
        and len(set(reader.fieldnames)) == len(reader.fieldnames),
        "unique CSV column names required",
    )
    result = list(reader)
    require(
        all(None not in row and None not in row.values() for row in result),
        "complete rectangular CSV rows required",
    )
    return result
