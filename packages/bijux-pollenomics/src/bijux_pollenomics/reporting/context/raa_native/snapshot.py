"""Capture independently pinned native registry aggregates without private rows."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, cast
from urllib.parse import urlsplit

from ....collection.sources.raa.point_grid.contracts import BOUNDARY, DISPOSITIONS
from ....collection.sources.raa.point_grid.projection import GRID
from ....core.filesystem import BoundedInputTree
from .projection import SUPPORT_BOUNDS, project_cells

REPORT_LIMIT = 64 * 1024
COUNTS_LIMIT = 16 * 1024
BUFFER_LIMIT = 1024 * 1024


def _digest(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None


def canonical_bytes(value: object) -> bytes:
    """Serialize finite public projections deterministically."""
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class NativeRegistrySource:
    """Independently granted administrative source identity, not scientific admission."""

    sha256: str
    byte_count: int
    captured_at_utc: str
    download_url: str
    rights: str

    def __post_init__(self) -> None:
        """Require a complete source epoch without interpreting capture as event time."""
        if (
            not _digest(self.sha256)
            or type(self.byte_count) is not int
            or self.byte_count < 1
        ):
            raise ValueError("Native registry source identity is invalid")
        parsed = datetime.fromisoformat(self.captured_at_utc)
        offset = parsed.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise ValueError("Native registry source capture requires UTC")
        if urlsplit(self.download_url).scheme != "https" or not self.rights.strip():
            raise ValueError("Native registry source URL or rights are missing")


@dataclass(frozen=True, slots=True)
class NativeRegistryContextSnapshot:
    """Bounded immutable aggregate buffers; original source need not remain open."""

    context_bytes: bytes
    counts_bytes: bytes
    cells_bytes: bytes

    def __post_init__(self) -> None:
        """Reject mutable buffers and oversized constructed snapshots."""
        for raw in (self.context_bytes, self.counts_bytes, self.cells_bytes):
            if type(raw) is not bytes or len(raw) > BUFFER_LIMIT:
                raise ValueError(
                    "Native registry snapshot requires bounded immutable bytes"
                )


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Native registry report contains duplicate keys")
        result[key] = value
    return result


def _integer(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Native registry count requires a nonnegative native integer")
    return value


def _read_cells(raw: bytes) -> tuple[tuple[int, int, int], ...]:
    lines = raw.decode("ascii").splitlines()
    if not lines or lines[0] != "west_longitude,south_latitude,uuid_count":
        raise ValueError("Native registry CSV header is unsupported")
    cells: list[tuple[int, int, int]] = []
    for line in lines[1:]:
        if re.fullmatch(r"-?\d+,-?\d+,\d+", line) is None:
            raise ValueError(
                "Native registry cells require native integer coordinates/counts"
            )
        west, south, count = map(int, line.split(","))
        if (
            not 10 <= west <= 24
            or not 54 <= south <= 69
            or count <= 0
            or cells
            and (west, south) <= cells[-1][:2]
        ):
            raise ValueError(
                "Native registry cells are duplicate, unsorted or unsupported"
            )
        cells.append((west, south, count))
    if len(cells) > 240:
        raise ValueError("Native registry cells exceed the declared finite grid")
    return tuple(cells)


def _report(raw: bytes, csv: bytes, source: NativeRegistrySource) -> dict[str, Any]:
    report = json.loads(raw, object_pairs_hook=_object)
    if (
        not isinstance(report, dict)
        or report.get("schema_version") != "raa-native-point-grid-v1"
    ):
        raise ValueError("Native registry report schema is unsupported")
    if report.get("source") != {
        "sha256": source.sha256,
        "byte_count": source.byte_count,
    }:
        raise ValueError(
            "Native registry source differs from independently declared identity"
        )
    for key, expected in (("grid", GRID), ("boundary", BOUNDARY)):
        if canonical_bytes(report.get(key)) != canonical_bytes(expected):
            raise ValueError(
                f"Native registry {key} differs from its conditional profile"
            )
    selection = {
        "native_owner": "lamning.uuid",
        "native_class_field": "antikvariskbedomning",
        "native_class_value": "Fornlämning",
        "raw_primary_point_occurrences": 1,
        "valid_primary_point_occurrences": 1,
        "uncertainty_role": "separately_counted_never_selected",
        "disposition_precedence": list(DISPOSITIONS),
    }
    if canonical_bytes(report.get("selection")) != canonical_bytes(selection):
        raise ValueError(
            "Native registry selection differs from exact native UUID/POINT scope"
        )
    if report.get("projection", {}).get("location_support_bounds") != list(
        SUPPORT_BOUNDS
    ):
        raise ValueError("Native registry support frame differs")
    if report.get("files", {}).get("cell-counts.csv") != {
        "sha256": sha256(csv).hexdigest(),
        "byte_count": len(csv),
    }:
        raise ValueError("Native registry report does not bind the captured count CSV")
    return cast(dict[str, Any], report)


def capture_native_registry_context(
    directory: Path,
    *,
    expected_report_sha256: str,
    expected_counts_sha256: str,
    source: NativeRegistrySource,
) -> NativeRegistryContextSnapshot:
    """Read only two selected, externally pinned aggregates and conserve all counts.

    Supplied pins must originate in the independently qualified closed result.
    Report declarations alone do not establish source authority or admission.
    """
    if not isinstance(source, NativeRegistrySource) or not all(
        _digest(pin) for pin in (expected_report_sha256, expected_counts_sha256)
    ):
        raise ValueError(
            "Native registry capture requires independent source and file pins"
        )
    root = Path(directory).absolute()
    buffers: dict[str, bytes] = {}
    with ExitStack() as stack:
        trees = {
            name: stack.enter_context(
                BoundedInputTree(
                    root,
                    max_bytes=limit,
                    max_files=1,
                    selected=name,
                )
            )
            for name, limit in (
                ("report.json", REPORT_LIMIT),
                ("cell-counts.csv", COUNTS_LIMIT),
            )
        }
        for name, expected in (
            ("report.json", expected_report_sha256),
            ("cell-counts.csv", expected_counts_sha256),
        ):
            tree = trees[name]
            buffers[name] = tree.read(root / name, max_bytes=tree.max_bytes)
            if sha256(buffers[name]).hexdigest() != expected:
                raise ValueError(
                    "Native registry aggregate differs from independent digest"
                )
        for tree in trees.values():
            tree.validate()
        for tree in trees.values():
            tree.check()
    report = _report(buffers["report.json"], buffers["cell-counts.csv"], source)
    cells = _read_cells(buffers["cell-counts.csv"])
    counts = report.get("counts")
    dispositions = report.get("dispositions")
    if (
        not isinstance(counts, dict)
        or not isinstance(dispositions, dict)
        or set(dispositions) != set(DISPOSITIONS)
    ):
        raise ValueError("Native registry conservation counts are incomplete")
    counts = {
        key: _integer(counts.get(key))
        for key in (
            "source_uuids",
            "selected_class_uuids",
            "included_uuids",
            "raw_point_occurrences",
            "valid_point_occurrences",
        )
    }
    dispositions = {key: _integer(value) for key, value in dispositions.items()}
    included = counts["included_uuids"]
    if (
        sum(dispositions.values()) != counts["source_uuids"]
        or counts["source_uuids"] - dispositions["unselected_native_class"]
        != counts["selected_class_uuids"]
        or dispositions["included"] != included
        or sum(cell[2] for cell in cells) != included
        or _integer(report.get("cell_count_total")) != included
        or counts["valid_point_occurrences"] > counts["raw_point_occurrences"]
    ):
        raise ValueError("Native registry source/cell count conservation differs")
    geojson, accounting, operation = project_cells(cells, source.sha256)
    context = {
        "schema_version": "raa-native-registry-context-v1",
        "source": asdict(source),
        "inputs": {
            name: {"sha256": sha256(raw).hexdigest(), "byte_count": len(raw)}
            for name, raw in buffers.items()
        },
        "grid": GRID,
        "selection": report["selection"],
        "boundary": BOUNDARY,
        "counts": counts,
        "dispositions": dispositions,
        "excluded_uuids": counts["source_uuids"] - included,
        "display_accounting": accounting,
        "display_operation": operation,
        "source_verification": "independently pinned qualified aggregates; no original source replay",
        "native_profile_binding": "producer binding; not independently reconstructed here",
        "scientific_admission": False,
        "country_assignment": "not_performed",
        "chronology": "unsupported",
        "legacy_WFS_equivalence": False,
    }
    return NativeRegistryContextSnapshot(
        canonical_bytes(context), buffers["cell-counts.csv"], canonical_bytes(geojson)
    )
