"""Strict semantic comparison without importing a normalization constructor."""

from __future__ import annotations

from collections import Counter
import csv
from decimal import Decimal
import io
import json
from typing import Any

LABELS = {
    "dating_basis": "locality_sample_coverage",
    "evidence_class": "locality_sample_coverage_hull",
    "precision_posture": "display_coverage_only",
}
HEADERS = (
    "schema_version",
    "chronology_role",
    "sample_ids",
    "sample_chronologies",
    "locality_token",
    "species_latin_name",
    "species_common_name",
    "project_accessions",
    "source_family",
    "source_releases",
    "record_modalities",
    "review_strengths",
    "provenance_qualities",
    "original_location_text",
    "locality",
    "political_entity",
    "latitude",
    "longitude",
    "latitude_text",
    "longitude_text",
    "coordinate_confidence",
    "chronology_text",
    "time_start_bp",
    "time_end_bp",
    "time_mean_bp",
    "dating_basis",
    "chronology_evidence_class",
    "chronology_precision_posture",
    "nordic_inclusion",
    "nordic_inclusion_reason",
    "interpretation_note",
)
CSV_LABELS = {
    "dating_basis": LABELS["dating_basis"],
    "chronology_evidence_class": LABELS["evidence_class"],
    "chronology_precision_posture": LABELS["precision_posture"],
}


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent locality coverage: " + message)


def decode(body: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "duplicate JSON member")
            result[key] = value
        return result

    def invalid(token: str) -> Any:
        raise ValueError("Nonfinite JSON constant: " + token)

    value = json.loads(
        body, parse_float=Decimal, parse_constant=invalid, object_pairs_hook=pairs
    )

    def finite(item: Any) -> None:
        if type(item) is Decimal:
            require(item.is_finite(), "finite JSON decimal")
        elif type(item) is dict:
            for child in item.values():
                finite(child)
        elif type(item) is list:
            for child in item:
                finite(child)

    finite(value)
    return value


def same(actual: Any, expected: Any) -> None:
    require(type(actual) is type(expected), "literal JSON type changed")
    if type(expected) is dict:
        require(actual.keys() == expected.keys(), "JSON field population changed")
        for key in expected:
            same(actual[key], expected[key])
    elif type(expected) is list:
        require(len(actual) == len(expected), "ordered JSON population changed")
        for first, second in zip(actual, expected, strict=True):
            same(first, second)
    else:
        require(actual == expected, "literal source field changed")
        if type(expected) is Decimal and expected == 0:
            require(actual.is_signed() == expected.is_signed(), "signed zero changed")


def csv_rows(body: bytes) -> list[dict[str, str]]:
    csv.field_size_limit(8 * 1024**2)
    reader = csv.DictReader(io.StringIO(body.decode("utf-8"), newline=""), strict=True)
    require(
        reader.fieldnames == list(HEADERS), "unchanged exact31-column v2 CSV schema"
    )
    result = list(reader)
    require(
        all(
            None not in row and all(type(x) is str for x in row.values())
            for row in result
        ),
        "CSV row field counts",
    )
    return result


def _csv_join(row: dict[str, str], locality: dict[str, Any], schema: str) -> None:
    for field in (
        "sample_ids",
        "project_accessions",
        "source_releases",
        "record_modalities",
        "review_strengths",
        "provenance_qualities",
    ):
        require(
            row[field] == ";".join(locality[field]), "CSV ordered source membership"
        )
    same(decode(row["sample_chronologies"].encode()), locality["sample_chronologies"])
    expected = {
        "schema_version": schema,
        "chronology_role": locality["chronology_role"],
        "locality_token": locality["identity"]["stable_token"],
        "species_latin_name": locality["species_latin_name"],
        "species_common_name": locality["species_common_name"],
        "source_family": locality["source_family"],
        "original_location_text": locality["original_location_text"],
        "locality": locality["locality"] or "",
        "political_entity": locality["identity"]["political_entity"] or "",
        "latitude_text": locality["coordinates"]["latitude_text"],
        "longitude_text": locality["coordinates"]["longitude_text"],
        "coordinate_confidence": locality["coordinates"]["confidence"],
        "chronology_text": locality["chronology"]["original_text"],
        "dating_basis": locality["chronology"]["dating_basis"],
        "chronology_evidence_class": locality["chronology"]["evidence_class"],
        "chronology_precision_posture": locality["chronology"]["precision_posture"],
        "nordic_inclusion": str(locality["nordic_inclusion"]),
        "nordic_inclusion_reason": locality["nordic_inclusion_reason"],
        "interpretation_note": locality["interpretation_note"],
    }
    require(
        all(row[key] == value for key, value in expected.items()),
        "CSV source metadata disagreement",
    )
    numeric = {
        **{key: locality["coordinates"][key] for key in ("latitude", "longitude")},
        **{
            key: locality["chronology"][key]
            for key in ("time_start_bp", "time_end_bp", "time_mean_bp")
        },
    }
    for key, value in numeric.items():
        require(
            row[key] == ""
            if value is None
            else bool(row[key])
            and Decimal(row[key]).is_finite()
            and Decimal(row[key]) == value,
            "CSV source numeric value disagreement",
        )


def _supports(localities: list[dict[str, Any]], samples: list[dict[str, Any]]) -> int:
    source = {r["master_id"]: r for r in samples}
    require(
        len(source) == len(samples)
        and len({r["identity"]["stable_token"] for r in samples}) == len(samples),
        "unique sample owner identities",
    )
    seen = []
    for locality in localities:
        owners = locality["sample_ids"]
        require(
            len(owners) == len(set(owners)) == locality["sample_count"]
            and [s["sample_id"] for s in locality["sample_chronologies"]] == owners,
            "complete unique ordered locality support membership",
        )
        require(
            locality["chronology_role"] == "locality_sample_coverage_hull",
            "explicit display hull role",
        )
        for support in locality["sample_chronologies"]:
            owner = support["sample_id"]
            require(owner in source, "source-owned support only")
            sample = source[owner]
            require(
                sample["locality_identity"]["stable_token"]
                == locality["identity"]["stable_token"],
                "support joined to its own locality",
            )
            expected = {
                "schema_version": "adna-sample-chronology-support.v1",
                "sample_id": owner,
                "chronology": sample["chronology"],
                "source_release": sample["source_release"],
                "provenance_path": sample["chronology_provenance_path"],
                "provenance_locator": sample["chronology_provenance_locator"],
                "provenance_excerpt": sample["chronology_provenance_text"],
                "provenance_kind": sample["chronology_provenance_kind"],
                "chronology_strength": sample["chronology_strength"],
                "normalization_status": sample["chronology_normalization_status"],
                "conflict_note": sample["chronology_conflict_note"],
                **{
                    k: sample.get(k, "not_separately_declared")
                    for k in (
                        "reference_epoch",
                        "age_type",
                        "calibration_status",
                        "model",
                    )
                },
            }
            same(support, expected)
            seen.append(owner)
    require(
        len(seen) == len(set(seen)) == len(source) and set(seen) == source.keys(),
        "every sample has exactly one owned support",
    )
    return len(seen)


def compare_payloads(
    normalization: dict[str, Any],
    baseline: dict[str, bytes],
    candidate: dict[str, bytes],
    canonical_samples: bytes,
) -> dict[str, Any]:
    """Permit exactly three display-hull label changes and preserve all owned evidence."""
    require(
        set(baseline) == set(candidate) == {"locality_json", "locality_csv", "bundle"},
        "three exact normalized products",
    )
    same(normalization["allowed_aggregate_chronology_changes"], LABELS)
    old, new = decode(baseline["locality_json"]), decode(candidate["locality_json"])
    old_bundle, new_bundle = decode(baseline["bundle"]), decode(candidate["bundle"])
    canonical = decode(canonical_samples)
    same(old["schema_version"], "adna-locality-summary-export.v2")
    same(new["schema_version"], old["schema_version"])
    same(
        {k: v for k, v in old.items() if k != "localities"},
        {k: v for k, v in new.items() if k != "localities"},
    )
    require(
        old["species_latin_name"] == normalization["species_name"],
        "single declared species",
    )
    same(old_bundle["locality_records"], old["localities"])
    same(new_bundle["locality_records"], new["localities"])
    same(
        {k: v for k, v in old_bundle.items() if k != "locality_records"},
        {k: v for k, v in new_bundle.items() if k != "locality_records"},
    )
    same(new_bundle["sample_records"], canonical["samples"])
    samples = new_bundle["sample_records"]
    require(
        len(samples)
        == normalization["sample_count"]
        == canonical["admitted_sample_count"],
        "all specimen sample owners retained",
    )
    refusals = new_bundle["refusals"]
    kinds = dict(Counter(r["record_kind"] for r in refusals))
    require(
        len(refusals) == normalization["refusal_count"]
        and kinds
        == {
            "sample_record": normalization["sample_refusal_count"],
            "locality_records": normalization["locality_refusal_count"],
        },
        "all sample/locality refusals retained",
    )
    same(
        [r for r in refusals if r["record_kind"] == "sample_record"],
        canonical["sample_refusals"],
    )
    require(
        canonical["refused_sample_count"] == normalization["sample_refusal_count"],
        "canonical refusal denominator",
    )
    before, after = old["localities"], new["localities"]
    require(
        len(before) == len(after) == normalization["locality_count"]
        and len({r["identity"]["stable_token"] for r in before}) == len(before),
        "complete unique ordered locality identities",
    )
    old_csv, new_csv = (
        csv_rows(baseline["locality_csv"]),
        csv_rows(candidate["locality_csv"]),
    )
    require(len(old_csv) == len(new_csv) == len(after), "full CSV locality population")
    changes = 0
    for a, b, ar, br in zip(before, after, old_csv, new_csv, strict=True):
        same(
            {k: v for k, v in a.items() if k != "chronology"},
            {k: v for k, v in b.items() if k != "chronology"},
        )
        require(
            a["chronology"].keys() == b["chronology"].keys(),
            "no chronology field creation or removal",
        )
        same(
            {k: v for k, v in a["chronology"].items() if k not in LABELS},
            {k: v for k, v in b["chronology"].items() if k not in LABELS},
        )
        for key, value in LABELS.items():
            same(b["chronology"][key], value)
            require(
                a["chronology"][key] != value,
                "each declared old specimen label is corrected",
            )
            changes += 1
        for key in HEADERS:
            require(
                br[key] == CSV_LABELS[key] if key in CSV_LABELS else br[key] == ar[key],
                "only three CSV display labels may change",
            )
        _csv_join(ar, a, old["schema_version"])
        _csv_join(br, b, new["schema_version"])
    supports = _supports(after, samples)
    require(
        supports == normalization["sample_support_count"],
        "all source-owned supports retained",
    )
    return {
        "status": "passed",
        "species": normalization["species_name"],
        "sample_owners_verified": len(samples),
        "localities_verified": len(after),
        "individual_supports_verified": supports,
        "refusals_unchanged": len(refusals),
        "json_hull_label_changes": changes,
        "bundle_hull_label_changes": changes,
        "csv_hull_label_changes": changes,
        "all_other_fields_and_order_unchanged": True,
        "scope": "Display-only hull labels; exact specimen dates, identities, source ownership, coordinates, refusal and uncertainty metadata unchanged",
    }
