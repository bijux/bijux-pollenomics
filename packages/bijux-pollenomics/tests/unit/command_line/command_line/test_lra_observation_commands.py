"""Conditional uncertainty command boundaries and separate observation coverage."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra_validation.experiments import (
    score_experiment_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
)
from bijux_pollenomics.cli import main
from bijux_pollenomics.command_line.runtime import lra_validation as runtime

from ...analysis.lra_validation.observation_uncertainty.support import fixture


def generate_args(root: Path, predictions: Path) -> list[str]:
    return [
        "prepare-lra-observation-uncertainty",
        str(predictions),
        "--plan",
        str(root / "plan.json"),
        "--evidence-root",
        str(root / "effort"),
        "--output",
        str(root / "uncertainty"),
    ]


@pytest.mark.parametrize(
    "taxa,counts,expected",
    [
        (("a", "b"), {"a": 7, "b": 3}, 0),
        (("a", "b"), {"a": 7, "b": 4}, 2),
        (("Å", "Ö"), {"Å": 7, "Ö": 3}, 0),
    ],
)
def test_actual_cli_generation_then_separate_coverage(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    taxa: tuple[str, str],
    counts: dict[str, int | None],
    expected: int,
) -> None:
    product, plan, inventory = fixture(tmp_path, taxa=taxa, counts=counts)
    (tmp_path / "plan.json").write_text(json.dumps(plan.as_dict()))
    (tmp_path / "outcomes").rename(tmp_path / "sealed")
    assert main(generate_args(tmp_path, product.directory)) == 0
    generated = json.loads(capsys.readouterr().out)
    assert generated["requested_units"] == 6 and generated["status_counts"] == {
        "generated": 6
    }
    assert generated["scientific_acceptance"] == "not_evaluated"
    (tmp_path / "sealed").rename(tmp_path / "outcomes")
    scores = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "outcomes",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    args = [
        "score-lra-observation-coverage",
        str(product.directory),
        "--uncertainty",
        generated["directory"],
        "--scores",
        str(scores.directory),
        "--expected-uncertainty-sha256",
        generated["manifest_sha256"],
        "--expected-scores-sha256",
        scores.manifest_sha256,
        "--output",
        str(tmp_path / "coverage"),
    ]
    assert main(args) == expected
    covered = json.loads(capsys.readouterr().out)
    assert covered["requested_units"] == 6
    assert covered["coverage_scored_units"] == (6 if expected == 0 else 0)
    assert covered["coverage_refused_units"] == (0 if expected == 0 else 6)
    assert covered["scientific_acceptance"] == "not_evaluated"


@pytest.mark.parametrize(
    "counts,expected",
    [
        ({"generated": 6}, 0),
        ({"generated": 4, "sampler_refused": 2}, 2),
        ({"generated": 1, "not_run": 5}, 130),
    ],
)
def test_generation_partial_and_interruption_exit_codes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    counts: dict[str, int],
    expected: int,
) -> None:
    parent, plan, _ = fixture(tmp_path)
    (tmp_path / "plan.json").write_text(json.dumps(plan.as_dict()))
    product = ExperimentProduct(tmp_path / "uncertainty", "a" * 64, "b" * 64)
    with (
        patch.object(
            runtime, "generate_pollen_observation_uncertainty", return_value=product
        ),
        patch.object(
            runtime,
            "read_experiment_product",
            return_value=(
                product,
                {"scientific_payload": {"requested_units": 6, "status_counts": counts}},
            ),
        ),
    ):
        assert main(generate_args(tmp_path, parent.directory)) == expected
    result = json.loads(capsys.readouterr().out)
    assert result["status_counts"] == counts and result["requested_units"] == 6


@pytest.mark.parametrize(
    "text", ["[]", '{"entries":[],"entries":[]}', '{"coverage":NaN}']
)
def test_invalid_plan_refuses_before_generation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str
) -> None:
    (tmp_path / "plan.json").write_text(text)
    with patch.object(runtime, "generate_pollen_observation_uncertainty") as generate:
        assert main(generate_args(tmp_path, tmp_path / "absent")) == 2
    generate.assert_not_called()
    assert json.loads(capsys.readouterr().out)["status"] == "refused"
    assert not (tmp_path / "uncertainty").exists()
