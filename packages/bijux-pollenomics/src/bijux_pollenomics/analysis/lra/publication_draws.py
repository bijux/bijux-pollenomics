"""Authenticate one published multi-site draw bin for the optional LRA engine."""

from __future__ import annotations

import csv
import hashlib
from io import StringIO
import json
import math
from pathlib import Path
import re
import stat
from typing import Any

from .engine.discovery import (
    MULTISITE_DRAW_LOVE_CAPABILITY,
    load_engine,
)
from .engine.errors import LRARefusal

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(path: Path) -> Any:
    value = json.loads(path.read_bytes(), object_pairs_hook=_pairs)
    json.dumps(value, allow_nan=False)
    return value


def _names(value: Any) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError("Source axes require unique nonempty string IDs")
    return tuple(value)


def _inventory(root: Path, expected_sha256: str) -> dict[str, dict[str, Any]]:
    if not _SHA256.fullmatch(expected_sha256):
        raise ValueError("Expected checksum-manifest SHA-256 is required")
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Multi-site bundle must be a real directory")
    checksum_path = root / "checksums.json"
    if _hash(checksum_path) != expected_sha256:
        raise ValueError("Checksum manifest differs from the pinned digest")
    checksums = _json(checksum_path)
    if not isinstance(checksums, dict) or not checksums:
        raise ValueError("Checksum manifest must list bundle members")
    paths = list(root.rglob("*"))
    if any(
        not (stat.S_ISREG(path.lstat().st_mode) or stat.S_ISDIR(path.lstat().st_mode))
        for path in paths
    ):
        raise ValueError("Multi-site bundle contains a nonregular member")
    actual = {
        path.relative_to(root).as_posix()
        for path in paths
        if stat.S_ISREG(path.lstat().st_mode) and path != checksum_path
    }
    if actual != set(checksums):
        raise ValueError("Bundle members differ from checksum inventory")
    for name, record in checksums.items():
        if (
            not isinstance(name, str)
            or not isinstance(record, dict)
            or set(record) != {"bytes", "sha256"}
            or type(record["bytes"]) is not int
            or record["bytes"] < 0
            or not isinstance(record["sha256"], str)
            or not _SHA256.fullmatch(record["sha256"])
        ):
            raise ValueError("Malformed bundle checksum entry")
        path = root / name
        if path.stat().st_size != record["bytes"] or _hash(path) != record["sha256"]:
            raise ValueError(f"Bundle member differs from checksum: {name}")
    if _hash(checksum_path) != expected_sha256:
        raise ValueError("Checksum manifest changed during verification")
    return checksums


def _csv(path: Path) -> list[list[str]]:
    rows = list(csv.reader(StringIO(path.read_text(encoding="utf-8"))))
    if not rows or any(not row for row in rows):
        raise ValueError("Published CSV is empty or malformed")
    return rows


def _selected_bin(
    root: Path, manifest: dict[str, Any], bin_id: str
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[tuple[float, float], ...],
    int,
    list[dict[str, Any]],
]:
    if (
        manifest.get("algorithm") != "REVEALS-multisite-publication-source"
        or manifest.get("parameters", {}).get("time_bins")
        != "explicit_calendar_years_bp_1950CE_younger_older"
    ):
        raise ValueError("Unsupported multi-site publication chronology")
    parameters = manifest["parameters"]
    axes = parameters["source_axes"]
    sites = _names(axes["site_ids"])
    bins = _names(axes["bin_ids"])
    taxa = _names(axes["taxon_ids"])
    if bin_id not in bins:
        raise ValueError("Selected bin is absent from source axes")
    bounds = parameters.get("bin_bounds_bp")
    if not isinstance(bounds, list) or len(bounds) != len(bins):
        raise ValueError("Typed BP bounds are absent or misaligned")
    parsed_bounds = []
    for pair in bounds:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or any(type(value) not in (int, float) for value in pair)
            or any(not math.isfinite(value) for value in pair)
            or pair[0] >= pair[1]
        ):
            raise ValueError("Published BP bounds are invalid")
        parsed_bounds.append((float(pair[0]), float(pair[1])))
    if any(
        left[1] > right[0]
        for left, right in zip(parsed_bounds, parsed_bounds[1:], strict=False)
    ):
        raise ValueError("Published BP bins overlap")
    availability = _csv(root / "availability.csv")
    if availability[0] != ["bin_id", *sites] or len(availability) != len(bins) + 1:
        raise ValueError("Availability axes differ from the scientific manifest")
    expected_index = []
    for position, (row, name) in enumerate(zip(availability[1:], bins, strict=True)):
        if (
            row[0] != name
            or len(row) != len(sites) + 1
            or any(value not in {"True", "False"} for value in row[1:])
        ):
            raise ValueError("Availability support is malformed or relabelled")
        if row[1:].count("True") > 1:
            expected_index.append(
                {
                    "bin_id": name,
                    "path": f"bin-{position}.csv",
                    "draw_index_base": 0,
                    "draw_count": 1000,
                    "taxon_ids": list(taxa),
                }
            )
    position = bins.index(bin_id)
    eligible = tuple(
        site
        for site, value in zip(sites, availability[position + 1][1:], strict=True)
        if value == "True"
    )
    if len(eligible) < 2:
        raise ValueError("Selected draw bin lacks multiple source sites")
    return sites, eligible, taxa, tuple(parsed_bounds), position, expected_index


def read_multisite_regional_draw_source(
    directory: str | Path,
    *,
    bin_id: str,
    expected_checksums_sha256: str,
) -> Any:
    """Return a sealed draw source after byte and semantic verification.

    The pinned checksum-manifest digest must come from a separately retained
    receipt. Internal checksums alone cannot authenticate source identity.
    Legacy bundles without explicit BP bounds are refused.
    """
    root = Path(directory).absolute()
    try:
        inventory = _inventory(root, expected_checksums_sha256)
        parent = root / "run-manifest.json"
        parent_sha256 = _hash(parent)
        manifest = _json(parent)
        if not isinstance(manifest, dict):
            raise ValueError("Scientific manifest must be an object")
        sites, eligible, taxa, all_bounds, position, expected_index = _selected_bin(
            root, manifest, bin_id
        )
        index = _json(root / "regional-cover-draws" / "index.json")
        if index != expected_index:
            raise ValueError("Regional draw index differs from source axes")
        item = next(item for item in index if item["bin_id"] == bin_id)
        member = root / "regional-cover-draws" / item["path"]
        member_sha256 = _hash(member)
        rows = _csv(member)
        if rows[0] != ["draw_index", *taxa] or len(rows) != 1001:
            raise ValueError("Regional draw CSV axes or count differ")
        values = []
        for number, row in enumerate(rows[1:]):
            if row[0] != str(number) or len(row) != len(taxa) + 1:
                raise ValueError("Regional draw IDs or width differ")
            values.append([float(value) for value in row[1:]])
        for path in (
            parent,
            root / "availability.csv",
            root / "regional-cover-draws" / "index.json",
            member,
        ):
            if _hash(path) != inventory[path.relative_to(root).as_posix()]["sha256"]:
                raise ValueError("Selected source members changed during verification")
        if _hash(root / "checksums.json") != expected_checksums_sha256:
            raise ValueError("Checksum manifest changed during verification")
        binding = load_engine(required_capability=MULTISITE_DRAW_LOVE_CAPABILITY)
        import numpy as np

        if manifest["inputs"].get("bin_bounds_bp") != (
            binding.api.publication_bin_bounds_sha256(all_bounds)
        ):
            raise ValueError("Published BP bounds differ from source-bound identity")
        bounds = all_bounds[position]
        source = binding.api.RegionalCoverDrawSource.from_verified_member(
            values=np.asarray(values, dtype=np.float64),
            taxon_ids=taxa,
            bin_id=bin_id,
            younger_bp=bounds[0],
            older_bp=bounds[1],
            draw_ids=tuple(range(1000)),
            regional_site_ids=sites,
            eligible_site_ids=eligible,
            parent_manifest_sha256=parent_sha256,
            draw_member_sha256=member_sha256,
        )
        _inventory(root, expected_checksums_sha256)
        return source
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
        StopIteration,
    ) as exc:
        raise LRARefusal("invalid_multisite_regional_draw_source", str(exc)) from exc
