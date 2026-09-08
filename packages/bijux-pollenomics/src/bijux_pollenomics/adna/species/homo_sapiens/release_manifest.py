"""Identity and file-integrity rules for an AADR release manifest."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
import re

from .text import clean_text


def validate_release_manifest_identity(
    payload: Mapping[str, object], release_dir: Path
) -> None:
    """Reject copied release identity and contradictory file lineage metadata."""
    source = clean_text(str(payload.get("source", "")))
    requested_version = clean_text(str(payload.get("requested_version", "")))
    if source != "AADR":
        raise ValueError(f"AADR release manifest has unexpected source: {source!r}")
    if requested_version != release_dir.name:
        raise ValueError(
            "AADR release manifest version does not match its release directory: "
            f"manifest={requested_version!r}, directory={release_dir.name!r}"
        )

    anno_files = payload.get("anno_files")
    if not isinstance(anno_files, list):
        raise ValueError("AADR release manifest anno_files must be a list")
    identities: set[tuple[str, str]] = set()
    declared_paths: set[Path] = set()
    all_rows_name_files = True
    for index, raw_row in enumerate(anno_files):
        declared_path = _validate_anno_file_row(
            raw_row,
            release_dir=release_dir,
            index=index,
            identities=identities,
        )
        if declared_path is None:
            all_rows_name_files = False
        else:
            declared_paths.add(declared_path)

    if all_rows_name_files:
        _validate_file_inventory(release_dir, declared_paths)


def _validate_anno_file_row(
    raw_row: object,
    *,
    release_dir: Path,
    index: int,
    identities: set[tuple[str, str]],
) -> Path | None:
    if not isinstance(raw_row, dict):
        raise ValueError(f"AADR anno_files[{index}] must be an object")
    dataset_name = clean_text(str(raw_row.get("dataset_name", "")))
    filename = clean_text(str(raw_row.get("filename", "")))
    if not dataset_name or Path(dataset_name).name != dataset_name:
        raise ValueError(f"AADR anno_files[{index}] has invalid dataset_name")
    if not filename:
        return None
    if Path(filename).name != filename:
        raise ValueError(f"AADR anno_files[{index}] has invalid filename")
    identity = (dataset_name, filename)
    if identity in identities:
        raise ValueError(f"AADR release manifest duplicates anno file {identity}")
    identities.add(identity)
    path = release_dir / dataset_name / filename
    if not path.is_file():
        raise ValueError(f"AADR release manifest file is missing: {path}")
    _validate_file_metadata(raw_row, path, index)
    return path.resolve()


def _validate_file_metadata(
    raw_row: Mapping[str, object], path: Path, index: int
) -> None:
    expected_size = raw_row.get("filesize")
    if expected_size is not None and (
        isinstance(expected_size, bool)
        or not isinstance(expected_size, int)
        or expected_size < 0
    ):
        raise ValueError(f"AADR anno_files[{index}] has invalid filesize")
    if isinstance(expected_size, int) and path.stat().st_size != expected_size:
        raise ValueError(f"AADR release manifest filesize mismatch for {path}")
    expected_md5 = clean_text(str(raw_row.get("md5", ""))).casefold()
    if not expected_md5:
        return
    if re.fullmatch(r"[0-9a-f]{32}", expected_md5) is None:
        raise ValueError(f"AADR anno_files[{index}] has invalid md5")
    actual_md5 = hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
    if actual_md5 != expected_md5:
        raise ValueError(f"AADR release manifest md5 mismatch for {path}")


def _validate_file_inventory(release_dir: Path, declared_paths: set[Path]) -> None:
    from .release import discover_homo_sapiens_anno_files

    actual_paths = {
        path.resolve() for path in discover_homo_sapiens_anno_files(release_dir)
    }
    if declared_paths == actual_paths:
        return
    missing = sorted(str(path) for path in actual_paths - declared_paths)
    unexpected = sorted(str(path) for path in declared_paths - actual_paths)
    raise ValueError(
        "AADR release manifest file inventory differs from the release directory: "
        f"undeclared={missing}, absent={unexpected}"
    )
