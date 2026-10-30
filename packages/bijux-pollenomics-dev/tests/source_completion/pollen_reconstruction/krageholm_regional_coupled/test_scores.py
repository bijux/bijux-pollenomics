"""Exact-count score controls retain every failed prediction and missing-outcome refusal."""

from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from . import predictions as observer
from .fixtures import prediction_fixture, write_product
from .lineage import digest
from .predictions import check_prediction
from .scalar import AXIS, METHODS
from .scores import check_scores
from .test_native_fits import TOLERANCE


def score_fixture(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    refused: bool = False,
    corruption: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    prediction_pin, context, native, _ = prediction_fixture(repository, refused=refused)
    monkeypatch.setattr(observer, "check_batches", lambda *args: native)
    prediction = check_prediction(repository, prediction_pin, context, TOLERANCE)
    spec = context["experiment"]
    inventory: dict[str, Any] = {
        "schema_version": "lra-source-pollen-outcomes.v1",
        "data_kind": "source_observations",
        "records": {
            site["record_id"]: site["raw"]
            for site in spec["sites"]
            if site["record_id"] in spec["target_record_ids"]
        },
    }
    rows, access = [], {}
    for fold in prediction["folds"]:
        target = fold["test_record_ids"][0]
        for method in METHODS:
            row: dict[str, Any] = {
                "fold_id": fold["fold_id"],
                "baseline": method,
                "record_id": target,
                "record_ids": [target],
                "group_id": fold["test_group_ids"][0],
                "target": "pollen_composition",
                "error_unit": "fraction",
                "evaluation_role": "heldout_pollen_prediction",
                "bin_id": "synthetic-bin",
            }
            key = fold["fold_id"], method
            if key not in prediction["predictions"]:
                row["score"] = {"status": "prediction_failed", "mae_fraction": None}
            else:
                available = prediction["predictions"][key]["row"]
                reference = inventory["records"][target]
                row.update(
                    prediction_manifest_sha256=available["prediction_manifest_sha256"],
                    prediction=available["pollen_fraction"],
                    observation_reference=reference,
                    observation_sha256=reference["sha256"],
                    observation={
                        "record_id": target,
                        "sample_id": target,
                        "pollen_count": dict(zip(AXIS, [2, 1], strict=True)),
                        "source_raw_sha256": reference["sha256"],
                    },
                    score={
                        "status": "scored",
                        "taxon_count": 2,
                        "scored_taxon_count": 2,
                        "missing_observed_taxa": [],
                        "observed_total_count": 3,
                        "mae_fraction": 1 / 24,
                        "total_variation": 1 / 24,
                        "signed_error_by_taxon": [
                            ["Betula", -1 / 24],
                            ["Ulmus", 1 / 24],
                        ],
                    },
                )
                access[target] = {
                    "record_id": target,
                    "observation_sha256": reference["sha256"],
                    "prediction_manifest_sha256": prediction_pin["manifest_sha256"],
                    "ordering": "verified_published_predictions_before_outcome_open",
                }
            rows.append(row)
    summaries = []
    for method in METHODS:
        group = [row for row in rows if row["baseline"] == method]
        summaries.append(
            {
                "baseline": method,
                "target": "pollen_composition",
                "requested": 3,
                "by_status": dict(Counter(row["score"]["status"] for row in group)),
                "scored": sum(row["score"]["status"] == "scored" for row in group),
                "mean_mae_fraction": 1 / 24,
            }
        )
    pairs = [
        {
            "fold_id": fold["fold_id"],
            "baseline": method,
            "reference_baseline": "training_mean",
            "target": "pollen_composition",
            "mae_improvement_fraction": 0.0,
        }
        for fold in prediction["folds"]
        for method in METHODS[1:]
        if (fold["fold_id"], method) in prediction["predictions"]
    ]
    science = {
        "prediction_manifest_sha256": prediction_pin["manifest_sha256"],
        "prediction_scientific_content_sha256": prediction_pin[
            "scientific_content_sha256"
        ],
        "outcome_inventory_sha256": digest(inventory),
        "scores": rows,
        "summaries": summaries,
        "paired_baseline_differences": pairs,
    }
    if corruption == "missing_row":
        rows.pop()
    elif corruption == "missing_outcome":
        next(row for row in rows if row["score"]["status"] == "scored")["score"] = {
            "status": "missing_observation",
            "mae_fraction": None,
        }
    elif corruption == "count_type":
        next(row for row in rows if row["score"]["status"] == "scored")["observation"][
            "pollen_count"
        ]["Betula"] = 2.0
    elif corruption == "metric":
        next(row for row in rows if row["score"]["status"] == "scored")["score"][
            "mae_fraction"
        ] = 0.0
    elif corruption == "reference":
        rows[0]["prediction_manifest_sha256"] = "0" * 64
    elif corruption == "access":
        access[next(iter(access))]["ordering"] = "outcome_before_predictions"
    elif corruption == "regional_outcome":
        science["outcome_inventory_sha256"] = digest(
            {**inventory, "regional": "KRAGMJNY"}
        )
    elif corruption == "summary":
        summaries[0]["scored"] = 0
    elif corruption == "pair":
        pairs[0]["mae_improvement_fraction"] = 0.1
    saved = {
        name + ".json": science[name]
        for name in ("scores", "summaries", "paired_baseline_differences")
    }
    saved["outcome_access.json"] = list(access.values())
    pin = write_product(repository / "artifacts/scores", science, saved, phase="scores")
    return pin, prediction_pin, prediction, context


@pytest.mark.parametrize("refused", [False, True])
def test_all_nine_scored_or_failed_method_dispositions_are_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, refused: bool
) -> None:
    pin, prior, prediction, context = score_fixture(
        tmp_path, monkeypatch, refused=refused
    )
    result = check_scores(tmp_path, pin, prior, prediction, context, TOLERANCE)
    assert len(result["dispositions"]) == 9
    assert result["scored"] == (6 if refused else 9)
    assert result["refused"] == (3 if refused else 0)


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_row",
        "missing_outcome",
        "count_type",
        "metric",
        "reference",
        "access",
        "regional_outcome",
        "summary",
        "pair",
    ],
)
def test_missing_outcomes_source_roles_score_values_and_publication_lineage_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    pin, prior, prediction, context = score_fixture(
        tmp_path, monkeypatch, corruption=corruption
    )
    with pytest.raises(ValueError):
        check_scores(tmp_path, pin, prior, prediction, context, TOLERANCE)
