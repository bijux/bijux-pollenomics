"""Reproduce a conditional English hybrid receiving-disk PPE account."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import shutil
import tempfile
from typing import Any

import numpy as np

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import (
    safe_source_file as _safe_file,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction import (
    english_shared_ppe as english,
)
from bijux_pollenomics_lra.api import fit_shared_ppe_likelihood

CAPTURE = Path("data/method-certification/english-receiver-annulus/kernel-capture.json")
CAPTURE_SHA256 = "f0eb17181b88498aafbea9c18b3cad47701d117cb3c5a07f2321ceec18723094"
NOMINAL_COVER = {
    "Betula": 0.000686079829522849,
    "Calluna.vulgaris": 0.021086575494765877,
    "Fagus.sylvatica": 0.0006659922836181732,
    "Fraxinus": 0.0010324648465220956,
    "Plantago.lanceolata.type": 0.0030438360051475324,
    "Poaceae": 0.9729444434199388,
    "Rumex.acetosa.t": 0.0005406081204845871,
}
NOMINAL_OBJECTIVE = 1.0121082419620198


def _captured_kernel(
    repository: Path, payload: dict[str, Any]
) -> tuple[np.ndarray, str]:
    """Use an independently admitted mathematical capture, never infer its authority."""
    path = _safe_file(repository, CAPTURE.as_posix(), "English receiver kernel capture")
    digest = english._sha(path)
    if digest != CAPTURE_SHA256:
        raise ValueError("English receiver kernel capture identity differs")
    record = json.loads(path.read_bytes())
    if (
        record["schema_version"] != "qualified-english-receiver-annulus-kernels.v1"
        or record["source_manifest_sha256"] != english.MANIFEST_SHA256
        or record["prepared_request_sha256"] != english.REQUEST_SHA256
        or record["producer_native_exit"] != 1
        or record["case_count"] != 60
        or record["receiver_radius_m"] != 80
    ):
        raise ValueError("English receiver capture scope differs")
    for name, expected in record["kernel_dependency_sha256"].items():
        if (
            english._sha(
                _safe_file(repository, name, "English receiver mathematical source")
            )
            != expected
        ):
            raise ValueError(
                "English receiver captured mathematical dependency changed"
            )
    cases = record["cases"]
    lookup = {
        (row["fall_speed_m_s"], row["inner_m"], row["outer_m"]): row for row in cases
    }
    expected_keys = {
        (p["fallspeed_m_s"], r["inner_m"], r["outer_m"])
        for p in payload["parameters"]
        for r in payload["rings"]
    }
    if len(cases) != 60 or len(lookup) != 60 or set(lookup) != expected_keys:
        raise ValueError("English receiver captured source/ring support differs")
    if set(record["case_sha256"]) != {
        json.dumps(list(key), separators=(",", ":")) for key in lookup
    }:
        raise ValueError("English receiver captured case identities differ")
    for key, row in lookup.items():
        encoded = json.dumps(
            row, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        if (
            hashlib.sha256(encoded).hexdigest()
            != record["case_sha256"][json.dumps(list(key), separators=(",", ":"))]
        ):
            raise ValueError("English receiver captured case bytes differ")
        if any(
            not math.isfinite(row[name]) or not 0 < row[name] <= 1
            for name in ("factor", "independent_order64", "independent_order128")
        ):
            raise ValueError("English receiver captured probability is unresolved")
        if any(
            not math.isfinite(row[name]) or row[name] < 0
            for name in (
                "estimated_absolute_error_nonrigorous",
                "coarse_fine_abs",
                "adaptive_fine_abs",
            )
        ):
            raise ValueError(
                "English receiver captured numerical diagnostic is unresolved"
            )
    if any(
        not row["passes_frozen_1e_minus7"]
        or abs(row["independent_order64"] - row["independent_order128"]) > 1e-7
        or abs(row["factor"] - row["independent_order128"]) > 1e-7
        for row in cases
    ):
        raise ValueError("English receiver captured independent comparison refused")
    matrix = np.array(
        [
            [
                lookup[(p["fallspeed_m_s"], r["inner_m"], r["outer_m"])]["factor"]
                for p in payload["parameters"]
            ]
            for r in payload["rings"]
        ]
    )
    if matrix.shape != (3, 30) or not np.isfinite(matrix).all() or np.any(matrix <= 0):
        raise ValueError("English receiver captured coefficients are unresolved")
    return matrix, digest


def _products(
    payload: dict[str, Any],
    result: Any,
    covariance_sha256: str,
    evidence: dict[str, str],
    capture_sha256: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report, diagnostics = english._compact_products(
        payload, result, covariance_sha256, evidence
    )
    report.update(
        {
            "schema_version": "english-receiver-annulus-shared-ppe-sensitivity.v1",
            "kernel_capture_sha256": capture_sha256,
            "zero_second_local_ring": False,
            "hybrid_geometry": True,
            "local_receiver_radius_m": 80,
            "local_source_annuli_m": [[81, 500], [500, 1000], [1000, 10000]],
            "regional_kernel": "historical source-compatible lake radius 150 m/cutoff 100000 m",
            "finite_domain": "80–81 m guard strip and sources beyond 10000 m excluded locally",
            "chronology": "author TW5 aggregate 1250–1750 BP labeled 1500; no independent physical-core chronology",
            "source_populations": {
                "regional": {
                    "original": 741,
                    "excluded_Filipendula": 42,
                    "retained": 699,
                },
                "local": {"original": 563, "excluded_Filipendula": 10, "retained": 553},
                "positive_site_cohort": {
                    "sites": 15,
                    "original": 20732,
                    "excluded_Filipendula": 159,
                    "retained": 20573,
                },
                "empty_author_windows": 2,
            },
            "maximum_vertex_condition_number": max(
                fit.vertex_condition_number for fit in result.fits
            ),
            "rounded_regional_cover_sum_min": float(
                result.regional_cover.sum(axis=1).min()
            ),
            "rounded_regional_cover_sum_max": float(
                result.regional_cover.sum(axis=1).max()
            ),
            "nominal_mean_negative_log_likelihood": result.fits[
                0
            ].mean_negative_log_likelihood,
            "interpretation": "Conditional PPE-only sensitivity on one previously exposed English training pair under a separately declared isotropic receiving-disk local model and unchanged historical regional model. No original historical reproduction, physical basin/core admission, measured vegetation or held-out accuracy, confidence coverage, source-use permission or qualified external review.",
        }
    )
    return report, diagnostics


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> None:
    """Read qualified external sources; atomically publish only derived summaries."""
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    descriptor = json.loads(qualified.inputs[source_descriptor.as_posix()].read_bytes())
    if (
        descriptor.get("schema_version") != "qualified-author-snapshot.v1"
        or descriptor.get("source_id") != english.SOURCE_ID
        or len(qualified.inputs) != 195
        or english._sha(qualified.directory / "snapshot-manifest.json")
        != english.MANIFEST_SHA256
    ):
        raise ValueError("English receiver qualified author snapshot differs")
    prepare_path = _safe_file(
        repository, english.PREPARE, "English maintained source preparation"
    )
    if english._sha(prepare_path) != english.PREPARE_SHA256:
        raise ValueError("English receiver maintained source preparation changed")
    stage = Path(tempfile.mkdtemp(prefix=".english-receiver-", dir=output.parent))
    published = False
    try:
        preparation = stage / "private-preparation"
        script = runpy.run_path(
            str(prepare_path), run_name="bijux_english_receiver_prepare"
        )
        summary = script["prepare"](qualified.directory, preparation)
        if (
            summary["original_cohort_counts"] != 20732
            or summary["excluded_cohort_counts"] != 159
            or summary["prepared"][1]["regional_removed_counts"] != 42
            or summary["prepared"][1]["local_removed_counts"] != 10
        ):
            raise ValueError(
                "English receiver original/excluded count populations changed"
            )
        input_root, request, evidence = english._prepared_request(preparation, summary)
        payload = english._training_payload(request, input_root)
        means, sd, covariance = english._source_moments(qualified.directory, payload)
        regional_k, _, fractions = english._kernels(payload)
        kernel, capture_sha256 = _captured_kernel(repository, payload)
        result = fit_shared_ppe_likelihood(
            payload["regional"]["samples"][0]["counts"],
            payload["local"]["samples"][0]["counts"],
            means,
            sd,
            covariance,
            regional_k,
            kernel,
            fractions,
            draws=english.DRAWS,
            seed=english.SEED,
            gap_tolerance=english.GAP_TOLERANCE,
            max_steps=english.MAX_STEPS,
            max_condition_number=english.MAX_CONDITION_NUMBER,
        )
        if (
            not np.array_equal(result.ppe_draws[0], means)
            or any(
                not fit.converged or fit.optimality_gap > english.GAP_TOLERANCE
                for fit in result.fits
            )
            or not np.isfinite(result.local_cover).all()
            or np.any(result.forward_max_abs > 1e-12)
        ):
            raise ValueError(
                "English receiver conditional numerical acceptance refused"
            )
        expected = np.array(
            [NOMINAL_COVER.get(taxon, 0.0) for taxon in payload["taxa"]]
        )
        if (
            not np.allclose(result.local_cover[0], expected, rtol=0, atol=1e-12)
            or abs(result.fits[0].mean_negative_log_likelihood - NOMINAL_OBJECTIVE)
            > 1e-12
        ):
            raise ValueError("English receiver admitted nominal anchor differs")
        covariance_sha256 = english._sha(
            qualified.directory / "author/run.REVEALS.files/avar-RPP.all.landclimII.csv"
        )
        report, diagnostics = _products(
            payload, result, covariance_sha256, evidence, capture_sha256
        )
        products = stage / "source-products"
        products.mkdir()
        for name, value in (("report.json", report), ("diagnostics.json", diagnostics)):
            (products / name).write_text(
                json.dumps(value, indent=2, allow_nan=False) + "\n"
            )
        english._require_unchanged_before_publication(
            repository,
            source_root,
            source_descriptor,
            qualified,
            prepare_path,
            input_root,
            evidence,
            output,
        )
        _, after_capture = _captured_kernel(repository, payload)
        if after_capture != capture_sha256:
            raise ValueError("English receiver capture changed before publication")
        os.replace(products, output)
        published = True
    finally:
        if published:
            shutil.rmtree(stage)


def main(argv: list[str] | None = None) -> int:
    """Parse the source-bound receiver-annulus publication command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", default=english.DESCRIPTOR, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
