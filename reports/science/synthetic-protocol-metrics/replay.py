"""Recompute archival synthetic metric means from retained score tables."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

FIELDS = (
    "protocol",
    "profile",
    "method",
    "target",
    "requested",
    "scored",
    "prediction_failed",
    "other_refused",
    "mean_mae_fraction",
    "interpretation",
    "interval_coverage",
    "score_manifest_sha256",
    "evidence_sha256",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def produce(source_manifest_path: Path) -> tuple[list[dict], dict]:
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if source_manifest["schema_version"] != "synthetic-score-source.v2":
        raise ValueError("Unexpected score-source manifest schema")
    source_root = source_manifest_path.resolve().parent
    bindings = source_manifest["protocols"]
    if len(bindings) != 6 or len({bound["label"] for bound in bindings}) != 6:
        raise ValueError("Retained protocol support changed")
    rows = []
    protocols = []
    totals: Counter[tuple[str, str]] = Counter()
    previous = {
        (r["protocol"], r["method"], r["target"]): r
        for r in source_manifest["historical_rows"]
    }
    if len(previous) != len(source_manifest["historical_rows"]):
        raise ValueError("Duplicate historical metric row")
    for bound in bindings:
        if bound["score_table"] != f"score_protocols/{bound['label']}.json":
            raise ValueError("Retained score source path changed")
        score_path = (source_root / bound["score_table"]).resolve()
        if not score_path.is_relative_to(source_root) or not score_path.is_file():
            raise ValueError("Retained score source path changed")
        if sha256(score_path) != bound["score_table_sha256"]:
            raise ValueError(f"Retained score source changed: {bound['label']}")
        scores = json.loads(score_path.read_text(encoding="utf-8"))
        if not isinstance(scores, list):
            raise ValueError("Retained score table changed")
        grouped = defaultdict(list)
        for score in scores:
            metric = score.get("score", score.get("metrics"))
            if metric is None:
                raise ValueError("Retained score metric changed")
            target = metric.get("target", score["target"])
            if target == "pollen":
                target = "pollen_composition"
            if target not in (
                "pollen_composition",
                "vegetation_cover",
            ):
                raise ValueError("Retained metric target changed")
            grouped[(score.get("baseline", score.get("method")), target)].append(score)
        for (method, target), units in sorted(grouped.items()):
            if method is None:
                raise ValueError("Missing retained score method")
            prior = previous[(bound["label"], method, target)]
            metrics = [unit.get("score", unit.get("metrics")) for unit in units]
            if any(metric is None for metric in metrics):
                raise ValueError("Missing retained score metric")
            status = Counter(metric["status"] for metric in metrics)
            scored = [metric for metric in metrics if metric["status"] == "scored"]
            failures = status.get("prediction_failed", 0)
            computed_mean = (
                sum(metric["mae_fraction"] for metric in scored) / len(scored)
                if scored
                else None
            )
            if (
                computed_mean is None
                or abs(computed_mean - prior["mean_mae_fraction"]) > 1e-15
            ):
                raise ValueError("Retained score mean differs from historical result")
            role = (
                "in_sample_diagnostic"
                if any(
                    unit.get("evaluation_role") == "in_sample_diagnostic"
                    or unit.get("eligible_for_heldout_acceptance") is False
                    for unit in units
                )
                else "heldout_prediction_exploratory"
            )
            row = {
                "protocol": bound["label"],
                "profile": prior["profile"],
                "method": method,
                "target": target,
                "requested": len(units),
                "scored": len(scored),
                "prediction_failed": failures,
                "other_refused": len(units) - len(scored) - failures,
                "mean_mae_fraction": prior["mean_mae_fraction"],
                "interpretation": role,
                "interval_coverage": None,
                "score_manifest_sha256": bound["score_manifest_sha256"],
                "evidence_sha256": prior["evidence_sha256"],
            }
            if row != {field: prior[field] for field in FIELDS}:
                raise ValueError("Retained score row differs from historical result")
            rows.append(row)
            for field in ("requested", "scored", "prediction_failed"):
                totals[(target, field)] += row[field]
        first_method, first_target = next(iter(grouped))
        if (
            bound["profile"]
            != previous[(bound["label"], first_method, first_target)]["profile"]
            or bound["historical_evidence_sha256"]
            != previous[(bound["label"], first_method, first_target)][
                "evidence_sha256"
            ]
        ):
            raise ValueError("Retained protocol identity changed")
        protocols.append(
            {
                "label": bound["label"],
                "profile": previous[(bound["label"], first_method, first_target)][
                    "profile"
                ],
                "prediction_manifest_sha256": bound["prediction_manifest_sha256"],
                "score_manifest_sha256": bound["score_manifest_sha256"],
                "historical_evidence_sha256": bound["historical_evidence_sha256"],
            }
        )
    if len(rows) != 16 or len(protocols) != 6:
        raise ValueError("Retained protocol support changed")
    accounting = {
        target: {
            field: totals[(target, field)]
            for field in ("requested", "scored", "prediction_failed")
        }
        for target in ("pollen_composition", "vegetation_cover")
    }
    if (
        accounting != source_manifest["source_report_accounting"]
    ):
        raise ValueError("Historical retained-score accounting changed")
    historical_rows = [
        {field: row[field] for field in FIELDS}
        for row in source_manifest["historical_rows"]
    ]
    if rows != historical_rows:
        raise ValueError("Retained score row order differs from historical result")
    report = {
        "schema_version": "synthetic-protocol-metrics.v1",
        "private_archive_sha256": source_manifest["archive_sha256"],
        "historical_report_sha256": source_manifest["source_report_sha256"],
        "protocols": protocols,
        "accounting": accounting,
        "pooled_accuracy_computed": False,
        "independent_vegetation_accuracy_claim": False,
        "current_reader_limit": "Current installed reader refuses the historical spatial-block profile; direct score arithmetic matches the historical reader output.",
        "rows": rows,
    }
    return rows, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Absent output destination required")
    rows, report = produce(args.source_manifest)
    args.output.mkdir(parents=True)
    with (args.output / "scores.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
