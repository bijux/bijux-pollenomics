"""Content-bound review of SEAD source-age meaning for typed chronology claims."""

from __future__ import annotations

from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

SOURCE_RUN_ID = "sead-full-evidence-39bfff6a-ce80714e"
PINNED_CLAIM_INDEX_SHA256 = (
    "b9accf421059eebf95b75a8c22fd237f4d51991fbc868e79530d20a694e6cd21"
)
EXPECTED_CLAIM_COUNT = 25_109
_NATIVE_FIELDS = {
    "dating_range": (
        "tbl_analysis_dating_ranges",
        "analysis_dating_range_id",
        ("age_type_id", "low_value", "high_value"),
    ),
    "dendrochronology": (
        "tbl_dendro_dates",
        "dendro_date_id",
        ("age_type_id", "age_older", "age_younger"),
    ),
    "relative_period": (
        "tbl_relative_dates",
        "relative_date_id",
        ("relative_age_id",),
    ),
    "geochronology": (
        "tbl_geochronology",
        "geochron_id",
        ("age", "error_older", "error_younger"),
    ),
    "analysis_entity_age": (
        "tbl_analysis_entity_ages",
        "analysis_entity_age_id",
        ("age", "age_older", "age_younger", "chronology_id"),
    ),
}
_CONTEXT = {
    "relative_period": (
        "relative_period",
        "source_relative_period",
        "not_calibrated",
        "context_only",
        "relative_period_requires_governed_mapping",
    ),
    "geochronology": (
        "radiometric_age_unspecified",
        "source_years",
        "unknown",
        "context_only",
        "geochronology_calibration_posture_unknown",
    ),
    "analysis_entity_age": (
        "analysis_entity_age_unspecified",
        "source_years",
        "unknown",
        "unresolved",
        "analysis_entity_age_basis_unspecified",
    ),
}
_REVIEW_FIELDS = (
    "chronology_claim_id",
    "claim_type",
    "source_table",
    "source_record_id",
    "source_age_type",
    "source_age_unit",
    "source_age_type_id",
    "native_year_values",
    "captured_bp_endpoints",
    "reviewed_age_basis",
    "comparability_status",
    "chronology_eligibility",
    "publication_role",
    "propagation_eligibility",
    "uncertainty_label",
    "reason_codes",
)


def _sha(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _document(
    path: Path, expected_sha256: str | None = None
) -> tuple[dict[str, Any], str]:
    payload = path.read_bytes()
    digest = _sha(payload)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"SEAD content digest changed: {path}")
    document: dict[str, Any] = json.loads(payload)
    if not isinstance(document, dict):
        raise TypeError(f"SEAD document must be an object: {path}")
    return document, digest


def _integral(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"SEAD {label} must be an integral native number")
    if not float(value).is_integer():
        raise ValueError(f"SEAD {label} must be an integral native number")
    return int(value)


def _source_row_map(
    raw_root: Path, table: str, id_field: str, expected_digest: str
) -> tuple[dict[int, dict[str, Any]], dict[str, object]]:
    path = raw_root / f"payloads/{table}.json"
    document, digest = _document(path, expected_digest)
    if (
        document.get("schema_version") != "sead-table-payload.v1"
        or document.get("table") != table
    ):
        raise ValueError(f"SEAD source table identity changed: {table}")
    rows = document.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise TypeError(f"SEAD source table rows invalid: {table}")
    by_id = {_integral(row[id_field], id_field): row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError(f"SEAD source table IDs duplicated: {table}")
    return by_id, {
        "path": f"data/sead/raw/acquisitions/{SOURCE_RUN_ID}/payloads/{table}.json",
        "sha256": digest,
        "row_count": len(rows),
    }


def review_claim_age_basis(
    claim: dict[str, Any],
    native: dict[str, Any],
    *,
    age_type: dict[str, Any],
    source_payload_sha256: str,
    source_build_id: str,
    acquisition_manifest_sha256: str,
) -> dict[str, str]:
    """Compare a claim with independent native age values and governed type ID."""
    kind = str(claim.get("claim_type"))
    if kind not in _NATIVE_FIELDS:
        raise ValueError(f"SEAD chronology claim kind unreviewed: {kind}")
    table, id_field, native_fields = _NATIVE_FIELDS[kind]
    claim_id = str(claim.get("chronology_claim_id"))
    source = claim.get("source_age_value")
    if not isinstance(source, dict):
        raise TypeError(f"SEAD claim source age is not an object: {claim_id}")
    if (
        claim.get("schema_version") != "sead-chronology-claim.v1"
        or claim.get("source_family") != "sead"
        or claim.get("source_table") != table
        or claim.get("source_record_id") != str(native[id_field])
        or claim.get("source_native_record_id") != str(native[id_field])
        or claim.get("source_payload_sha256") != source_payload_sha256
        or claim.get("build_id") != source_build_id
        or claim.get("acquisition_manifest_sha256") != acquisition_manifest_sha256
        or not claim_id.endswith(f":{kind}:{native[id_field]}")
    ):
        raise ValueError(f"SEAD claim source identity changed: {claim_id}")
    for field in (id_field, *native_fields):
        if source.get(field) != native.get(field):
            raise ValueError(f"SEAD native age field changed: {claim_id}:{field}")
    if (
        claim.get("propagation_eligibility") != "refused"
        or claim.get("selection_status") != "retained_unselected"
    ):
        raise ValueError(
            f"SEAD claim gained unsupported propagation or selection: {claim_id}"
        )
    if kind in {"dating_range", "dendrochronology"}:
        if (
            age_type.get("age_type_id") != 1
            or age_type.get("age_type") != "AD"
            or source.get("age_type_id") != 1
            or source.get("age_type") != "AD"
            or claim.get("source_age_type") != "AD"
            or claim.get("source_age_unit") != "calendar_year"
            or claim.get("calibration_status") != "not_applicable"
            or claim.get("transformation_id") != "sead-calendar-year-to-cal-bp-1950-v1"
        ):
            raise ValueError(f"SEAD AD age-type authority changed: {claim_id}")
        if "age_type_description" in source and source[
            "age_type_description"
        ] != age_type.get("description"):
            raise ValueError(f"SEAD AD age-type description changed: {claim_id}")
        fields = (
            ("low_value", "high_value")
            if kind == "dating_range"
            else ("age_older", "age_younger")
        )
        years = [
            _integral(native[field], field)
            for field in fields
            if native.get(field) is not None
        ]
        if not years:
            raise ValueError(f"SEAD AD claim lacks native calendar year: {claim_id}")
        expected = sorted(1950 - year for year in years)
        expected_interval = (expected[0], expected[-1])
        captured = tuple(
            sorted(
                (
                    _integral(source.get("time_start_bp"), "time_start_bp"),
                    _integral(source.get("time_end_bp"), "time_end_bp"),
                )
            )
        )
        if captured != expected_interval:
            raise ValueError(f"SEAD AD conversion differs from native year: {claim_id}")
        open_ended = (
            kind == "dendrochronology" and native.get("dating_uncertainty_id") == 4
        )
        if open_ended and (
            source.get("uncertainty_label") != "From"
            or native.get("age_younger") is not None
        ):
            raise ValueError(f"SEAD open-ended dendro source changed: {claim_id}")
        negative = expected_interval[0] < 0
        expected_status = (
            "context_only" if open_ended else "refused" if negative else "comparable"
        )
        expected_eligibility = "refused" if open_ended or negative else "eligible"
        expected_reasons = (
            {"open_ended_dendro_from_uncertainty", "chronology_not_comparable"}
            if open_ended
            else {"negative_bp", "chronology_not_comparable"}
            if negative
            else set()
        )
        expected_published = (
            "review_only" if open_ended or negative else "chronology_display_only"
        )
        if (
            claim.get("comparability_status") != expected_status
            or claim.get("chronology_eligibility") != expected_eligibility
            or claim.get("publication_role") != expected_published
            or set(claim.get("reason_codes", [])) != expected_reasons
            or claim.get("younger_bp")
            != (None if open_ended or negative else expected_interval[0])
            or claim.get("older_bp")
            != (None if open_ended or negative else expected_interval[1])
        ):
            raise ValueError(f"SEAD AD claim status or interval changed: {claim_id}")
        basis = (
            "ad_calendar_year_open_ended_from_context"
            if open_ended
            else "ad_calendar_year_negative_bp_refused"
            if negative
            else "ad_calendar_year_to_1950_bp"
        )
        native_year_values = ";".join(str(year) for year in years)
        captured_bp = f"{captured[0]};{captured[1]}"
    else:
        source_type, unit, calibration, comparability, reason = _CONTEXT[kind]
        if (
            claim.get("source_age_type") != source_type
            or claim.get("source_age_unit") != unit
            or claim.get("calibration_status") != calibration
            or claim.get("comparability_status") != comparability
            or claim.get("chronology_eligibility") != "refused"
            or claim.get("publication_role") != "review_only"
            or claim.get("transformation_id") is not None
            or claim.get("younger_bp") is not None
            or claim.get("older_bp") is not None
            or set(claim.get("reason_codes", []))
            != {reason, "chronology_not_comparable"}
        ):
            raise ValueError(
                f"SEAD contextual age gained unsupported numeric status: {claim_id}"
            )
        basis = reason
        native_year_values = ""
        captured_bp = ";".join(
            str(source.get(field, "")) for field in ("time_start_bp", "time_end_bp")
        )
    return {
        "chronology_claim_id": claim_id,
        "claim_type": kind,
        "source_table": table,
        "source_record_id": str(native[id_field]),
        "source_age_type": str(claim["source_age_type"]),
        "source_age_unit": str(claim["source_age_unit"]),
        "source_age_type_id": str(source.get("age_type_id") or ""),
        "native_year_values": native_year_values,
        "captured_bp_endpoints": captured_bp,
        "reviewed_age_basis": basis,
        "comparability_status": str(claim["comparability_status"]),
        "chronology_eligibility": str(claim["chronology_eligibility"]),
        "publication_role": str(claim["publication_role"]),
        "propagation_eligibility": str(claim["propagation_eligibility"]),
        "uncertainty_label": str(source.get("uncertainty_label") or ""),
        "reason_codes": ";".join(sorted(claim["reason_codes"])),
    }


def build_sead_chronology_age_review(
    data_root: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Review all pinned claim parts against raw source age rows and type authority."""
    acquisition = data_root / "sead/raw/acquisitions" / SOURCE_RUN_ID
    normalized = data_root / "sead/normalized/acquisitions" / SOURCE_RUN_ID
    index, index_digest = _document(
        normalized / "chronology_claims.json", PINNED_CLAIM_INDEX_SHA256
    )
    admission, admission_digest = _document(acquisition / "admission.json")
    _, manifest_digest = _document(
        acquisition / "manifest.json", index["acquisition_manifest_sha256"]
    )
    if (
        index.get("source_run_id") != SOURCE_RUN_ID
        or index.get("claim_count") != EXPECTED_CLAIM_COUNT
        or admission.get("run_id") != SOURCE_RUN_ID
        or admission.get("build_id") != index.get("source_build_id")
        or admission.get("acquisition_manifest_sha256") != manifest_digest
        or admission.get("scope_id") != index.get("source_scope_id")
    ):
        raise ValueError("SEAD pinned chronology source lineage changed")
    table_digests = index["table_payload_sha256"]
    age_types, age_digest = _source_row_map(
        acquisition, "tbl_age_types", "age_type_id", table_digests["tbl_age_types"]
    )
    if set(age_types) != {1} or age_types[1].get("age_type") != "AD":
        raise ValueError("SEAD age-type authority changed")
    native_tables: dict[str, dict[int, dict[str, Any]]] = {}
    source_files: list[dict[str, object]] = [age_digest]
    for kind, (table, id_field, _) in _NATIVE_FIELDS.items():
        native_tables[kind], identity = _source_row_map(
            acquisition, table, id_field, table_digests[table]
        )
        source_files.append(identity)
    part_descriptors = index["partitioned_fields"]["claims"]["parts"]
    if len(part_descriptors) != 6:
        raise ValueError("SEAD pinned claim part count changed")
    reviews: list[dict[str, str]] = []
    observed_ids: set[str] = set()
    observed_native_ids: dict[str, set[int]] = {kind: set() for kind in _NATIVE_FIELDS}
    part_files: list[dict[str, object]] = []
    claims_by_type: Counter[str] = Counter()
    comparability: Counter[str] = Counter()
    eligibility: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    basis_counts: Counter[str] = Counter()
    uncertainty: Counter[str] = Counter()
    gold_examples: dict[str, dict[str, str]] = {}
    for descriptor in part_descriptors:
        relative = descriptor["path"]
        part, digest = _document(normalized / relative, descriptor["sha256"])
        claims = part.get("claims")
        if (
            part.get("schema_version") != "sead-evidence-multipart.v1"
            or part.get("field") != "claims"
            or part.get("logical_document") != "chronology_claims.json"
            or part.get("part_number") != descriptor["part_number"]
            or part.get("row_start") != descriptor["row_start"]
            or part.get("row_end") != descriptor["row_end"]
            or not isinstance(claims, list)
            or len(claims) != descriptor["row_count"]
            or descriptor["row_end"] - descriptor["row_start"] != len(claims)
            or descriptor["row_start"] != len(reviews)
        ):
            raise ValueError(f"SEAD claim partition identity changed: {relative}")
        for claim in claims:
            if not isinstance(claim, dict):
                raise TypeError("SEAD chronology claim must be an object")
            kind = str(claim.get("claim_type"))
            if kind not in _NATIVE_FIELDS:
                raise ValueError(f"SEAD claim type unreviewed: {kind}")
            source_id = _integral(
                int(str(claim.get("source_record_id"))), "source_record_id"
            )
            native = native_tables[kind].get(source_id)
            if native is None:
                raise ValueError(f"SEAD claim native row missing: {kind}:{source_id}")
            review = review_claim_age_basis(
                claim,
                native,
                age_type=age_types[1],
                source_payload_sha256=table_digests[_NATIVE_FIELDS[kind][0]],
                source_build_id=index["source_build_id"],
                acquisition_manifest_sha256=manifest_digest,
            )
            claim_id = review["chronology_claim_id"]
            if claim_id in observed_ids:
                raise ValueError(f"SEAD chronology claim ID duplicated: {claim_id}")
            if source_id in observed_native_ids[kind]:
                raise ValueError(
                    f"SEAD native chronology row reviewed twice: {kind}:{source_id}"
                )
            observed_ids.add(claim_id)
            observed_native_ids[kind].add(source_id)
            reviews.append(review)
            claims_by_type[kind] += 1
            comparability[review["comparability_status"]] += 1
            eligibility[review["chronology_eligibility"]] += 1
            basis_counts[review["reviewed_age_basis"]] += 1
            for reason in claim["reason_codes"]:
                reasons[str(reason)] += 1
            if review["uncertainty_label"]:
                uncertainty[f"{kind}:{review['uncertainty_label']}"] += 1
            gold_key = f"{kind}:{review['reviewed_age_basis']}"
            if gold_key not in gold_examples:
                gold_examples[gold_key] = review
        part_files.append(
            {
                "path": f"data/sead/normalized/acquisitions/{SOURCE_RUN_ID}/{relative}",
                "sha256": digest,
                "row_count": len(claims),
            }
        )
    if any(
        observed_native_ids[kind] != set(rows) for kind, rows in native_tables.items()
    ):
        raise ValueError("SEAD native chronology rows are missing from claim review")
    if (
        len(reviews) != EXPECTED_CLAIM_COUNT
        or dict(claims_by_type) != index["claim_type_counts"]
        or dict(comparability) != index["comparability_counts"]
        or dict(eligibility) != index["chronology_eligibility_counts"]
        or dict(reasons) != index["refusal_reason_counts"]
    ):
        raise ValueError(
            "SEAD chronology review denominators differ from pinned claim index"
        )
    report: dict[str, Any] = {
        "schema_version": "sead-chronology-age-review.v1",
        "requirement_id": "SEAD-003",
        "source_run_id": SOURCE_RUN_ID,
        "source_build_id": index["source_build_id"],
        "claim_count": len(reviews),
        "claim_type_counts": dict(sorted(claims_by_type.items())),
        "comparability_counts": dict(sorted(comparability.items())),
        "chronology_eligibility_counts": dict(sorted(eligibility.items())),
        "reviewed_age_basis_counts": dict(sorted(basis_counts.items())),
        "refusal_reason_counts": dict(sorted(reasons.items())),
        "nonempty_uncertainty_label_counts": dict(sorted(uncertainty.items())),
        "gold_examples": dict(sorted(gold_examples.items())),
        "age_type_authority": age_types[1],
        "input_hashes": {
            "claim_index_sha256": index_digest,
            "admission_sha256": admission_digest,
            "manifest_sha256": manifest_digest,
            "source_tables": source_files,
            "claim_parts": part_files,
        },
        "review_posture": {
            "typed_age_basis_verified_for_all_claims": True,
            "scientific_chronology_admission_approved": False,
            "event_propagation_approved": False,
            "qualified_uncertainty_review_complete": False,
            "reason": "Source age type and native-value conversion were checked; contextual, unresolved, negative-BP and qualified open-ended dates were not promoted to independent event evidence.",
        },
    }
    return report, reviews


def write_sead_chronology_age_review(data_root: Path, output: Path) -> dict[str, Any]:
    """Retain grouped findings and one review decision for every pinned claim."""
    if output.exists():
        raise ValueError("SEAD chronology age review output must be absent")
    report, reviews = build_sead_chronology_age_review(data_root)
    output.mkdir(parents=True)
    with (output / "claims.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=_REVIEW_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(reviews)
    csv_bytes = (output / "claims.csv").read_bytes()
    report["claim_review_csv"] = {
        "path": "claims.csv",
        "sha256": _sha(csv_bytes),
        "row_count": len(reviews),
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    return report
