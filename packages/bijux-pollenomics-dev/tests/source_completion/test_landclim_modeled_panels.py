"""Source-bound LandClim panel semantics and numerical refusal checks."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.modeled_context import build_modeled_context_manifest
from bijux_pollenomics_dev.source_completion.landclim_modeled_panels import (
    SOURCE,
    _range,
    derive,
)

REPOSITORY = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module")
def source_and_manifest() -> tuple[dict[str, Any], dict[str, Any]]:
    source_path = REPOSITORY / SOURCE
    geojson = json.loads(source_path.read_text())
    layer = build_external_polygon_layer(geojson, source_path=source_path)
    manifest = cast(dict[str, Any], build_modeled_context_manifest([layer]))
    return geojson, manifest


def test_four_source_panels_keep_country_windows_quality_and_uncertainty(
    source_and_manifest: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    geojson, manifest = source_and_manifest
    rows = derive(geojson, manifest)
    assert len(rows) == 400
    assert {row["metric_key"] for row in rows} == {"ET", "ST", "OL", "AL"}
    oldest_denmark = [
        row
        for row in rows
        if row["country"] == "Denmark" and row["source_window"] == "11200-11700 BP"
    ]
    assert len(oldest_denmark) == 4
    assert all(row["cell_count"] == 6 for row in oldest_denmark)
    assert all(row["modeled_count"] == 1 for row in oldest_denmark)
    assert all(row["no_pollen_data_count"] == 5 for row in oldest_denmark)
    assert all(row["minimum_standard_error_percent"] != "" for row in oldest_denmark)
    agricultural = next(row for row in oldest_denmark if row["metric_key"] == "AL")
    assert agricultural["source_class"] == "source_pft_component_of_open_land"
    assert agricultural["source_label"] == "Agricultural land - cereals"
    assert agricultural["minimum_estimate_percent"] == "0"


def test_source_label_drift_is_refused(
    source_and_manifest: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    geojson, manifest = source_and_manifest
    stale = deepcopy(manifest)
    families = stale["metric_families"]
    agricultural = next(
        metric
        for family in families
        if family["key"] == "source_pft_codes"
        for metric in family["metrics"]
        if metric["key"] == "AL"
    )
    agricultural["definition"] = "Measured crop pollen"
    with pytest.raises(ValueError, match="Source metric label changed: AL"):
        derive(geojson, stale)


def test_empty_modeled_group_has_null_numeric_ranges() -> None:
    assert _range([]) == ("", "")
