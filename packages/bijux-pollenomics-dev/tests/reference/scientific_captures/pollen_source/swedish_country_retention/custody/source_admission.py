"""Require a physical independently reviewed controller source closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from source_inputs import exact_union, verify_rows


def verify_namespace(root: Path) -> None:
    from entry import verify

    verify(root)


def reviewed_controls(root: Path) -> tuple[Path, Path, list[dict[str, Any]]]:
    verify_namespace(root)
    manifest = root / "prepared-source-manifest.json"
    review = root / "independent-source-review.json"
    for path in (manifest, review):
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("Reviewed source controls must be regular owned files")
    raw = manifest.read_bytes()
    document = json.loads(raw)
    review_raw = review.read_bytes()
    admission = json.loads(review_raw)
    if (
        document["source_only"] is not True
        or admission["approved"] is not True
        or admission["source_manifest_sha256"] != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError(
            "Controller source has not received exact independent approval"
        )
    names = [row["path"] for row in document["files"]]
    if names != sorted(set(names)):
        raise ValueError("Controller source membership must be sorted and unique")
    for row in document["files"]:
        path = Path(row["path"])
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not path.is_relative_to(root)
            or any(p.is_symlink() for p in (path, *path.parents))
        ):
            raise ValueError("Controller member leaves its owned source closure")
        if (
            not path.is_file()
            or type(row["bytes"]) is not int
            or path.stat().st_size != row["bytes"]
        ):
            raise ValueError("Controller source member length changed")
        with path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        if checksum != row["sha256"]:
            raise ValueError("Controller source bytes changed after independent review")
    rows = exact_union(
        document["files"],
        [
            {
                "path": str(manifest),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            },
            {
                "path": str(review),
                "sha256": hashlib.sha256(review_raw).hexdigest(),
                "bytes": len(review_raw),
            },
        ],
    )
    verify_rows(rows)
    return manifest, review, rows


def authenticate_controls(root: Path) -> tuple[Path, Path]:
    manifest, review, _ = reviewed_controls(root)
    return manifest, review
