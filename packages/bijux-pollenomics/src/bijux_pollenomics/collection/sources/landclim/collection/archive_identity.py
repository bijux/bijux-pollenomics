"""Deterministic identity for members of the LandClim II archive."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

from ..catalog import inspect_landclim_ii_archive
from .model import LandClimRawReceiptError


def build_landclim_archive_receipt(path: Path) -> dict[str, object]:
    """Describe the safe, non-directory members in a LandClim II archive."""
    try:
        structure = inspect_landclim_ii_archive(path)
        with ZipFile(path) as archive:
            infos = sorted(
                (info for info in archive.infolist() if not info.is_dir()),
                key=lambda info: info.filename,
            )
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise LandClimRawReceiptError(
                    "LandClim II archive contains duplicate member paths"
                )
            members = []
            uncompressed_size_bytes = 0
            for info in infos:
                member_path = PurePosixPath(info.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise LandClimRawReceiptError(
                        "LandClim II archive contains an unsafe member path"
                    )
                payload = archive.read(info)
                uncompressed_size_bytes += len(payload)
                members.append(
                    {
                        "path": info.filename,
                        "size_bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                )
    except (BadZipFile, OSError) as error:
        raise LandClimRawReceiptError("LandClim II archive is unreadable") from error
    member_payload = json.dumps(
        members,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "filename": path.name,
        "member_count": len(members),
        "uncompressed_size_bytes": uncompressed_size_bytes,
        "member_manifest_sha256": hashlib.sha256(member_payload).hexdigest(),
        "member_digest_basis": "sha256-canonical-json-path-size-sha256",
        "mean_file_count": structure["mean_file_count"],
        "standard_error_file_count": structure["standard_error_file_count"],
        "time_windows": structure["time_windows"],
    }
