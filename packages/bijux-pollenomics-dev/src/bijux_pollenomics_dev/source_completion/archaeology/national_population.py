"""Reconcile national native populations without adopting historical WFS equivalence."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable, Mapping
import json
from pathlib import Path
import sqlite3
import time
from typing import cast

from bijux_pollenomics.collection.sources.raa.materialization.context import (
    open_raa_source_context,
)
from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    SOURCE_COLUMNS,
)
from bijux_pollenomics.collection.sources.raa.materialization.ownership import (
    canonical_bytes,
    iter_audit_documents,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    quote_identifier,
)
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

CATEGORY_FIELDS = (
    "lamningstyp",
    "antikvariskbedomning",
    "aktualitetstatus",
    "skadestatus",
    "undersokningsstatus",
)


def summarize(documents: Iterable[dict[str, object]]) -> dict[str, object]:
    """Consume the maintained lossless owner audit, retaining typed category bins."""
    categories: dict[str, Counter[bytes]] = {
        field: Counter() for field in CATEGORY_FIELDS
    }
    summary: dict[str, object] | None = None
    source_rows = 0
    for document in documents:
        if document["kind"] == "summary":
            if summary is not None:
                raise ValueError("multiple native population summaries")
            summary = document
        elif document["kind"] == "source_row":
            source_rows += 1
            if summary is not None:
                raise ValueError("native source row follows terminal summary")
            if document["table"] != "lamning":
                continue
            values = cast(dict[str, object], document["source_values"])
            for field in CATEGORY_FIELDS:
                value = values[field]
                if value is not None and not isinstance(value, str):
                    raise ValueError("native category must retain text or null")
                categories[field][canonical_bytes(value)] += 1
    if summary is None:
        raise ValueError("native population summary absent")
    tables = cast(dict[str, dict[str, object]], summary["tables"])
    if source_rows != sum(cast(int, row["source_rows"]) for row in tables.values()):
        raise ValueError("native row and terminal denominators differ")
    population = cast(int, tables["lamning"]["source_rows"])
    if any(sum(counts.values()) != population for counts in categories.values()):
        raise ValueError("native category denominator differs")
    return {
        "native_ownership_summary": summary,
        "native_categories": {
            field: [
                {"value": json.loads(value), "source_rows": count}
                for value, count in sorted(counts.items())
            ]
            for field, counts in categories.items()
        },
    }


def verify_sql(connection: sqlite3.Connection, report: dict[str, object]) -> None:
    """Check every table/field denominator independently using SQLite aggregates."""
    summary = cast(dict[str, object], report["native_ownership_summary"])
    tables = cast(dict[str, dict[str, object]], summary["tables"])
    for table, columns in SOURCE_COLUMNS.items():
        expressions = ["count(*)"]
        for name in columns:
            column = quote_identifier(name)
            expressions.extend(
                (
                    f"coalesce(sum({column} IS NULL),0)",
                    f"coalesce(sum(typeof({column}) IN ('integer','real') AND {column}=0),0)",
                    f"coalesce(sum(typeof({column})='text' AND {column}=''),0)",
                )
            )
        row = connection.execute(
            f"SELECT {','.join(expressions)} FROM {quote_identifier(table)}"
        ).fetchone()
        total = int(row[0])
        expected = tables[table]
        if total != expected["source_rows"]:
            raise ValueError("independent SQL native population differs")
        cells = cast(dict[str, dict[str, int]], expected["source_cells"])
        for index, name in enumerate(columns):
            null, zero, empty = tuple(row[1 + index * 3 : 4 + index * 3])
            observed = {
                "null": null,
                "non_null": total - null,
                "numeric_zero": zero,
                "empty_text": empty,
            }
            if any(cells[name].get(key, 0) != count for key, count in observed.items()):
                raise ValueError("independent SQL null/zero/empty counts differ")
    categories = cast(dict[str, list[dict[str, object]]], report["native_categories"])
    for field in CATEGORY_FIELDS:
        column = quote_identifier(field)
        observed_categories = {
            canonical_bytes(row[0]): row[1]
            for row in connection.execute(
                f"SELECT {column},count(*) FROM lamning GROUP BY {column}"
            )
        }
        expected_categories = {
            canonical_bytes(row["value"]): row["source_rows"]
            for row in categories[field]
        }
        if observed_categories != expected_categories:
            raise ValueError("independent SQL native categories differ")


def historical_comparison(
    report: dict[str, object], historical: Mapping[str, object]
) -> dict[str, object]:
    """Compare declared aggregates only; their difference cannot identify records."""
    summary = cast(dict[str, object], report["native_ownership_summary"])
    tables = cast(dict[str, dict[str, object]], summary["tables"])
    categories = cast(dict[str, list[dict[str, object]]], report["native_categories"])
    classes = {
        row["value"]: cast(int, row["source_rows"])
        for row in categories["antikvariskbedomning"]
    }
    if "Fornlämning" not in classes or "Möjlig fornlämning" not in classes:
        raise ValueError("native class labels do not support historical comparison")
    native = {
        "all_published_sites": tables["lamning"]["source_rows"],
        "fornlamning": classes["Fornlämning"],
        "fornlamning_or_possible": classes["Fornlämning"]
        + classes["Möjlig fornlämning"],
    }
    counts = cast(dict[str, object], historical["counts"])
    result = {}
    for name, count in native.items():
        earlier = counts[name]
        if type(earlier) is not int or earlier < 0:
            raise ValueError(
                "historical aggregate must be a declared nonnegative integer"
            )
        result[name] = {
            "native_source_rows": count,
            "historical_wfs_declared_hits": earlier,
            "difference_native_minus_historical": cast(int, count) - earlier,
        }
    return {
        "aggregate_counts": result,
        "record_level_reconciliation": "unavailable_missing_historical_feature_inventory",
        "individual_additions_or_removals": None,
        "population_equivalence": False,
        "geometry_equivalence": False,
        "interpretation": "Native remains rows versus retained declared WFS query hits without jointly bound source dates. Equal labels or a net count difference do not establish identical classification rules, matched records, temporal change, additions/removals or center-point geometry.",
    }


def main() -> int:
    """Reconcile national population aggregates from retained source inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repository
    output = require_absent_artifact_output(root, args.output)
    descriptor = json.loads(
        (root / "data/raa/raw/national_geopackage_source.json").read_bytes()
    )
    historical = json.loads(
        (root / "data/raa/normalized/sweden_archaeology_layer.json").read_bytes()
    )
    started = time.monotonic()
    with open_raa_source_context(args.source, descriptor) as context:
        connection = context.connection
        connection.set_progress_handler(
            lambda: int(time.monotonic() - started > 600), 10000
        )
        report = summarize(iter_audit_documents(connection))
        verify_sql(connection, report)
        report["source_context_profile"] = context.profile
    report.update(
        source_identity={
            key: descriptor[key]
            for key in ("sha256", "byte_count", "captured_at_utc", "http_last_modified")
        },
        historical_comparison=historical_comparison(report, historical),
        independent_sql_check="all seven native table populations, every field null/non-null/zero/empty denominator and all declared category bins match",
        chronology_admission=False,
        scientific_admission=False,
        canonical_source_adoption=False,
        rights_scope=descriptor["rights_status"],
        elapsed_seconds=time.monotonic() - started,
    )
    output.mkdir()
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    print(json.dumps(report["historical_comparison"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
