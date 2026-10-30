"""Execute the committed ABBO conditional profile into one owned result."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import inspect
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.essd_reproduction.pft_covariance.lengths import (
    sum_length_range,
)
from bijux_pollenomics_lra.api import fixed_site_cover_covariance
from bijux_pollenomics_lra.dispersal.kernels import gpm_values
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus

from . import calculation, inputs, sources


def source_revision(repository: Path) -> str:
    """Require committed scientific code and identify every directly used owner."""
    owned = list(Path(__file__).parent.glob("*.py"))
    functions: list[Callable[..., Any]] = [
        fixed_site_cover_covariance,
        circular_receiver_annulus,
        sum_length_range,
        gpm_values,
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
    """Consume original inputs once; report conditional moments and refusals."""
    started = time.monotonic()
    repository = repository.resolve()
    destination = require_absent_artifact_output(repository, output)
    revision = source_revision(repository)
    loaded = sources.load_sources(repository, source_root)
    selected = inputs.panel_inputs(loaded)
    result = {
        "schema_version": "abborrtjarnen-ppe-dependence.v1",
        "status": "conditional_physical_delta_ppe_dependence",
        "source_commit": revision,
        "input_sha256": loaded["input_sha256"],
        "taxon_axis": list(sources.TAXA),
        "parameters": loaded["parameters"],
        "sample_account": selected["sample_account"],
        "sample_status_counts": dict(
            Counter(r["status"] for r in selected["sample_account"])
        ),
        "selected_sample_count": sum(
            r["status"] == "selected_complete_panel" for r in selected["sample_account"]
        ),
        **calculation.calculate(selected),
        "model_fits": 0,
        "chronology_draws_consumed": 0,
        "historical_core_admission_changed": False,
        "whole_vegetation_or_calibrated_coverage_claim": False,
    }
    sources.bound_files(source_root, loaded["protocol"]["source_store_files"])
    sources.bound_files(repository, loaded["protocol"]["repository_files"])
    sources.require(
        revision == source_revision(repository),
        "Scientific source changed during execution",
    )
    elapsed = time.monotonic() - started
    result["elapsed_seconds"] = elapsed
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    budget = loaded["protocol"]["resource_budget"]
    sources.require(
        elapsed <= budget["wall_seconds"]
        and len(body.encode()) <= budget["output_bytes"],
        "Declared execution/output budget exceeded",
    )
    destination.mkdir(parents=True)
    (destination / "result.json").write_text(body)
    return result
