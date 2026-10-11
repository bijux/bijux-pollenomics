"""Observed pollen has explicit ancestry; vegetation remains separately held out."""

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    grouped_leave_one_out,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.experiments import (
    LocalPollenSpec,
    score_experiment_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    LOCAL_EVALUATION_ROLES,
    LOCAL_METHOD,
    LOCAL_PROFILE,
    ExperimentSpec,
    object_mapping,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    channel_catalogue,
    local_channel_evidence,
    make_request,
    read_observed_local_pollen,
    read_training_observation,
)
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
    publish_phase,
    stage_directory,
    write_json,
)

from .test_inputs import fixture_inputs, store


def local_payload(root: Path) -> dict[str, Any]:
    payload = fixture_inputs(root)
    payload.pop("baselines")
    payload.update(profile=LOCAL_PROFILE, method=LOCAL_METHOD)
    return payload


def test_local_profile_is_not_a_baseline_or_all_channel_holdout(tmp_path: Path) -> None:
    payload = local_payload(tmp_path)
    spec = LocalPollenSpec(payload)
    assert not hasattr(spec, "baselines")
    assert spec.method == LOCAL_METHOD
    with pytest.raises(ValidationRefusal):
        ExperimentSpec(payload)
    payload["method"] = "nearest_site"
    with pytest.raises(ValidationRefusal):
        LocalPollenSpec(payload)


def test_exact_observed_local_channel_is_admitted_without_weakening_training_guard(
    tmp_path: Path,
) -> None:
    spec = LocalPollenSpec(local_payload(tmp_path))
    fold = next(
        f
        for f in grouped_leave_one_out([s.record for s in spec.sites])
        if "p01" in f.test_record_ids
    )
    target, anchor = spec.sites[:2]
    with pytest.raises(ValidationRefusal):
        read_training_observation(tmp_path, target, fold, spec)
    sample = read_observed_local_pollen(tmp_path, target, fold, spec)
    assert sample["counts"] == [600, 400]
    with pytest.raises(ValidationRefusal):
        read_observed_local_pollen(tmp_path, anchor, fold, spec)
    request = make_request(spec, target, anchor, fold, tmp_path)
    assert (
        object_mapping(request["local"], "local")["samples"]
        != object_mapping(request["regional"], "regional")["samples"]
    )
    with pytest.raises(ValidationRefusal):
        make_request(spec, target, target, fold, tmp_path)


def synthetic_local_product(
    root: Path, *, mutation: str | None = None
) -> tuple[ExperimentProduct, dict[str, Any]]:
    spec = LocalPollenSpec(local_payload(root / "inputs"))
    folds = grouped_leave_one_out([s.record for s in spec.sites])
    predictions = []
    outcomes = {}
    for fold in folds:
        record = fold.test_record_ids[0]
        target = next(site for site in spec.sites if site.record.record_id == record)
        anchor = next(
            site
            for site in spec.sites
            if site.record.record_id == fold.train_record_ids[0]
        )
        counts = json.loads((root / "inputs" / target.raw.path).read_text())["sample"][
            "counts"
        ]
        row: dict[str, Any] = {
            "profile": LOCAL_PROFILE,
            "fold_id": fold.fold_id,
            "record_id": record,
            "group_id": fold.test_group_ids[0],
            "bin_id": "test-bin",
            "method": LOCAL_METHOD,
            "method_kind": "local_pollen_assimilation",
            "outer_fold": fold.as_dict(),
            "evaluation_roles": dict(LOCAL_EVALUATION_ROLES),
            "pollen_eligible_for_heldout_acceptance": False,
            "vegetation_fraction": {"Alnus": 0.6, "Betula": 0.4},
            "pollen_fraction": {"Alnus": 0.7, "Betula": 0.3},
            "observed_pollen_count": dict(
                zip(("Alnus", "Betula"), counts, strict=True)
            ),
            "channel_admission": local_channel_evidence(spec, fold, target, anchor),
            "observed_pollen_unit": "count",
            "observed_local_pollen_source": {
                "record_id": record,
                "group_id": fold.test_group_ids[0],
                "role": "observed_local_pollen",
                "path": target.raw.path,
                "sha256": target.raw.sha256,
            },
            "regional_pollen_source": {
                "record_id": fold.train_record_ids[0],
                "role": "training_regional_pollen",
                "path": anchor.raw.path,
                "sha256": anchor.raw.sha256,
            },
        }
        if mutation == "role":
            row["evaluation_roles"]["pollen_composition"] = "heldout_prediction"
        elif mutation == "anchor":
            row["regional_pollen_source"]["record_id"] = record
        elif mutation == "missing_source":
            row["observed_local_pollen_source"].pop("record_id")
        elif mutation == "quantitative_edge":
            row["channel_admission"]["quantitative_lineage"]["raw:" + record] = [record]
            row["channel_admission"]["quantitative_lineage"][record] = []
        elif mutation == "source_hash":
            row["observed_local_pollen_source"]["sha256"] = "a" * 64
        elif mutation == "negative":
            row["pollen_fraction"] = {"Alnus": 1.1, "Betula": -0.1}
        row["prediction_manifest_sha256"] = manifest_sha256(row)
        predictions.append(row)
        outcomes[record] = store(
            root / "inputs",
            record + "-vegetation.json",
            {
                "schema_version": "lra-local-vegetation-observation.v1",
                "data_kind": "synthetic",
                "record_id": record,
                "bin_id": "test-bin",
                "vegetation_unit": "fraction",
                "vegetation_fraction": {"Alnus": 0.5, "Betula": 0.5},
            },
        )
    scientific: dict[str, object] = {
        "profile": LOCAL_PROFILE,
        "folds": [f.as_dict() for f in folds],
        "predictions": predictions,
        "failures": [],
        "evaluation_roles": LOCAL_EVALUATION_ROLES,
        "pollen_eligible_for_heldout_acceptance": False,
    }
    destination = root / "predictions"
    stage = stage_directory(destination)
    write_json(stage, "predictions.json", predictions)
    write_json(
        stage, "experiment.json", {"observation_channels": channel_catalogue(spec)}
    )
    return publish_phase(
        stage,
        destination,
        phase="predictions",
        scientific=scientific,
        profile=LOCAL_PROFILE,
    ), {
        "schema_version": "lra-local-pollen-outcomes.v1",
        "data_kind": "synthetic",
        "records": outcomes,
    }


def test_vegetation_scores_and_assimilated_pollen_diagnostics_are_separate(
    tmp_path: Path,
) -> None:
    product, inventory = synthetic_local_product(tmp_path)
    inventory["records"].pop("p01")
    scored = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "inputs",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    rows = json.loads((scored.directory / "scores.json").read_text())
    assert len(rows) == 8
    vegetation = [r for r in rows if r["target"] == "vegetation_cover"]
    pollen = [r for r in rows if r["target"] == "pollen_composition"]
    assert all(r["evaluation_role"] == "heldout_prediction" for r in vegetation)
    assert len([r for r in vegetation if r["score"]["status"] == "scored"]) == 3
    assert all(
        r["evaluation_role"] == "in_sample_diagnostic"
        and r["eligible_for_heldout_acceptance"] is False
        and r["score"]["status"] == "scored"
        for r in pollen
    )
    assert len(json.loads((scored.directory / "outcome_access.json").read_text())) == 3


@pytest.mark.parametrize(
    "mutation",
    [
        "role",
        "anchor",
        "negative",
        "missing_source",
        "quantitative_edge",
        "source_hash",
    ],
)
def test_mislabeled_or_invalid_prediction_refused_before_outcome_access(
    tmp_path: Path, mutation: str
) -> None:
    product, inventory = synthetic_local_product(tmp_path, mutation=mutation)
    with pytest.raises(ValidationRefusal):
        score_experiment_predictions(
            product.directory,
            expected_manifest_sha256=product.manifest_sha256,
            outcome_root=tmp_path / "absent",
            outcome_inventory=inventory,
            destination=tmp_path / "scores",
        )
    assert not (tmp_path / "scores").exists()


def test_outcome_pollen_substitution_cannot_replace_assimilated_counts(
    tmp_path: Path,
) -> None:
    product, inventory = synthetic_local_product(tmp_path)
    ref = inventory["records"]["p01"]
    value = json.loads((tmp_path / "inputs" / ref["path"]).read_text())
    value["pollen_count"] = {"Alnus": 0, "Betula": 100}
    inventory["records"]["p01"] = store(tmp_path / "inputs", ref["path"], value)
    scored = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "inputs",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    rows = [
        r
        for r in json.loads((scored.directory / "scores.json").read_text())
        if r["record_id"] == "p01"
    ]
    assert (
        next(r for r in rows if r["target"] == "vegetation_cover")["score"]["status"]
        == "observation_refused"
    )
    assert next(r for r in rows if r["target"] == "pollen_composition")[
        "observation"
    ] == {"Alnus": 600, "Betula": 400}


def test_final_local_scoring_refuses_before_any_file_access(tmp_path: Path) -> None:
    with pytest.raises(ValidationRefusal) as error:
        score_experiment_predictions(
            tmp_path / "absent",
            expected_manifest_sha256="bad",
            outcome_root=tmp_path / "absent",
            outcome_inventory={"schema_version": "lra-local-pollen-outcomes.v1"},
            destination=tmp_path / "scores",
            purpose="final",
        )
    assert error.value.reason_code == "final_experiment_not_implemented"
    assert list(tmp_path.iterdir()) == []


def test_failed_local_request_rechecks_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from .test_inputs import fixture_inputs
    from .test_workflow import check_failed_source_revalidation

    request = fixture_inputs(tmp_path / "inputs")
    request.pop("baselines")
    request.update(
        profile="synthetic-local-pollen-available-v1",
        method="analytical_love_local_pollen",
    )
    check_failed_source_revalidation(
        tmp_path,
        monkeypatch,
        "bijux_pollenomics.analysis.lra_validation.experiments.assimilation",
        "prepare_local_pollen_predictions",
        request,
        local=True,
    )
