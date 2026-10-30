"""Prespecified numerical follow-through for two previously withheld fits.

Only Namibia_T7 at native radius labels 200 and 500 m is excluded. The other
nine events, including both T4 and T5, retain their original five-axis native
counts and areas. Natural multinomial effort, score tolerance 1e-12, relative
count tolerance 1e-10 and the 200-step budget remain fixed. The current solver
has the qualified small-step objective-difference implementation. The original
135-fit study and CSV are not rerun or overwritten. Exactly two previously
failed training problems are recomputed separately, without held-out scoring.
Saved step-limit dispositions remain historical evidence, not proof of their
internal arithmetic cause.

For q_si=A_si*w_i/sum_j(A_sj*w_j), output w has Combretaceae=1. These are
empirical response multipliers, not PPE or vegetation. The returned objective
is per-grain natural-log negative multinomial likelihood, omitting only the
multinomial coefficient. Converged fits expose only training probabilities;
failures retain diagnostics and withhold multipliers and probabilities. No
held-out probability, score, other radius, baseline or model selection occurs.

The independent prospective comparison uses Decimal160 on these same two
training problems: probability error <=1e-8 and per-grain objective error
<=1e-10, without relaxing production stationarity or information guards.
The complete run is bounded to 30 seconds and one result of at most 64 KiB.
This numerical development comparison does not establish field applicability,
independence, ERV/PPE, calibrated uncertainty or historical solver equivalence.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.likelihood import (
    multisite_likelihood as engine,
)

from ....ci.report_rebuild.artifact_paths import require_absent_artifact_output
from ....ci.report_rebuild.source_paths import safe_source_file
from ..namibia_source_join import DESCRIPTOR
from . import inputs, producer
from .comparison import CSV_FIELDS
from .inputs import SITES, TAXA, NativeSource

RADII = (200, 500)
HELDOUT = "Namibia_T7"
TRAINING = tuple(site for site in SITES if site != HELDOUT)
HISTORICAL_REPORT = Path(
    "reports/science/vegetation-reference/namibia-pollen-prediction.csv"
)
HISTORICAL_POINT_SOURCE = "9f3b7d49ce5f841ea31b4b136e552f79a62dd3f3"
MAX_SECONDS = 30
MAX_OUTPUT_BYTES = 64 * 1024


def _diagnostic(value: float) -> float | str:
    return value if math.isfinite(value) else str(value)


def _historical_pin(repository: Path) -> str:
    lock = safe_source_file(
        repository, "reports/source-lock.json", "Scientific raw source lock"
    )
    value = json.loads(lock.read_bytes())["sources"][HISTORICAL_REPORT.as_posix()]
    if not isinstance(value, str):
        raise ValueError("Historical Namibia numerical source identity is unavailable")
    return value


def historical_fits(body: bytes) -> dict[int, dict[str, object]]:
    """Read the two fixed old failures without interpreting or rescoring others."""
    if len(body) > 1024**2:
        raise ValueError("Historical Namibia CSV exceeds its existing size limit")
    reader = csv.DictReader(io.StringIO(body.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != CSV_FIELDS:
        raise ValueError("Historical Namibia CSV fields differ")
    rows = list(reader)
    if len(rows) != 150:
        raise ValueError("Historical Namibia population differs")
    result: dict[int, dict[str, object]] = {}
    for row in rows:
        if row["heldout_site"] != HELDOUT or row["radius_label_m"] not in {
            "200",
            "500",
        }:
            continue
        radius = int(row["radius_label_m"])
        if (
            radius in result
            or row["heldout_group"] != HELDOUT
            or row["fit_id"] != f"{radius}:{HELDOUT}"
            or row["training_sites"] != "|".join(TRAINING)
            or row["training_grains"] != "6077"
            or row["fit_status"] != "not_converged"
            or row["fit_stop_reason"] != "step_limit"
            or row["fit_steps"] != "200"
            or row["empirical_status"] != "fit_not_converged"
            or any(
                row[f"response_multiplier_{taxon}"] or row[f"empirical_{taxon}"]
                for taxon in TAXA
            )
        ):
            raise ValueError("Historical frozen T7 failure disposition differs")
        result[radius] = {
            "fit_id": row["fit_id"],
            "status": row["fit_status"],
            "stop_reason": row["fit_stop_reason"],
            "steps": 200,
            "training_grains": 6077,
        }
    if set(result) != set(RADII):
        raise ValueError("Historical T7 failure selection is incomplete")
    return result


def evaluate(
    source: NativeSource, old: Mapping[int, Mapping[str, object]]
) -> list[dict[str, object]]:
    """Make exactly two calls with only fixed training inputs; keep every outcome."""
    if set(old) != set(RADII):
        raise ValueError("Two fixed historical fits are required")
    counts = [source.counts[site] for site in TRAINING]
    if any(
        len(row) != len(TAXA) or any(type(n) is not int or n <= 0 for n in row)
        for row in counts
    ):
        raise ValueError("Positive native five-taxon integer training counts required")
    total = sum(map(sum, counts))
    if any(old[radius].get("training_grains") != total for radius in RADII):
        raise ValueError("Historical and native training effort differ")
    result = []
    for radius in RADII:
        areas = [source.areas[(site, radius)] for site in TRAINING]
        if any(
            len(row) != len(TAXA)
            or any(
                type(value) not in (int, float)
                or not math.isfinite(value)
                or value <= 0
                for value in row
            )
            for row in areas
        ):
            raise ValueError(
                "Positive finite native five-taxon training areas required"
            )
        record: dict[str, object] = {
            "radius_label_m": radius,
            "historical_fit": dict(old[radius]),
            "status": "refused",
            "stop_reason": None,
            "steps": None,
            "mean_negative_log_likelihood": None,
            "score_residual": None,
            "relative_count_residual": None,
            "hessian_condition_number": None,
            "minimum_relative_information": None,
            "information_resolution_floor": None,
            "response_multipliers": None,
            "training_probabilities": None,
        }
        try:
            fit = engine.fit_multisite_likelihood(
                np.asarray(counts),
                np.asarray(areas),
                taxon_measured=np.ones((len(TRAINING), len(TAXA)), dtype=bool),
                score_tolerance=1e-12,
                relative_count_tolerance=1e-10,
                max_steps=200,
            )
        except ValidationError as exc:
            record["stop_reason"] = str(exc)
            result.append(record)
            continue
        record.update(
            status="converged" if fit.converged else "not_converged",
            stop_reason=fit.stop_reason,
            steps=fit.steps,
            mean_negative_log_likelihood=_diagnostic(fit.mean_negative_log_likelihood),
            score_residual=_diagnostic(fit.score_residual),
            relative_count_residual=_diagnostic(fit.relative_count_residual),
            hessian_condition_number=_diagnostic(fit.hessian_condition_number),
            minimum_relative_information=_diagnostic(fit.minimum_relative_information),
            information_resolution_floor=_diagnostic(fit.information_resolution_floor),
        )
        if fit.converged:
            with np.errstate(over="ignore", invalid="ignore"):
                weights = tuple(float(value / fit.cover[-1]) for value in fit.cover)
            if any(not math.isfinite(value) or value <= 0 for value in weights):
                record.update(
                    status="refused",
                    stop_reason="response_multiplier_gauge_not_representable",
                )
            else:
                record.update(
                    response_multipliers=weights,
                    training_probabilities=fit.predicted.tolist(),
                )
        result.append(record)
    return result


def run(repository: Path, source_store: Path, output: Path) -> dict[str, object]:
    """Use shared sources and committed code; publish only after terminal checks."""
    started = time.monotonic()
    repository, source_store = (
        repository.resolve(strict=True),
        source_store.resolve(strict=True),
    )
    output = require_absent_artifact_output(repository, output)
    if output.is_relative_to(source_store) or source_store.is_relative_to(output):
        raise ValueError("Namibia result overlaps shared sources")
    if Path(__file__).resolve() != repository / producer.PACKAGE / "fit_resolution.py":
        raise ValueError("Namibia fit-resolution module origin differs")
    source_revision = producer.revision(repository)
    original_path = safe_source_file(
        repository, HISTORICAL_REPORT.as_posix(), "Historical Namibia CSV"
    )
    original = original_path.read_bytes()
    original_pin = _historical_pin(repository)
    if hashlib.sha256(original).hexdigest() != original_pin:
        raise ValueError("Historical Namibia numerical source identity differs")
    committed = subprocess.check_output(
        ["git", "show", f"{source_revision}:{HISTORICAL_REPORT.as_posix()}"],
        cwd=repository,
    )
    if committed != original:
        raise ValueError("Historical Namibia report is not its committed bytes")
    old = historical_fits(original)
    source = inputs.load(repository, source_store)
    fits = evaluate(source, old)
    report: dict[str, object] = {
        "schema_version": "namibia-frozen-fit-resolution.v1",
        "source_revision": source_revision,
        "historical_point_source_revision": HISTORICAL_POINT_SOURCE,
        "historical_report": HISTORICAL_REPORT.as_posix(),
        "historical_report_sha256": original_pin,
        "source_descriptor": str(DESCRIPTOR),
        "heldout_group": HELDOUT,
        "training_sites": TRAINING,
        "taxa": TAXA,
        "solver_profile": engine.PROFILE,
        "backend": "bijux-pollenomics-lra Python/NumPy/SciPy likelihood; no R or adopted C++",
        "solver_options": {
            "score_tolerance": 1e-12,
            "relative_count_tolerance": 1e-10,
            "max_steps": 200,
        },
        "objective": "natural_count_weighted_per_grain_negative_log_likelihood_without_multinomial_coefficient",
        "weight_gauge": "Combretaceae=1; empirical multipliers, not vegetation or PPE",
        "failed_output_posture": "probabilities_and_multipliers_withheld",
        "nonfinite_diagnostic_posture": "explicit_string_not_a_finite_number",
        "comparison_bounds": {
            "probability_absolute": 1e-8,
            "mean_negative_log_likelihood_absolute": 1e-10,
        },
        "fits": fits,
        "limits": [
            "No held-out prediction or scoring",
            "Original failures remain unchanged",
            "No historical internal-cause inference",
            "No physical, ecological, uncertainty or field admission",
        ],
    }
    body = (json.dumps(report, allow_nan=False, indent=2) + "\n").encode()
    if len(body) > MAX_OUTPUT_BYTES:
        raise ValueError("Two-fit result exceeds 64 KiB")
    if (
        inputs.load(repository, source_store) != source
        or original_path.read_bytes() != original
        or _historical_pin(repository) != original_pin
        or producer.revision(repository) != source_revision
    ):
        raise ValueError("Namibia inputs or consumed source changed during fitting")
    if time.monotonic() - started > MAX_SECONDS:
        raise ValueError("Two-fit runtime budget exceeded")
    with output.open("xb") as stream:
        stream.write(body)
    return report


def main(argv: list[str] | None = None) -> int:
    """Run only the two frozen training problems into one numerical JSON result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.source_store, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
