"""Score published constrained LOVE predictions against exact withheld source rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bijux_pollenomics.analysis.lra_validation.experiments import (
    score_experiment_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)


def score(
    inputs: Path, predictions: Path, destination: Path, prediction_manifest_sha256: str
) -> dict[str, object]:
    """Open target pollen only after authenticated prediction publication."""
    inputs, predictions, destination = (
        path.resolve() for path in (inputs, predictions, destination)
    )
    report = json.loads((inputs / "source-report.json").read_text())
    experiment = inputs / "experiment.json"
    if (
        hashlib.sha256(experiment.read_bytes()).hexdigest()
        != report["experiment_sha256"]
    ):
        raise ValueError("Source experiment bytes changed")
    spec = SourceExperimentSpec(json.loads(experiment.read_text()))
    inventory = {
        "schema_version": "lra-source-pollen-outcomes.v1",
        "data_kind": "source_observations",
        "records": {
            site.record.record_id: {"path": site.raw.path, "sha256": site.raw.sha256}
            for site in spec.sites
        },
    }
    actual_manifest_sha256 = hashlib.sha256(
        (predictions / "manifest.json").read_bytes()
    ).hexdigest()
    if actual_manifest_sha256 != prediction_manifest_sha256:
        raise ValueError("Published prediction manifest differs from frozen identity")
    product = score_experiment_predictions(
        predictions,
        expected_manifest_sha256=prediction_manifest_sha256,
        outcome_root=inputs,
        outcome_inventory=inventory,
        destination=destination,
    )
    return {
        "prediction_manifest_sha256": prediction_manifest_sha256,
        "score_manifest_sha256": product.manifest_sha256,
        "eligible_sites": len(spec.sites),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--prediction-manifest-sha256", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            score(
                args.inputs,
                args.predictions,
                args.destination,
                args.prediction_manifest_sha256,
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
