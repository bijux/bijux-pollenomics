"""Admit three saved-score comparison products without fitting or rescoring."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/method-comparison/"
OWNER = "pollen-reconstruction/author-lra-constrained/method-comparison/report-products"
AUTHORITY = "reports/science/source-cohorts/author-love-matched-method-comparison.json"
AUTHORITY_SHA256: str | None = (
    "23a6d11f763c0e262a25b6f77dc2437bfaa9f7691ca8db7d2826e7566e2e22f1"
)
PRODUCTS = {
    "report": "report.json",
    "paired_scores": "paired-scores.csv",
    "fold_dispositions": "fold-dispositions.csv",
}
SOURCE_NAMES = ["comparison.py", "replay.py", "sources.py"]
METRICS = (
    "mae_fraction",
    "rmse_fraction",
    "total_variation",
    "bias_fraction",
    "count_conditioned_deviance",
)


def _read(repository: Path, name: str, expected: str, size: int) -> bytes:
    path: Path = _regular_confined_file(
        repository, name, "saved LOVE comparison evidence"
    )
    if (
        type(size) is not int
        or not 0 <= size <= 32 * 1024**2
        or path.stat().st_nlink != 1
        or path.stat().st_size != size
    ):
        raise ReportRebuildError("Saved LOVE comparison evidence size/alias differs")
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != expected:
        raise ReportRebuildError("Saved LOVE comparison evidence identity differs")
    return raw


def _csv(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def validate_products(bodies: dict[str, bytes], expected: dict[str, Any]) -> JsonObject:
    """Require exact recomputed report, both CSV projections and paired populations."""
    if (
        set(bodies) != set(PRODUCTS)
        or expected.get("schema_version") != "author-love-matched-method-comparison.v1"
        or expected.get("comparison_performed_without_refits_or_rescoring") is not True
        or expected.get("counts")
        != {
            "all_folds": 15,
            "original_scored_folds": 14,
            "original_refused_folds": 1,
            "cohort_scored_folds": 15,
            "cohort_refused_folds": 0,
            "matched_folds": 14,
            "paired_baseline_rows": 42,
        }
        or len(expected["paired_scores"]) != 42
        or len(expected["fold_dispositions"]) != 15
        or len(expected["unmatched_cohort_scores"]) != 3
        or any(
            row["original_score"] is not None
            or row["paired_comparison_available"] is not False
            for row in expected["unmatched_cohort_scores"]
        )
    ):
        raise ReportRebuildError(
            "Exact14 matched/15 disposition/three unpaired populations required"
        )
    expected_json = (
        json.dumps(expected, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    flat = [
        {
            "fold_id": row["fold_id"],
            "record_id": row["record_id"],
            "baseline": row["baseline"],
            "metric": metric,
            **values,
        }
        for row in expected["paired_scores"]
        for metric in METRICS
        for values in (row["metrics"][metric],)
    ]
    projections = {
        "report": expected_json,
        "paired_scores": _csv(
            flat,
            (
                "fold_id",
                "record_id",
                "baseline",
                "metric",
                "original",
                "cohort",
                "delta",
                "category",
            ),
        ),
        "fold_dispositions": _csv(
            expected["fold_dispositions"],
            (
                "fold_id",
                "record_id",
                "original_status",
                "original_reason",
                "cohort_status",
                "paired_baseline_rows",
            ),
        ),
    }
    if bodies != projections:
        raise ReportRebuildError(
            "Saved comparison report or CSV arithmetic/projection differs"
        )
    return {
        "counts": expected["counts"],
        "negative_transfer_pairs": len(expected["negative_transfer_cases"]),
        "unmatched_cohort_scores": 3,
        "saved_source_support_and_arithmetic_verified": True,
        "models_or_rescoring_executed": False,
        "scope": expected["scope"],
    }


def validated_author_method_comparison(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate execution/ownership and reuse byte-authenticated pure helpers."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared and not (repository / AUTHORITY).exists():
        return (), {}
    if AUTHORITY_SHA256 is None:
        raise ReportRebuildError("Actual saved LOVE comparison authority required")
    path = _regular_confined_file(repository, AUTHORITY, "LOVE comparison authority")
    authority = json.loads(
        _read(repository, AUTHORITY, AUTHORITY_SHA256, path.stat().st_size)
    )
    execution = authority["execution"]
    candidate = authority.get("source_candidate")
    if (
        authority.get("schema_version")
        != "author-love-matched-method-execution-authority.v1"
        or not isinstance(candidate, str)
        or re.fullmatch(r"[a-f0-9]{40}", candidate) is None
        or execution.get("candidate") != candidate
        or any(
            type(execution.get(k)) is not int or execution[k] != 0
            for k in ("native_exit", "common_exit", "outer_exit")
        )
        or any(
            execution.get(k) is not True
            for k in (
                "source_before_after_equal",
                "inputs_before_after_equal",
                "runtime_before_after_equal",
            )
        )
    ):
        raise ReportRebuildError(
            "Actual successful saved LOVE comparison execution required"
        )
    products = authority["products"]
    if (
        set(products) != set(PRODUCTS)
        or any(products[role].get("name") != name for role, name in PRODUCTS.items())
        or len(declared) != 1
        or declared[0].get("role") != "retained_source"
        or declared[0].get("paths")
        != sorted(PREFIX + name for name in PRODUCTS.values())
        or declared[0].get("producer_paths") != []
        or declared[0].get("producer_inputs") != []
    ):
        raise ReportRebuildError(
            "Exact saved LOVE comparison three-product ownership required"
        )
    protocol_pin = authority["protocol"]
    protocol = json.loads(
        _read(
            repository,
            PREFIX + "protocol.json",
            protocol_pin["sha256"],
            protocol_pin["bytes"],
        )
    )
    source_rows = authority["producer_sources"]
    if (
        len(source_rows) != 3
        or [row["name"] for row in source_rows] != SOURCE_NAMES
        or source_rows != protocol["source_files"]
        or protocol.get("schema_version") != "author-love-matched-method-protocol.v1"
    ):
        raise ReportRebuildError(
            "Exact three executed comparison source declarations required"
        )
    sources = {
        row["name"]: _read(
            repository, PREFIX + row["name"], row["sha256"], row["bytes"]
        )
        for row in source_rows
    }
    replay = next(row for row in source_rows if row["name"] == "replay.py")
    if any(protocol["producer"][key] != replay[key] for key in ("sha256", "bytes")):
        raise ReportRebuildError("Executed comparison entry differs from protocol")
    rows = {
        **protocol["inputs"],
        **{
            "prepared:" + name: row for name, row in protocol["prepared_inputs"].items()
        },
    }
    if (
        len(protocol["inputs"]) != 14
        or len(protocol["prepared_inputs"]) != 37
        or len(rows) != 51
        or len({row["path"] for row in rows.values()}) != 51
    ):
        raise ReportRebuildError("Exact51 distinct saved comparison inputs required")
    inputs = {
        role: _read(repository, row["path"], row["sha256"], row["bytes"])
        for role, row in rows.items()
    }
    source_scope: dict[str, Any] = {"__name__": "_saved_love_comparison_sources"}
    exec(
        compile(sources["sources.py"], str(repository / PREFIX / "sources.py"), "exec"),
        source_scope,
    )
    comparison_scope: dict[str, Any] = {
        "__name__": "_saved_love_comparison_arithmetic",
        "sources": source_scope,
    }
    exec(
        compile(
            sources["comparison.py"], str(repository / PREFIX / "comparison.py"), "exec"
        ),
        comparison_scope,
    )
    try:
        expected = comparison_scope["compare"](inputs, protocol)
        accepted = []
        bodies = {}
        for role, row in products.items():
            reference = row["original_reference"]
            name = PREFIX + row["name"]
            entry = tracked_by_path.get(name)
            if (
                entry is None
                or entry.sha256 != reference["sha256"]
                or entry.size != reference["bytes"]
            ):
                raise ReportRebuildError(
                    "Saved LOVE comparison Git product identity differs"
                )
            bodies[role] = _read(
                repository, name, reference["sha256"], reference["bytes"]
            )
            accepted.append(entry)
        result = validate_products(bodies, expected)
    except (KeyError, TypeError, ValueError) as error:
        raise ReportRebuildError(
            "Saved LOVE comparison support/arithmetic refused: " + str(error)
        ) from error
    return tuple(accepted), {
        "owner_id": OWNER,
        "authority_sha256": AUTHORITY_SHA256,
        "executed_source_candidate": candidate,
        **result,
    }
