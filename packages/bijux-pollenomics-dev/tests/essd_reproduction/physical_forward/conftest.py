"""Complete artificial eight-core sources; no scientific source values loaded."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.physical_forward import prediction as p
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import PROTOCOL


@pytest.fixture(scope="module")
def protocol() -> dict[str, Any]:
    """Return the declared read-only physical comparison protocol."""
    value = json.loads((Path(__file__).resolve().parents[5] / PROTOCOL).read_bytes())
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def artificial_sources(
    protocol: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Construct artificial source tables using only declared schema metadata."""
    swedish: dict[str, Any] = {
        "schema_version": "swedish-static-basin-maintained-producer.v1",
        "producer_candidate": protocol["source_epochs"]["swedish"],
        "cores": [],
    }
    nordic: dict[str, Any] = {
        "candidate": protocol["source_epochs"]["nordic"],
        "cases": [],
    }
    for expected in protocol["source_cores"]:
        size = len(expected["axis"])
        counts = list(range(2, size + 2))
        row = {
            key: expected[key]
            for key in (
                "native_site_id",
                "native_dataset_id",
                "native_collection_unit_id",
            )
        }
        row["parameter_taxa"] = expected["axis"]
        results = [
            {
                "younger_cal_bp": younger,
                "older_cal_bp_exclusive": older,
                "counts": [counts],
                "panel_count_denominator": sum(counts),
                "actual_source_panel_presence": True,
                "assumed_zero_cells": 0,
                "local_native_sample_support_sha256": "0" * 64,
                "local_actual_source_support_sha256": "0" * 64,
                "profile": "metadata_radius_wind_3",
            }
            for younger, older in expected["windows"]
        ]
        row["results"] = results
        if expected["country"] == "SE":
            row.update(
                metadata_code=expected["id"],
                ppe=[2.0] * size,
                ppe_standard_deviation=[0.1] * size,
                quadrature=[
                    {"profile": "metadata_radius_wind_3", "factors": [[0.5] * size]}
                ],
            )
            swedish["cores"].append(row)
        else:
            row.update(
                source_handle=expected["id"],
                case_id=expected["source_profile"],
                PPE=[2.0] * size,
                PPE_SD=[0.1] * size,
                physical_response={"factors": [[0.5] * size]},
                static_geometry={"id": "metadata_static_radius"},
            )
            nordic["cases"].append(row)
    for number in range(5):
        extra = copy.deepcopy(nordic["cases"][0])
        extra["static_geometry"]["id"] = "artificial-nonbaseline-" + str(number)
        nordic["cases"].append(extra)
    return swedish, nordic


@pytest.fixture
def fake_points(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install deterministic inverse and forward stubs for the owned fixtures."""
    monkeypatch.setattr(
        p,
        "_inverse",
        lambda source: tuple(n / sum(source.counts) for n in source.counts),
    )

    def forward(target: p.Target, cover: tuple[float, ...]) -> tuple[float, ...]:
        mass = [
            c * k * e for c, k, e in zip(cover, target.kernels, target.ppe, strict=True)
        ]
        return tuple(v / sum(mass) for v in mass)

    monkeypatch.setattr(p, "_forward", forward)
