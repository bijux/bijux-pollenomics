"""Freeze matched conditional predictions before scoring retained pollen counts."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
from typing import Any

from .inputs import Core, buffer, decode, digest, load, physical, require
from .prediction import FAMILIES, predictions

SCOPES = ("swedish_only", "pooled_eligible_nordic")
SOURCE_NAMES = {
    "__init__.py",
    "__main__.py",
    "inputs.py",
    "prediction.py",
    "producer.py",
}
LIMITS = "Prior-exposed restricted-panel point predictions only. No four-country matched accuracy, independent vegetation, historical reproduction, calibrated uncertainty, source-rights or complete scientific certification. Saved native/source epochs remain distinct from this execution."


def _score(predicted: dict[str, float], counts: dict[str, int]) -> Any:
    from bijux_pollenomics.analysis.lra_validation.metrics import score_pollen

    return score_pollen(predicted, counts)


def score_rows(
    rows: list[dict[str, Any]], cores: tuple[Core, ...], *, enabled: bool
) -> tuple[list[dict[str, Any]], bool]:
    """Score declared predictions against separately accessed target counts."""
    from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal

    original = {core.id: core for core in cores}
    output = []
    fatal = not enabled
    for row in rows:
        identity = row["identity"]
        for family in FAMILIES:
            score: dict[str, Any] = {
                "identity": identity,
                "family": family,
                "status": "not_run_after_fatal",
                "mae_fraction": None,
                "total_variation": None,
                "signed_error": None,
            }
            if not fatal:
                prediction = row["families"][family]
                if prediction["status"] != "predicted":
                    score.update(
                        status="prediction_refused",
                        reason=prediction.get("reason", prediction["status"]),
                    )
                else:
                    try:
                        core = original[identity["core"]]
                        cell = next(
                            c
                            for c in core.cells
                            if list(c.window) == identity["window_cal_bp"]
                        )
                        axis = identity["axis"]
                        counts = {
                            name: cell.counts[core.axis.index(name)] for name in axis
                        }
                        total = sum(counts.values())
                        score.update(
                            target_counts=counts,
                            target_panel_N=total,
                            target_source_support_sha256=cell.source_support_sha256,
                        )
                        if total == 0:
                            score.update(status="unavailable_zero_target_panel")
                        else:
                            predicted = dict(
                                zip(axis, prediction["pollen_fraction"], strict=True)
                            )
                            result = _score(predicted, counts)
                            require(
                                result.status == "scored"
                                and result.observed_total_count == total
                                and result.taxon_count == len(axis),
                                "Actual pollen score denominator differs",
                            )
                            require(
                                all(
                                    type(v) in (float, int)
                                    and math.isfinite(v)
                                    and 0 <= v <= 1
                                    for v in (
                                        result.mae_fraction,
                                        result.total_variation,
                                    )
                                ),
                                "Finite MAE/TV fractions required",
                            )
                            score.update(
                                status="scored",
                                mae_fraction=result.mae_fraction,
                                total_variation=result.total_variation,
                                signed_error={
                                    name: predicted[name] - counts[name] / total
                                    for name in axis
                                },
                            )
                    except ValidationRefusal as error:
                        score.update(
                            status="refused_validation",
                            reason=error.reason_code,
                            message=str(error),
                        )
                    except Exception as error:
                        fatal = True
                        score.update(
                            status="fatal",
                            error_type=type(error).__name__,
                            message=str(error),
                        )
            output.append(score)
    require(len(output) == 308, "All308family outcomes required")
    return output, not fatal


def matched_summary(scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize method differences on their exact common target population."""
    groups: dict[
        tuple[str, tuple[float, ...]], dict[tuple[str, str], dict[str, Any]]
    ] = {}
    for row in scores:
        identity = row["identity"]
        key = (identity["core"], tuple(identity["window_cal_bp"]))
        cell = groups.setdefault(key, {})
        subkey = identity["scope"], row["family"]
        require(subkey not in cell, "Duplicate score context")
        cell[subkey] = row
    expected = {(scope, family) for scope in SCOPES for family in FAMILIES}
    matched: dict[str, list[dict[tuple[str, str], dict[str, Any]]]] = {}
    for (core, _), group in groups.items():
        require(
            set(group) == expected, "Complete scope/family score membership required"
        )
        if all(row["status"] == "scored" for row in group.values()):
            first = next(iter(group.values()))
            require(
                all(
                    row["target_counts"] == first["target_counts"]
                    and row["identity"]["axis"] == first["identity"]["axis"]
                    for row in group.values()
                ),
                "Matched response denominator differs",
            )
            matched.setdefault(core, []).append(group)
    require(
        sum(len(w) for w in matched.values()) <= 26 and len(matched) <= 2,
        "Paired structural upper bound exceeded",
    )
    by_method = {}
    for scope, family in sorted(expected):
        sites = {}
        for core, windows in sorted(matched.items()):
            sites[core] = {
                "matched_windows": len(windows),
                **{
                    metric: math.fsum(w[scope, family][metric] for w in windows)
                    / len(windows)
                    for metric in ("mae_fraction", "total_variation")
                },
            }
        by_method[scope + "/" + family] = {
            "physical_targets": len(sites),
            "matched_windows": sum(s["matched_windows"] for s in sites.values()),
            "per_target": sites,
            **{
                metric: math.fsum(s[metric] for s in sites.values()) / len(sites)
                if sites
                else None
                for metric in ("mae_fraction", "total_variation")
            },
        }
    return {
        "matched_target_windows": sum(len(w) for w in matched.values()),
        "physical_targets": len(matched),
        "scope_family_site_macros": by_method,
        "aggregation": "Equal windows per target then equal physical targets; same four-way response/eligibility. Null when no joint scored target.",
    }


def write_json(path: Path, value: dict[str, Any], budget: list[int]) -> dict[str, Any]:
    """Write a bounded JSON product and return its byte identity."""
    raw = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) + budget[0] <= 8388608, "Scientific output exceeds8MiB")
    with path.open("xb") as stream:
        stream.write(raw)
    budget[0] += len(raw)
    return {"path": str(path), "sha256": digest(raw), "bytes": len(raw)}


def _source_pins() -> list[dict[str, Any]]:
    source = Path(__file__).absolute().parent
    require(
        {p.name for p in source.glob("*.py")} == SOURCE_NAMES,
        "Physical-forward module membership differs",
    )
    result = []
    for name in sorted(SOURCE_NAMES):
        path = source / name
        physical(path)
        raw = path.read_bytes()
        row: dict[str, Any] = {
            "path": str(path),
            "sha256": digest(raw),
            "bytes": len(raw),
        }
        buffer(path, row["sha256"], row["bytes"])
        result.append(row)
    return result


def run(repository: Path, output: Path, candidate: str) -> dict[str, Any]:
    """Freeze conditional predictions before writing matched scoring products."""
    physical(repository)
    physical(output)
    require(
        repository.is_dir() and re.fullmatch("[0-9a-f]{40}", candidate),
        "Exact repository and execution epoch required",
    )
    require(
        output.is_relative_to(repository / "artifacts")
        and output != repository / "artifacts"
        and not output.exists()
        and output.parent.is_dir(),
        "Absent confined artifact output required",
    )
    cores, protocol, pins = load(repository)
    source_pins = _source_pins()
    require(
        protocol["scopes"] == list(SCOPES)
        and protocol["point_estimates_only"] is True
        and protocol["uncertainty_claimed"] is False,
        "Point-only training-scope declaration differs",
    )
    rows, prediction_completed = predictions(cores, protocol)
    output.mkdir()
    budget = [0]
    for pin in pins + source_pins:
        buffer(Path(pin["path"]), pin["sha256"], pin["bytes"])
    freeze_value = {
        "schema_version": "matched-pollen-forward.prediction-freeze.v1",
        "candidate": candidate,
        "source_epochs": protocol["source_epochs"],
        "input_pins": pins,
        "producer_pins": source_pins,
        "prediction_completed": prediction_completed,
        "contexts": rows,
        "outcome_access": protocol["outcome_access"],
        "limits": LIMITS,
    }
    freeze = write_json(output / "prediction-freeze.json", freeze_value, budget)
    require(
        decode(buffer(Path(freeze["path"]), freeze["sha256"], freeze["bytes"]))
        == freeze_value,
        "Persisted prediction freeze differs",
    )
    # No target score call occurs until every prediction/disposition is persisted.
    scores, scoring_completed = score_rows(rows, cores, enabled=prediction_completed)
    scored = write_json(
        output / "scores.json",
        {
            "schema_version": "matched-pollen-forward.scores.v1",
            "prediction_freeze": freeze,
            "outcomes": scores,
        },
        budget,
    )
    report = {
        "schema_version": "matched-pollen-forward.report.v1",
        "candidate": candidate,
        "source_epochs": protocol["source_epochs"],
        "completed": prediction_completed and scoring_completed,
        "prediction_contexts": len(rows),
        "family_outcomes": len(scores),
        "prediction_freeze": freeze,
        "scores": scored,
        "status_counts": dict(sorted(Counter(row["status"] for row in scores).items())),
        "matched": matched_summary(scores),
        "uncertainty_evaluated": False,
        "new_kernel_R_fit_optimizer_calls": 0,
        "previously_exposed_development": True,
        "limits": LIMITS,
    }
    for pin in pins + source_pins:
        buffer(Path(pin["path"]), pin["sha256"], pin["bytes"])
    buffer(Path(freeze["path"]), freeze["sha256"], freeze["bytes"])
    buffer(Path(scored["path"]), scored["sha256"], scored["bytes"])
    write_json(output / "report.json", report, budget)
    return report


def main(argv: list[str] | None = None) -> int:
    """Parse arguments for the maintained conditional comparison writer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execution-epoch", required=True)
    args = parser.parse_args(argv)
    return (
        0 if run(args.repository, args.output, args.execution_epoch)["completed"] else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
