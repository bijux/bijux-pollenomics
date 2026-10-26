"""Account for every native geometry payload and check it against NumPy blocks."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import time
from typing import TextIO, cast

from bijux_pollenomics.collection.sources.raa.geometry.rows import (
    iter_geometry_documents,
)
from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    GEOMETRY_TYPES,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    quote_identifier,
    read_only_database,
)
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .geometry_oracle import coordinate_summary


def scan(
    connection: sqlite3.Connection,
    refused: TextIO,
    *,
    deadline: float | None = None,
    refusal_byte_limit: int = 16 * 1024 * 1024,
) -> dict[str, object]:
    """Compare independently read native blobs without storing accepted row copies."""
    raw = {
        table: connection.execute(
            f"SELECT fid,geometri FROM {quote_identifier(table)} ORDER BY fid"
        )
        for table in GEOMETRY_TYPES
    }
    crossed: dict[str, Counter[str]] = {table: Counter() for table in GEOMETRY_TYPES}
    totals: dict[str, Counter[str]] = {table: Counter() for table in GEOMETRY_TYPES}
    crs: dict[str, object] | None = None
    summary: dict[str, object] | None = None
    checks = byte_count = occurrences = 0
    for document in iter_geometry_documents(connection):
        if document["kind"] == "source_profile":
            crs = cast(dict[str, object], document["crs"])
            continue
        if document["kind"] == "summary":
            summary = document
            continue
        occurrences += 1
        if (
            occurrences % 1024 == 0
            and deadline is not None
            and time.monotonic() > deadline
        ):
            raise TimeoutError("national geometry wall budget exceeded")
        table = str(document["table"])
        original = raw[table].fetchone()
        if original is None or original["fid"] != document["fid"]:
            raise ValueError("independent native geometry identity population differs")
        geometry = cast(dict[str, object], document["geometry"])
        compared_geometry = {
            **geometry,
            "linestring_component_count": int(table == "linestring"),
        }
        maintained_status = str(geometry["status"])
        blob = original["geometri"]
        oracle: dict[str, object] | None = None
        oracle_reason: str | None = None
        if blob is None:
            independent_status = "source_null"
        elif not isinstance(blob, bytes):
            independent_status = "refused"
            oracle_reason = "independent_non_blob_geometry"
        else:
            try:
                oracle = coordinate_summary(blob, GEOMETRY_TYPES[table])
                independent_status = (
                    "accepted_empty"
                    if oracle["coordinate_count"] == 0
                    else "accepted_nonempty"
                )
            except ValueError as error:
                independent_status = "refused"
                oracle_reason = str(error)
        crossed[table][maintained_status + ":" + independent_status] += 1
        accepted = maintained_status in {
            "structurally_valid_nonempty",
            "structurally_valid_empty",
        }
        mismatch = accepted and (
            oracle is None
            or any(compared_geometry[key] != value for key, value in oracle.items())
        )
        if not accepted or mismatch:
            witness = {
                key: document[key]
                for key in ("table", "fid", "source_fields", "geometry")
            }
            witness.update(
                independent_status=independent_status,
                independent_reason=oracle_reason,
                independent_summary=oracle,
                mismatch=mismatch,
            )
            line = json.dumps(witness, ensure_ascii=False, allow_nan=False) + "\n"
            byte_count += len(line.encode())
            if byte_count > refusal_byte_limit:
                raise ValueError("national geometry refusal output byte limit exceeded")
            refused.write(line)
            refused.flush()
        if mismatch:
            raise ValueError(
                "independent geometry coordinate or structure comparison differs"
            )
        if accepted:
            checks += 1
            for key in (
                "coordinate_count",
                "ring_count",
                "polygon_count",
                "empty_polygon_count",
                "linestring_component_count",
                "zero_coordinate_values",
            ):
                totals[table][key] += cast(int, compared_geometry[key])
    if summary is None or crs is None or occurrences != summary["geometry_occurrences"]:
        raise ValueError("complete national geometry summary absent")
    for cursor in raw.values():
        if cursor.fetchone() is not None:
            raise ValueError("independent geometry source contains extra occurrences")
    return {
        "native_geometry_summary": summary,
        "crs": crs,
        "independent_status_cross_counts": {
            key: dict(sorted(value.items())) for key, value in crossed.items()
        },
        "accepted_geometry_coordinate_structure_totals": {
            key: dict(sorted(value.items())) for key, value in totals.items()
        },
        "independently_compared_geometry_occurrences": checks,
        "private_refusal_witness_bytes": byte_count,
        "comparison": "Independent NumPy binary blocks versus maintained scalar GP/WKB reader; exact coordinate/ring/polygon/empty-polygon/zero counts, numeric extrema, finite coordinates, ring closure, 2D declared types and optional source envelopes. No topology, coordinate accuracy, center-point or scientific admission.",
        "geometry_roles": {
            table: "positional_uncertainty"
            if table == "lämningar_sverige_lägesosäkerhet"
            else "native_remains_geometry"
            for table in GEOMETRY_TYPES
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = require_absent_artifact_output(args.repository, args.output)
    descriptor = json.loads(
        (args.repository / "data/raa/raw/national_geopackage_source.json").read_bytes()
    )
    started = time.monotonic()
    deadline = started + 1200
    with read_only_database(
        args.source,
        expected_sha256=descriptor["sha256"],
        expected_byte_count=descriptor["byte_count"],
    ) as connection:
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
        output.mkdir()
        with (output / "refused.ndjson").open("x") as refused:
            report = scan(connection, refused, deadline=deadline)
    report.update(
        source_identity={
            key: descriptor[key]
            for key in ("sha256", "byte_count", "captured_at_utc", "http_last_modified")
        },
        elapsed_seconds=time.monotonic() - started,
    )
    payload = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if len(payload.encode()) > 100 * 1024:
        raise ValueError("national geometry compact summary byte limit exceeded")
    (output / "report.json").write_text(payload)
    print(json.dumps(report["native_geometry_summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
