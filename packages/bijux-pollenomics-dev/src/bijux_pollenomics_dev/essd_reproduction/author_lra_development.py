"""Materialize a bounded author-prepared LRA development cohort."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from .author_pollen_spatial.source import _study

WINDOW = 5
LABEL_BP = "1500"
YOUNGER_BP = 1250
OLDER_BP = 1750
FALL_SPEED_PROFILE = "landclimii-2016-gpm-neutral-analytical-v1"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path, expected: str) -> list[list[str]]:
    if _sha(path) != expected:
        raise ValueError(f"Author source bytes changed: {path.name}")
    with path.open(newline="") as stream:
        return list(csv.reader(stream))


def _store(root: Path, name: str, value: object) -> dict[str, str]:
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode()
    (root / name).write_bytes(data)
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}


def _rings(radius: float, *, inversion: bool) -> list[dict[str, float]]:
    edges = [radius + (1 if inversion else 0), 500, 1000, 10_000, 100_000]
    if not 0 < radius < 500:
        raise ValueError("Author basin radius exceeds the declared local rings")
    return [
        {
            "inner_m": low,
            "outer_m": high,
            "mean_m": (low + high) / 2,
            "ring_area_m2": math.pi * (high * high - low * low),
            "terrestrial_area_m2": math.pi * (high * high - low * low),
        }
        for low, high in zip(edges[:-1], edges[1:], strict=True)
    ]


def materialize_author_lra_development(source_root: Path, output: Path) -> Path:
    """Keep author counts private and expose source-bound local experiment inputs."""
    source_root, output = source_root.resolve(), output.resolve()
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    author = source_root / "author"
    study = _study(author, source_root / "reference")
    snapshot = json.loads((source_root / "snapshot-manifest.json").read_text())
    source_hashes: dict[str, str] = snapshot["files"]

    def checked(relative: str) -> list[list[str]]:
        return _rows(author / relative, source_hashes["author/" + relative])

    boundaries = [int(row[0]) for row in checked("bins.csv")]
    lookup = checked("TWlookup.csv")
    if (
        len(boundaries) != 26
        or (boundaries[WINDOW - 1], boundaries[WINDOW]) != (YOUNGER_BP, OLDER_BP)
        or lookup[WINDOW] != [str(WINDOW), LABEL_BP]
    ):
        raise ValueError("Author time-window support changed")
    means = checked("run.REVEALS.files/av-RPP.all.landclimII.csv")
    covariance = checked("run.REVEALS.files/avar-RPP.all.landclimII.csv")
    if (
        len(means) != 32
        or len(covariance) != 32
        or [row[0] for row in means[1:]] != study.taxa
        or [row[0] for row in covariance[1:]] != study.taxa
        or covariance[0][1:] != study.taxa
    ):
        raise ValueError("Author parameter axes changed")
    parameters = []
    for index, (mean, cov) in enumerate(zip(means[1:], covariance[1:], strict=True), 1):
        if cov[0] != mean[0] or len(cov) != 32:
            raise ValueError("Author PPE covariance row changed")
        ppe, speed, variance = float(mean[1]), float(mean[2]), float(cov[index])
        if not all(math.isfinite(x) for x in (ppe, speed, variance)) or (
            ppe <= 0 or not 0.006 <= speed <= 0.15 or variance < 0
        ):
            raise ValueError("Author PPE or fall-speed domain changed")
        parameters.append(
            {
                "taxon": study.prepared_taxa[index - 1],
                "ppe": ppe,
                "fallspeed_m_s": speed,
                "ppe_sd": math.sqrt(variance),
            }
        )

    observations: list[tuple[Any, float, list[int]]] = []
    unavailable = []
    for site in study.sites:
        relative = "run.REVEALS.files/" + site.count_filename
        rows = checked(relative)
        if (
            len(rows) != 34
            or rows[1][0] != "radius"
            or rows[2][0] != "model"
            or [row[0] for row in rows[3:]] != study.prepared_taxa
        ):
            raise ValueError(f"Author prepared taxon axis changed: {site.site_id}")
        column = rows[0].index(LABEL_BP)
        radius = float(rows[1][column])
        model = int(rows[2][column])
        counts = [int(row[column]) for row in rows[3:]]
        if any(count < 0 for count in counts):
            raise ValueError("Author prepared pollen count changed")
        if sum(counts) == 0:
            if radius != 0 or model != 0:
                raise ValueError("Empty author window has positive basin metadata")
            unavailable.append(site.site_id)
            continue
        if radius != site.radius_m or model != 2:
            raise ValueError("Author lake radius or model disagrees with site metadata")
        observations.append((site, radius, counts))
    if len(observations) != 15 or len(unavailable) != 2:
        raise ValueError("Author TW5 eligible denominator changed")

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".author-lra-", dir=output.parent))
    try:
        chronology = _store(
            stage,
            "chronology.json",
            {
                "source": "author bins.csv/TWlookup.csv",
                "window": WINDOW,
                "bounds_cal_bp": [YOUNGER_BP, OLDER_BP],
                "label_bp": LABEL_BP,
            },
        )
        taxonomy = _store(
            stage,
            "taxa.json",
            {
                "source_sha256": source_hashes["reference/taxon-name-crosswalk.csv"],
                "prepared_taxa": study.prepared_taxa,
            },
        )
        parameter_reference = _store(
            stage,
            "parameters.json",
            {
                "means_sha256": source_hashes[
                    "author/run.REVEALS.files/av-RPP.all.landclimII.csv"
                ],
                "covariance_sha256": source_hashes[
                    "author/run.REVEALS.files/avar-RPP.all.landclimII.csv"
                ],
            },
        )
        lock = _store(
            stage,
            "dependency-lock.json",
            {"source_manifest_sha256": study.source_manifest_sha256},
        )
        decision = _store(
            stage,
            "decision.json",
            {
                "purpose": "exploratory-author-prepared-LRA-development",
                "ring_assumption": "circular-basin-and-homogeneous-terrestrial-annuli",
                "vegetation_truth": "none",
            },
        )
        evidence = [
            {"evidence_id": role, "role": role, **reference}
            for role, reference in (
                ("chronology", chronology),
                ("taxa", taxonomy),
                ("parameters", parameter_reference),
                ("dependency_lock", lock),
                ("decision", decision),
            )
        ]
        sites = []
        for site, radius, counts in observations:
            metadata = {
                "site_id": site.site_id,
                "sample_id": site.site_id + ":TW5",
                "coordinate": 1500,
                "bin_id": "author-TW5",
                "age_type": "calendar_bp",
                "age_support_bp": [[YOUNGER_BP, OLDER_BP]],
                "chronology_evidence_id": "chronology",
            }
            geometry = {
                "basin": {"diameter_m": radius * 2, "site_type": "lake"},
                "inversion_rings": _rings(radius, inversion=True)[:2],
                "forward_rings": _rings(radius, inversion=False),
                "sample_metadata": metadata,
                "longitude": site.longitude,
                "latitude": site.latitude,
            }
            sites.append(
                {
                    "record_id": site.record_id,
                    "site_id": site.site_id,
                    "identity_keys": [],
                    "raw": _store(
                        stage,
                        site.site_id + "-raw.json",
                        {
                            "data_kind": "source_observations",
                            "taxa": study.prepared_taxa,
                            "sample": dict(metadata, counts=counts),
                        },
                    ),
                    "geometry": _store(
                        stage, site.site_id + "-geometry.json", geometry
                    ),
                }
            )
        methods = ("training_mean", "nearest_site", "inverse_distance_squared")
        profile = {
            "schema_version": "lra-experiment.v1",
            "profile": "source-observations-withheld-site-baselines-v1",
            "sites": sites,
            "regional_priority": [site["record_id"] for site in sites],
            "baselines": methods,
            "local_ring_count": 2,
            "local_support_radius_m": 1000,
            "support_profile": "same-outer-radius-homogeneous-v1",
            "request_template": {
                "schema_version": "lra-request.v1",
                "operation": "lra",
                "data_kind": "source_observations",
                "purpose": "exploratory",
                "method_profile": "disqover-0.9.14-source-compatible",
                "taxa": study.prepared_taxa,
                "pollen_unit": "count",
                "configuration": {
                    "seed": 7,
                    "love": {
                        "method": "analytical",
                        "stochastic": False,
                        "max_ring": 2,
                        "repeats": 2,
                        "distance_weighting": "gpm neutral",
                        "fall_speed_profile": FALL_SPEED_PROFILE,
                    },
                    "reveals": {
                        "stochastic": False,
                        "iterations": 2,
                        "distance_weighting": "gpm neutral",
                        "fall_speed_profile": FALL_SPEED_PROFILE,
                    },
                },
                "parameters": parameters,
                "evidence": evidence,
                "exclusions": [],
                "uncertainty_omissions": [
                    "chronology",
                    "basin_geometry",
                    "parameter_domain",
                    "spatial_model",
                    "ppe_covariance",
                ],
                "temporal_matching": {
                    "rule": "declared_bin_stationarity",
                    "decision_evidence_id": "decision",
                    "bins": [
                        {
                            "bin_id": "author-TW5",
                            "younger_bp": YOUNGER_BP,
                            "older_bp": OLDER_BP,
                        }
                    ],
                },
                "versions": dict.fromkeys(
                    ("binning", "chronology", "geometry", "parameters", "taxonomy"),
                    study.source_manifest_sha256,
                ),
            },
        }
        reference = _store(stage, "experiment.json", profile)
        _store(
            stage,
            "source-report.json",
            {
                "schema_version": "author-lra-development-inputs.v1",
                "source_manifest_sha256": study.source_manifest_sha256,
                "experiment_sha256": reference["sha256"],
                "eligible_sites": [site["site_id"] for site in sites],
                "zero_count_sites": sorted(unavailable),
                "total_count": sum(sum(counts) for _, _, counts in observations),
                "selected_window": WINDOW,
                "age_support_bp": [YOUNGER_BP, OLDER_BP],
                "ring_geometry": "declared circular/homogeneous modeling assumption",
                "scientific_posture": "prior-exposed exploratory development; no vegetation truth",
            },
        )
        os.replace(stage, output)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = materialize_author_lra_development(args.author_source_root, args.output)
    print(output / "source-report.json")


if __name__ == "__main__":
    main()
