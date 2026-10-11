"""Saved block declarations cannot contradict complete folds or scientific posture."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.experiments.fitted.metadata import (
    validate_block_metadata,
)

from .test_reading import refusal_inventory


@pytest.mark.parametrize(
    "mutation",
    [
        "removed_block",
        "catalogue_block",
        "empirical",
        "uncertainty",
        "interrupt_type",
        "hidden_interruption",
        "invented_fit",
    ],
)
def test_complete_metadata_refuses_rehashed_contradictions(
    tmp_path: Path, mutation: str
) -> None:
    scientific = refusal_inventory(tmp_path)
    request = json.loads((tmp_path / "declared-request.json").read_text())
    experiment = {
        "schema_version": "lra-spatial-block-experiment.v1",
        "request": request,
    }
    original = deepcopy(scientific)
    folds = {fold["fold_id"]: fold for fold in scientific["folds"]}
    validate_block_metadata(experiment, scientific, folds, {}, {})
    if mutation == "removed_block":
        removed = scientific["folds"].pop()["fold_id"]
        scientific["failures"] = [
            row for row in scientific["failures"] if row["fold_id"] != removed
        ]
        scientific.update(
            requested_folds=2,
            requested_predictions=6,
            failed_predictions=6,
            failed_folds=2,
            split_manifest_sha256=manifest_sha256(scientific["folds"]),
        )
        folds.pop(removed)
    elif mutation == "catalogue_block":
        request["sites"][0]["block_id"] = request["sites"][4]["block_id"]
    elif mutation == "empirical":
        request["request_template"]["data_kind"] = "empirical"
    elif mutation == "uncertainty":
        scientific["uncertainty_status"] = "validated_joint_intervals"
    elif mutation == "interrupt_type":
        scientific["interrupted"] = 0
    elif mutation == "hidden_interruption":
        scientific["failures"][0].update(
            status="not_run", reason_code="experiment_interrupted"
        )
    else:
        scientific["block_model_sha256"] = {next(iter(folds)): "a" * 64}
    with pytest.raises(ValidationRefusal):
        validate_block_metadata(experiment, scientific, folds, {}, {})
    assert original["requested_predictions"] == 9


def test_shared_training_state_admits_non_block_criterion_and_binds_coordinates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.analysis.lra_validation.experiments.fitted import (
        validate_training_state,
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.fitted.model import (
        fit_reconstructed_training,
        retained_training_state,
    )
    from bijux_pollenomics.analysis.lra_validation.spatial import SiteCoordinate
    from bijux_pollenomics.analysis.lra_validation.splits import admit_training_groups

    from .test_model import fitted_fixture

    spec, fold, fits, groups = fitted_fixture(tmp_path, monkeypatch)
    admission = admit_training_groups(
        fold,
        [site.record for site in spec.sites],
        fold.train_group_ids,
        criterion={"profile": "declared-temporal-test-only"},
    )
    sites = {site.record.record_id: site for site in spec.sites}
    products = []
    for value in fits.fit_identities:
        site = sites[str(value["record_id"])]
        refs = {}
        for role, owner in [("local", site), ("regional", fits.anchor)]:
            for field, ref in [("raw", owner.raw), ("geometry", owner.geometry)]:
                refs[role + "_" + field] = {"path": ref.path, "sha256": ref.sha256}
        products.append(
            dict(
                value,
                request_template_sha256=manifest_sha256(spec.template()),
                source_references=refs,
                local_support_radius_m=spec.local_support_radius_m,
                support_profile=spec.support_profile,
            )
        )
    fits = replace(fits, fit_identities=tuple(products))
    state = fit_reconstructed_training(
        spec, fold, fits, groups, input_root=tmp_path, training_admission=admission
    )
    saved = retained_training_state(state, groups)
    coordinates = dict(zip(state.model.groups, state.model.centres, strict=True))
    admitted = validate_training_state(
        spec, fold, admission, saved, expected_coordinates=coordinates
    )
    assert admitted.model_sha256 == state.model.model_sha256
    malformed = dict(saved)
    malformed.pop("model_sha256")
    with pytest.raises(ValidationRefusal):
        validate_training_state(
            spec, fold, admission, malformed, expected_coordinates=coordinates
        )
    key = next(iter(coordinates))
    coordinates[key] = SiteCoordinate(0, 0)
    with pytest.raises(ValidationRefusal, match="fit coordinates"):
        validate_training_state(
            spec, fold, admission, saved, expected_coordinates=coordinates
        )
