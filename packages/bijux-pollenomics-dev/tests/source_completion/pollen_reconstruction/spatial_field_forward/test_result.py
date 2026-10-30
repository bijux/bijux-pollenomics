"""Verify the saved spatial study against original sources and separate arithmetic."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import pytest

from .integration import normalized_first_bounds, verify_saved_geometry
from .native_panels import core_panels
from .scoring import (
    Pair,
    close,
    reconstruct_predictions,
    source_cover,
    verify_score_ledger,
)
from .sources import AXIS, EXPECTED, WINDOWS, bound_files, original_inputs

pytestmark = pytest.mark.generated_artifacts
REPOSITORY = Path(__file__).resolve().parents[6]
OUTPUT = "artifacts/physical-core/spatial-field-forward/native-run"
FAMILIES = (
    "direct_pollen_idw",
    "centre_cover_idw_forward",
    "spatial_cover_idw_forward",
)


def _same(first: object, second: object) -> None:
    assert json.dumps(first, sort_keys=True, allow_nan=False) == json.dumps(
        second, sort_keys=True, allow_nan=False
    )


def test_saved_spatial_study_matches_originals_and_independent_arithmetic() -> None:
    source_root = REPOSITORY.parent / "-bijux-pollenomics-data"
    original = original_inputs(REPOSITORY, source_root)
    protocol, cores = original["protocol"], original["cores"]
    paths = {
        name: REPOSITORY / OUTPUT / name
        for name in ("prediction-freeze.json", "result.json")
    }
    bodies = {name: path.read_bytes() for name, path in paths.items()}
    frozen = json.loads(bodies["prediction-freeze.json"])
    result = json.loads(bodies["result.json"])
    ppe_pair = (float(frozen["ppe"][0]), float(frozen["ppe"][1]))
    fall_pair = (float(frozen["fall"][0]), float(frozen["fall"][1]))
    assert (
        result["source_commit"] == frozen["source_commit"]
        and len(frozen["source_commit"]) == 40
    )
    assert frozen["axis"] == list(AXIS)
    assert frozen["ppe"] == [row[0] for row in original["parameters"]]
    assert frozen["fall"] == [row[2] for row in original["parameters"]]
    expected_pins = {
        **{
            f"repository/{name}": identity["sha256"]
            for name, identity in protocol["repository_files"].items()
        },
        **{
            f"source-store/{name}": identity["sha256"]
            for name, identity in protocol["source_store_files"].items()
        },
    }
    assert frozen["input_sha256"] == result["input_sha256"] == expected_pins
    assert result["prediction_file"] == {
        "path": "prediction-freeze.json",
        "bytes": len(bodies["prediction-freeze.json"]),
        "sha256": sha256(bodies["prediction-freeze.json"]).hexdigest(),
    }
    all_accounts, panels = [], {}
    for name, core in cores.items():
        accounts, cells = core_panels(core["spec"], core["site"])
        all_accounts.extend(accounts)
        panels.update(
            {f"{name}:{low}:{high}": cell for (low, high), cell in cells.items()}
        )
    assert (
        len(all_accounts) == 147
        and sum(row["status"] == "selected_frozen_subset" for row in all_accounts) == 59
    )
    assert len(panels) == 18
    assert (
        len(result["sample_accounts"])
        == len({(r["core"], r["sample_id"]) for r in result["sample_accounts"]})
        == 147
    )
    assert result["sample_status_counts"] == dict(
        Counter(r["status"] for r in all_accounts)
    )
    _same(
        {
            (row["core"] + ":" + str(row["sample_id"])): row
            for row in result["sample_accounts"]
        },
        {(row["core"] + ":" + str(row["sample_id"])): row for row in all_accounts},
    )
    recorded_observations = {
        f"{row['core']}:{row['window'][0]}:{row['window'][1]}": row
        for row in result["observations"]
    }
    assert len(recorded_observations) == len(result["observations"]) == 18
    _same(recorded_observations, panels)
    declarations = {name: core["spec"] for name, core in cores.items()}
    homogeneous, diagnostics = verify_saved_geometry(
        frozen["geometry"], declarations, protocol["physical"], fall_pair
    )
    geometries = {row["core"]: row for row in frozen["geometry"]}
    contexts = {row["context_id"]: row for row in frozen["contexts"]}
    assert len(contexts) == len(frozen["contexts"]) == 18
    assert set(contexts) == {
        f"{core}:{low}:{high}" for core in EXPECTED for low, high in WINDOWS
    }
    expected_predictions, expected_bounds = {}, {}
    for identity, context in contexts.items():
        core, low, high = identity.split(":")
        spec, observation = declarations[core], panels[identity]
        target = context["target"]
        _same(
            target,
            {
                "core": core,
                "site_id": spec["site_id"],
                "dataset_id": spec["dataset_id"],
                "collection_unit_id": spec["collection_unit_id"],
                "centre_lon_lat": spec["analysis_centre_lon_lat"],
                "radius_m": spec["radius_m"],
                "window": [int(low), int(high)],
                "sample_ids": observation["sample_ids"],
            },
        )
        assert context["geometry_core"] == core
        anchor_names = sorted(set(EXPECTED) - {core})
        assert [row["core"] for row in context["training"]] == anchor_names
        assert len({row["site_id"] for row in context["training"]}) == 2
        counts: list[Pair] = []
        for name, training in zip(anchor_names, context["training"], strict=True):
            source, declaration = panels[f"{name}:{low}:{high}"], declarations[name]
            for field in (
                "site_id",
                "dataset_id",
                "collection_unit_id",
                "window",
                "sample_ids",
            ):
                _same(training[field], source[field])
            assert training["site_id"] != target["site_id"]
            assert not set(training["sample_ids"]).intersection(target["sample_ids"])
            assert training["centre_lon_lat"] == declaration["analysis_centre_lon_lat"]
            assert training["radius_m"] == declaration["radius_m"]
            assert training["counts"] == source["projected_counts"]
            vector = (
                float(source["projected_counts"][0]),
                float(source["projected_counts"][1]),
            )
            assert training["pollen_fraction"] == pytest.approx(
                close(vector), abs=2e-12, rel=0
            )
            if name in homogeneous:
                expected_cover = source_cover(vector, homogeneous[name], ppe_pair)
                if "cover" in training:
                    assert training["cover"] == pytest.approx(
                        expected_cover, abs=2e-12, rel=0
                    )
                    assert training["homogeneous_factors"] == pytest.approx(
                        homogeneous[name], abs=2e-12, rel=0
                    )
            counts.append(vector)
        geometry = geometries[core]
        weights = geometry["centre_weights"]
        fractions = [close(vector) for vector in counts]
        expected: dict[str, Pair] = {
            FAMILIES[0]: (
                sum(weights[s] * fractions[s][0] for s in range(2)),
                sum(weights[s] * fractions[s][1] for s in range(2)),
            )
        }
        covers = None
        if all(name in homogeneous for name in [core, *anchor_names]):
            spatial = (
                (
                    (
                        float(geometry["taxa"][0]["primary"]["anchor_factors"][0]),
                        float(geometry["taxa"][0]["primary"]["anchor_factors"][1]),
                    ),
                    (
                        float(geometry["taxa"][1]["primary"]["anchor_factors"][0]),
                        float(geometry["taxa"][1]["primary"]["anchor_factors"][1]),
                    ),
                )
                if geometry["status"] == "qualified"
                else None
            )
            expected, covers = reconstruct_predictions(
                (counts[0], counts[1]),
                (homogeneous[anchor_names[0]], homogeneous[anchor_names[1]]),
                ppe_pair,
                homogeneous[core],
                weights[0],
                spatial,
            )
        assert set(context["families"]) == set(FAMILIES)
        for family, record in context["families"].items():
            if family not in expected:
                assert record["status"] == "refused_prediction" and record["reason"]
                continue
            prediction = expected[family]
            assert record["status"] == "predicted"
            assert record["pollen_fraction"] == pytest.approx(
                prediction, abs=2e-12, rel=0
            )
            if family == FAMILIES[2]:
                assert covers is not None
                mass = [
                    [
                        frozen["ppe"][i]
                        * sum(
                            geometry["taxa"][i]["step_bounds"]["anchor_factor_bounds"][
                                s
                            ][end]
                            * covers[s][i]
                            for s in range(2)
                        )
                        for i in range(2)
                    ]
                    for end in range(2)
                ]
                limits = normalized_first_bounds(
                    (mass[0][0], mass[0][1]), (mass[1][0], mass[1][1])
                )
            else:
                limits = prediction[0], prediction[0]
            assert record["prediction_bounds"][0] == pytest.approx(
                limits, abs=2e-12, rel=0
            )
            assert record["prediction_bounds"][1] == pytest.approx(
                (1 - limits[1], 1 - limits[0]), abs=2e-12, rel=0
            )
            expected_predictions[identity, family] = (prediction[0], prediction[1])
            expected_bounds[identity, family] = limits
    observed = {
        identity: (float(row["projected_counts"][0]), float(row["projected_counts"][1]))
        for identity, row in panels.items()
    }
    checked = verify_score_ledger(
        result, expected_predictions, expected_bounds, observed
    )
    assert (
        result["requested_contexts"] == 18 and result["requested_family_outcomes"] == 54
    )
    assert result["model_fits"] == 0
    for flag in (
        "target_score_parameter_selection",
        "untouched_validation_or_vegetation_accuracy_claim",
        "historical_core_admission_changed",
    ):
        assert result[flag] is False
    bound_files(REPOSITORY, protocol["repository_files"])
    bound_files(source_root, protocol["source_store_files"])
    assert all(path.read_bytes() == bodies[name] for name, path in paths.items())
    print(
        json.dumps(
            {
                "source_rows": 147,
                "selected_samples": 59,
                "source_contexts": 18,
                "predictions_sha256": sha256(
                    bodies["prediction-freeze.json"]
                ).hexdigest(),
                "result_sha256": sha256(bodies["result.json"]).hexdigest(),
                "integration": diagnostics,
                "scores": checked,
            },
            indent=2,
            allow_nan=False,
        )
    )
