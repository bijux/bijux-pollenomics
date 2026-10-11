"""Resolve source context and publications for nearby EMPD2–NFI leads."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Any, cast

_MAX_DISTANCE_M = 1_000
_METADATA_FIELDS = (
    "samplename",
    "originalsamplename",
    "sitename",
    "country",
    "longitude",
    "latitude",
    "locationreliability",
    "locationnotes",
    "areaofsite",
    "samplecontext",
    "sampletype",
    "samplemethod",
    "agebp",
    "ageuncertainty",
    "notes",
    "empd_version",
)


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def source_dossier(
    sqlite_path: Path,
    source_sha256: str,
    spatial_report_path: Path,
    spatial_sha256: str,
) -> dict[str, object]:
    """Keep exact source fields, age codes and citations without pairing labels."""
    if _digest(sqlite_path) != source_sha256:
        raise ValueError("source_digest_mismatch")
    if _digest(spatial_report_path) != spatial_sha256:
        raise ValueError("spatial_report_digest_mismatch")
    spatial = cast(
        dict[str, Any], json.loads(spatial_report_path.read_text(encoding="utf-8"))
    )
    if (
        spatial.get("schema_version") != "empd2-nfi-spatial-feasibility.v2"
        or spatial.get("scientific_admission") != "candidate_only"
        or spatial.get("source_hashes", {}).get("empd2_source") != source_sha256
    ):
        raise ValueError("spatial_report_posture_mismatch")
    nearest = spatial.get("nearest_nfi_row_by_pollen_sample")
    if not isinstance(nearest, list) or len(nearest) != spatial.get(
        "swedish_pollen_samples"
    ):
        raise ValueError("spatial_report_sample_denominator_mismatch")
    selected = [
        row
        for row in nearest
        if isinstance(row, dict)
        and row.get("distance_m_wgs84", float("inf")) <= _MAX_DISTANCE_M
    ]
    if len(selected) != spatial.get("thresholds_descriptive_only", {}).get(
        "1000", {}
    ).get("pollen_samples") or len({row["pollen_sample"] for row in selected}) != len(
        selected
    ):
        raise ValueError("spatial_selection_denominator_mismatch")

    db = sqlite3.connect(
        sqlite_path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True
    )
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only = ON")
        columns = {row[1] for row in db.execute("PRAGMA table_info(metadata)")}
        if not set(_METADATA_FIELDS) <= columns or any(
            key in column.casefold()
            for column in columns
            for key in ("collect", "date", "year")
        ):
            raise ValueError("metadata_schema_requires_timing_review")
        uncertainty = {
            row["ageuncertainty"]: {
                "source_age_range_label": row["age"],
                "source_description": row["description"],
            }
            for row in db.execute(
                "SELECT ageuncertainty, age, description FROM ageuncertainties"
            )
        }
        rows: list[dict[str, object]] = []
        age_codes: Counter[str] = Counter()
        age_values: Counter[str] = Counter()
        samples_with_publication = 0
        collection_note_leads = 0
        for lead in sorted(selected, key=lambda row: row["pollen_sample"]):
            name = lead["pollen_sample"]
            found = db.execute(
                "SELECT "
                + ",".join(_METADATA_FIELDS)
                + " FROM metadata WHERE samplename=?",
                (name,),
            ).fetchall()
            if len(found) != 1:
                raise ValueError("source_sample_identity_mismatch")
            source = dict(found[0])
            if (
                source["country"] != "Sweden"
                or source["agebp"] != lead["pollen_agebp_source_native"]
                or source["ageuncertainty"]
                != lead["pollen_ageuncertainty_source_native"]
            ):
                raise ValueError("source_chronology_or_country_mismatch")
            citations = [
                dict(item)
                for item in db.execute(
                    "SELECT mp.publiid,p.doi,p.reference FROM metapubli AS mp "
                    "LEFT JOIN publications AS p ON p.publiid=mp.publiid "
                    "WHERE mp.samplename=? ORDER BY mp.publiid",
                    (name,),
                )
            ]
            age_codes[str(source["ageuncertainty"])] += 1
            native_age = source["agebp"]
            age_values[
                "numeric"
                if isinstance(native_age, (int, float))
                else "missing_or_source_text"
            ] += 1
            samples_with_publication += bool(citations)
            source_note = source["notes"]
            collection_note = (
                source_note
                if isinstance(source_note, str) and "collect" in source_note.casefold()
                else None
            )
            collection_note_leads += collection_note is not None
            rows.append(
                {
                    "spatial_lead": lead,
                    "source_metadata_excluding_vegdescription": source,
                    "source_age_uncertainty_lookup": uncertainty.get(
                        source["ageuncertainty"]
                    ),
                    "source_publications": citations,
                    "publication_link_count": len(citations),
                    "collection_time_source_note": collection_note,
                    "collection_time_status": (
                        "source_note_requires_review"
                        if collection_note is not None
                        else "not_authenticated_from_source_fields"
                    ),
                    "independent_vegetation_pair_admission": False,
                }
            )
        if _digest(sqlite_path) != source_sha256:
            raise ValueError("source_changed_during_dossier")
        return {
            "schema_version": "empd2-nfi-source-dossier.v1",
            "source_sha256": source_sha256,
            "spatial_report_sha256": spatial_sha256,
            "selection": "unrounded distance_m_wgs84 <= 1000; descriptive source review only",
            "source_metadata_columns": list(_METADATA_FIELDS),
            "source_explicit_collection_date_column": None,
            "selected_lead_count": len(rows),
            "samples_with_publication_links": samples_with_publication,
            "samples_with_collection_note_cues": collection_note_leads,
            "source_age_uncertainty_counts": dict(sorted(age_codes.items())),
            "source_age_value_kinds": dict(sorted(age_values.items())),
            "rows": rows,
            "scientific_admission": "candidate_only",
            "independent_vegetation_pair_count": 0,
        }
    finally:
        db.close()


def main() -> None:
    """Publish one source-bound, no-replace review dossier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--spatial-report", type=Path, required=True)
    parser.add_argument("--spatial-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = source_dossier(
        args.source, args.source_sha256, args.spatial_report, args.spatial_sha256
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=args.output.parent,
            prefix=f".{args.output.name}.pending-",
            delete=False,
        ) as stream:
            stage = Path(stream.name)
            json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(stage, args.output)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
    print(json.dumps({"leads": report["selected_lead_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
