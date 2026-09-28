"""Run bounded whole-site LRA folds for author-prepared development inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bijux_pollenomics.analysis.lra_validation.experiments import (
    prepare_experiment_predictions,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = args.inputs.resolve()
    source = json.loads((inputs / "source-report.json").read_text())
    experiment = inputs / "experiment.json"
    if (
        source["schema_version"] != "author-lra-development-inputs.v1"
        or source["experiment_sha256"]
        != hashlib.sha256(experiment.read_bytes()).hexdigest()
    ):
        raise ValueError("Author development input schema differs")
    payload = json.loads(experiment.read_text())
    product = prepare_experiment_predictions(
        payload,
        input_root=inputs,
        cache_root=args.cache_root.resolve(),
        destination=args.output.resolve(),
        workers=1,
    )
    print(product.directory, product.manifest_sha256)


if __name__ == "__main__":
    main()
