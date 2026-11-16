"""Grouped summaries retain full covariance and the original conditioning event."""

from __future__ import annotations

import copy
import csv
from hashlib import sha256
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest


def projection() -> ModuleType:
    """Load the maintained consumer without opening any retained source result."""
    return importlib.import_module(
        "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
        "abborrtjarnen_age_ppe.grouped.projection"
    )


def generated_result() -> dict[str, Any]:
    """Supply a four-window closed-panel law sharing identical random vectors."""
    taxa = [
        ("Betula", 29),
        ("Cyperaceae", 74),
        ("Juniperus communis", 4416),
        ("Pinus sylvestris", 1287),
        ("Poaceae", 417),
    ]
    fraction = np.array([0.2, 0.1, 0.1, 0.3, 0.3])
    covariance = (np.diag(fraction) - np.outer(fraction, fraction)) / 100
    count = np.tile(covariance, (4, 4))
    zero = np.zeros_like(count).tolist()
    return {
        "schema_version": "abborrtjarnen-age-ppe-account.v1",
        "status": "conditional_age_count_ppe_delta_mixture",
        "conditioning_event": "all_four_windows_defined_with_complete_five_taxon_members",
        "requested_draws": 32000,
        "complete_draws": 29332,
        "undefined_draws": 2668,
        "complete_probability": 29332 / 32000,
        "unconditional": {
            "status": "refused_undefined_mass",
            "undefined_fraction": 2668 / 32000,
            "mean": None,
            "covariance": None,
        },
        "source_support": {
            "original_samples": 107,
            "explicit_five_panel_complete": 99,
            "incomplete_five_panel_samples": [
                {"sample_id": n, "missing_taxa": ["Poaceae"]} for n in range(1, 9)
            ],
        },
        "component_axis": [
            {"window_id": w, "taxon": name, "native_taxon_id": native}
            for w in (3, 4, 5, 9)
            for name, native in taxa
        ],
        "conditional_on_complete": {
            "status": "conditional_on_complete",
            "draws": 29332,
            "mean": np.tile(fraction, 4).tolist(),
            "covariance_components": {
                "age": zero,
                "count": count.tolist(),
                "shared_ppe": zero,
                "total": count.tolist(),
                "mean_gradient_ppe": zero,
                "age_ppe_interaction": zero,
            },
        },
    }


def test_group_mean_and_spread_use_the_off_diagonal_covariance() -> None:
    p = np.array([0.2, 0.3, 0.5])
    covariance = (np.diag(p) - np.outer(p, p)) / 100
    mean, grouped = projection().project_linear_moments(
        p, covariance, np.array([[1, 1, 0], [0, 0, 1]])
    )
    assert mean.tolist() == pytest.approx([0.5, 0.5])
    assert np.sqrt(grouped[0, 0]) == pytest.approx(0.05)
    assert np.sqrt(covariance[0, 0] + covariance[1, 1]) == pytest.approx(0.0608276253)
    assert np.max(np.abs(grouped.sum(axis=0))) < 1e-15


def test_shared_result_difference_cancels_and_axes_can_be_permuted() -> None:
    payload = generated_result()
    result = projection().project_retained_result(payload)
    assert len(result["groups"]) == 3
    assert len(result["components"]) == 12
    assert len(result["contrasts"]) == 18
    assert all(
        row["standard_deviation_percentage_points"] == 0 for row in result["contrasts"]
    )
    assert result["components"][0]["mean_percent"] == pytest.approx(50)
    assert result["components"][0][
        "standard_deviation_percentage_points"
    ] == pytest.approx(5)
    assert result["covariance_components_percent_squared"]["total"][0][
        0
    ] == pytest.approx(25)
    assert result["requested_draws"] == 32000 and result["undefined_draws"] == 2668
    assert result["unconditional"] == payload["unconditional"]
    permuted = copy.deepcopy(payload)
    order = np.arange(20)[::-1]
    permuted["component_axis"] = [payload["component_axis"][i] for i in order]
    moments = permuted["conditional_on_complete"]
    moments["mean"] = np.asarray(moments["mean"])[order].tolist()
    for name, matrix in moments["covariance_components"].items():
        moments["covariance_components"][name] = np.asarray(matrix)[
            np.ix_(order, order)
        ].tolist()
    reordered = projection().project_retained_result(permuted)
    assert reordered["groups"] == result["groups"]
    for name in result["covariance_components_percent_squared"]:
        np.testing.assert_allclose(
            reordered["covariance_components_percent_squared"][name],
            result["covariance_components_percent_squared"][name],
            rtol=1e-12,
            atol=1e-14,
        )
    assert [r["mean_percent"] for r in reordered["components"]] == pytest.approx(
        [r["mean_percent"] for r in result["components"]]
    )


@pytest.mark.parametrize(
    "fault",
    [
        "negative_variance",
        "duplicate_axis",
        "wrong_native_taxon",
        "wrong_denominator",
        "undefined_unconditional",
        "component_mismatch",
        "nested_draws",
        "nested_status",
        "float_native_taxon",
        "unconditional_status",
        "source_panel_mask",
    ],
)
def test_incompatible_source_moments_refuse(fault: str) -> None:
    payload = generated_result()
    if fault == "negative_variance":
        payload["conditional_on_complete"]["covariance_components"]["total"][0][0] = -1
    elif fault == "duplicate_axis":
        payload["component_axis"][1] = payload["component_axis"][0]
    elif fault == "wrong_native_taxon":
        payload["component_axis"][0]["native_taxon_id"] = 999
    elif fault == "wrong_denominator":
        payload["undefined_draws"] = 0
    elif fault == "undefined_unconditional":
        payload["unconditional"]["mean"] = [0.2] * 20
    elif fault == "component_mismatch":
        payload["conditional_on_complete"]["covariance_components"]["age"] = np.eye(
            20
        ).tolist()
    elif fault == "nested_draws":
        payload["conditional_on_complete"]["draws"] = 29331
    elif fault == "nested_status":
        payload["conditional_on_complete"]["status"] = "unconditional"
    elif fault == "float_native_taxon":
        payload["component_axis"][0]["native_taxon_id"] = 29.0
    elif fault == "unconditional_status":
        payload["unconditional"]["status"] = "complete"
    else:
        payload["source_support"]["explicit_five_panel_complete"] = 107
    with pytest.raises(ValueError):
        projection().project_retained_result(payload)


@pytest.mark.parametrize(
    "value",
    [
        np.array([0.2 + 1j, 0.8]),
        np.array([True, False]),
        np.array([np.nan, 1]),
        np.ma.array([0.2, 0.8], mask=[True, False]),
    ],
)
def test_linear_projection_refuses_lossy_or_nonfinite_inputs(value: np.ndarray) -> None:
    with pytest.raises(ValueError):
        projection().project_linear_moments(value, np.eye(2), np.eye(2))


def test_publication_binds_source_export_and_preserves_existing_output(
    tmp_path: Path,
) -> None:
    publication = importlib.import_module(
        "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
        "abborrtjarnen_age_ppe.grouped.publication"
    )
    source = tmp_path / "result.json"
    raw = (json.dumps(generated_result()) + "\n").encode()
    source.write_bytes(raw)
    target = tmp_path / "grouped"
    with pytest.raises(ValueError, match="digest"):
        publication.publish_grouped_result(
            source, expected_result_sha256="0" * 64, destination=target
        )
    assert not target.exists()
    receipt = publication.publish_grouped_result(
        source, expected_result_sha256=sha256(raw).hexdigest(), destination=target
    )
    assert (target / "source-result.json").read_bytes() == raw
    report = json.loads((target / "report.json").read_bytes())
    assert report["source_result_sha256"] == sha256(raw).hexdigest()
    assert report["complete_draws"] == 29332 and report["undefined_draws"] == 2668
    assert "confidence interval" in (target / "index.html").read_text()
    assert "not whole vegetation" in (target / "index.html").read_text()
    manifest = json.loads((target / "manifest.json").read_bytes())
    assert (
        receipt["manifest_sha256"]
        == sha256((target / "manifest.json").read_bytes()).hexdigest()
    )
    assert all(
        sha256((target / name).read_bytes()).hexdigest() == pin
        for name, pin in manifest["files"].items()
    )
    prior = {p.name: p.read_bytes() for p in target.iterdir()}
    for name in ("components.csv", "contrasts.csv"):
        assert b"\r" not in (target / name).read_bytes()
        with (target / name).open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert all(
            row[field] == report[field]
            for row in rows
            for field in (
                "denominator",
                "cover_policy",
                "uncertainty",
                "source_result_sha256",
            )
        )
    with pytest.raises(FileExistsError):
        publication.publish_grouped_result(
            source, expected_result_sha256=sha256(raw).hexdigest(), destination=target
        )
    assert {p.name: p.read_bytes() for p in target.iterdir()} == prior


def test_component_covariance_cannot_vary_a_closed_panel_total() -> None:
    payload = generated_result()
    for name in ("age", "total"):
        matrix = np.array(
            payload["conditional_on_complete"]["covariance_components"][name]
        )
        payload["conditional_on_complete"]["covariance_components"][name] = (
            matrix + 0.001
        ).tolist()
    with pytest.raises(ValueError, match="closed-panel"):
        projection().project_retained_result(payload)


def test_redirected_output_parent_refuses_before_creating_foreign_directories(
    tmp_path: Path,
) -> None:
    publication = importlib.import_module(
        "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
        "abborrtjarnen_age_ppe.grouped.publication"
    )
    source = tmp_path / "result.json"
    raw = json.dumps(generated_result()).encode()
    source.write_bytes(raw)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "marker").write_bytes(b"existing owner")
    alias = tmp_path / "alias"
    alias.symlink_to(foreign, target_is_directory=True)
    with pytest.raises(ValueError):
        publication.publish_grouped_result(
            source,
            expected_result_sha256=sha256(raw).hexdigest(),
            destination=alias / "requested-parent" / "nested" / "grouped",
        )
    assert sorted(p.name for p in foreign.iterdir()) == ["marker"]
    assert (foreign / "marker").read_bytes() == b"existing owner"


@pytest.mark.parametrize("attack", ["replace_candidate", "tamper_member"])
def test_owned_publication_refuses_foreign_or_changed_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    publication = importlib.import_module(
        "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
        "abborrtjarnen_age_ppe.grouped.publication"
    )
    source = tmp_path / "result.json"
    raw = json.dumps(generated_result()).encode()
    source.write_bytes(raw)
    target, retained = tmp_path / "grouped", tmp_path / "retained"
    original = publication.publish_owned_replacement
    observed = []

    def attach(writer: Any, **kwargs: Any) -> Any:
        observed.append(writer.root)
        if attack == "replace_candidate":
            writer.root.rename(retained)
            writer.root.mkdir()
            (writer.root / "foreign.txt").write_bytes(b"other writer")
        else:
            (writer.root / "report.json").write_bytes(b"changed by another writer")
        return original(writer, **kwargs)

    monkeypatch.setattr(publication, "publish_owned_replacement", attach)
    with pytest.raises(ValueError):
        publication.publish_grouped_result(
            source, expected_result_sha256=sha256(raw).hexdigest(), destination=target
        )
    assert len(observed) == 1 and not target.exists()
    if attack == "replace_candidate":
        assert (retained / "source-result.json").read_bytes() == raw
        assert (observed[0] / "foreign.txt").read_bytes() == b"other writer"
    else:
        assert (
            observed[0] / "report.json"
        ).read_bytes() == b"changed by another writer"
