"""Reject owner, capture, partition and scientific-contract drift without integration."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
import math
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    ring_inputs as inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.study_inputs import (
    AXIS,
    CORES,
    geometry_record,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.radial_envelope_workflow import (
    nested_edges,
)

from .test_study_inputs import packets


def ring_packets() -> tuple[dict[str, Any], ...]:
    public, original, _ = packets()
    protocol = json.loads(Path(inputs.PROTOCOL).read_text())
    prediction: dict[str, Any] = {"axis": list(AXIS), "geometry": []}
    freeze: dict[str, Any] = {
        "source_commit": protocol["captured_law_source_commit"],
        "schema_version": "continuous-receiver-input-freeze.v1",
        "historical_A_authenticated": False,
        "native_prefix": [],
        "cases": [],
    }
    for index, taxon in enumerate(AXIS):
        survival = (0.5, 0.25)[index]

        def captured(value: float) -> dict[str, Any]:
            numerator, denominator = value.as_integer_ratio()
            return {
                "hex": value.hex(),
                "numerator": numerator,
                "denominator": denominator,
            }

        freeze["native_prefix"].append(
            {
                "taxon": taxon,
                "S1": captured(survival),
                "A": captured(-math.log(survival)),
                "parameters": {
                    "fall_speed_m_s": (0.024, 0.032)[index],
                    "diffusion_coefficient": 0.12,
                    "turbulence_parameter": 0.25,
                    "wind_speed_m_s": 3.0,
                },
            }
        )
    for index, core in enumerate(CORES):
        row = public["geometry"][index * 2]
        radius = original["cores"][index]["radius_m"]
        edges = [radius + (100000 - radius) * j / 8 for j in range(9)]
        saved = {
            "core": core,
            "radius_m": radius,
            "anchor_order": row["anchor_order"],
            "anchor_xy_m": row["anchor_xy_m"],
            "taxa": [
                {
                    "step_bounds": {
                        "annuli": [
                            {"inner_radius_m": a, "outer_radius_m": b}
                            for a, b in zip(edges[:-1], edges[1:], strict=True)
                        ]
                    }
                }
            ],
        }
        prediction["geometry"].append(saved)
        protocol["edges_exact"][core] = [
            str(Fraction(v)) for v in nested_edges(saved, 100000.0)
        ]
        for taxon_index, taxon in enumerate(AXIS):
            geometry = Geometry(
                Fraction(-math.log((0.5, 0.25)[taxon_index])),
                Fraction(radius),
                Fraction(100000),
                (
                    Fraction(row["anchor_xy_m"][0][0]),
                    Fraction(row["anchor_xy_m"][0][1]),
                ),
                (
                    Fraction(row["anchor_xy_m"][1][0]),
                    Fraction(row["anchor_xy_m"][1][1]),
                ),
            )
            freeze["cases"].append(
                {
                    "core": core,
                    "taxon": taxon,
                    "anchor_order": row["anchor_order"],
                    "geometry": geometry_record(geometry),
                }
            )
    return public, original, freeze, prediction, protocol


def test_captured_law_and_all_774_exact_edge_owners() -> None:
    values = ring_packets()
    inputs.validate_protocol(values[-1])
    geometries, edges = inputs.select_geometry(*values)
    assert len(geometries) == 6 and sum(map(len, edges)) == 774
    for i, (model, boundaries) in enumerate(zip(geometries, edges, strict=True)):
        assert model.receiver == boundaries[0] and model.outer == boundaries[-1]
        assert boundaries == edges[i - i % 2]


@pytest.mark.parametrize(
    "mutation",
    [
        "owner",
        "anchors",
        "radius",
        "capture",
        "ratio",
        "parameters",
        "edges",
        "historical",
    ],
)
def test_reject_scientific_source_drift(mutation: str) -> None:
    public, original, freeze, prediction, protocol = deepcopy(ring_packets())
    if mutation == "owner":
        public["geometry"].reverse()
    elif mutation == "anchors":
        prediction["geometry"][0]["anchor_xy_m"][0][0] += 1
    elif mutation == "radius":
        original["cores"][0]["radius_m"] += 1
    elif mutation == "capture":
        freeze["native_prefix"][0]["A"]["hex"] = (0.3).hex()
    elif mutation == "ratio":
        freeze["native_prefix"][0]["A"]["numerator"] = True
    elif mutation == "parameters":
        freeze["native_prefix"][0]["parameters"]["wind_speed_m_s"] = 4.0
    elif mutation == "edges":
        protocol["edges_exact"]["BOKE"][1] = "81"
    else:
        freeze["historical_A_authenticated"] = True
    with pytest.raises(ValueError):
        inputs.select_geometry(public, original, freeze, prediction, protocol)


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("numerical_contract", "endpoint_population", 773),
        ("numerical_contract", "coefficient_full_width_exact", "1/1000000"),
        ("resources", "wall_seconds", 181),
        ("independent_resources", "all_output_bytes", 6000000),
        ("numerical_contract", "all_initial_endpoints_before_refinement", 1),
        ("resources", "wall_seconds", 180.0),
    ],
)
def test_reject_precision_population_or_resource_escalation(
    section: str, key: str, value: object
) -> None:
    protocol = ring_packets()[-1]
    protocol[section][key] = value
    with pytest.raises(ValueError):
        inputs.validate_protocol(protocol)


def test_contribution_profile_preserves_original_numeric_contract() -> None:
    protocol = ring_packets()[-1]
    original = deepcopy(protocol["numerical_contract"])
    protocol["frontier"] = {
        "priority": "coefficient_contribution",
        "q_uncertainty_full_width_exact": "1/16000000000",
    }
    inputs.validate_protocol(protocol)
    assert protocol["numerical_contract"] == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("priority", "score_selected"),
        ("priority", "raw_width"),
        ("q_uncertainty_full_width_exact", "1/1000"),
    ],
)
def test_reject_changed_contribution_scope(field: str, value: str) -> None:
    protocol = ring_packets()[-1]
    protocol["frontier"] = {
        "priority": "coefficient_contribution",
        "q_uncertainty_full_width_exact": "1/16000000000",
    }
    protocol["frontier"][field] = value
    with pytest.raises(ValueError):
        inputs.validate_protocol(protocol)
