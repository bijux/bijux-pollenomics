"""Exercise retained aggregate, denominator and atomic publication boundaries."""

from __future__ import annotations

import copy
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_source_chronology import (
    producer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_source_chronology.authority import (
    CAPTURE_PINS,
    DESCRIPTOR,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_source_chronology.sources import (
    load_inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_source_chronology.summary import (
    summarize,
)


@pytest.fixture
def retained_repository(tmp_path):
    source = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages/bijux-pollenomics-dev/pyproject.toml").is_file()
    )
    for name in (*CAPTURE_PINS, DESCRIPTOR):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    return tmp_path


def test_parent_traversal_cannot_escape_artifact_output(tmp_path):
    with pytest.raises(ValueError, match="canonical"):
        producer.publish(tmp_path, tmp_path / "artifacts/../outside")
    assert not (tmp_path / "outside").exists()


def test_artifact_root_itself_is_not_a_summary_output(tmp_path):
    with pytest.raises(ValueError, match="below repository artifacts"):
        producer.publish(tmp_path, tmp_path / "artifacts")
    assert not (tmp_path / "artifacts").exists()


def test_saved_aggregate_summary_derives_actual_denominators(retained_repository):
    result = producer.publish(
        retained_repository, retained_repository / "artifacts/output"
    )
    assert result["saved_case_window_rows_inspected"] == 184
    assert result["source_point_bin_moves_from_retained_diagnostic"] == 12
    assert sorted(
        row["chronology_totals"]["native_default_calibrated_points"][
            "mapped_pollen_NISP"
        ]
        for row in result["parameter_summaries"]
    ) == [12259, 38384, 42275, 42275]
    assert all(
        row["changed_count_windows"] == 16 for row in result["parameter_summaries"]
    )
    assert sorted(
        path.name for path in (retained_repository / "artifacts/output").iterdir()
    ) == ["summary.json"]


@pytest.mark.parametrize("name", [*CAPTURE_PINS, DESCRIPTOR])
def test_every_source_identity_is_enforced_before_output(retained_repository, name):
    path = retained_repository / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source bytes changed"):
        producer.publish(retained_repository, retained_repository / "artifacts/output")
    assert not (retained_repository / "artifacts/output").exists()


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("fractional_count", "nonnegative integer"),
        ("negative_count", "nonnegative integer"),
        ("flat_count_matrix", "count matrix shape"),
        ("residual", "conserve NISP"),
        ("duplicate_case", "case axis"),
        ("missing_case", "complete case"),
        ("duplicate_window", "window axis duplicates"),
        ("incomplete_union", "union is incomplete"),
        ("false_delta", "cover difference"),
        ("false_covariance", "covariance components"),
        ("false_se", "standard error"),
        ("false_source_scope", "conditional source scope"),
        ("false_diagnostic", "summary differs from diagnostic"),
    ],
)
def test_saved_output_invariants_refuse_changed_payload(
    retained_repository, mutation, reason
):
    inputs = load_inputs(retained_repository)
    report = copy.deepcopy(inputs["report.json"])
    diagnostic = copy.deepcopy(inputs["execution/read-only-diagnostic.json"])
    row = report["cases"][0]["results"][0]
    if mutation == "fractional_count":
        row["hypothesized_panel_counts"][0][0] = 0.5
    elif mutation == "negative_count":
        row["hypothesized_panel_counts"][0][0] = -1
    elif mutation == "flat_count_matrix":
        row["hypothesized_panel_counts"] = row["hypothesized_panel_counts"][0]
    elif mutation == "residual":
        row["unparameterized_reported_NISP_sum"] += 1
    elif mutation == "duplicate_case":
        report["cases"].append(copy.deepcopy(report["cases"][0]))
    elif mutation == "missing_case":
        report["cases"].pop()
    elif mutation == "duplicate_window":
        report["cases"][0]["results"].append(copy.deepcopy(row))
    elif mutation == "incomplete_union":
        report["chronology_comparisons"][0]["windows"].pop()
    elif mutation == "false_delta":
        report["chronology_comparisons"][0]["windows"][0][
            "cover_alternative_minus_native"
        ][0] += 0.1
    elif mutation == "false_covariance":
        row["total_conditional_covariance"][0][0] += 0.1
    elif mutation == "false_se":
        row["conditional_standard_error"][0] += 0.1
    elif mutation == "false_source_scope":
        report["cases"][0]["source_measurement_complete_claimed"] = True
    elif mutation == "false_diagnostic":
        diagnostic["parameter_summaries"][0]["signed_conditional_cover_change"] += 0.1
    with pytest.raises(ValueError, match=reason):
        summarize(report, diagnostic)


def test_existing_output_is_preserved(retained_repository):
    output = retained_repository / "artifacts/output"
    output.mkdir(parents=True)
    (output / "user.txt").write_text("preserve")
    with pytest.raises(ValueError, match="existing summary output"):
        producer.publish(retained_repository, output)
    assert (output / "user.txt").read_text() == "preserve"


def test_symlink_output_ancestor_refuses(retained_repository):
    root = retained_repository / "artifacts"
    root.mkdir()
    (root / "linked").symlink_to(retained_repository, target_is_directory=True)
    with pytest.raises(ValueError, match="real directory"):
        producer.publish(retained_repository, root / "linked/output")


def test_atomic_promotion_failure_has_no_published_output(
    retained_repository, monkeypatch
):
    def refuse(*args):
        raise OSError("publication refused")

    monkeypatch.setattr(producer.os, "rename", refuse)
    with pytest.raises(OSError, match="publication refused"):
        producer.publish(retained_repository, retained_repository / "artifacts/output")
    assert list((retained_repository / "artifacts").iterdir()) == []


@pytest.mark.parametrize("failure_at", [2, 3])
def test_source_tamper_at_promotion_removes_only_owned_output(
    retained_repository, monkeypatch, failure_at
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
        producer.publish(retained_repository, retained_repository / "artifacts/output")
    assert not (retained_repository / "artifacts/output").exists()
