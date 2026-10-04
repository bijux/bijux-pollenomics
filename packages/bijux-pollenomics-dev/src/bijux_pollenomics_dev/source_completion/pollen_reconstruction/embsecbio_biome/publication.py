"""Publish scoped EMBSeCBIO summaries from qualified private source inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

from .cohorts import entities, original_matrices, profiles
from .numerical import ORDER, evaluate
from .source import keyed, model, pollen
from .training import training_product

CAPTURE = Path("data/method-certification/embsecbio-biome/fixed-model-capture.json")
CAPTURE_SHA256 = "4c9f109424e0cdffd01a61904602f4080758542d01f8a0fc52516ee5e5a6bc1b"
SOURCE_ID = "embsecbio/published-biome-model-training"
TRAINING_CAPTURE = Path(
    "data/method-certification/embsecbio-biome/training-reconstruction-capture.json"
)
TRAINING_CAPTURE_SHA256 = (
    "41da00e15108202e0a2adee8eae318acefeaebd3ceac7cb464058449c4861342"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def products(
    directory: Path, capture: dict, training_capture: dict | None = None
) -> dict[str, dict]:
    """Recompute actual saved-model cells; separately consume retained source audit."""
    for name, expected in capture["source_sha256"].items():
        if digest(directory / name) != expected:
            raise ValueError("EMBSeCBIO captured source dependency changed")
    taxa, means, sd = model(directory)
    samples, source_rows = pollen(directory, taxa)
    labels = keyed(directory, "resolution1kmfrom250m_window21km_perside.csv")
    native_r = keyed(directory, "r-numerical.csv")
    if set(native_r) != set(samples) or set(labels) != set(samples):
        raise ValueError("native R/PNV sample population differs")
    predictions = {}
    maximum = {"distance": 0.0, "score": 0.0}
    cells = 0
    for sid, sample in sorted(samples.items()):
        distances, scores, winner = evaluate(
            [sample["values"].get(t, 0.0) for t in taxa], means, sd
        )
        predictions[sid] = winner
        if winner != native_r[sid]["prediction"]:
            raise ValueError("saved-model native R winner differs")
        for kind, values in (("distance", distances), ("score", scores)):
            for biome, value in values.items():
                reference = float(native_r[sid][biome + "_" + kind])
                difference = abs(value - reference)
                tolerance = (1e-10 if kind == "distance" else 1e-13) + 1e-12 * max(
                    abs(value), abs(reference)
                )
                if not math.isfinite(reference) or difference > tolerance:
                    raise ValueError("saved-model native R numerical cell differs")
                maximum[kind] = max(maximum[kind], difference)
                cells += 1
    selected = keyed(directory, "selected-location-samples.csv")
    if not set(selected) <= set(samples):
        raise ValueError("selected native sample is absent from published source")
    for sid, row in selected.items():
        for field in ("latitude", "longitude"):
            if float(row[field]) != float(samples[sid]["metadata"][field]):
                raise ValueError("selected native coordinates differ")
        if (
            row["Dominant"] != labels[sid]["Dominant"]
            or row["Subdominant"] != labels[sid]["Subdominant"]
        ):
            raise ValueError("selected source map labels differ")
    emb = {
        sid
        for sid, row in selected.items()
        if labels[sid]["Dominant"] in ORDER
        and 28 < float(row["latitude"]) < 49.25
        and 20 < float(row["longitude"]) < 62
    }
    historical = original_matrices(
        directory, entities(samples, labels, predictions, emb)
    )
    if (source_rows, len(samples), len(taxa), cells) != (149555, 5765, 242, 103770):
        raise ValueError("published source/model denominator changed")
    if (
        len(selected) != 4398
        or len(emb) != 917
        or not all(row["all_cells_exact"] for row in historical.values())
    ):
        raise ValueError("retained source-seed matrix replay differs")
    report = {
        "schema_version": "embsecbio-fixed-biome-model.v1",
        "source_pollen_rows": source_rows,
        "native_samples": len(samples),
        "model_taxa": len(taxa),
        "numerical_cells_compared": cells,
        "maximum_absolute_differences": maximum,
        "all_predictions_exact": True,
        "source_sha256": capture["source_sha256"],
        "equation": "distance_b=sqrt(sum_t(((percentage_t-mean_bt)/(sample_sd_bt+0.5))^2)); score_b=exp(-distance_b/100)",
        "source_percentages_renormalized": False,
        "absent_model_taxa": "zero under source-compatible declared fill",
        "sample_class_tie_order": list(ORDER),
        "score_interpretation": "unnormalized exponential distances, not calibrated probabilities or vegetation cover",
        "limits": capture["limits"],
        "capture_authority": capture["authority"],
    }
    generated = {
        "report.json": report,
        "source-audit.json": {
            "schema_version": "embsecbio-retained-native-source-audit.v1",
            "publication_scope": "Compact admitted actual native source-audit capture; current fixed-model producer does not claim a fresh raw-table scan",
            **capture["source_audit"],
        },
        "cohort-diagnostics.json": {
            "schema_version": "embsecbio-complete-cohort-map-diagnostics.v1",
            "profiles": profiles(samples, labels, predictions),
        },
        "historical-comparison.json": {
            "schema_version": "embsecbio-source-seed-matrix-compatibility.v1",
            "selection_capture_sha256": capture["source_sha256"][
                "selected-location-samples.csv"
            ],
            "source_seed": 2501,
            "all_location_samples": len(selected),
            "emb_selected_samples": len(emb),
            "matrices": historical,
            "scoped_compatibility": capture["historical_compatibility"],
        },
    }
    if training_capture is not None:
        generated["training-reconstruction.json"] = training_product(
            directory, training_capture, samples, labels, taxa, means, sd
        )
    return generated


def run(
    repository: Path,
    source_root: Path,
    descriptor: Path,
    output: Path,
    *,
    training_only: bool = False,
) -> None:
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(repository, source_root, descriptor)
    if json.loads((repository / descriptor).read_bytes())["source_id"] != SOURCE_ID:
        raise ValueError("EMBSeCBIO external source scope differs")
    capture_path = safe_source_file(
        repository, CAPTURE.as_posix(), "EMBSeCBIO numerical/source capture"
    )
    if digest(capture_path) != CAPTURE_SHA256:
        raise ValueError("EMBSeCBIO capture authority changed")
    capture = json.loads(capture_path.read_bytes())
    if capture["schema_version"] != "qualified-embsecbio-fixed-model-capture.v1":
        raise ValueError("EMBSeCBIO capture schema differs")
    training_capture_path = safe_source_file(
        repository, TRAINING_CAPTURE.as_posix(), "EMBSeCBIO training capture"
    )
    if digest(training_capture_path) != TRAINING_CAPTURE_SHA256:
        raise ValueError("EMBSeCBIO training capture authority changed")
    training_capture = json.loads(training_capture_path.read_bytes())
    stage = Path(tempfile.mkdtemp(prefix=".embsecbio-biome-", dir=output.parent))
    published = False
    try:
        if training_only:
            for name, expected in capture["source_sha256"].items():
                if digest(qualified.directory / name) != expected:
                    raise ValueError("EMBSeCBIO captured source dependency changed")
            taxa, means, sd = model(qualified.directory)
            samples, _ = pollen(qualified.directory, taxa)
            labels = keyed(
                qualified.directory, "resolution1kmfrom250m_window21km_perside.csv"
            )
            if set(labels) != set(samples):
                raise ValueError("training source/PNV sample population differs")
            generated = {
                "training-reconstruction.json": training_product(
                    qualified.directory,
                    training_capture,
                    samples,
                    labels,
                    taxa,
                    means,
                    sd,
                )
            }
        else:
            generated = products(qualified.directory, capture, training_capture)
        for name, value in generated.items():
            (stage / name).write_text(
                json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
            )
        stage.replace(output)
        published = True
    finally:
        if not published:
            pass  # Preserve refused publication bytes for artifact inspection.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--source-descriptor",
        type=Path,
        default=Path("configs/ci/qualified-report-sources/embsecbio-biome-model.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--training-only",
        action="store_true",
        help="Replay only source training statistics from the admitted native IDs",
    )
    args = parser.parse_args()
    run(
        args.repository,
        args.source_root,
        args.source_descriptor,
        args.output,
        training_only=args.training_only,
    )


if __name__ == "__main__":
    main()
