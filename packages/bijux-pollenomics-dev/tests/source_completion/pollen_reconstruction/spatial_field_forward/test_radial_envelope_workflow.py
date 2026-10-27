"""Fixed call populations, literal failures and the persisted scoring boundary."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward import (
    radial_envelope as exact,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward import (
    radial_envelope_workflow as workflow,
)


def synthetic_geometry(core: str) -> dict[str, Any]:
    edges = [float(2**i) for i in range(9)]
    anchors = [name for name in workflow.CORES if name != core]
    return {
        "core": core,
        "anchor_order": anchors,
        "anchor_xy_m": [[1000.0, 0.0], [-1000.0, 0.0]],
        "radius_m": 1.0,
        "homogeneous_taxa": [{"factor": 0.128} for _ in range(2)],
        "taxa": [
            {
                "taxon": name,
                "fall_speed_m_s": fall,
                "primary": {
                    "homogeneous_factor": 0.128,
                    "anchor_factors": [0.064, 0.064],
                },
                "step_bounds": {
                    "annuli": [
                        {"inner_radius_m": a, "outer_radius_m": b}
                        for a, b in zip(edges[:-1], edges[1:], strict=True)
                    ]
                },
            }
            for name, fall in zip(workflow.AXIS, (0.024, 0.032), strict=True)
        ],
    }


def synthetic_context(geometry: dict[str, Any], index: int) -> dict[str, Any]:
    core = geometry["core"]
    return {
        "context_id": f"{core}:{index}",
        "target": {"core": core, "window": [index, index + 1], "sample_ids": [index]},
        "training": [
            {"core": name, "cover": [0.5, 0.5]} for name in geometry["anchor_order"]
        ],
        "families": {
            name: {"pollen_fraction": [0.5, 0.5]} for name in workflow.FAMILIES
        },
    }


def test_nested_partition_preserves_every_coarse_boundary() -> None:
    geometry = synthetic_geometry("BOKE")
    edges = workflow.nested_edges(geometry, 256)
    assert len(edges) == 129
    assert edges[::16] == [float(2**i) for i in range(9)]
    geometry["taxa"][0]["step_bounds"]["annuli"][2]["inner_radius_m"] = 0
    with pytest.raises(ValueError, match="Original ring"):
        workflow.nested_edges(geometry, 256)


def test_reference_point_outside_does_not_widen_the_conditional_model() -> None:
    saved = synthetic_geometry("BOKE")
    geometry = {
        "core": "BOKE",
        "anchor_order": saved["anchor_order"],
        "status": "finite_mass_envelope",
        "taxa": [
            {
                "refined_K_exact": "1",
                "anchor_factor_bounds_exact": [["1/2", "1/2"], ["1/2", "1/2"]],
                "legacy_mass_correspondence_status": "passed_numerical_mass_diagnostic",
            }
            for _ in range(2)
        ],
    }
    context = synthetic_context(saved, 0)
    original = workflow.prediction_context(context, geometry, [1, 1])
    context["families"][workflow.FAMILIES[2]]["pollen_fraction"] = [0.9, 0.1]
    outside = workflow.prediction_context(context, geometry, [1, 1])
    assert outside["reference_point_status"] == "refused_reference_point_correspondence"
    assert outside["status"] == "finite_mass_envelope"
    assert (
        outside["conditional_spatial_prediction_bounds_exact"]
        == original["conditional_spatial_prediction_bounds_exact"]
    )
    assert outside["deposition_bounds_exact"] == original["deposition_bounds_exact"]


@pytest.mark.parametrize("fail_first", [False, True])
def test_full_synthetic_consumer_closes_ranges_before_observations_and_keeps_all_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail_first: bool
) -> None:
    repository = Path(__file__).resolve().parents[6]
    protocol = json.loads((repository / workflow.PROTOCOL).read_text())
    protocol_path = tmp_path / workflow.PROTOCOL
    protocol_path.parent.mkdir(parents=True)
    protocol_path.write_text(json.dumps(protocol))
    geometries = [synthetic_geometry(core) for core in workflow.CORES]
    contexts = [
        synthetic_context(geometry, i) for geometry in geometries for i in range(6)
    ]
    prediction = {
        "source_commit": protocol["prior_producer_source_commit"],
        "geometry": geometries,
        "contexts": contexts,
        "ppe": [1.0, 1.0],
    }
    physical = {
        "regional_extent_m": 256.0,
        "diffusion_coefficient": 0.12,
        "turbulence_parameter": 0.25,
        "wind_speed_m_s": 3.0,
    }
    source_scores = [
        {
            "context_id": context["context_id"],
            "core": context["target"]["core"],
            "window": context["target"]["window"],
            "sample_ids": context["target"]["sample_ids"],
            "family": family,
            "predicted_fraction": [0.5, 0.5],
            "observed_fraction": [0.5, 0.5],
            "status": "scored",
            **dict.fromkeys(exact.METRICS, 0.0),
        }
        for context in contexts
        for family in workflow.FAMILIES
    ]
    old_summaries = {
        "families": [
            {
                "family": family,
                "equal_place": {"metrics": dict.fromkeys(exact.METRICS, 0.0)},
            }
            for family in workflow.FAMILIES
        ],
        "pairwise": [
            {
                "first_family": a,
                "second_family": b,
                "metrics": {
                    metric: {"point_difference": 0.0} for metric in exact.METRICS
                },
            }
            for a, b in combinations(workflow.FAMILIES, 2)
        ],
    }
    native = {
        "source_commit": prediction["source_commit"],
        "prediction_file": {
            "sha256": protocol["repository_inputs"][protocol["source_prediction"]][
                "sha256"
            ]
        },
        "scores": source_scores,
        "summaries": old_summaries,
    }
    destination = tmp_path / "artifacts/radial-envelope-synthetic"
    destination.parent.mkdir()
    observed_read_after_close = []

    def pinned_files(root: Path, declarations: dict[str, Any]) -> dict[str, bytes]:
        assert root == tmp_path
        if protocol["source_result"] in declarations:
            frozen = destination / "prediction-ranges.json"
            assert frozen.is_file()
            assert len(json.loads(frozen.read_text())["contexts"]) == 18
            observed_read_after_close.append(True)
        return {name: json.dumps(native).encode() for name in declarations}

    count = 0

    def ring_response(**kwargs: Any) -> Any:
        nonlocal count
        count += 1
        assert kwargs["absolute_tolerance"] == 1e-9 / 128
        if fail_first and count == 1:
            raise ValueError("Synthetic ring refusal remains literal")
        return SimpleNamespace(factor=0.001, estimated_absolute_error=1e-12)

    monkeypatch.setattr(workflow, "source_revision", lambda *_: "committed_source")
    monkeypatch.setattr(
        workflow,
        "read_prediction_inputs",
        lambda *_: (deepcopy(prediction), {"physical": physical}),
    )
    monkeypatch.setattr(workflow, "bound_files", pinned_files)
    monkeypatch.setattr(workflow, "circular_receiver_annulus", ring_response)
    result = workflow.publish(tmp_path, destination)
    assert count == result["actual_ring_calls"] == 768
    assert observed_read_after_close
    assert len(result["scores"]) == 54
    assert result["refused_ring_calls"] == int(fail_first)
    assert result["prior_point_values_changed"] is False
    packet = json.loads((destination / "prediction-ranges.json").read_text())
    assert len(packet["geometry"]) == 3
    assert all(
        len(geometry["angular_certificates"]) == 129 for geometry in packet["geometry"]
    )
    if fail_first:
        failed = packet["geometry"][0]["taxa"][0]
        assert (
            failed["ring_refusals"][0]
            == "ValueError: Synthetic ring refusal remains literal"
        )
        assert failed["refined_K_exact"] is None
        assert (
            sum(
                row["status"] == "refused_geometry_envelope" for row in result["scores"]
            )
            == 6
        )
        assert (
            result["summaries"]["families"][2]["status"] == "refused_incomplete_context"
        )
    else:
        total = Fraction(packet["geometry"][0]["taxa"][0]["refined_K_exact"])
        assert total == 128 * Fraction(0.001)
        assert result["reference_point_refusals"] == 0
        assert all(
            row["status"] == "complete_conditional_context"
            for row in result["summaries"]["families"]
        )
