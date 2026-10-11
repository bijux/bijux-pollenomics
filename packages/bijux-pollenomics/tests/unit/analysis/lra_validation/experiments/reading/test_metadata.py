"""Canonical singleton declarations remain mandatory before scoring."""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal, manifest_sha256
from bijux_pollenomics.analysis.lra_validation.experiments import (
    read_withheld_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reading.metadata import (
    validate_singleton_metadata,
)

from ..test_scoring import prediction_product


@pytest.mark.parametrize(
    "mutation",
    [
        "omitted_fold",
        "catalogue",
        "empirical",
        "joint_intervals",
        "duplicate_record",
        "missing_ref",
        "interrupt_type",
        "false_count",
    ],
)
def test_singleton_metadata_contradictions_are_refused(
    tmp_path: Path, mutation: str
) -> None:
    product, _ = prediction_product(tmp_path)
    _, manifest, folds, rows, methods = read_withheld_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
        object_mapping,
    )

    scientific: dict[str, Any] = deepcopy(
        object_mapping(manifest["scientific_payload"], "scientific_payload")
    )
    metadata = json.loads((product.directory / "experiment.json").read_text())
    if mutation == "omitted_fold":
        removed = scientific["folds"].pop()["fold_id"]
        folds.pop(removed)
        rows = {key: row for key, row in rows.items() if key[0] != removed}
        scientific["predictions"] = list(rows.values())
        scientific.update(
            requested_folds=len(folds),
            requested_predictions=len(rows),
            generated_predictions=len(rows),
            split_manifest_sha256=manifest_sha256(scientific["folds"]),
        )
    elif mutation == "catalogue":
        metadata["source_catalogue"][0]["record_id"] = "replaced-owner"
    elif mutation == "empirical":
        metadata["request_template"]["data_kind"] = "empirical"
    elif mutation == "joint_intervals":
        scientific["uncertainty_status"] = "validated-joint-intervals"
    elif mutation == "duplicate_record":
        metadata["source_catalogue"][0] = metadata["source_catalogue"][1]
    elif mutation == "missing_ref":
        metadata["source_catalogue"][0]["raw_sha256"] = ""
    elif mutation == "interrupt_type":
        scientific["interrupted"] = 0
    else:
        scientific["generated_predictions"] = len(rows) - 1
    with pytest.raises(ValidationRefusal):
        validate_singleton_metadata(metadata, scientific, folds, rows, methods)
