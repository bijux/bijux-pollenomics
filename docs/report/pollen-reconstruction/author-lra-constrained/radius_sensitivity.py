"""Replay target-basin forward transport with fixed author LRA vegetation."""

from __future__ import annotations

import argparse
from copy import deepcopy
import csv
import hashlib
import json
from math import pi
from pathlib import Path
from statistics import mean
from typing import Any, cast

from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.prediction import (
    prepare_forward_geometry,
)
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)

FACTORS = (0.8, 1.0, 1.2)
EXPERIMENT_SHA = "aba70474156edfd1e03ac777ddb1083b8f396f3e3a21a03d104a3b3713a544b4"
PUBLISHED_PREDICTIONS_SHA = (
    "85ce8fd89d992db10a17f15b799fa5c96de0c658eb0eec1a9e117e51a008e110"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> Any:
    return json.loads(path.read_text())


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _sources(
    inputs: Path, predictions: Path
) -> tuple[SourceExperimentSpec, dict[str, str]]:
    experiment = inputs / "experiment.json"
    manifest = predictions / "manifest.json"
    if _sha(experiment) != EXPERIMENT_SHA:
        raise ValueError("published source experiment changed")
    manifest_data = _read(manifest)
    for name in ("predictions.json", "preparations.json", "experiment.json"):
        if manifest_data["files"].get(name) != _sha(predictions / name):
            raise ValueError(f"prediction bundle member differs: {name}")
    published = Path(__file__).parent / "predictions.csv"
    if _sha(published) != PUBLISHED_PREDICTIONS_SHA:
        raise ValueError("published numerical prediction table changed")
    rows = _read(predictions / "predictions.json")
    candidate = {
        (row["fold_id"], row["record_id"], row["baseline"], taxon): (
            value,
            row["pollen_fraction"][taxon],
        )
        for row in rows
        for taxon, value in row["vegetation_fraction"].items()
    }
    with published.open(newline="", encoding="utf-8") as stream:
        retained = list(csv.DictReader(stream))
    if len(rows) != 42 or len(candidate) != 1260 or len(retained) != 1260:
        raise ValueError("published prediction coverage changed")
    for row in retained:
        key = (
            row["fold_id"],
            row["target_record_id"],
            row["method"],
            row["taxon"],
        )
        if candidate.pop(key, None) != (
            float(row["vegetation_fraction"]),
            float(row["forward_pollen_fraction"]),
        ):
            raise ValueError(
                "candidate prediction differs from published numerical result"
            )
    if candidate:
        raise ValueError("candidate contains extra prediction cells")
    spec = SourceExperimentSpec(_read(experiment))
    source = _read(inputs / "source-report.json")
    if source["experiment_sha256"] != EXPERIMENT_SHA:
        raise ValueError("source input report changed")
    return spec, {
        "producer_sha256": _sha(Path(__file__)),
        "experiment_sha256": _sha(experiment),
        "source_report_sha256": _sha(inputs / "source-report.json"),
        "prediction_manifest_sha256": _sha(manifest),
        "predictions_sha256": _sha(predictions / "predictions.json"),
        "preparations_sha256": _sha(predictions / "preparations.json"),
    }


def _geometry(geometry: dict[str, Any], factor: float) -> dict[str, Any]:
    result = deepcopy(geometry)
    basin = result["basin"]
    if basin["site_type"] != "lake":
        raise ValueError("target is not a lake")
    original_radius = basin["diameter_m"] / 2
    radius = original_radius * factor
    if not 0 < radius < 500:
        raise ValueError("radius leaves declared first ring")
    basin["diameter_m"] = 2 * radius
    for field, inner in (("forward_rings", radius), ("inversion_rings", radius + 1)):
        ring = result[field][0]
        if (
            abs(
                geometry[field][0]["inner_m"]
                - (original_radius + (field == "inversion_rings"))
            )
            > 1e-9
        ):
            raise ValueError("original basin and first ring disagree")
        outer = ring["outer_m"]
        area = pi * (outer * outer - inner * inner)
        ring.update(
            inner_m=inner,
            mean_m=(inner + outer) / 2,
            ring_area_m2=area,
            terrestrial_area_m2=area,
        )
    return result


def freeze(inputs: Path, predictions: Path, output: Path) -> None:
    """Use frozen vegetation and target geometry only; never open target pollen."""
    spec, source = _sources(inputs, predictions)
    if output.exists():
        raise FileExistsError(output)
    sites = {site.record.record_id: site for site in spec.sites}
    preparations = {
        row["fold_id"]: row for row in _read(predictions / "preparations.json")
    }
    rows = _read(predictions / "predictions.json")
    if len(rows) != 42 or len(preparations) != 14:
        raise ValueError("published fold coverage changed")
    output_rows = []
    for row in rows:
        site = sites[row["record_id"]]
        geometry_path = inputs / site.geometry.path
        if _sha(geometry_path) != site.geometry.sha256:
            raise ValueError("target geometry changed")
        original = _read(geometry_path)
        preparation = preparations[row["fold_id"]]
        if preparation["target_geometry_sha256"] != site.geometry.sha256:
            raise ValueError("prediction preparation geometry differs")
        for factor in FACTORS:
            varied = _geometry(original, factor)
            binding, prepared = prepare_forward_geometry(
                spec.template(),
                varied,
                tuple(preparation["regional_cover"]),
                local_ring_count=spec.local_ring_count,
            )
            vegetation = row["vegetation_fraction"]
            output_pollen = binding.api.forward_deposition(
                tuple(vegetation[taxon] for taxon in prepared.taxa),
                tuple(prepared.regional_deposition),
                tuple(tuple(ring) for ring in prepared.local_k),
                tuple(prepared.terrestrial_fraction),
                tuple(prepared.ppe),
            )
            pollen = dict(
                zip(prepared.taxa, output_pollen.pollen_fraction, strict=True)
            )
            if factor == 1.0 and pollen != row["pollen_fraction"]:
                raise ValueError(
                    "published baseline forward prediction did not replay exactly"
                )
            output_rows.append(
                {
                    "record_id": row["record_id"],
                    "fold_id": row["fold_id"],
                    "method": row["baseline"],
                    "radius_factor": factor,
                    "original_radius_m": original["basin"]["diameter_m"] / 2,
                    "modeled_radius_m": varied["basin"]["diameter_m"] / 2,
                    "geometry_sha256": site.geometry.sha256,
                    "published_prediction_sha256": row["prediction_manifest_sha256"],
                    "pollen_fraction": pollen,
                }
            )
    if len(output_rows) != 126:
        raise ValueError("radius projection coverage changed")
    output.mkdir(parents=True)
    _write(
        output / "predictions.json",
        {
            "schema_version": "author-lra-forward-radius-freeze.v1",
            "source": source,
            "factors": FACTORS,
            "rows": output_rows,
            "outcomes_opened": False,
            "interpretation": "Fixed published LRA vegetation and regional cover; target-basin forward transport only. Prior-exposed English development sites.",
        },
    )


def score(inputs: Path, predictions: Path, frozen: Path, output: Path) -> None:
    """Open target counts only after verifying an immutable prediction freeze."""
    spec, source = _sources(inputs, predictions)
    receipt = _read(frozen)
    if receipt["source"] != source or receipt["factors"] != list(FACTORS):
        raise ValueError("frozen source or design changed")
    if receipt["outcomes_opened"] is not False or len(receipt["rows"]) != 126:
        raise ValueError("invalid prediction freeze")
    if output.exists():
        raise FileExistsError(output)
    sites = {site.record.record_id: site for site in spec.sites}
    baseline = {}
    with (Path(__file__).parent / "scores.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["status"] == "scored":
                baseline[row["target_record_id"], row["method"]] = float(
                    row["mae_fraction"]
                )
    scored = []
    for row in receipt["rows"]:
        site = sites[row["record_id"]]
        raw_path = inputs / site.raw.path
        if _sha(raw_path) != site.raw.sha256:
            raise ValueError("target pollen source changed")
        raw = _read(raw_path)
        counts = dict(zip(raw["taxa"], raw["sample"]["counts"], strict=True))
        pollen = row["pollen_fraction"]
        result = score_pollen(pollen, counts)
        if result.status != "scored" or result.mae_fraction is None:
            raise ValueError("unexpected unscored target")
        observed = {
            taxon: count / sum(counts.values()) for taxon, count in counts.items()
        }
        if (
            row["radius_factor"] == 1.0
            and abs(result.mae_fraction - baseline[row["record_id"], row["method"]])
            > 1e-15
        ):
            raise ValueError("published baseline score did not replay")
        scored.append(
            {
                key: row[key]
                for key in (
                    "record_id",
                    "method",
                    "radius_factor",
                    "original_radius_m",
                    "modeled_radius_m",
                )
            }
            | {
                "mae_fraction": result.mae_fraction,
                "hellinger_distance": hellinger_distance(pollen, observed),
                "observed_count": sum(counts.values()),
                "observation_sha256": site.raw.sha256,
            }
        )
    summary = []
    for method in spec.baselines:
        for factor in FACTORS:
            subset = [
                row
                for row in scored
                if row["method"] == method and row["radius_factor"] == factor
            ]
            if len(subset) != 14:
                raise ValueError("paired site coverage changed")
            summary.append(
                {
                    "method": method,
                    "radius_factor": factor,
                    "scored_sites": len(subset),
                    "site_macro_mae_fraction": mean(
                        cast(float, row["mae_fraction"]) for row in subset
                    ),
                    "site_macro_hellinger_distance": mean(
                        cast(float, row["hellinger_distance"]) for row in subset
                    ),
                }
            )
    output.mkdir(parents=True)
    with (output / "scores.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(scored[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(scored)
    _write(
        output / "report.json",
        {
            "schema_version": "author-lra-forward-radius-score.v1",
            "prediction_freeze_sha256": _sha(frozen),
            "source": source,
            "eligible_sites": 15,
            "scored_sites": 14,
            "refused_site": "author:BECKHAM",
            "prediction_rows": len(receipt["rows"]),
            "scored_rows": len(scored),
            "site_macro": summary,
            "interpretation": "Previously exposed English examples; fixed LRA vegetation, regional cover, PPE and training fits. This is forward transport sensitivity, not refitted LRA, radius calibration, vegetation accuracy or Swedish admission.",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("freeze", "score"))
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--frozen", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.operation == "freeze":
        freeze(args.inputs, args.predictions, args.output)
    elif args.frozen is None:
        parser.error("--frozen is required for scoring")
    else:
        score(args.inputs, args.predictions, args.frozen, args.output)


if __name__ == "__main__":
    main()
