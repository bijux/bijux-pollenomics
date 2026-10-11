"""Retained source declarations join actual request bodies, including failed attempts."""

from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.batches.models import LRABatchItem
from bijux_pollenomics.analysis.lra_validation.contracts import Fold, manifest_sha256
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    ExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import make_request
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import write_json
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out


def retained_fold_evidence(
    spec: ExperimentSpec, fold: Fold, root: Path, composition: dict[str, float]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Actual admitted request fixtures; declared synthetic fits do not claim solver execution."""
    sites = {site.record.record_id: site for site in spec.sites}
    groups = {
        record: candidate.test_group_ids[0]
        for candidate in grouped_leave_one_out([site.record for site in spec.sites])
        for record in candidate.test_record_ids
    }
    anchor = next(
        record for record in spec.regional_priority if record in fold.train_record_ids
    )
    items = []
    products = []
    for record in fold.train_record_ids:
        if record == anchor:
            continue
        request = make_request(spec, sites[record], sites[anchor], fold, root)
        item = LRABatchItem(record, request)
        items.append(
            {
                "item_id": record,
                "request_sha256": item.request_sha256,
                "request": request,
            }
        )
        products.append(
            {
                "record_id": record,
                "group_id": groups[record],
                "composition": composition,
                "request_sha256": item.request_sha256,
            }
        )
    training = {
        "fold_id": fold.fold_id,
        "outer_fold": fold.as_dict(),
        "regional_anchor_record_id": anchor,
        "regional_anchor_group_id": groups[anchor],
        "predictor_group_ids": sorted(
            groups[record] for record in fold.train_record_ids if record != anchor
        ),
        "training_products": products,
    }
    return training, {"event": "attempt_started", "items": items}


def fixture_identities(
    spec: ExperimentSpec, record: str, training: dict[str, Any]
) -> tuple[str, str, str]:
    template = spec.template()
    target = next(site for site in spec.sites if site.record.record_id == record)
    return (
        "experiment-regional:"
        + manifest_sha256(
            {
                "anchor": training["regional_anchor_record_id"],
                "fits": training["training_products"],
            }
        ),
        "experiment-parameters:"
        + manifest_sha256(
            {"parameters": template["parameters"], "evidence": template["evidence"]}
        ),
        "experiment-geometry:" + target.geometry.sha256,
    )


def write_retained_evidence(
    stage: Path, training: list[dict[str, Any]], batches: list[dict[str, Any]]
) -> None:
    write_json(stage, "training.json", training)
    for index, batch in enumerate(batches):
        directory = stage / "batches" / f"fold-{index:04}"
        directory.mkdir(parents=True)
        write_json(directory, "receipt.json", batch)


def test_source_reference_and_ppe_contradictions_refuse_before_outcomes(
    tmp_path: Path,
) -> None:
    from copy import deepcopy
    import hashlib
    import json
    import shutil

    import pytest

    from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
    from bijux_pollenomics.analysis.lra_validation.experiments import (
        score_experiment_predictions,
    )

    from ..test_scoring import prediction_product

    product, inventory = prediction_product(tmp_path / "original")
    for field in (
        "raw_sha256",
        "geometry_sha256",
        "ppe",
        "missing_batch",
        "request_digest",
    ):
        destination = tmp_path / field
        shutil.copytree(product.directory, destination)
        manifest = json.loads((destination / "manifest.json").read_text())
        metadata = json.loads((destination / "experiment.json").read_text())
        if field in {"raw_sha256", "geometry_sha256"}:
            metadata["source_catalogue"][0][field] = "0" * 64
        elif field == "ppe":
            metadata["request_template"]["parameters"][0]["ppe"] += 1
        else:
            receipt = destination / "batches" / "fold-0000" / "receipt.json"
            if field == "missing_batch":
                receipt.unlink()
            else:
                batch = json.loads(receipt.read_text())
                batch["items"][0]["request_sha256"] = "0" * 64
                receipt.write_text(json.dumps(batch))
        (destination / "experiment.json").write_text(json.dumps(metadata))
        manifest["files"] = {
            p.relative_to(destination).as_posix(): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in destination.rglob("*")
            if p.is_file() and p != destination / "manifest.json"
        }
        (destination / "manifest.json").write_text(json.dumps(manifest))
        with pytest.raises(ValidationRefusal):
            score_experiment_predictions(
                destination,
                expected_manifest_sha256=hashlib.sha256(
                    (destination / "manifest.json").read_bytes()
                ).hexdigest(),
                outcome_root=tmp_path / "unopened",
                outcome_inventory=deepcopy(inventory),
                destination=tmp_path / ("score-" + field),
            )
        assert not (tmp_path / ("score-" + field)).exists()
