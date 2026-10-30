"""Publish a committed spatial field hypothesis, then its matched diagnostics."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import inspect
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from bijux_pollenomics.analysis.lra_validation.metrics import hellinger_distance
from bijux_pollenomics.collection.intake.workbooks import read_xlsx_sheet_rows
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_lra.dispersal.kernels import gpm_values
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus
from bijux_pollenomics_lra.dispersal.two_anchor_bounds import (
    two_anchor_annulus_step_bounds,
)
from bijux_pollenomics_lra.dispersal.two_anchor_receiver import (
    two_anchor_circular_receiver_annulus,
)
from bijux_pollenomics_lra.reconstruction.fixed_site_covariance import (
    fixed_site_cover_covariance,
)
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition

from ..swedish_static_basin.reconstruction import parameter_vectors
from ..swedish_static_basin.sources import (
    explicit_panel,
    pollen_counts,
    read_bound,
    selected_age,
)
from . import geometry, inputs, prediction, scoring, sources


def source_revision(repository: Path) -> str:
    """Require committed consumed source and identify its existing Git revision."""
    owned = list(Path(__file__).parent.glob("*.py"))
    functions: list[Callable[..., Any]] = [
        gpm_values,
        circular_receiver_annulus,
        two_anchor_annulus_step_bounds,
        two_anchor_circular_receiver_annulus,
        fixed_site_cover_covariance,
        forward_deposition,
        hellinger_distance,
        parameter_vectors,
        read_bound,
        pollen_counts,
        selected_age,
        explicit_panel,
        read_xlsx_sheet_rows,
    ]
    owned.extend(Path(inspect.getfile(f)) for f in functions)
    owned.append(repository / sources.PROTOCOL)
    relative = sorted({str(p.resolve().relative_to(repository)) for p in owned})
    command = ["git", "-C", str(repository)]
    revision = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True
    ).strip()
    subprocess.run(
        [*command, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*command, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
    )
    return revision


def publish(repository: Path, source_root: Path, output: Path) -> dict[str, Any]:
    """Close all predictions before calling the separate observed-data scorer."""
    started = time.monotonic()
    repository = repository.resolve()
    destination = require_absent_artifact_output(repository, output)
    revision = source_revision(repository)
    prepared = inputs.prepare_inputs(sources.load_sources(repository, source_root))
    geometry_started = time.monotonic()
    geometries = geometry.geometry_inputs(prepared["protocol"], prepared["fall"])
    geometry_elapsed = time.monotonic() - geometry_started
    geometry_budget = prepared["protocol"]["geometry_qualification"]
    sources.require(
        geometry_elapsed <= geometry_budget["wall_seconds"]
        and len(json.dumps(geometries, allow_nan=False).encode())
        <= geometry_budget["output_bytes"],
        "Count-free geometry runtime/output budget exceeded",
    )
    homogeneous = {
        g["core"]: [t["factor"] for t in g["homogeneous_taxa"]]
        for g in geometries
        if all(t["status"] == "qualified" for t in g["homogeneous_taxa"])
    }
    contexts = []
    for g in geometries:
        for window in prepared["windows"]:
            target, anchors = inputs.predictor_inputs(prepared, g["core"], window)
            contexts.append(
                prediction.predict(target, anchors, g, homogeneous, prepared["ppe"])
            )
    packet = {
        "schema_version": "spatial-field-forward-predictions.v1",
        "source_commit": revision,
        "input_sha256": prepared["input_sha256"],
        "axis": list(sources.AXIS),
        "ppe": prepared["ppe"],
        "fall": prepared["fall"],
        "geometry": geometries,
        "geometry_elapsed_seconds": geometry_elapsed,
        "contexts": contexts,
    }
    destination.mkdir(parents=True)
    prediction_path = destination / "prediction-freeze.json"
    prediction_path.write_text(json.dumps(packet, indent=2, allow_nan=False) + "\n")
    observations = list(prepared["cells"].values())
    scored = scoring.score_frozen(prediction_path, observations)
    result = {
        "schema_version": "spatial-field-forward-result.v1",
        "status": "conditional_development_spatial_forward_comparison",
        "source_commit": revision,
        "input_sha256": prepared["input_sha256"],
        "sample_accounts": prepared["sample_accounts"],
        "sample_status_counts": dict(
            Counter(r["status"] for r in prepared["sample_accounts"])
        ),
        "observations": observations,
        "source_attribution": prepared["attribution"],
        "current_policy_urls": prepared["policy_urls"],
        **scored,
        "requested_contexts": 18,
        "requested_family_outcomes": 54,
        "geometry_elapsed_seconds": geometry_elapsed,
        "model_fits": 0,
        "target_score_parameter_selection": False,
        "untouched_validation_or_vegetation_accuracy_claim": False,
        "historical_core_admission_changed": False,
    }
    sources.bound_inputs(repository, source_root, prepared["protocol"])
    sources.require(
        source_revision(repository) == revision,
        "Consumed scientific source changed during execution",
    )
    result["elapsed_seconds"] = time.monotonic() - started
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    budget = prepared["protocol"]["resource_budget"]
    sources.require(
        result["elapsed_seconds"] <= budget["wall_seconds"]
        and len(body.encode()) + prediction_path.stat().st_size
        <= budget["output_bytes"],
        "Execution/output budget exceeded",
    )
    (destination / "result.json").write_text(body)
    return result
