"""Count-only joint regions on the original BOKE three/BUS two measured panels."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)
from bijux_pollenomics_lra.models import validation
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.likelihood import multisite_likelihood
from bijux_pollenomics_lra.reconstruction.uncertainty import (
    measured_panel_counting as engine,
)
from bijux_pollenomics_lra.reconstruction.uncertainty import (
    multisite_counting,
    regional_counting,
    two_taxon_counting,
)

from ..physical_forward import inputs
from ..physical_forward.inputs import require
from . import cohort

AXIS = ["Betula", "Fraxinus", "Ulmus"]
LIMITS = [
    "New per-declared-window joint 95% relative-cover region conditional on one common three-taxon cover, fixed positive original site responses, a BOKE three-taxon multinomial and a BUS Betula/Ulmus binomial. BUS Fraxinus is unmeasured, not zero or predicted.",
    "The original full-panel sample eligibility, calibrated point-age windows, source exclusions and full measured-panel efforts are fixed. No successful point fit or positive BOKE Betula/Ulmus subtotal is required. A random zero subtotal gives an uninformative conditional Betula/Ulmus constraint rather than dropping that window.",
    "Three separately budgeted certified binomial intervals give the stated Bonferroni bound without independence between sites or the BOKE conditional and Fraxinus constraints. Coverage of the conditional Betula/Ulmus interval holds for each random subtotal and hence by averaging. Pooled native samples are not established homogeneous independent trials; no sampling calibration or common field cover is validated.",
    "The joint region is the exact transformed/intersected constraint set, not the Cartesian product of its coordinate envelopes. Exact rational closure corners and endpoint-attainment flags distinguish attained bounds from limiting infima/suprema. The Fraxinus-only vertex is excluded because the BUS conditional pollen distribution is undefined there.",
    "These are thirteen separate conditional regions, not a simultaneous study-wide band, posterior, predictive interval or untouched confirmation. The same cores and previous compatibility outcomes were exposed during development. No MLE-containment or model-selection guarantee is imposed.",
    "PPE, saved non-rigorous receiver-annulus quadrature, geometry, chronology, measurement error, within-window heterogeneity and between-site/model uncertainty remain fixed or omitted. Source rights and original basin/chronology limitations persist; this calculation authorizes no raw redistribution and makes no historical-reproduction or vegetation-accuracy claim.",
    "Six unmatched BUS windows retain their native counts and support but receive no two-site joint region. Refused and empty results remain explicit; no pseudocount, taxon imputation, refit or new kernel calculation is used.",
]


def _domain(condition: object, message: str) -> None:
    if not condition:
        raise ValidationError(message, reason_code="measured_panel_source_domain")


def evaluate(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate every admitted count window without consulting any fitted outcome."""
    responses = loaded["full_panel_responses"]
    require(
        [r["core"] for r in responses] == list(cohort.CORES)
        and [r["taxa"] for r in responses] == [AXIS, list(cohort.TAXA)],
        "Original complete/partial response axes differ",
    )
    rows = []
    fatal = False
    for group in loaded["groups"]:
        row: dict[str, Any] = {
            "window_cal_bp": group["window_cal_bp"],
            "sites": group["sites"],
            "status": "not_run" if fatal else "computed",
            "counting_region": None,
        }
        if not fatal:
            try:
                _domain(len(group["sites"]) == 2, "Exactly two measured sites required")
                boke, bus = group["sites"]
                _domain(
                    [s["core"] for s in (boke, bus)] == list(cohort.CORES)
                    and boke["original_axis"] == AXIS
                    and bus["original_axis"] == list(cohort.TAXA)
                    and boke["taxon_measured_on_common_axis"] == [True, True, True]
                    and bus["taxon_measured_on_common_axis"] == [True, False, True]
                    and all(
                        type(v) is bool
                        for s in (boke, bus)
                        for v in s["taxon_measured_on_common_axis"]
                    )
                    and bus["Fraxinus_original_panel_count"] is None,
                    "Original measured-panel identities or missingness differ",
                )
                region = engine.measured_panel_counting_region(
                    boke["original_counts"],
                    bus["original_counts"],
                    responses[0]["response_PPE_times_K"],
                    responses[1]["response_PPE_times_K"],
                    complete_taxon_measured=boke["original_taxon_measured"],
                    partial_taxon_measured=bus["original_taxon_measured"],
                    confidence_level=0.95,
                )
                _domain(
                    sum(region.complete_counts) == boke["original_panel_N"]
                    and sum(region.partial_counts) == bus["original_panel_N"],
                    "Fixed full-panel efforts differ from admitted counts",
                )
                row["counting_region"] = asdict(region)
            except ValidationError as error:
                row.update(
                    status="refused", reason=error.reason_code, detail=str(error)
                )
            except Exception as error:
                fatal = True
                row.update(
                    status="fatal", reason=type(error).__name__, detail=str(error)
                )
        rows.append(row)
    return rows


def _revision(repository: Path) -> str:
    """Bind consumed maintained code to one canonical Git revision."""
    dev = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev"
    lra = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra"
    modules = [
        (
            sys.modules[__name__],
            f"{dev}/essd_reproduction/common_cover/measured_panel_counting.py",
        ),
        (cohort, f"{dev}/essd_reproduction/common_cover/cohort.py"),
        (inputs, f"{dev}/essd_reproduction/physical_forward/inputs.py"),
        (
            sources,
            f"{dev}/source_completion/pollen_reconstruction/swedish_static_basin/sources.py",
        ),
        (validation, f"{lra}/models/validation.py"),
        (
            multisite_likelihood,
            f"{lra}/reconstruction/likelihood/multisite_likelihood.py",
        ),
        (engine, f"{lra}/reconstruction/uncertainty/measured_panel_counting.py"),
        (multisite_counting, f"{lra}/reconstruction/uncertainty/multisite_counting.py"),
        (regional_counting, f"{lra}/reconstruction/uncertainty/regional_counting.py"),
        (two_taxon_counting, f"{lra}/reconstruction/uncertainty/two_taxon_counting.py"),
    ]
    for module, relative in modules:
        path = Path(module.__file__ or "")
        require(
            path.resolve(strict=True) == path == repository / relative,
            "Consumed module is outside canonical source",
        )
    paths = [relative for _, relative in modules]

    def git(*args: str) -> bytes:
        return subprocess.check_output(
            ["git", "-C", str(repository), *args], timeout=30
        )

    revision = git("rev-parse", "HEAD").decode().strip()
    git("ls-files", "--error-unmatch", "--", *paths)
    git("diff", "--exit-code", revision, "--", *paths)
    return revision


def main() -> None:
    """Validate canonical sources and write the declared measured-panel account."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.absolute()
    require(
        repository.resolve(strict=True) == repository,
        "Physical canonical repository required",
    )
    output = require_absent_artifact_output(repository, args.output)
    revision = _revision(repository)
    loaded = cohort.load_count_groups(repository)
    rows = evaluate(loaded)
    for pin in loaded["scientific_inputs"]:
        path = Path(pin["path"])
        relative = (
            str(path.relative_to(repository)) if path.is_absolute() else str(path)
        )
        sources.read_bound(repository, relative, pin)
    require(
        _revision(repository) == revision, "Consumed source changed during calculation"
    )
    result = {
        "schema_version": "boke-bus-measured-panel-joint-counting-regions.v1",
        "source_commit": revision,
        "command": sys.orig_argv,
        "profile": engine.PROFILE,
        "taxa": AXIS,
        "age_unit": "calibrated years BP, AD1950 reference",
        "confidence_level_per_window": 0.95,
        "simultaneous_across_windows_claimed": False,
        "point_fit_selection_applied": False,
        "positive_projected_effort_selection_applied": False,
        **{
            key: loaded[key]
            for key in (
                "cores",
                "full_panel_responses",
                "unmatched",
                "scientific_inputs",
                "original_source_epochs",
            )
        },
        "groups": rows,
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "region_status_counts": dict(
            Counter(
                r["counting_region"]["status"]
                for r in rows
                if r["status"] == "computed"
            )
        ),
        "new_point_fits": 0,
        "new_kernel_evaluations": 0,
        "common_field_cover_admitted": False,
        "sampling_calibration_established": False,
        "raw_redistribution_authorized": False,
        "development_exposed": True,
        "limits": LIMITS,
    }
    raw = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= 1024**2, "Essential output exceeds one MiB")
    with output.open("xb") as stream:
        stream.write(raw)
    raise SystemExit(1 if any(r["status"] in {"fatal", "not_run"} for r in rows) else 0)


if __name__ == "__main__":
    main()
