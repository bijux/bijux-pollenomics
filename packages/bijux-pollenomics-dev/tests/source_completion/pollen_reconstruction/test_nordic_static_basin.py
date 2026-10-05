"""Check native population, panel, mathematical and owned publication boundaries."""

from __future__ import annotations

import copy
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin import (
    producer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.authority import (
    CAPTURE_PINS,
    DESCRIPTOR,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.sources import (
    load_inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.summary import (
    products,
)


@pytest.fixture
def captured_repository(tmp_path):
    source = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages/bijux-pollenomics-dev/pyproject.toml").is_file()
    )
    for name in (*CAPTURE_PINS, DESCRIPTOR):
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, destination)
    return tmp_path


def test_retained_nordic_account_keeps_panels_and_cohorts_separate(captured_repository):
    result = producer.publish(
        captured_repository, captured_repository / "artifacts/output"
    )
    assert set(result) == producer.OUTPUTS
    domain = result["source-domain.json"]
    assert domain["unknown_reported_age_bounds_samples"] == 222
    assert domain["distinct_sites"] == 3
    assert domain["accepted_point_domain_samples"] == 313
    assert {
        row["native_dataset_id"]: row["parameter_taxa"] for row in domain["cores"]
    } == {
        4445: ["Betula", "Calluna vulgaris"],
        4446: [
            "Alnus glutinosa",
            "Betula",
            "Calluna vulgaris",
            "Corylus avellana",
            "Tilia",
            "Ulmus",
        ],
        20034: ["Betula", "Pinus sylvestris", "Poaceae"],
        52082: ["Betula", "Pinus sylvestris"],
    }
    assert (
        result["account.json"]["scientific_verification"][
            "current_retained_account_equation_check"
        ]["scalar_values_compared"]
        == 6840
    )
    assert result["attribution.json"]["rights_and_raw_redistribution_admitted"] is False
    assert (
        set(path.name for path in (captured_repository / "artifacts/output").iterdir())
        == producer.OUTPUTS
    )


@pytest.mark.parametrize("name", [*CAPTURE_PINS, DESCRIPTOR])
def test_every_retained_source_is_pinned(captured_repository, name):
    path = captured_repository / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source bytes changed"):
        producer.publish(captured_repository, captured_repository / "artifacts/output")
    assert not (captured_repository / "artifacts/output").exists()


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("fractional_count", "nonnegative integer"),
        ("residual", "NISP conservation"),
        ("hypothesized_mask", "imputation"),
        ("duplicate_case", "case, source or panel"),
        ("wrong_chronology", "named chronology"),
        ("false_covariance", "numerical equation"),
        ("false_se", "numerical equation"),
        ("bad_geometry", "hectare-to-radius"),
        ("cross_panel_axis", "numerical parameter axis"),
        ("bad_comparison", "comparison differs"),
        ("missing_bounds_claim", "missing chronology-bound"),
    ],
)
def test_changed_saved_scientific_contract_refuses(
    captured_repository, mutation, reason
):
    inputs = copy.deepcopy(load_inputs(captured_repository))
    report = inputs["report.json"]
    row = report["cases"][0]["results"][0]
    if mutation == "fractional_count":
        row["counts"][0][0] += 0.5
    elif mutation == "residual":
        row["unparameterized_reported_NISP_sum"] += 1
    elif mutation == "hypothesized_mask":
        row["assumed_zero_cells"] = 1
    elif mutation == "duplicate_case":
        report["cases"].append(copy.deepcopy(report["cases"][0]))
    elif mutation == "wrong_chronology":
        report["cases"][0]["selected_named_calibrated_chronology"]["chronology_id"] += 1
    elif mutation == "false_covariance":
        row["counting_covariance"][0][0] += 0.1
    elif mutation == "false_se":
        row["conditional_standard_error"][0] += 0.1
    elif mutation == "bad_geometry":
        report["cases"][1]["static_geometry"]["radius_m"] += 1
    elif mutation == "cross_panel_axis":
        report["cases"][0]["PPE"].pop()
    elif mutation == "bad_comparison":
        report["within_core_comparisons"][0]["windows"][0][
            "static_geometry_cover_minus_metadata_baseline"
        ][0] += 0.1
    elif mutation == "missing_bounds_claim":
        for case in report["cases"]:
            for value in case["results"]:
                value["source_age_bounds_missing"] = 0
    with pytest.raises(ValueError, match=reason):
        products(inputs)


@pytest.mark.parametrize("kind", ["existing", "traversal", "artifact_root", "symlink"])
def test_owned_output_boundary_preserves_user_paths(captured_repository, kind):
    output = captured_repository / "artifacts/output"
    if kind == "existing":
        output.mkdir(parents=True)
        (output / "user.txt").write_text("preserve")
    elif kind == "traversal":
        output = captured_repository / "artifacts/../escape"
    elif kind == "artifact_root":
        output = captured_repository / "artifacts"
    else:
        (captured_repository / "artifacts").mkdir()
        (captured_repository / "artifacts/link").symlink_to(
            captured_repository, target_is_directory=True
        )
        output = captured_repository / "artifacts/link/output"
    with pytest.raises(ValueError):
        producer.publish(captured_repository, output)
    if kind == "existing":
        assert (output / "user.txt").read_text() == "preserve"
    assert not (captured_repository / "escape").exists()


def test_atomic_failure_leaves_no_nordic_products(captured_repository, monkeypatch):
    def refuse(*args):
        raise OSError("atomic publication refused")

    monkeypatch.setattr(producer.os, "rename", refuse)
    with pytest.raises(OSError, match="publication refused"):
        producer.publish(captured_repository, captured_repository / "artifacts/output")
    assert list((captured_repository / "artifacts").iterdir()) == []


@pytest.mark.parametrize("failure_at", [2, 3])
def test_late_source_tamper_removes_only_owned_products(
    captured_repository, monkeypatch, failure_at
):
    original = producer.load_inputs
    calls = 0

    def monitored(root):
        nonlocal calls
        calls += 1
        if calls == failure_at:
            path = root / next(iter(CAPTURE_PINS))
            path.write_bytes(path.read_bytes() + b" ")
        return original(root)

    monkeypatch.setattr(producer, "load_inputs", monitored)
    with pytest.raises(ValueError, match="source bytes changed"):
        producer.publish(captured_repository, captured_repository / "artifacts/output")
    assert not (captured_repository / "artifacts/output").exists()


def test_doi_and_investigator_records_do_not_close_primary_publications(
    captured_repository,
):
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.attribution import (
        attribution,
    )

    inputs = load_inputs(captured_repository)
    assert all(
        row["raw_source_metadata"]["dataset"]["doi"]
        for row in inputs["verification/source-census.json"]["cores"]
    )
    assert all(
        row["raw_source_metadata"]["dataset"]["datasetpi"]
        for row in inputs["verification/source-census.json"]["cores"]
    )
    del inputs["verification/publication-metadata/dataset-4445.json"]
    with pytest.raises(ValueError, match="primary publication source capture missing"):
        attribution(inputs)


def test_chronology_citation_uses_actual_named_solsoe_models(captured_repository):
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.attribution import (
        attribution,
    )

    inputs = load_inputs(captured_repository)
    account = attribution(inputs)
    chronology = account["preferred_policy_citations"][2]
    assert "Giesecke et al. (2014)" in chronology["reference"]
    actual_models = {
        row["source_core"]["native_dataset_id"]: row[
            "selected_named_calibrated_chronology"
        ]
        for row in inputs["verification/source-census.json"]["cores"]
    }
    assert chronology["selected_chronology_ids"] == [
        actual_models[4445]["chronology_id"],
        actual_models[4446]["chronology_id"],
    ]
    assert all(
        "Giesecke et al. 2014" in actual_models[did]["model"]["chronologyname"]
        for did in (4445, 4446)
    )
    assert (
        actual_models[20034]["chronology_id"]
        not in chronology["selected_chronology_ids"]
    )
    assert (
        actual_models[52082]["chronology_id"]
        not in chronology["selected_chronology_ids"]
    )
    assert "no article acquisition" in chronology["scope_limit"]
