"""Publish a compact conditional English shared-PPE training account."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import tempfile
from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics.analysis.lra.engine.discovery import (
    load_engine,
    required_capability_for_profile,
)
from bijux_pollenomics.analysis.lra.execution.adapter import _configuration
from bijux_pollenomics.analysis.lra.execution.service import validate_lra_inputs
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import (
    safe_source_file as _safe_file,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_lra.api import fit_shared_ppe_likelihood
from bijux_pollenomics_lra.dispersal.kernels import DispersalFactorK
from bijux_pollenomics_lra.reconstruction.optimized import calK
from bijux_pollenomics_lra.workflows.local import _prepare_love_params

DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
PREPARE = (
    "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/prepare.py"
)
PREPARE_SHA256 = "da95cfa034480cab61b18028239cf1a2b8da753a07b97d8824df4f356ca64e06"
SOURCE_ID = "landclim/author-reference"
MANIFEST_SHA256 = "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
SOURCE_REPORT_SHA256 = (
    "680cb486f39dc91d45c07eaa1e0be53d6db859c9b04888893ed134675d9c56f5"
)
REQUEST_SHA256 = "bf99b6d8add47095749b1770a0e62a575c1f90217af2c477f36525ddd0a5d69c"
EVIDENCE_NAMES = frozenset(
    {
        "chronology.json",
        "taxa.json",
        "parameters.json",
        "dependency-lock.json",
        "decision.json",
        "LARKBARR-raw.json",
        "LARKBARR-geometry.json",
        "BECKHAM-raw.json",
        "BECKHAM-geometry.json",
    }
)
SEED = 20261002
DRAWS = 64
GAP_TOLERANCE = 1e-7
MAX_STEPS = 10_000
MAX_CONDITION_NUMBER = 1e12
NOMINAL_COVER = {
    "Betula": 0.0002397291308666335,
    "Calluna.vulgaris": 0.02162160847996488,
    "Fagus.sylvatica": 0.000813372859609062,
    "Fraxinus": 0.00029528294733806895,
    "Plantago.lanceolata.type": 0.0025590139964023918,
    "Poaceae": 0.9744709925858192,
}
NOMINAL_NEGATIVE_LOG_LIKELIHOOD = 1.014024172453369


def _sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _real_file(root: Path, relative: str) -> Path:
    item = Path(relative)
    if (
        item.is_absolute()
        or not item.parts
        or any(part in {".", ".."} for part in item.parts)
    ):
        raise ValueError("Prepared English evidence path is not relative and canonical")
    path = root / item
    if path.resolve(strict=True) != path or not path.is_file():
        raise ValueError(f"Prepared English evidence is not a real file: {relative}")
    return path


def _rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.reader(stream))


def _source_moments(
    directory: Path, payload: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    means_rows = _rows(directory / "author/run.REVEALS.files/av-RPP.all.landclimII.csv")
    covariance_rows = _rows(
        directory / "author/run.REVEALS.files/avar-RPP.all.landclimII.csv"
    )
    crosswalk_rows = _rows(directory / "reference/taxon-name-crosswalk.csv")
    source_taxa = [row[0] for row in means_rows[1:]]
    if (
        len(source_taxa) != 31
        or len(set(source_taxa)) != 31
        or source_taxa != covariance_rows[0][1:]
        or source_taxa != [row[0] for row in covariance_rows[1:]]
        or source_taxa[15] != "Filipendula"
        or crosswalk_rows[0] != ["source", "prepared"]
    ):
        raise ValueError("English author PPE source axis differs")
    crosswalk = dict(crosswalk_rows[1:])
    keep = [index for index in range(31) if index != 15]
    if (
        len(crosswalk) != 31
        or [crosswalk.get(source_taxa[index]) for index in keep] != payload["taxa"]
        or payload["taxa"] != [row["taxon"] for row in payload["parameters"]]
    ):
        raise ValueError("English source-to-request taxon mapping differs")
    try:
        means = np.array([float(row[1]) for row in means_rows[1:]], dtype=float)[keep]
        covariance = np.array(
            [[float(value) for value in row[1:]] for row in covariance_rows[1:]],
            dtype=float,
        )
        prepared = np.array([row["ppe"] for row in payload["parameters"]], dtype=float)
        sd = np.array([row["ppe_sd"] for row in payload["parameters"]], dtype=float)
    except (IndexError, TypeError, ValueError) as exc:
        raise ValueError("English PPE source moments are invalid") from exc
    selected = (
        covariance[np.ix_(keep, keep)] if covariance.shape == (31, 31) else covariance
    )
    if (
        covariance.shape != (31, 31)
        or not np.isfinite(covariance).all()
        or not np.array_equal(covariance, covariance.T)
        or not np.array_equal(means, prepared)
        or not np.isfinite(sd).all()
        or np.any(sd < 0)
        or not np.allclose(np.diag(selected), sd * sd, rtol=1e-12, atol=0)
        or np.count_nonzero(selected - np.diag(np.diag(selected))) != 0
    ):
        raise ValueError("English source PPE covariance or request moments differ")
    return prepared, sd, selected


def _prepared_request(
    preparation: Path, summary: dict[str, Any]
) -> tuple[Path, dict[str, Any], dict[str, str]]:
    prepared = summary.get("prepared")
    if (
        summary.get("source_manifest_sha256") != MANIFEST_SHA256
        or not isinstance(prepared, list)
        or [row.get("label") for row in prepared] != ["initial", "extended"]
        or prepared[1].get("request_sha256") != REQUEST_SHA256
    ):
        raise ValueError("Prepared English source/request derivation differs")
    source_report = _real_file(preparation / "source-inputs", "source-report.json")
    if _sha(source_report) != SOURCE_REPORT_SHA256:
        raise ValueError("English source report identity differs")
    input_root = preparation / "extended/inputs"
    request_path = _real_file(input_root, "request.json")
    if _sha(request_path) != REQUEST_SHA256:
        raise ValueError("Exact English training request differs")
    request = json.loads(request_path.read_bytes())
    evidence = request["evidence"]
    if (
        not isinstance(evidence, list)
        or len(evidence) != 9
        or frozenset(entry["path"] for entry in evidence) != EVIDENCE_NAMES
    ):
        raise ValueError("English request evidence population differs")
    evidence_hashes: dict[str, str] = {}
    for entry in evidence:
        name, expected = entry["path"], entry["sha256"]
        if _sha(_real_file(input_root, name)) != expected:
            raise ValueError(f"English prepared evidence differs: {name}")
        evidence_hashes[name] = expected
    return input_root, request, evidence_hashes


def _training_payload(request: dict[str, Any], input_root: Path) -> dict[str, Any]:
    payload = validate_lra_inputs(request, input_root=input_root).payload()
    regional = payload["regional"]["samples"][0]
    local = payload["local"]["samples"][0]
    rings = payload["rings"]
    config = payload["configuration"]
    if (
        payload["operation"] != "lra"
        or payload["method_profile"] != "ring-taxon-preserving"
        or len(payload["taxa"]) != 30
        or regional["site_id"] != "BECKHAM"
        or local["site_id"] != "LARKBARR"
        or sum(regional["counts"]) != 699
        or sum(local["counts"]) != 553
        or payload["regional"]["basin"]
        != {
            "diameter_m": 300.0,
            "geometry_evidence_id": "geometry:author:BECKHAM",
            "site_type": "lake",
        }
        or payload["local"]["basin"]
        != {
            "diameter_m": 160.0,
            "geometry_evidence_id": "geometry:author:LARKBARR",
            "site_type": "lake",
        }
        or [(row["inner_m"], row["outer_m"]) for row in rings]
        != [(81, 500), (500, 1000), (1000, 10000)]
        or any(row["ring_area_m2"] != row["terrestrial_area_m2"] for row in rings)
        or config["seed"] != 7
        or config["love"]["max_ring"] != 2
        or config["love"]["repeats"] != 1
        or config["love"]["stochastic"]
        or config["reveals"]["stochastic"]
        or config["love"]["distance_weighting"] != "gpm neutral"
        or config["reveals"]["distance_weighting"] != "gpm neutral"
    ):
        raise ValueError("English exposed training pair or geometry differs")
    return payload


def _kernels(payload: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    binding = load_engine(
        required_capability=required_capability_for_profile(payload["method_profile"])
    )
    reveals, love, paired = _configuration(binding, payload)
    if (
        reveals is None
        or love is None
        or paired is None
        or reveals.stochastic
        or love.stochastic
        or love.max_ring != 2
        or reveals.basin_type != "lake"
        or reveals.basin_diameter_m != 300
        or reveals.region_cutoff_m != 100_000
        or reveals.distance_weighting != "gpm neutral"
    ):
        raise ValueError("English source-compatible kernel configuration differs")
    parameters = pd.DataFrame(
        [
            {
                "species": row["taxon"],
                "fallspeed": row["fallspeed_m_s"],
                "ppe": row["ppe"],
                "ppe.error": row["ppe_sd"],
            }
            for row in payload["parameters"]
        ]
    )
    local_parameters = _prepare_love_params(parameters, payload["taxa"], love)
    rings = pd.DataFrame(
        [
            {
                "inner": row["inner_m"],
                "outer": row["outer_m"],
                "mean": row["mean_m"],
                "ring": row["ring_area_m2"],
                "terrestrial": row["terrestrial_area_m2"],
            }
            for row in payload["rings"]
        ]
    )
    local_k = calK(rings, local_parameters).to_numpy(dtype=float)
    fractions = rings["terrestrial"].to_numpy(dtype=float) / rings["ring"].to_numpy(
        dtype=float
    )
    regional_k = np.array(
        [
            DispersalFactorK(
                row["fallspeed_m_s"],
                reveals.basin_type,
                reveals.basin_diameter_m,
                reveals.distance_weighting,
                reveals.region_cutoff_m,
            )
            for row in payload["parameters"]
        ],
        dtype=float,
    )
    if (
        local_k.shape != (3, 30)
        or regional_k.shape != (30,)
        or not np.isfinite(local_k).all()
        or not np.isfinite(regional_k).all()
        or np.any(local_k < 0)
        or np.any(regional_k <= 0)
        or not np.array_equal(fractions, np.ones(3))
        or not np.array_equal(local_k[1], np.zeros(30))
    ):
        raise ValueError("English source-compatible zero middle ring differs")
    return regional_k, local_k, fractions


def _compact_products(
    payload: dict[str, Any],
    result: Any,
    covariance_sha256: str,
    evidence_hashes: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    taxa = payload["taxa"]
    stochastic = result.local_cover[1:]
    if stochastic.shape != (63, 30) or len(result.fits) != DRAWS:
        raise ValueError("English conditional draw population differs")
    diagnostics = [
        {
            "draw": index,
            "converged": fit.converged,
            "optimality_gap": fit.optimality_gap,
            "mean_negative_log_likelihood": fit.mean_negative_log_likelihood,
            "steps": fit.steps,
            "stop_reason": fit.stop_reason,
            "vertex_condition_number": fit.vertex_condition_number,
            "forward_max_abs": float(result.forward_max_abs[index]),
        }
        for index, fit in enumerate(result.fits)
    ]
    summaries = {
        "nominal_cover": result.local_cover[0],
        "stochastic_cover_mean": stochastic.mean(axis=0),
        "stochastic_cover_sd": stochastic.std(axis=0, ddof=1),
        "stochastic_cover_q05": np.quantile(stochastic, 0.05, axis=0),
        "stochastic_cover_q95": np.quantile(stochastic, 0.95, axis=0),
    }
    report = {
        "schema_version": "english-shared-ppe-likelihood-sensitivity.v1",
        "source_id": SOURCE_ID,
        "source_manifest_sha256": MANIFEST_SHA256,
        "source_covariance_sha256": covariance_sha256,
        "prepared_request_sha256": REQUEST_SHA256,
        "prepared_evidence_sha256": dict(sorted(evidence_hashes.items())),
        "taxa": taxa,
        "fixed_counts": {"regional": 699, "local": 553},
        "seed": SEED,
        "draws": DRAWS,
        "stochastic_draws": DRAWS - 1,
        "ppe_covariance": "source-declared diagonal, source-normal whole-vector rejection",
        "same_ppe_regional_and_local": True,
        "zero_second_local_ring": True,
        "fit_profile": result.fits[0].profile,
        "gap_tolerance": GAP_TOLERANCE,
        "max_steps": MAX_STEPS,
        "max_condition_number": MAX_CONDITION_NUMBER,
        "maximum_observed_gap": max(row["optimality_gap"] for row in diagnostics),
        "maximum_forward_abs": max(row["forward_max_abs"] for row in diagnostics),
        "conditional_only": True,
        "interpretation": "Conditional sensitivity for one exposed English training pair; no historical vegetation, held-out accuracy, field covariance, source-rights or ecological admission.",
        "cover_by_taxon": [
            {
                "taxon": taxon,
                **{name: float(values[index]) for name, values in summaries.items()},
            }
            for index, taxon in enumerate(taxa)
        ],
    }
    return report, diagnostics


def _require_unchanged_before_publication(
    repository: Path,
    source_root: Path,
    source_descriptor: Path,
    qualified: QualifiedReportSources,
    prepare_path: Path,
    input_root: Path,
    evidence_hashes: dict[str, str],
    output: Path,
) -> None:
    after = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        after.inputs != qualified.inputs
        or after.descriptor_sha256 != qualified.descriptor_sha256
        or _sha(prepare_path) != PREPARE_SHA256
        or _sha(_real_file(input_root, "request.json")) != REQUEST_SHA256
        or any(
            _sha(_real_file(input_root, name)) != digest
            for name, digest in evidence_hashes.items()
        )
    ):
        raise ValueError("English source/request changed before publication")
    require_absent_artifact_output(repository, output)


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> None:
    """Rebuild the private request transiently and publish only derived metrics."""
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    descriptor = json.loads(qualified.inputs[source_descriptor.as_posix()].read_bytes())
    if (
        descriptor.get("schema_version") != "qualified-author-snapshot.v1"
        or descriptor.get("source_id") != SOURCE_ID
        or len(qualified.inputs) != 195
        or _sha(qualified.directory / "snapshot-manifest.json") != MANIFEST_SHA256
    ):
        raise ValueError("English qualified author snapshot differs")
    prepare_path = _safe_file(repository, PREPARE, "English source preparation")
    if _sha(prepare_path) != PREPARE_SHA256:
        raise ValueError("English maintained request preparation changed")
    stage = Path(tempfile.mkdtemp(prefix=".english-shared-ppe-", dir=output.parent))
    try:
        preparation = stage / "private-preparation"
        script = runpy.run_path(
            str(prepare_path), run_name="bijux_english_shared_ppe_prepare"
        )
        summary = script["prepare"](qualified.directory, preparation)
        input_root, request, evidence_hashes = _prepared_request(preparation, summary)
        payload = _training_payload(request, input_root)
        means, sd, covariance = _source_moments(qualified.directory, payload)
        regional_k, local_k, fractions = _kernels(payload)
        result = fit_shared_ppe_likelihood(
            payload["regional"]["samples"][0]["counts"],
            payload["local"]["samples"][0]["counts"],
            means,
            sd,
            covariance,
            regional_k,
            local_k,
            fractions,
            draws=DRAWS,
            seed=SEED,
            gap_tolerance=GAP_TOLERANCE,
            max_steps=MAX_STEPS,
            max_condition_number=MAX_CONDITION_NUMBER,
        )
        if (
            not np.array_equal(result.ppe_draws[0], means)
            or not np.isfinite(result.local_cover).all()
            or any(
                not fit.converged or fit.optimality_gap > GAP_TOLERANCE
                for fit in result.fits
            )
        ):
            raise ValueError("English conditional fit or nominal anchor differs")
        expected_nominal = np.array(
            [NOMINAL_COVER.get(taxon, 0.0) for taxon in payload["taxa"]]
        )
        if (
            len(NOMINAL_COVER) != 6
            or not set(NOMINAL_COVER).issubset(payload["taxa"])
            or not np.allclose(
                result.local_cover[0], expected_nominal, rtol=0, atol=1e-12
            )
            or abs(
                result.fits[0].mean_negative_log_likelihood
                - NOMINAL_NEGATIVE_LOG_LIKELIHOOD
            )
            > 1e-12
        ):
            raise ValueError("English retained nominal likelihood anchor differs")
        covariance_sha256 = _sha(
            qualified.directory / "author/run.REVEALS.files/avar-RPP.all.landclimII.csv"
        )
        report, diagnostics = _compact_products(
            payload, result, covariance_sha256, evidence_hashes
        )
        products = stage / "source-products"
        products.mkdir()
        (products / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        (products / "diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2) + "\n"
        )
        _require_unchanged_before_publication(
            repository,
            source_root,
            source_descriptor,
            qualified,
            prepare_path,
            input_root,
            evidence_hashes,
            output,
        )
        os.replace(products, output)
    finally:
        shutil.rmtree(stage)


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and publish a compact conditional English shared-PPE training account."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", default=DESCRIPTOR, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
