"""Authenticate one published multi-site draw bin for the optional LRA engine."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
import csv
import hashlib
from io import StringIO
import json
import math
from pathlib import Path
import re
from typing import Any

from ...core.filesystem import BoundedInputTree
from .engine.discovery import (
    MULTISITE_DRAW_LOVE_CAPABILITY,
    load_engine,
)
from .engine.errors import LRARefusal

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(content: bytes) -> Any:
    value = json.loads(content, object_pairs_hook=_pairs)
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


@contextmanager
def _source_inputs(
    root: Path, expected_sha256: str
) -> Iterator[tuple[BoundedInputTree, dict[str, dict[str, Any]]]]:
    """Hold one checksum epoch and a source-declared finite ordinary namespace."""
    if not isinstance(expected_sha256, str) or not _SHA256.fullmatch(expected_sha256):
        raise ValueError("Expected checksum-manifest SHA-256 is required")
    checksum_path = root / "checksums.json"
    with ExitStack() as stack:
        checksum_seal = stack.enter_context(
            BoundedInputTree(
                root,
                max_bytes=max(1, checksum_path.lstat().st_size),
                max_files=1,
                selected="checksums.json",
            )
        )
        raw = checksum_seal.read(checksum_path)
        if hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise ValueError("Checksum manifest differs from the pinned digest")
        checksums = _json(raw)
        if not isinstance(checksums, dict) or not checksums:
            raise ValueError("Checksum manifest must list bundle members")
        total = len(raw)
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
            total += record["bytes"]
        inputs = stack.enter_context(
            BoundedInputTree(
                root,
                max_bytes=max(1, total),
                max_files=len(checksums) + 1,
            )
        )
        if (
            inputs.anchor.identity != checksum_seal.anchor.identity
            or inputs.files.get("checksums.json")
            != checksum_seal.files["checksums.json"]
        ):
            raise ValueError("Checksum manifest changed during source inventory")
        yield inputs, checksums
        inputs.check()
        checksum_seal.check()


def _inventory(
    inputs: BoundedInputTree,
    checksums: dict[str, dict[str, Any]],
    expected_sha256: str,
) -> None:
    if set(inputs.files) != {"checksums.json", *checksums}:
        raise ValueError("Bundle members differ from checksum inventory")
    for name, record in checksums.items():
        if inputs.files[name][4] != record["bytes"]:
            raise ValueError(f"Bundle member differs from checksum: {name}")
    try:
        inputs.validate()
    except ValueError as error:
        raise ValueError(
            "Bundle member differs from checksum or source seal"
        ) from error
    if inputs.digests["checksums.json"] != expected_sha256:
        raise ValueError("Checksum manifest changed during verification")
    for name, record in checksums.items():
        if inputs.digests[name] != record["sha256"]:
            raise ValueError(f"Bundle member differs from checksum: {name}")


def _member(
    inputs: BoundedInputTree, checksums: dict[str, dict[str, Any]], name: str
) -> bytes:
    if name not in checksums:
        raise ValueError(f"Selected source member is undeclared: {name}")
    return inputs.read(inputs.root / name, max_bytes=checksums[name]["bytes"])


def _csv(content: bytes) -> list[list[str]]:
    rows = list(csv.reader(StringIO(content.decode("utf-8"))))
    if not rows or any(not row for row in rows):
        raise ValueError("Published CSV is empty or malformed")
    return rows


def _selected_bin(
    availability: list[list[str]], manifest: dict[str, Any], bin_id: str
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
        with _source_inputs(root, expected_checksums_sha256) as (inputs, inventory):
            _inventory(inputs, inventory, expected_checksums_sha256)
            parent_bytes = _member(inputs, inventory, "run-manifest.json")
            parent_sha256 = hashlib.sha256(parent_bytes).hexdigest()
            manifest = _json(parent_bytes)
            if not isinstance(manifest, dict):
                raise ValueError("Scientific manifest must be an object")
            sites, eligible, taxa, all_bounds, position, expected_index = _selected_bin(
                _csv(_member(inputs, inventory, "availability.csv")), manifest, bin_id
            )
            index = _json(_member(inputs, inventory, "regional-cover-draws/index.json"))
            if index != expected_index:
                raise ValueError("Regional draw index differs from source axes")
            item = next(item for item in index if item["bin_id"] == bin_id)
            member_name = "regional-cover-draws/" + item["path"]
            member_bytes = _member(inputs, inventory, member_name)
            member_sha256 = hashlib.sha256(member_bytes).hexdigest()
            rows = _csv(member_bytes)
            if rows[0] != ["draw_index", *taxa] or len(rows) != 1001:
                raise ValueError("Regional draw CSV axes or count differ")
            values = []
            for number, row in enumerate(rows[1:]):
                if row[0] != str(number) or len(row) != len(taxa) + 1:
                    raise ValueError("Regional draw IDs or width differ")
                values.append([float(value) for value in row[1:]])
            binding = load_engine(required_capability=MULTISITE_DRAW_LOVE_CAPABILITY)
            import numpy as np

            if manifest["inputs"].get("bin_bounds_bp") != (
                binding.api.publication_bin_bounds_sha256(all_bounds)
            ):
                raise ValueError(
                    "Published BP bounds differ from source-bound identity"
                )
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
            _inventory(inputs, inventory, expected_checksums_sha256)
            return source
    except (
        OSError,
        ValueError,
        csv.Error,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
        StopIteration,
    ) as exc:
        raise LRARefusal("invalid_multisite_regional_draw_source", str(exc)) from exc
