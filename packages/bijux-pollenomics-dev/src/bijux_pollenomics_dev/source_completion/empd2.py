"""Screen source-native EMPD2 Nordic rows without admitting benchmark data."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Any

COUNTRIES = {
    name.casefold(): name for name in ("Sweden", "Denmark", "Norway", "Finland")
}
REQUIRED_METADATA = {
    "samplename",
    "country",
    "longitude",
    "latitude",
    "agebp",
    "ageuncertainty",
    "ispercent",
    "isdigitised",
}
REQUIRED_COUNTS = {"samplename", "var_", "count"}


def file_sha256(path: Path) -> str:
    """Hash external custody bytes without copying them into the repository."""
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}


def _valid_count(value: object) -> tuple[bool, bool]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False, False
    number = float(value)
    return isfinite(number) and number >= 0 and number.is_integer(), number > 0


def _overlap_leads(path: Path | None, expected_sha256: str | None) -> dict[str, str]:
    if path is None:
        if expected_sha256 is not None:
            raise ValueError("overlap_digest_without_file")
        return {}
    content = path.read_bytes()
    if (
        expected_sha256 is None
        or hashlib.sha256(content).hexdigest() != expected_sha256
    ):
        raise ValueError("overlap_digest_mismatch")
    leads: dict[str, str] = {}
    for line in content.decode("utf-8").splitlines():
        row = json.loads(line)
        if row["identity_decision"] != "unresolved_hypothesis":
            raise ValueError("unreviewed_overlap_decision")
        name = row["empd_samplename"]
        if name in leads:
            raise ValueError("duplicate_overlap_sample")
        leads[name] = row["empd_country"]
    return leads


def screen_empd2(
    source: Path,
    expected_sha256: str,
    *,
    overlap_review: Path | None = None,
    overlap_sha256: str | None = None,
) -> dict[str, Any]:
    """Return four-country, sample-owned count decisions on pinned source bytes.

    Mechanical count eligibility is distinct from chronology, PPE, basin,
    physical identity, vegetation truth and scientific admission.
    """
    if len(expected_sha256) != 64 or file_sha256(source) != expected_sha256:
        raise ValueError("source_digest_mismatch")
    overlap = _overlap_leads(overlap_review, overlap_sha256)
    db = sqlite3.connect(source.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only = ON")
        if (
            _columns(db, "metadata") < REQUIRED_METADATA
            or _columns(db, "p_counts") < REQUIRED_COUNTS
        ):
            raise ValueError("unsupported_empd2_schema")
        samples: dict[str, dict[str, Any]] = {}
        all_sample_names: set[str] = set()
        all_metadata_rows = 0
        for row in db.execute(
            "SELECT samplename,country,longitude,latitude,agebp,ageuncertainty,"
            "ispercent,isdigitised FROM metadata"
        ):
            all_metadata_rows += 1
            name = row["samplename"]
            if not isinstance(name, str) or not name or name in all_sample_names:
                raise ValueError("invalid_or_duplicate_source_sample_identity")
            all_sample_names.add(name)
            country = COUNTRIES.get(str(row["country"] or "").strip().casefold())
            if country is None:
                continue
            samples[name] = {
                "source_sample_name": name,
                "source_country": row["country"],
                "country": country,
                "source_longitude": row["longitude"],
                "source_latitude": row["latitude"],
                "source_agebp": row["agebp"],
                "source_ageuncertainty": row["ageuncertainty"],
                "source_ispercent": row["ispercent"],
                "source_isdigitised": row["isdigitised"],
                "count_rows": 0,
                "positive_integer_count_rows": 0,
                "invalid_count_rows": [],
            }
        for row in db.execute('SELECT samplename,var_,"count" FROM p_counts'):
            sample = samples.get(row["samplename"])
            if sample is None:
                continue
            sample["count_rows"] += 1
            valid, positive = _valid_count(row["count"])
            sample["positive_integer_count_rows"] += int(valid and positive)
            if not valid:
                sample["invalid_count_rows"].append(
                    {
                        "source_var_id": row["var_"],
                        "source_count": row["count"],
                        "reason_code": "not_finite_nonnegative_integer_count",
                    }
                )
        if not overlap.keys() <= samples.keys():
            raise ValueError("overlap_sample_absent_from_nordic_source")
        if any(
            samples[name]["country"] != country for name, country in overlap.items()
        ):
            raise ValueError("overlap_country_disagrees_with_source")
        country_counts: dict[str, Counter[str]] = {
            name: Counter() for name in COUNTRIES.values()
        }
        for name, sample in sorted(samples.items()):
            reasons = []
            if sample["count_rows"] == 0:
                reasons.append("no_count_rows")
            if sample["invalid_count_rows"]:
                reasons.append("invalid_count_value")
            if sample["positive_integer_count_rows"] == 0:
                reasons.append("no_positive_integer_count")
            if sample["source_ispercent"] != 0:
                reasons.append("source_percent_flag_not_zero")
            if sample["source_isdigitised"] != 0:
                reasons.append("source_digitised_flag_not_zero")
            sample["mechanical_count_candidate"] = not reasons
            if name in overlap:
                reasons.append("cross_source_identity_unresolved")
            sample["review_reason_codes"] = reasons
            sample["scientific_admission"] = "candidate_only"
            counter = country_counts[sample["country"]]
            counter["metadata_samples"] += 1
            counter["count_rows"] += sample["count_rows"]
            counter["invalid_count_rows"] += len(sample["invalid_count_rows"])
            counter["mechanical_count_candidates"] += int(
                sample["mechanical_count_candidate"]
            )
            counter["unresolved_overlap_samples"] += int(name in overlap)
        if file_sha256(source) != expected_sha256:
            raise ValueError("source_changed_during_screen")
        return {
            "schema_version": "empd2-nordic-candidate-screen.v1",
            "source_sha256": expected_sha256,
            "source_bytes": source.stat().st_size,
            "overlap_review_sha256": overlap_sha256,
            "source_metadata_rows_all_countries": all_metadata_rows,
            "nordic_sample_count": len(samples),
            "overlap_review_complete": overlap_review is not None,
            "country_counts": {
                country: dict(country_counts[country]) for country in COUNTRIES.values()
            },
            "samples": [samples[name] for name in sorted(samples)],
            "scientific_admission": "candidate_only",
            "measured_vegetation_reference_count": 0,
            "note": "Count screen only; source age is not a collection date, and no taxon/PPE, basin, rights-for-join, cross-source identity or measured vegetation review is implied.",
        }
    finally:
        db.close()


def main() -> int:
    """Write a new, atomic candidate screen while keeping source custody external."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--overlap-review", type=Path)
    parser.add_argument("--overlap-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = screen_empd2(
        args.source,
        args.sha256,
        overlap_review=args.overlap_review,
        overlap_sha256=args.overlap_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=args.output.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(report, handle, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            os.link(temporary, args.output)
        finally:
            temporary.unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "nordic_sample_count": report["nordic_sample_count"],
                "country_counts": report["country_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
