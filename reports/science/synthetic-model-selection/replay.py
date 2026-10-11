"""Recompute the retained synthetic trial scores and selection from tracked rows."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
TAXA = frozenset({"broadleaf", "conifer", "open_land"})


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rank(rows: list[dict[str, Any]]) -> list[dict[str, float | int | str]]:
    scores: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        candidate = row["candidate_id"]
        case = row["case_id"]
        if case in scores[candidate] or row["run_id"] != f"{candidate}-{case}":
            raise ValueError("Duplicate or inconsistent synthetic trial")
        metrics = row["metrics"]
        estimated = metrics["estimated_cover_fraction"]
        truth = metrics["true_support_vegetation_fraction"]
        if set(estimated) != TAXA or set(truth) != TAXA:
            raise ValueError("Synthetic taxon axis differs")
        if any(not 0 <= value <= 1 for value in (*estimated.values(), *truth.values())):
            raise ValueError("Synthetic cover leaves fraction bounds")
        measured = sum(abs(estimated[taxon] - truth[taxon]) for taxon in TAXA) / 3
        if abs(measured - metrics["vegetation_mae_fraction"]) > 1e-12:
            raise ValueError("Reported synthetic trial error differs")
        if row["status"] != "completed":
            raise ValueError("Incomplete synthetic trial")
        scores[candidate][case] = measured
    return sorted(
        (
            {
                "candidate_id": candidate,
                "cases": len(values),
                "mean_mae_fraction": sum(values.values()) / len(values),
                "max_case_mae_fraction": max(values.values()),
            }
            for candidate, values in scores.items()
        ),
        key=lambda row: (
            row["mean_mae_fraction"],
            row["max_case_mae_fraction"],
            row["candidate_id"],
        ),
    )


def build() -> dict[str, object]:
    policy_path = HERE / "policy.json"
    report_path = HERE / "report.json"
    policy = json.loads(policy_path.read_text())
    report = json.loads(report_path.read_text())
    policy_sha = _sha(policy_path)
    if report["policy_sha256"] != policy_sha:
        raise ValueError("Synthetic report policy identity differs")
    candidates = {row["id"] for row in policy["candidates"]}
    cases = set(policy["cases"])
    if (
        len(candidates) != 6
        or len(cases) != 2
        or policy["objective"]["final_test_access"] is not False
    ):
        raise ValueError("Synthetic development design differs")
    rows = report["trials"]
    if (
        report["attempted_trials"] != len(rows)
        or report["completed_trials"] != len(rows)
        or len(rows) != 12
        or report["failed_trials"] != 0
        or report["refused_trials"] != 0
        or report["claims"]["final_test_access"] is not False
    ):
        raise ValueError("Synthetic trial coverage differs")
    ranking = _rank(rows)
    if {row["candidate_id"] for row in ranking} != candidates or any(
        row["cases"] != 2 for row in ranking
    ):
        raise ValueError("Synthetic candidate coverage differs")
    if {(row["candidate_id"], row["case_id"]) for row in rows} != {
        (candidate, case) for candidate in candidates for case in cases
    }:
        raise ValueError("Synthetic candidate/case pairs differ")
    expected = report["eligible_candidates"]
    if len(expected) != len(ranking) or any(
        row["candidate_id"] != historical["candidate_id"]
        or abs(row["mean_mae_fraction"] - historical["mean_mae_fraction"]) > 1e-12
        or abs(row["max_case_mae_fraction"] - historical["max_case_mae_fraction"])
        > 1e-12
        for row, historical in zip(ranking, expected, strict=True)
    ):
        raise ValueError("Synthetic candidate ranking differs")
    selected = ranking[0]
    if selected["candidate_id"] != report["selected"]["candidate_id"] or any(
        abs(selected[field] - report["selected"][field]) > 1e-12
        for field in ("mean_mae_fraction", "max_case_mae_fraction")
    ):
        raise ValueError("Synthetic winner differs")
    other = [row for row in ranking if row["candidate_id"] != selected["candidate_id"]]
    perturbation_changes_selection = float(other[0]["mean_mae_fraction"]) < 1.0
    if not perturbation_changes_selection:
        raise ValueError("Selection perturbation did not change winner")
    return {
        "schema_version": "synthetic-development-selection-audit.1",
        "status": "passed",
        "policy_sha256": policy_sha,
        "report_sha256": _sha(report_path),
        "trial_count": len(rows),
        "ranking": ranking,
        "perturbed_selected_rows_change_selection": perturbation_changes_selection,
        "scope": "Tracked trial values and selection only; historical item envelopes and numerical LRA execution are not replayed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
