"""Declared model bins support display without promoting source chronology."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.lra_products.api import render_lra_report
from bijux_pollenomics.reporting.map_document.temporal_admission import feature_interval

from .support import encoded, geometry_fixture, product_fixture, rebind, sha


@pytest.mark.parametrize("endpoints", [(0, 0), (5400.25, 5600.75)])
def test_synthetic_model_bin_preserves_declared_support(
    tmp_path: Path, endpoints: tuple[float, float]
) -> None:
    product, request = product_fixture(tmp_path)
    for role in ("regional", "local"):
        request[role]["samples"][0]["age_support_bp"] = [list(endpoints)]
    request["temporal_matching"]["bins"][0].update(
        younger_bp=endpoints[0], older_bp=endpoints[1]
    )
    rebind(product, request)
    geometry = tmp_path / "geometry.json"
    geometry.write_bytes(encoded(geometry_fixture(product, request)))
    result = render_lra_report(
        product,
        expected_manifest_sha256=sha((product / "manifest.json").read_bytes()),
        geometry_path=geometry,
        expected_geometry_sha256=sha(geometry.read_bytes()),
        destination=tmp_path / "report",
    )
    layers = json.loads((result.directory / "model-layers.json").read_bytes())
    for layer in layers:
        assert layer["scientific_selection_enabled"] is False
        for feature in layer["features"]:
            semantics = feature["temporal_semantics"]
            assert feature_interval(feature) == endpoints
            assert semantics["time_start_bp"] == endpoints[0]
            assert semantics["time_end_bp"] == endpoints[1]
            assert semantics["evidence_class"] == "declared_stationarity_envelope"
            assert semantics["source_age_type"] == "calendar_bp"
            assert "reference_epoch" not in semantics
            assert "calibration" not in semantics
            assert feature["source_age_support_bp"] == [list(endpoints)]
            assert feature["scientific_acceptance"] == "not_evaluated"
            assert feature["candidate_ranking_eligible"] is False
