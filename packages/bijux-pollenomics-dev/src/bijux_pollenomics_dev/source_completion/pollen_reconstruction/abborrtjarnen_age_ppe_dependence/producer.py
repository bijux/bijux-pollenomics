"""Study one shared PPE covariance class using qualified immutable saved covers."""

from __future__ import annotations

from collections import Counter
import inspect
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import numpy as np
import scipy

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..abborrtjarnen_ppe_dependence.calculation import ppe_jacobian
from ..abborrtjarnen_ppe_dependence.sources import bound_files, require
from . import covariance_bounds, inputs, quadratic_forms


def source_revision(repository: Path) -> str:
    files = [*Path(__file__).parent.glob("*.py"), repository / inputs.PROTOCOL]
    files.extend(
        Path(inspect.getfile(f))
        for f in (ppe_jacobian, bound_files, require_absent_artifact_output)
    )
    relative = sorted({str(path.resolve().relative_to(repository)) for path in files})
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


def scalar_results(
    forms: np.ndarray, source: dict[str, Any], protocol: dict[str, Any]
) -> list[dict[str, Any]]:
    """Retain all fifty outcomes, signed certificates and unsupported SD displays."""
    identities = quadratic_forms.scalar_axes()
    references = quadratic_forms.reference_scalars(source)
    require(
        forms.shape == (50, 4, 4) and len(references) == len(identities) == 50,
        "Scalar comparison population differs",
    )
    records = []
    for identity, matrix, reference in zip(identities, forms, references, strict=True):
        diagonal = float(np.trace(matrix))
        gap = abs(diagonal - reference["diagonal_ppe_variance"])
        require(
            gap <= protocol["correspondence"]["diagonal_absolute_tolerance"],
            "Saved diagonal PPE baseline differs from the finite Q target",
        )
        record: dict[str, Any] = {
            "scalar_id": identity,
            "Q": matrix.tolist(),
            **reference,
            "diagonal_correspondence_gap": gap,
        }
        try:
            certified = covariance_bounds.bounds(matrix, protocol["search"])
        except ValueError as error:
            records.append(
                {
                    **record,
                    "status": "refused_covariance_form",
                    "reason": str(error),
                    "minimum": None,
                    "maximum": None,
                    "total_variance_outer_interval": None,
                    "standard_deviation_display": {
                        "status": "refused_covariance_form",
                        "lower": None,
                        "upper": None,
                    },
                }
            )
            continue
        record.update(certified)
        record.update(
            covariance_bounds.total_variance(
                certified,
                reference["fixed_age_variance"],
                reference["fixed_count_variance"],
            )
        )
        records.append(record)
    return records


def publish(repository: Path, output: Path) -> dict[str, Any]:
    """Freeze source, authenticate saved inputs and keep all numerical outcomes."""
    started = time.monotonic()
    repository = repository.resolve()
    destination = require_absent_artifact_output(repository, output)
    revision = source_revision(repository)
    case = inputs.load(repository)
    protocol, source = case["protocol"], case["source_result"]
    require(
        protocol["environment"]
        == {"numpy": np.__version__, "scipy": scipy.__version__},
        "Declared NumPy/SciPy environment differs",
    )
    ppe = np.array([p["ppe"] for p in case["parameters"]])
    sd = np.array([p["published_sd"] for p in case["parameters"]])
    destination.mkdir(parents=True)
    forms, requested, complete = quadratic_forms.accumulate(
        inputs.cover_rows(case["ledger_body"], source), ppe, sd
    )
    require(
        requested == 32000 and complete == 31999,
        "Finite Q conditioning population differs",
    )
    records = scalar_results(forms, source, protocol)
    result = {
        "schema_version": "abborrtjarnen-age-ppe-dependence.v1",
        "status": "common_ppe_covariance_sensitivity",
        "source_commit": revision,
        "input_sha256": {
            f"repository/{k}": v["sha256"]
            for k, v in protocol["repository_inputs"].items()
        },
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "native_population": {
            "rows": requested,
            "complete": complete,
            "undefined": requested - complete,
            "samples": 107,
        },
        "conditioning_event": "C_source: all four source-supported windows defined; one of 32,000 rows remains undefined and unconditional moments remain refused.",
        "parameter_axis": [
            {
                "taxon": p["name"],
                "native_taxon_id": p["native_taxon_id"],
                "ppe": p["ppe"],
                "published_sd": p["published_sd"],
            }
            for p in case["parameters"][:4]
        ],
        "fixed_parameter": {
            "taxon": "Poaceae",
            "native_taxon_id": 417,
            "ppe": 1.0,
            "published_sd": 0.0,
            "output_uncertainty_retained": True,
        },
        "scalars": records,
        "summary": {
            "scalar_count": len(records),
            "component_count": 20,
            "contrast_count": 30,
            "status_counts": dict(Counter(r["status"] for r in records)),
            "endpoint_status_counts": dict(
                Counter(
                    r[k]["status"]
                    for r in records
                    for k in ("minimum", "maximum")
                    if r[k] is not None
                )
            ),
            "sd_display_status_counts": dict(
                Counter(r["standard_deviation_display"]["status"] for r in records)
            ),
            "maximum_diagonal_correspondence_gap": max(
                r["diagonal_correspondence_gap"] for r in records
            ),
            "optimizer_attempts": sum(
                len(r[k]["search_attempts"])
                for r in records
                for k in ("minimum", "maximum")
                if r[k] is not None
            ),
        },
        "precision_and_scope": protocol["precision_and_scope"],
        "rights_and_use": protocol["rights_and_use"],
        "model_fits": 0,
        "new_ppe_draws": 0,
        "raw_count_or_age_inputs_read": False,
        "distribution_law_adopted": False,
        "field_calibration_or_coverage_claim": False,
        "one_covariance_attains_all_scalar_extrema": False,
    }
    bound_files(repository, protocol["repository_inputs"])
    require(
        source_revision(repository) == revision,
        "Consumed source changed during common covariance study",
    )
    result["elapsed_seconds"] = time.monotonic() - started
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    require(
        result["elapsed_seconds"] <= protocol["resource_budget"]["wall_seconds"]
        and len(body.encode()) <= protocol["resource_budget"]["output_bytes"],
        "Common covariance study resource/output bound exceeded",
    )
    (destination / "result.json").write_text(body)
    return result
