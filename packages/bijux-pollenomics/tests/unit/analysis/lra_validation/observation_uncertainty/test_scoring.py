"""Coverage never selects counting effort from heldout count totals."""

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.scoring import (
    score_experiment_predictions,
)
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty import (
    generate_pollen_observation_uncertainty,
    score_pollen_observation_coverage,
)

from .support import fixture


@pytest.mark.parametrize(
    "counts,expected",
    [
        ({"a": 7, "b": 3}, "coverage_scored"),
        ({"a": 0, "b": 10}, "coverage_scored"),
        ({"a": 0, "b": 0}, "coverage_refused"),
        ({"a": 7, "b": 4}, "coverage_refused"),
        ({"a": None, "b": 3}, "coverage_refused"),
    ],
)
def test_actual_separate_coverage(
    tmp_path: Path, counts: dict[str, int | None], expected: str
) -> None:
    product, plan, inventory = fixture(tmp_path, counts=counts)
    uncertainty = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "draws",
    )
    scores = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "outcomes",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    coverage = score_pollen_observation_coverage(
        product.directory,
        uncertainty.directory,
        scores.directory,
        expected_uncertainty_sha256=uncertainty.manifest_sha256,
        expected_scores_sha256=scores.manifest_sha256,
        destination=tmp_path / "coverage",
    )
    rows = json.loads((coverage.directory / "coverage.json").read_text())
    assert len(rows) == 6
    assert all(row["status"] == expected for row in rows)
    if sum(v or 0 for v in counts.values()) == 11:
        assert all(row["reason_code"] == "observation_effort_mismatch" for row in rows)
    assert all(row["entry"]["effort"] == 10 for row in rows)


def test_missing_observation_and_prediction_denominators(tmp_path: Path) -> None:
    product, plan, inventory = fixture(tmp_path, failed=True)
    inventory["records"].pop("p2")
    uncertainty = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "draws",
    )
    scores = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "outcomes",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    output = score_pollen_observation_coverage(
        product.directory,
        uncertainty.directory,
        scores.directory,
        expected_uncertainty_sha256=uncertainty.manifest_sha256,
        expected_scores_sha256=scores.manifest_sha256,
        destination=tmp_path / "coverage",
    )
    rows = json.loads((output.directory / "coverage.json").read_text())
    assert len(rows) == 6
    assert sum(row["status"] == "coverage_refused" for row in rows) == 4


def test_changed_uncertainty_refuses_before_output(tmp_path: Path) -> None:
    product, plan, inventory = fixture(tmp_path)
    uncertainty = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "draws",
    )
    (uncertainty.directory / "uncertainty.json").write_text("[]")
    with pytest.raises(ValidationRefusal):
        score_pollen_observation_coverage(
            product.directory,
            uncertainty.directory,
            tmp_path / "scores-absent",
            expected_uncertainty_sha256=uncertainty.manifest_sha256,
            expected_scores_sha256="0" * 64,
            destination=tmp_path / "coverage",
        )
    assert not (tmp_path / "coverage").exists()


def test_unicode_engine_canonical_bytes_survive_host_encoding(tmp_path: Path) -> None:
    product, plan, inventory = fixture(tmp_path, taxa=("Å", "Ö"))
    uncertainty = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "draws",
    )
    scores = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "outcomes",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    result = score_pollen_observation_coverage(
        product.directory,
        uncertainty.directory,
        scores.directory,
        expected_uncertainty_sha256=uncertainty.manifest_sha256,
        expected_scores_sha256=scores.manifest_sha256,
        destination=tmp_path / "coverage",
    )
    rows = json.loads((result.directory / "coverage.json").read_text())
    assert all(r["status"] == "coverage_scored" for r in rows)
    assert {r["taxon"] for r in rows[0]["marginal_taxa"]} == {"Å", "Ö"}


@pytest.mark.parametrize(
    "kind",
    [
        "score_parent",
        "draw_profile",
        "draw_plan",
        "displayed_draws",
        "retained_posture",
    ],
)
def test_rehashed_contradictions_refuse(tmp_path: Path, kind: str) -> None:
    from .support import rewrite

    product, plan, inventory = fixture(tmp_path)
    uncertainty = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "draws",
    )
    scores = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "outcomes",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    if kind == "score_parent":
        scores = rewrite(
            scores,
            payload_change=lambda p: p.__setitem__(
                "prediction_manifest_sha256", "0" * 64
            ),
        )
    elif kind == "retained_posture":
        uncertainty = rewrite(
            uncertainty,
            payload_change=lambda p: p.__setitem__("scientific_acceptance", "accepted"),
        )
    else:

        def modify(rows: list[dict[str, Any]]) -> None:
            result = rows[0]["engine_result"]
            if kind == "displayed_draws":
                result["counts"][0] = [0, 10]
                return
            if kind == "draw_profile":
                result["profile"] = "unsupported"
            else:
                result["declaration"]["prediction_sha256"] = "0" * 64
            import hashlib

            text = json.dumps(
                result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            rows[0]["engine_result_canonical_json"] = text
            rows[0]["engine_result_sha256"] = hashlib.sha256(text.encode()).hexdigest()

        uncertainty = rewrite(
            uncertainty, member="uncertainty.json", member_change=modify
        )
    with pytest.raises(ValidationRefusal):
        score_pollen_observation_coverage(
            product.directory,
            uncertainty.directory,
            scores.directory,
            expected_uncertainty_sha256=uncertainty.manifest_sha256,
            expected_scores_sha256=scores.manifest_sha256,
            destination=tmp_path / "coverage",
        )
    assert not (tmp_path / "coverage").exists()


def test_missing_retained_plan_has_stable_refusal(tmp_path: Path) -> None:
    from .support import rewrite

    product, plan, _ = fixture(tmp_path)
    uncertainty = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "draws",
    )
    uncertainty = rewrite(uncertainty, payload_change=lambda p: p.pop("plan"))
    with pytest.raises(ValidationRefusal) as error:
        score_pollen_observation_coverage(
            product.directory,
            uncertainty.directory,
            tmp_path / "absent",
            expected_uncertainty_sha256=uncertainty.manifest_sha256,
            expected_scores_sha256="0" * 64,
            destination=tmp_path / "coverage",
        )
    assert error.value.reason_code == "invalid_observation_coverage_input"
