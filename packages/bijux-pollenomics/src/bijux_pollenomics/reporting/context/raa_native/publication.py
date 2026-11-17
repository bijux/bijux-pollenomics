"""Publish only bounded aggregate buffers through the shared callback tree owner."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

from ....core.errors.cleanup import add_cleanup_note
from ....core.filesystem import BoundedInputTree, DirectoryAnchor
from ....core.filesystem.callback_publication import publish_callback_tree
from ...map_publication_raa_native import NATIVE_REGISTRY_POSTURE
from .projection import project_cells
from .snapshot import (
    BUFFER_LIMIT,
    COUNTS_LIMIT,
    PROFILE_BINDING_SCOPE,
    REPORT_LIMIT,
    SOURCE_VERIFICATION,
    NativeRegistryContextSnapshot,
    NativeRegistrySource,
    _conservation,
    _digest,
    _object,
    _read_cells,
    _report,
    canonical_bytes,
)

RELATIVE_DIRECTORY = Path("context/raa-native-registry")
_NAMES = (
    "context.json",
    "cell-counts.csv",
    "cells.geojson",
    "publication_manifest.json",
)


def _payloads(
    snapshot: NativeRegistryContextSnapshot,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(snapshot, NativeRegistryContextSnapshot):
        raise ValueError("Native registry publication requires a captured snapshot")
    context = json.loads(snapshot.context_bytes, object_pairs_hook=_object)
    if (
        not isinstance(context, dict)
        or set(context)
        != {
            "schema_version",
            "source",
            "inputs",
            "grid",
            "selection",
            "boundary",
            "counts",
            "dispositions",
            "excluded_uuids",
            "display_accounting",
            "display_operation",
            "source_verification",
            "native_profile_binding",
            "scientific_admission",
            "country_assignment",
            "chronology",
            "legacy_WFS_equivalence",
        }
        or context.get("schema_version") != "raa-native-registry-context-v1"
        or context.get("scientific_admission") is not False
        or context.get("country_assignment") != "not_performed"
        or context.get("chronology") != "unsupported"
        or context.get("legacy_WFS_equivalence") is not False
    ):
        raise ValueError("Native registry snapshot posture differs")
    profile = context["native_profile_binding"]
    inputs = context["inputs"]
    if (
        context["source_verification"] != SOURCE_VERIFICATION
        or not isinstance(profile, dict)
        or set(profile) != {"sha256", "scope"}
        or not _digest(profile["sha256"])
        or profile["scope"] != PROFILE_BINDING_SCOPE
        or not isinstance(inputs, dict)
        or set(inputs) != {"report.json", "cell-counts.csv"}
    ):
        raise ValueError("Native registry public provenance scope differs")
    for name, limit in (
        ("report.json", REPORT_LIMIT),
        ("cell-counts.csv", COUNTS_LIMIT),
    ):
        record = inputs[name]
        if (
            not isinstance(record, dict)
            or set(record) != {"sha256", "byte_count"}
            or not _digest(record["sha256"])
            or type(record["byte_count"]) is not int
            or not 0 < record["byte_count"] <= limit
        ):
            raise ValueError("Native registry public input record differs")
    source = NativeRegistrySource(**context["source"])
    cells = _read_cells(snapshot.counts_bytes)
    _report(
        canonical_bytes(
            {
                **context,
                "schema_version": "raa-native-point-grid-v1",
                "source": {"sha256": source.sha256, "byte_count": source.byte_count},
                "native_profile_sha256": context["native_profile_binding"]["sha256"],
                "projection": {
                    "location_support_bounds": context["display_operation"][
                        "support_bounds"
                    ]
                },
                "files": {"cell-counts.csv": context["inputs"]["cell-counts.csv"]},
            }
        ),
        snapshot.counts_bytes,
        source,
    )
    counts, _ = _conservation(
        {**context, "cell_count_total": sum(row[2] for row in cells)}, cells
    )
    if canonical_bytes(context["counts"]) != canonical_bytes(counts):
        raise ValueError("Native registry public count fields differ")
    if (
        type(context["excluded_uuids"]) is not int
        or context["excluded_uuids"]
        != counts["source_uuids"] - counts["included_uuids"]
    ):
        raise ValueError("Native registry excluded count differs")
    geojson, accounting, operation = project_cells(cells, source.sha256)
    if (
        canonical_bytes(geojson) != snapshot.cells_bytes
        or canonical_bytes(accounting)
        != canonical_bytes(context.get("display_accounting"))
        or canonical_bytes(operation)
        != canonical_bytes(context.get("display_operation"))
        or context.get("counts", {}).get("included_uuids")
        != accounting["mapped_full_cell_uuids"]
        or context.get("inputs", {}).get("cell-counts.csv")
        != {
            "sha256": sha256(snapshot.counts_bytes).hexdigest(),
            "byte_count": len(snapshot.counts_bytes),
        }
    ):
        raise ValueError("Native registry snapshot geometry/count conservation differs")
    return context, geojson


def build_native_registry_layer(
    snapshot: NativeRegistryContextSnapshot,
) -> dict[str, object]:
    """Describe full-cell counts without country, calendar or analytical selection."""
    context, geojson = _payloads(snapshot)
    maximum = max(
        (row["properties"]["count"] for row in geojson["features"]), default=0
    )
    for feature in geojson["features"]:
        properties = feature["properties"]
        properties.update(
            {
                "registry_fill": next(
                    (
                        color
                        for threshold, color in (
                            (0.75, "#7f1d1d"),
                            (0.55, "#b91c1c"),
                            (0.35, "#ef4444"),
                            (0.20, "#f87171"),
                            (0.08, "#fca5a5"),
                        )
                        if maximum and properties["count"] / maximum >= threshold
                    ),
                    "#fee2e2",
                ),
                "name": properties["cell_id"],
                "category": "Conditional native registry cell",
                "popup_rows": [
                    {
                        "label": "Registry UUIDs per original 1° cell",
                        "value": properties["count"],
                    },
                    {
                        "label": "Native cell bounds (EPSG:4619)",
                        "value": json.dumps(properties["native_cell_bounds"]),
                    },
                    {
                        "label": "Display footprint",
                        "value": "Partial; full-cell count retained, not prorated"
                        if properties["partial_display_footprint"]
                        else "Full; full-cell count retained",
                    },
                    {
                        "label": "Source capture (not event time)",
                        "value": context["source"]["captured_at_utc"],
                    },
                    {
                        "label": "Limits",
                        "value": "Context only; country unassigned; chronology unsupported. Not events, population or count per km².",
                    },
                    {
                        "label": "Display operation",
                        "value": "EPSG:1879 approximate WGS84 display; native coordinate accuracy unknown",
                    },
                ],
            }
        )
    counts = [feature["properties"]["count"] for feature in geojson["features"]]
    partial = context["display_accounting"]["partial_footprint_cells"]
    return {
        **NATIVE_REGISTRY_POSTURE,
        "label": "Retained registry UUIDs per 1° SWEREF99 cell",
        "source_name": "Riksantikvarieämbetet retained native registry",
        "coverage_label": "Country unassigned; chronology unsupported; context only.",
        "geometry_label": "Synthetic full-cell count footprints",
        "description": (
            "Conditional native Fornlämning UUID counts per original 1° SWEREF99 cell; "
            "exactly one raw and one valid primary POINT. Not events, population or "
            "count per km². Exclusions remain in the aggregate report. "
            f"{partial} partial display footprints retain full-cell counts without prorating. "
            "Display operation EPSG:1879 is approximate; native coordinate accuracy unknown."
        ),
        "count": len(counts),
        "max_count": max(counts, default=0),
        "count_value_label": "Registry UUIDs per original 1° cell",
        "source": context["source"],
        "counts": context["counts"],
        "dispositions": context["dispositions"],
        "display_accounting": context["display_accounting"],
        "display_operation": context["display_operation"],
        "grid": context["grid"],
        "geojson": geojson,
        "style": {"stroke": "#7f1d1d", "fill": "#b91c1c"},
    }


def _buffers(snapshot: NativeRegistryContextSnapshot) -> dict[str, bytes]:
    _payloads(snapshot)
    result = dict(
        zip(
            _NAMES[:3],
            (snapshot.context_bytes, snapshot.counts_bytes, snapshot.cells_bytes),
            strict=True,
        )
    )
    result[_NAMES[3]] = canonical_bytes(
        {
            "schema_version": "raa-native-registry-publication-v1",
            "files": {
                name: {"sha256": sha256(raw).hexdigest(), "byte_count": len(raw)}
                for name, raw in result.items()
            },
        }
    )
    if any(len(raw) > BUFFER_LIMIT for raw in result.values()):
        raise ValueError("Native registry public buffers exceed their finite limits")
    return result


def publish_native_registry_context(
    snapshot: NativeRegistryContextSnapshot, *, output_dir: Path
) -> list[tuple[str, str]]:
    """Attach a closed four-file aggregate subtree, preserving prior/refused trees."""
    buffers = _buffers(snapshot)
    final = Path(output_dir).absolute() / RELATIVE_DIRECTORY

    def write(root: Path) -> None:
        with DirectoryAnchor(root) as anchor:
            for name, raw in buffers.items():
                anchor.check()
                descriptor = os.open(
                    name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=anchor.fd,
                )
                try:
                    remaining = memoryview(raw)
                    while remaining:
                        size = os.write(descriptor, remaining)
                        if size <= 0:
                            raise OSError(
                                "Native registry aggregate write made no progress"
                            )
                        remaining = remaining[size:]
                    anchor.check()
                except BaseException as error:
                    try:
                        os.close(descriptor)
                    except OSError as secondary:

                        def close_note(failure: OSError = secondary) -> str:
                            return f"Native registry descriptor close failed: {type(failure).__name__}"

                        add_cleanup_note(error, close_note)
                    raise
                else:
                    os.close(descriptor)

    def validate(root: Path) -> None:
        with BoundedInputTree(root, max_bytes=4 * BUFFER_LIMIT, max_files=4) as tree:
            if set(tree.files) != set(buffers) or set(tree.directories) != {""}:
                raise ValueError("Native registry publication namespace differs")
            for name, expected in buffers.items():
                if tree.read(root / name, max_bytes=BUFFER_LIMIT) != expected:
                    raise ValueError("Native registry published aggregate bytes differ")
            tree.validate()

    publish_callback_tree(
        final,
        write,
        namespace="raa-native-registry",
        label="Native registry context",
        validate=validate,
    )
    return [
        (f"Native registry {name}", (RELATIVE_DIRECTORY / name).as_posix())
        for name in _NAMES
    ]
