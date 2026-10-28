"""Check native population, panel, mathematical and owned publication boundaries."""

from __future__ import annotations

import copy
import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin import (
    producer,
    sources,
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


def _object(value: object) -> dict[str, object]:
    """Require a retained JSON object while preserving its mutation identity."""
    assert isinstance(value, dict) and all(isinstance(key, str) for key in value)
    return value


def _array(value: object) -> list[object]:
    """Require a retained JSON array while preserving its mutation identity."""
    assert isinstance(value, list)
    return value


def _records(value: object) -> list[dict[str, object]]:
    """Admit saved records without replacing the objects under mutation."""
    return [_object(row) for row in _array(value)]


def _number(value: object) -> int | float:
    """Require an actual numerical cell before changing a retained count or value."""
    assert isinstance(value, (int, float)) and type(value) in (int, float)
    return value


def _text(value: object) -> str:
    """Require an actual citation or chronology label before reading its text."""
    assert isinstance(value, str)
    return value


@pytest.fixture
def captured_repository(tmp_path: Path) -> Path:
    """Provide captured repository for the retained source contract."""
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


def test_retained_nordic_account_keeps_panels_and_cohorts_separate(
    captured_repository: Path,
) -> None:
    """Verify retained nordic account keeps panels and cohorts separate."""
    result = producer.publish(
        captured_repository, captured_repository / "artifacts/output"
    )
    assert set(result) == set(producer.OUTPUTS)
    domain = _object(result["source-domain.json"])
    assert domain["unknown_reported_age_bounds_samples"] == 222
    assert domain["distinct_sites"] == 3
    assert domain["accepted_point_domain_samples"] == 313
    assert {
        row["native_dataset_id"]: row["parameter_taxa"]
        for row in _records(domain["cores"])
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
        _object(
            _object(_object(result["account.json"])["scientific_verification"])[
                "current_retained_account_equation_check"
            ]
        )["scalar_values_compared"]
        == 6840
    )
    assert (
        _object(result["attribution.json"])["rights_and_raw_redistribution_admitted"]
        is False
    )
    assert {
        path.name for path in (captured_repository / "artifacts/output").iterdir()
    } == producer.OUTPUTS


@pytest.mark.parametrize("name", [*CAPTURE_PINS, DESCRIPTOR])
def test_every_retained_source_is_pinned(captured_repository: Path, name: str) -> None:
    """Verify every retained source is pinned."""
    path = captured_repository / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source bytes changed"):
        producer.publish(captured_repository, captured_repository / "artifacts/output")
    assert not (captured_repository / "artifacts/output").exists()


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("fractional_count", "Nordic retained report field shapes differ"),
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
    captured_repository: Path, mutation: str, reason: str
) -> None:
    """Verify changed saved scientific contract refuses."""
    inputs = copy.deepcopy(load_inputs(captured_repository))
    report = _object(inputs["report.json"])
    row = _object(_array(_object(_array(report["cases"])[0])["results"])[0])
    if mutation == "fractional_count":
        _array(_array(row["counts"])[0])[0] = (
            _number(_array(_array(row["counts"])[0])[0]) + 0.5
        )
    elif mutation == "residual":
        row["unparameterized_reported_NISP_sum"] = (
            _number(row["unparameterized_reported_NISP_sum"]) + 1
        )
    elif mutation == "hypothesized_mask":
        row["assumed_zero_cells"] = 1
    elif mutation == "duplicate_case":
        _array(report["cases"]).append(copy.deepcopy(_array(report["cases"])[0]))
    elif mutation == "wrong_chronology":
        changed_record = _object(
            _object(_array(report["cases"])[0])["selected_named_calibrated_chronology"]
        )
        changed_record["chronology_id"] = _number(changed_record["chronology_id"]) + 1
    elif mutation == "false_covariance":
        _array(_array(row["counting_covariance"])[0])[0] = (
            _number(_array(_array(row["counting_covariance"])[0])[0]) + 0.1
        )
    elif mutation == "false_se":
        _array(row["conditional_standard_error"])[0] = (
            _number(_array(row["conditional_standard_error"])[0]) + 0.1
        )
    elif mutation == "bad_geometry":
        _object(_object(_array(report["cases"])[1])["static_geometry"])["radius_m"] = (
            _number(
                _object(_object(_array(report["cases"])[1])["static_geometry"])[
                    "radius_m"
                ]
            )
            + 1
        )
    elif mutation == "cross_panel_axis":
        _array(_object(_array(report["cases"])[0])["PPE"]).pop()
    elif mutation == "bad_comparison":
        changed_cells = _array(
            _object(
                _array(
                    _object(_array(report["within_core_comparisons"])[0])["windows"]
                )[0]
            )["static_geometry_cover_minus_metadata_baseline"]
        )
        changed_cells[0] = _number(changed_cells[0]) + 0.1
    elif mutation == "missing_bounds_claim":
        for case in _records(report["cases"]):
            for value in _records(case["results"]):
                value["source_age_bounds_missing"] = 0
    with pytest.raises(ValueError, match=reason):
        products(inputs)


@pytest.mark.parametrize("kind", ["existing", "traversal", "artifact_root", "symlink"])
def test_owned_output_boundary_preserves_user_paths(
    captured_repository: Path, kind: str
) -> None:
    """Verify owned output boundary preserves user paths."""
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


def test_atomic_failure_leaves_no_nordic_products(
    captured_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify atomic failure leaves no nordic products."""

    def refuse(*args: object) -> None:
        raise OSError("atomic publication refused")

    monkeypatch.setattr(os, "rename", refuse)
    with pytest.raises(OSError, match="publication refused"):
        producer.publish(captured_repository, captured_repository / "artifacts/output")
    assert list((captured_repository / "artifacts").iterdir()) == []


@pytest.mark.parametrize("failure_at", [2, 3])
def test_late_source_tamper_removes_only_owned_products(
    captured_repository: Path, monkeypatch: pytest.MonkeyPatch, failure_at: int
) -> None:
    """Verify late source tamper removes only owned products."""
    original = sources.load_inputs
    calls = 0

    def monitored(root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls == failure_at:
            path = root / next(iter(CAPTURE_PINS))
            path.write_bytes(path.read_bytes() + b" ")
        return dict(original(root))

    monkeypatch.setattr(producer, "load_inputs", monitored)
    with pytest.raises(ValueError, match="source bytes changed"):
        producer.publish(captured_repository, captured_repository / "artifacts/output")
    assert not (captured_repository / "artifacts/output").exists()


def test_doi_and_investigator_records_do_not_close_primary_publications(
    captured_repository: Path,
) -> None:
    """Verify doi and investigator records do not close primary publications."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.attribution import (
        attribution,
    )

    inputs = load_inputs(captured_repository)
    assert all(
        _object(_object(row["raw_source_metadata"])["dataset"])["doi"]
        for row in _records(_object(inputs["verification/source-census.json"])["cores"])
    )
    assert all(
        _object(_object(row["raw_source_metadata"])["dataset"])["datasetpi"]
        for row in _records(_object(inputs["verification/source-census.json"])["cores"])
    )
    del inputs["verification/publication-metadata/dataset-4445.json"]
    with pytest.raises(ValueError, match="primary publication source capture missing"):
        attribution(inputs)


def test_chronology_citation_uses_actual_named_solsoe_models(
    captured_repository: Path,
) -> None:
    """Verify chronology citation uses actual named solsoe models."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.attribution import (
        attribution,
    )

    inputs = load_inputs(captured_repository)
    account = attribution(inputs)
    chronology = _object(_array(account["preferred_policy_citations"])[2])
    assert "Giesecke et al. (2014)" in _text(chronology["reference"])
    actual_models = {
        _object(row["source_core"])["native_dataset_id"]: row[
            "selected_named_calibrated_chronology"
        ]
        for row in _records(_object(inputs["verification/source-census.json"])["cores"])
    }
    assert chronology["selected_chronology_ids"] == [
        _object(actual_models[4445])["chronology_id"],
        _object(actual_models[4446])["chronology_id"],
    ]
    assert all(
        "Giesecke et al. 2014"
        in _text(_object(_object(actual_models[did])["model"])["chronologyname"])
        for did in (4445, 4446)
    )
    assert _object(actual_models[20034])["chronology_id"] not in _array(
        chronology["selected_chronology_ids"]
    )
    assert _object(actual_models[52082])["chronology_id"] not in _array(
        chronology["selected_chronology_ids"]
    )
    assert "no article acquisition" in _text(chronology["scope_limit"])
