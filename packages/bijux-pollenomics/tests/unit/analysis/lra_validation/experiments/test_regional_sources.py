"""Regional-only roles stay immutable, grouped and absent from held-out channels."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    grouped_leave_one_out,
)
from bijux_pollenomics.analysis.lra_validation.experiments import (
    SourceExperimentSpec,
    read_withheld_predictions,
    reconstruction,
    workflow,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    make_request,
    read_geometry,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reading.metadata import (
    validate_singleton_metadata,
)

from .test_inputs import source_fixture_inputs, store


def regional_inputs(root: Path) -> dict[str, Any]:
    payload = source_fixture_inputs(root)
    payload["target_record_ids"] = ["p01", "p02", "p03"]
    payload["regional_priority"] = ["p04"]
    anchor = payload["sites"][-1]
    geometry = json.loads((root / anchor["geometry"]["path"]).read_bytes())
    del geometry["inversion_rings"], geometry["forward_rings"]
    geometry["basin"]["diameter_m"] = 1674
    anchor["geometry"] = store(root, anchor["geometry"]["path"], geometry)
    return payload


def test_role_selection_and_template_are_immutable(tmp_path: Path) -> None:
    payload = regional_inputs(tmp_path)
    spec = SourceExperimentSpec(payload)
    payload["target_record_ids"].append("p04")
    assert spec.target_record_ids == ("p01", "p02", "p03")
    with pytest.raises(FrozenInstanceError):
        spec.target_record_ids = ("p04",)  # type: ignore[misc]
    assert (
        len(
            grouped_leave_one_out(
                [site.record for site in spec.sites],
                target_record_ids=spec.target_record_ids,
            )
        )
        == 3
    )


def test_absent_selection_retains_all_original_folds(tmp_path: Path) -> None:
    spec = SourceExperimentSpec(source_fixture_inputs(tmp_path))
    assert spec.target_record_ids is None
    old = grouped_leave_one_out([site.record for site in spec.sites])
    assert len(old) == 4
    assert (
        grouped_leave_one_out(
            [site.record for site in spec.sites],
            target_record_ids=[site.record.record_id for site in spec.sites],
        )
        == old
    )


@pytest.mark.parametrize("selection", [[], ["p01", "p01"], ["unknown"], None])
def test_invalid_target_population_refused_without_source_access(
    tmp_path: Path, selection: object
) -> None:
    payload = regional_inputs(tmp_path)
    payload["target_record_ids"] = selection
    for site in payload["sites"]:
        (tmp_path / site["raw"]["path"]).unlink()
    with pytest.raises(ValidationRefusal):
        SourceExperimentSpec(payload)


def test_full_transitive_family_is_built_before_role_selection(tmp_path: Path) -> None:
    payload = regional_inputs(tmp_path)
    payload["sites"][3]["identity_keys"] = ["bridge"]
    payload["sites"][2]["identity_keys"] = ["bridge", "p02"]
    for site in payload["sites"]:
        (tmp_path / site["raw"]["path"]).unlink()
    with pytest.raises(ValidationRefusal) as error:
        SourceExperimentSpec(payload)
    assert error.value.reason_code == "cross_role_identity_group"


def test_regional_geometry_has_no_invented_local_rings(tmp_path: Path) -> None:
    spec = SourceExperimentSpec(regional_inputs(tmp_path))
    anchor = spec.sites[-1]
    geometry = read_geometry(tmp_path, anchor, spec)
    assert set(geometry) == {"basin", "sample_metadata", "longitude", "latitude"}
    assert geometry["basin"] == {"diameter_m": 1674, "site_type": "lake"}
    geometry["inversion_rings"] = []
    ref = store(tmp_path, anchor.geometry.path, geometry)
    changed = replace(anchor, geometry=replace(anchor.geometry, sha256=ref["sha256"]))
    with pytest.raises(ValidationRefusal, match="Unexpected or missing geometry"):
        read_geometry(tmp_path, changed, spec)


def test_regional_local_and_withheld_requests_refused_before_observations(
    tmp_path: Path,
) -> None:
    spec = SourceExperimentSpec(regional_inputs(tmp_path))
    catalogue = grouped_leave_one_out([site.record for site in spec.sites])
    fold = next(fold for fold in catalogue if fold.test_record_ids == ("p01",))
    groups = {
        record: row.test_group_ids[0]
        for row in catalogue
        for record in row.test_record_ids
    }
    for site in spec.sites:
        (tmp_path / site.raw.path).unlink()
    with pytest.raises(ValidationRefusal) as error:
        make_request(spec, spec.sites[-1], spec.sites[-1], fold, tmp_path)
    assert error.value.reason_code == "regional_only_local_source"
    regional_target = next(row for row in catalogue if row.test_record_ids == ("p04",))
    with pytest.raises(ValidationRefusal):
        reconstruction.reconstruct_fold(
            spec,
            regional_target,
            groups,
            input_root=tmp_path,
            cache_root=tmp_path / "cache",
            report_root=tmp_path / "batch",
            workers=1,
        )
    assert not (tmp_path / "batch").exists()


def test_each_admitted_target_has_exactly_two_local_requests(tmp_path: Path) -> None:
    spec = SourceExperimentSpec(regional_inputs(tmp_path))
    assert spec.target_record_ids is not None
    for fold in grouped_leave_one_out(
        [site.record for site in spec.sites], target_record_ids=spec.target_record_ids
    ):
        predictors = [
            site
            for site in spec.sites
            if site.record.record_id in fold.train_record_ids
            and site.record.record_id in spec.target_record_ids
        ]
        assert len(predictors) == 2
        for local in predictors:
            request: Any = make_request(spec, local, spec.sites[-1], fold, tmp_path)
            assert request["regional"]["basin"]["diameter_m"] == 1674
            assert request["local"]["samples"][0]["sample_id"].startswith(
                local.record.record_id
            )
            assert request["regional"]["samples"][0]["sample_id"].startswith("p04")


def test_one_negative_local_fit_cannot_fall_back_to_the_other(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = SourceExperimentSpec(regional_inputs(tmp_path))
    catalogue = grouped_leave_one_out([site.record for site in spec.sites])
    groups = {
        record: row.test_group_ids[0]
        for row in catalogue
        for record in row.test_record_ids
    }
    fold = next(row for row in catalogue if row.test_record_ids == ("p01",))
    items = []

    def batch(values: Any, **kwargs: Any) -> Any:
        items.extend(values)
        return SimpleNamespace(
            interrupted=False,
            all_items_completed=True,
            items=[
                SimpleNamespace(
                    item_id=item.item_id,
                    product=object(),
                    request_sha256=item.request_sha256,
                )
                for item in values
            ],
        )

    extracted = []

    def extract(*args: Any) -> Any:
        extracted.append(args)
        if len(extracted) == 2:
            raise ValidationRefusal(
                "invalid_composition",
                "Synthetic signed vector -0.1,1.1 retained by native owner",
            )
        return {"Alnus": 0.6, "Betula": 0.4}, (0.5, 0.5), {}

    monkeypatch.setattr(reconstruction, "run_lra_batch", batch)
    monkeypatch.setattr(reconstruction, "extract_reconstruction", extract)
    with pytest.raises(ValidationRefusal, match="signed vector"):
        reconstruction.reconstruct_fold(
            spec,
            fold,
            groups,
            input_root=tmp_path,
            cache_root=tmp_path / "cache",
            report_root=tmp_path / "batch",
            workers=1,
        )
    assert len(items) == len(extracted) == 2


def refused_product(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    payload = regional_inputs(tmp_path / "inputs")
    monkeypatch.setattr(workflow, "load_engine", object)
    monkeypatch.setattr(
        workflow, "capture_code_identity", lambda _: SimpleNamespace(payload=dict)
    )
    monkeypatch.setattr(workflow, "verify_code_identity", lambda *args: None)
    monkeypatch.setattr(workflow, "_implementation", dict)

    def negative(*args: Any, **kwargs: Any) -> Any:
        raise ValidationRefusal(
            "invalid_composition", "Synthetic required local predictor is negative"
        )

    monkeypatch.setattr(workflow, "reconstruct_fold", negative)
    return workflow.prepare_experiment_predictions(
        payload,
        input_root=tmp_path / "inputs",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "prediction",
    )


def test_three_refused_folds_reopen_with_nine_method_dispositions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = refused_product(tmp_path, monkeypatch)
    _, manifest, folds, predictions, methods = read_withheld_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    scientific: Any = manifest["scientific_payload"]
    assert len(folds) == 3 and len(methods) == 3 and not predictions
    assert scientific["requested_predictions"] == 9 and len(scientific["failures"]) == 3
    retained_folds: Any = folds
    assert all(
        "p04" in fold["train_record_ids"] and "p04" not in fold["test_record_ids"]
        for fold in retained_folds.values()
    )


@pytest.mark.parametrize(
    "mutation", ["omitted_selection", "regional_target", "omitted_target"]
)
def test_reopened_target_selection_tampering_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    product = refused_product(tmp_path, monkeypatch)
    _, manifest, folds, predictions, methods = read_withheld_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    metadata = json.loads((product.directory / "experiment.json").read_bytes())
    scientific: Any = manifest["scientific_payload"]
    if mutation == "omitted_selection":
        del metadata["target_record_ids"]
    elif mutation == "regional_target":
        metadata["target_record_ids"].append("p04")
    else:
        metadata["target_record_ids"].pop()
    with pytest.raises(ValidationRefusal):
        validate_singleton_metadata(metadata, scientific, folds, predictions, methods)
