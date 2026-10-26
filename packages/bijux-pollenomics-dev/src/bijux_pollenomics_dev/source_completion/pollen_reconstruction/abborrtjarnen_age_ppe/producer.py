"""Integrate shared age membership with the existing conditional physical moments."""

from __future__ import annotations

from collections import Counter
import csv
import gzip
import hashlib
import inspect
import io
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import numpy as np

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_lra.api import fixed_site_cover_covariance

from ..abborrtjarnen_ppe_dependence.calculation import ppe_jacobian
from ..abborrtjarnen_ppe_dependence.inputs import native_counts, source_age
from ..abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    TAXON_IDS,
    WINDOWS,
    bound_files,
    load_sources,
    require,
)
from . import chronology, inputs, moments


def source_revision(repository: Path) -> str:
    """Identify committed consumed mathematics and source adapters."""
    files = [
        *Path(__file__).parent.glob("*.py"),
        repository / chronology.PROTOCOL,
        repository
        / "reports/science/pollen-reconstruction/abborrtjarnen-ppe-dependence/protocol.json",
    ]
    files.extend(
        Path(inspect.getfile(f))
        for f in (
            fixed_site_cover_covariance,
            ppe_jacobian,
            native_counts,
            source_age,
            load_sources,
        )
    )
    relative = sorted({str(p.resolve().relative_to(repository)) for p in files})
    git = ["git", "-C", str(repository)]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(
        [*git, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*git, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
    )
    return revision


def fixed_age_check(case: dict[str, Any], get_moment: Any) -> dict[str, Any]:
    """Require the frozen source-point case to reproduce the prior physical moments."""
    ages = [s["source_point_age_bp"] for s in case["samples"]]
    maximum = 0.0
    for bin_id, reference in zip(WINDOWS, case["fixed_age_reference"], strict=True):
        support, counts = inputs.membership(case["samples"], ages, bin_id)
        require(
            support["status"] == "defined" and counts is not None,
            "Original fixed-age source support differs",
        )
        assert counts is not None
        result = get_moment(counts)
        require(
            support["sample_ids"] == reference["sample_ids"]
            and list(counts) == reference["pooled_panel_counts"],
            "Original fixed-age raw member/count identities differ",
        )
        for field, expected in (
            ("cover", "cover"),
            ("count", "counting_covariance"),
            ("gradient", "ppe_gradient"),
        ):
            maximum = max(
                maximum,
                float(np.max(np.abs(result[field] - np.asarray(reference[expected])))),
            )
    require(maximum <= 1e-12, "Frozen-age physical control exceeds tolerance")
    return {"windows_checked": 4, "maximum_absolute_gap": maximum, "passed": True}


def ledger_fields() -> list[str]:
    return [
        "seed",
        "native_row",
        "complete",
        *[
            f"bin_{b}_{name}"
            for b in WINDOWS
            for name in (
                "status",
                "sample_ids",
                "sample_count",
                "reported_panel_subtotal",
                "panel_mass",
                "all_reported_pollen_nisp",
                "omitted_reported_pollen_nisp",
                "missing_members",
            )
        ],
        *[f"cover_{b}_{taxon}" for b in WINDOWS for taxon in TAXON_IDS],
    ]


def publish(repository: Path, source_root: Path, output: Path) -> dict[str, Any]:
    """Preserve all saved rows; publish explicit defined-event mixture moments."""
    started = time.monotonic()
    repository = repository.resolve()
    destination = require_absent_artifact_output(repository, output)
    revision = source_revision(repository)
    case = inputs.prepare(repository, source_root)
    ppe = np.array([p["ppe"] for p in case["parameters"]])
    covariance = np.diag(np.square([p["published_sd"] for p in case["parameters"]]))
    cache: dict[tuple[int, ...], dict[str, np.ndarray]] = {}

    def get_moment(counts: tuple[int, ...]) -> dict[str, np.ndarray]:
        if counts not in cache:
            cache[counts] = moments.window_moments(
                counts, case["deposition"], ppe, covariance
            )
        return cache[counts]

    control = fixed_age_check(case, get_moment)
    total = moments.PopulationMoments(covariance)
    supports: dict[str, Counter[str]] = {str(b): Counter() for b in WINDOWS}
    chains = []
    requested = 0
    destination.mkdir(parents=True)
    ledger = destination / "draw-ledger.csv.gz"
    with (
        gzip.GzipFile(filename=str(ledger), mode="wb", mtime=0) as compressed,
        io.TextIOWrapper(compressed, newline="") as stream,
    ):
        writer = csv.DictWriter(stream, fieldnames=ledger_fields())
        writer.writeheader()
        for entry in case["protocol"]["age_inputs"]:
            chain = moments.PopulationMoments(covariance)
            chain_rows = 0
            for native_row, ages in chronology.age_rows(
                repository, entry, case["sample_ids"]
            ):
                require(
                    native_row == entry["first_native_row"] + chain_rows,
                    "Saved native-row order differs",
                )
                chain_rows += 1
                requested += 1
                row: dict[str, Any] = {"seed": entry["seed"], "native_row": native_row}
                complete = []
                for b in WINDOWS:
                    support, counts = inputs.membership(case["samples"], ages, b)
                    supports[str(b)][support["status"]] += 1
                    for key, value in support.items():
                        row[f"bin_{b}_{key}"] = (
                            json.dumps(value, separators=(",", ":"), sort_keys=True)
                            if key in {"sample_ids", "missing_members"}
                            else value
                        )
                    if counts is not None:
                        moment = get_moment(counts)
                        complete.append(moment)
                        for taxon, value in zip(
                            TAXON_IDS, moment["cover"], strict=True
                        ):
                            row[f"cover_{b}_{taxon}"] = float(value)
                row["complete"] = int(len(complete) == 4)
                if len(complete) == 4:
                    cover, count, gradient = moments.joint_window_moments(complete)
                    total.add(cover, count, gradient)
                    chain.add(cover, count, gradient)
                writer.writerow(row)
            require(
                chain_rows == entry["retained_rows"], "Saved chain multiplicity differs"
            )
            chains.append(
                {
                    "seed": entry["seed"],
                    "requested_draws": chain_rows,
                    "complete_draws": chain.n,
                    "conditional_mean": None if not chain.n else chain.mean.tolist(),
                }
            )
    expected = case["protocol"]["age_authority"]["requested_rows"]
    require(requested == expected, "Requested saved-row population differs")
    undefined = requested - total.n
    result = {
        "schema_version": "abborrtjarnen-age-ppe.v1",
        "status": "conditional_age_count_ppe_delta_mixture",
        "source_commit": revision,
        "input_sha256": case["input_sha256"],
        "age_authority": case["age_authority"],
        "parameters": case["parameters"],
        "physical_response": case["physical_response"],
        "sample_accounts": case["sample_accounts"],
        "component_axis": [
            {"window_id": b, "taxon": name, "native_taxon_id": taxon}
            for b in WINDOWS
            for name, taxon in zip(TAXA, TAXON_IDS, strict=True)
        ],
        "requested_draws": requested,
        "complete_draws": total.n,
        "undefined_draws": undefined,
        "complete_probability": total.n / requested,
        "support_by_window": {
            b: {"status_counts": dict(counts), "probability_denominator": requested}
            for b, counts in supports.items()
        },
        "chain_summaries": chains,
        "unconditional": {
            "status": "refused_undefined_mass"
            if undefined
            else "defined_for_all_saved_rows",
            "undefined_fraction": undefined / requested,
            "mean": None,
            "covariance": None,
            "defined_moments_reference": None
            if undefined
            else "conditional_on_complete",
        },
        "conditional_on_complete": total.result(),
        "fixed_age_control": control,
        "conditional_count_support_cache_entries": len(cache),
        "model_fits": 0,
        "new_ppe_draws": 0,
        "field_calibration_or_coverage_claim": False,
        "historical_core_admission_changed": False,
    }
    chronology.check_inputs(repository, case["protocol"])
    bound_files(source_root, case["source_protocol"]["source_store_files"])
    bound_files(repository, case["source_protocol"]["repository_files"])
    require(
        source_revision(repository) == revision, "Consumed scientific source changed"
    )
    result["draw_ledger"] = {
        "path": ledger.name,
        "bytes": ledger.stat().st_size,
        "sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "rows": requested,
    }
    result["elapsed_seconds"] = time.monotonic() - started
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    budget = case["protocol"]["resource_budget"]
    require(
        result["elapsed_seconds"] <= budget["wall_seconds"]
        and len(body.encode()) + ledger.stat().st_size <= budget["output_bytes"],
        "Declared joint calculation resource/output budget exceeded",
    )
    (destination / "result.json").write_text(body)
    return result
