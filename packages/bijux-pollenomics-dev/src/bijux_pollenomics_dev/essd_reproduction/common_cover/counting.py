"""Conditional count-only sets on the committed BOKE/BUS point-study inputs."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import re
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
    multisite_counting,
    regional_counting,
    two_taxon_counting,
)

from ..physical_forward import inputs
from ..physical_forward.inputs import require
from . import cohort

POINT_REPORT = "reports/science/pollen-reconstruction/common-cover/report.json"
LIMITS = [
    "Per-declared-window 95% confidence sets conditional on a common relative Betula/Ulmus cover, fixed positive site responses and binomial marginal counts at each site. Independence across sites is not required for the Bonferroni bound.",
    "Pooled native samples are not proven homogeneous or independent binomial trials. The calculation does not establish sampling calibration, common field cover, vegetation accuracy or historical applicability.",
    "Thirteen windows repeatedly use the same two cores. These are thirteen separate conditional sets, not a simultaneous 95% band across windows or an uncertainty distribution over independent sites.",
    "PPE, saved receiver-annulus K, geometry, chronology, within-window heterogeneity, between-site variation, measurement error and model uncertainty are omitted. The original point-report source/rights limitations remain.",
    "Use the point report's already-rounded binary64 PPE*K responses, measured panel and original sample eligibility exactly. No optimizer, kernel, new parameter fitting, pseudocount or zero substitution is involved.",
    "Empty intersections are retained as conditional model incompatibilities, not repaired cover estimates or algorithm failures. Nonempty sets do not validate the common-cover model. No MLE-containment condition or midpoint estimate is imposed.",
    "The six unmatched BUS windows remain unpaired and receive no two-site set. Zero-effort site rows, if present, are explicitly uninformative; two empty sites refuse.",
]


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(repository), *arguments], timeout=30
    )


def read_point_report(repository: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Use committed numerical bytes, preserving publication and execution epochs."""
    path = repository / POINT_REPORT
    inputs.physical(path)
    require(
        path.is_file() and 0 < path.stat().st_size <= 1024**2,
        "Bounded point report required",
    )
    raw = path.read_bytes()
    require(
        raw == _git(repository, "show", f"HEAD:{POINT_REPORT}"),
        "Point report differs from committed bytes",
    )
    publication = (
        _git(repository, "log", "-1", "--format=%H", "--", POINT_REPORT)
        .decode()
        .strip()
    )
    report = inputs.decode(raw)
    source = report.get("source_commit")
    require(
        isinstance(source, str)
        and re.fullmatch("[0-9a-f]{40}", source)
        and re.fullmatch("[0-9a-f]{40}", publication),
        "Point report execution/publication commits required",
    )
    assert isinstance(source, str)
    require(
        _git(repository, "cat-file", "-t", source).strip() == b"commit",
        "Point source revision is not a commit",
    )
    _git(repository, "merge-base", "--is-ancestor", source, "HEAD")
    require(
        report.get("schema_version") == "boke-bus-conditional-multisite-likelihood.v1"
        and report.get("taxa") == list(cohort.TAXA)
        and report.get("age_unit") == "calibrated years BP, AD1950 reference"
        and report.get("status_counts") == {"computed": 13}
        and len(report.get("groups", [])) == 13
        and all(r.get("status") == "computed" for r in report["groups"]),
        "Original point-study schema/axis/age/population differs",
    )
    return report, {
        "path": POINT_REPORT,
        "publication_commit": publication,
        "point_source_commit": source,
    }


def authenticate_inputs(repository: Path, report: dict[str, Any]) -> None:
    """Reuse native admission without refitting points or recomputing kernels."""
    admitted = cohort.load_groups(repository)
    require(
        [
            {"window_cal_bp": r["window_cal_bp"], "sites": r["sites"]}
            for r in report["groups"]
        ]
        == admitted["groups"],
        "Committed point count/support windows differ from admitted native inputs",
    )
    for key in ("cores", "unmatched", "scientific_inputs", "original_source_epochs"):
        require(
            report[key] == admitted[key],
            f"Committed point {key} differs from admitted inputs",
        )
    require(len(report["unmatched"]) == 6, "Original six unmatched windows required")


def evaluate(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Calculate from saved counts/responses only, retaining each terminal outcome."""
    responses = [c["response_PPE_times_K"] for c in report["cores"]]
    rows = []
    fatal = False
    for group in report["groups"]:
        row = {
            "window_cal_bp": group["window_cal_bp"],
            "sites": group["sites"],
            "point_status": group["status"],
            "status": "not_run",
            "counting_set": None,
        }
        if not fatal:
            try:
                result = multisite_counting.multisite_two_taxon_counting_set(
                    [s["projected_counts"] for s in group["sites"]],
                    responses,
                    taxon_measured=[s["taxon_measured"] for s in group["sites"]],
                    confidence_level=0.95,
                )
                row.update(status="computed", counting_set=asdict(result))
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
    dev = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev"
    lra = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra"
    modules = [
        (sys.modules[__name__], f"{dev}/essd_reproduction/common_cover/counting.py"),
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
    revision = _git(repository, "rev-parse", "HEAD").decode().strip()
    _git(repository, "ls-files", "--error-unmatch", "--", *paths)
    _git(repository, "diff", "--exit-code", revision, "--", *paths)
    return revision


def main() -> None:
    """Validate canonical inputs and write the declared conditional account."""
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
    report, point_identity = read_point_report(repository)
    authenticate_inputs(repository, report)
    rows = evaluate(report)
    for pin in report["scientific_inputs"]:
        path = Path(pin["path"])
        relative = (
            str(path.relative_to(repository)) if path.is_absolute() else str(path)
        )
        sources.read_bound(repository, relative, pin)
    _, final_point_identity = read_point_report(repository)
    require(
        final_point_identity == point_identity and _revision(repository) == revision,
        "Consumed source changed during calculation",
    )
    result = {
        "schema_version": "boke-bus-conditional-counting-sets.v1",
        "source_commit": revision,
        "command": sys.orig_argv,
        "point_report": point_identity,
        "taxa": report["taxa"],
        "age_unit": report["age_unit"],
        "confidence_level_per_window": 0.95,
        "simultaneous_across_windows_claimed": False,
        **{
            key: report[key]
            for key in (
                "cores",
                "unmatched",
                "scientific_inputs",
                "original_source_epochs",
            )
        },
        "groups": rows,
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "set_status_counts": dict(
            Counter(
                r["counting_set"]["status"] for r in rows if r["status"] == "computed"
            )
        ),
        "new_point_fits": 0,
        "new_kernel_evaluations": 0,
        "common_field_cover_admitted": False,
        "sampling_calibration_established": False,
        "raw_redistribution_authorized": False,
        "limits": LIMITS,
    }
    raw = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= 1024**2, "Essential output exceeds one MiB")
    with output.open("xb") as stream:
        stream.write(raw)
    raise SystemExit(1 if any(r["status"] in {"fatal", "not_run"} for r in rows) else 0)


if __name__ == "__main__":
    main()
