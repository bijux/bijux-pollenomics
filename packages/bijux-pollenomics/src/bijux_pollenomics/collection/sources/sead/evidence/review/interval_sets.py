"""Bind pinned SEAD chronology claims to separate exported record intervals."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .chronology_claims import (
    EXPECTED_CLAIM_COUNT,
    PINNED_CLAIM_INDEX_SHA256,
    SOURCE_RUN_ID,
    build_sead_chronology_age_review,
)

EXPECTED_TEMPORAL_FEATURES = 8_172
EXPECTED_SITE_FEATURES = 2_069
_SITE_FIELDS = (
    "site_uuid",
    "source_site_id",
    "display_start_bp",
    "display_end_bp",
    "eligible_claim_count",
    "record_interval_count",
    "phase_count",
    "gap_count",
    "phases_json",
    "gaps_json",
)


def _document(
    path: Path, expected_sha256: str | None = None
) -> tuple[dict[str, Any], str]:
    payload = path.read_bytes()
    digest = sha256(payload).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"SEAD interval source digest changed: {path}")
    document: dict[str, Any] = json.loads(payload)
    if not isinstance(document, dict):
        raise TypeError(f"SEAD interval source must be an object: {path}")
    return document, digest


def coalesce_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Union only overlapping or adjacent closed integer intervals; retain gaps."""
    phases: list[tuple[int, int]] = []
    for younger, older in sorted(intervals):
        if younger < 0 or older < younger:
            raise ValueError("SEAD eligible interval has invalid BP bounds")
        if phases and younger <= phases[-1][1] + 1:
            phases[-1] = (phases[-1][0], max(phases[-1][1], older))
        else:
            phases.append((younger, older))
    return phases


def build_sead_interval_set_review(
    data_root: Path,
) -> tuple[dict[str, Any], list[dict[str, object]]]:
    """Reconcile every native-reviewed claim with exported record and site features."""
    normalized = data_root / "sead/normalized"
    acquisition = normalized / "acquisitions" / SOURCE_RUN_ID
    index, index_sha = _document(
        acquisition / "chronology_claims.json", PINNED_CLAIM_INDEX_SHA256
    )
    age_review, age_rows = build_sead_chronology_age_review(data_root)
    reviewed = {row["chronology_claim_id"]: row for row in age_rows}
    if len(reviewed) != EXPECTED_CLAIM_COUNT:
        raise ValueError("SEAD native-reviewed claim IDs are duplicated")

    claims: dict[str, dict[str, Any]] = {}
    part_hashes: list[dict[str, object]] = []
    for descriptor in index["partitioned_fields"]["claims"]["parts"]:
        relative = descriptor["path"]
        part, digest = _document(acquisition / relative, descriptor["sha256"])
        claim_part_rows = part.get("claims")
        if (
            not isinstance(claim_part_rows, list)
            or len(claim_part_rows) != descriptor["row_count"]
        ):
            raise ValueError(f"SEAD claim part cardinality changed: {relative}")
        for claim in claim_part_rows:
            if not isinstance(claim, dict):
                raise TypeError("SEAD claim must be an object")
            claim_id = claim.get("chronology_claim_id")
            if not isinstance(claim_id, str) or claim_id in claims:
                raise ValueError("SEAD claim ID is missing or duplicated")
            if (
                reviewed[claim_id]["chronology_eligibility"]
                != claim["chronology_eligibility"]
            ):
                raise ValueError(f"SEAD native review differs from claim: {claim_id}")
            claims[claim_id] = claim
        part_hashes.append(
            {
                "path": f"data/sead/normalized/acquisitions/{SOURCE_RUN_ID}/{relative}",
                "sha256": digest,
                "row_count": len(claim_part_rows),
            }
        )
    if len(claims) != EXPECTED_CLAIM_COUNT or set(claims) != set(reviewed):
        raise ValueError("SEAD source claims differ from native age review")
    eligible = {
        claim_id: claim
        for claim_id, claim in claims.items()
        if claim["chronology_eligibility"] == "eligible"
    }

    temporal_path = normalized / "nordic_temporal_evidence.geojson"
    temporal, temporal_sha = _document(temporal_path)
    features = temporal.get("features")
    if not isinstance(features, list) or len(features) != EXPECTED_TEMPORAL_FEATURES:
        raise ValueError("SEAD temporal feature count changed")
    site_path = normalized / "nordic_environmental_sites.geojson"
    sites, sites_sha = _document(site_path)
    site_features = sites.get("features")
    if (
        not isinstance(site_features, list)
        or len(site_features) != EXPECTED_SITE_FEATURES
    ):
        raise ValueError("SEAD site feature count changed")
    sites_by_uuid: dict[str, dict[str, Any]] = {}
    for feature in site_features:
        props = feature["properties"]
        site_uuid = props["site_uuid"]
        if (
            props.get("source") != "SEAD"
            or props.get("layer_key") != "sead-sites"
            or not isinstance(site_uuid, str)
            or site_uuid in sites_by_uuid
        ):
            raise ValueError(f"SEAD site feature identity changed: {site_uuid}")
        sites_by_uuid[site_uuid] = props

    seen: set[str] = set()
    intervals_by_site: dict[str, list[tuple[int, int]]] = defaultdict(list)
    native_claims_by_site: dict[str, list[dict[str, object]]] = defaultdict(list)
    feature_counts: Counter[str] = Counter()
    claim_counts: Counter[str] = Counter()
    for feature in features:
        props = feature["properties"]
        semantics = props["temporal_semantics"]
        site_uuid = props["site_uuid"]
        kind = str(semantics.get("evidence_class", "")).removeprefix("sead_")
        bounds = (props["time_start_bp"], props["time_end_bp"])
        identifiers = semantics.get("chronology_claim_ids")
        native_ids = semantics.get("source_record_ids")
        if (
            props.get("source") != "SEAD"
            or props.get("layer_key") != "sead-temporal-evidence"
            or site_uuid not in sites_by_uuid
            or semantics.get("source_family") != "sead"
            or semantics.get("precision_posture") != "linked_record_interval"
            or semantics.get("time_start_bp") != bounds[0]
            or semantics.get("time_end_bp") != bounds[1]
            or not isinstance(identifiers, list)
            or not identifiers
            or not isinstance(native_ids, list)
            or len(identifiers) != len(native_ids)
            or len(identifiers) != props["record_count"]
            or len(identifiers) != semantics.get("source_record_count")
            or not all(isinstance(value, int) for value in bounds)
        ):
            raise ValueError(
                f"SEAD record interval identity changed: {props.get('record_id')}"
            )
        for claim_id, native_id in zip(identifiers, native_ids, strict=True):
            claim = eligible.get(claim_id)
            if (
                claim is None
                or claim_id in seen
                or claim["site_uuid"] != site_uuid
                or claim["source_site_id"] != sites_by_uuid[site_uuid]["record_id"]
                or claim["claim_type"] != kind
                or claim["source_native_record_id"] != str(native_id)
                or (claim["younger_bp"], claim["older_bp"]) != bounds
            ):
                raise ValueError(
                    f"SEAD record interval not owned by eligible claim: {claim_id}"
                )
            seen.add(claim_id)
            claim_counts[site_uuid] += 1
            native_claims_by_site[site_uuid].append(
                {
                    "chronology_claim_id": claim_id,
                    "source_native_record_id": str(native_id),
                    "claim_type": kind,
                    "younger_bp": bounds[0],
                    "older_bp": bounds[1],
                }
            )
        intervals_by_site[site_uuid].append(bounds)
        feature_counts[site_uuid] += 1
    if seen != set(eligible):
        raise ValueError(
            f"SEAD exported record coverage differs: {len(seen)} / {len(eligible)}"
        )

    rows: list[dict[str, object]] = []
    disjoint_examples: list[dict[str, object]] = []
    phase_counts: Counter[int] = Counter()
    sites_with_display_envelope = 0
    display_bounds_differ = 0
    for site_uuid, site in sorted(sites_by_uuid.items()):
        phases = coalesce_intervals(intervals_by_site[site_uuid])
        gaps = [(left[1] + 1, right[0] - 1) for left, right in zip(phases, phases[1:])]
        display = (site["time_start_bp"], site["time_end_bp"])
        if all(isinstance(value, int) for value in display):
            sites_with_display_envelope += 1
            if phases and display != (phases[0][0], phases[-1][1]):
                display_bounds_differ += 1
        phase_counts[len(phases)] += 1
        row: dict[str, object] = {
            "site_uuid": site_uuid,
            "source_site_id": site["record_id"],
            "display_start_bp": display[0],
            "display_end_bp": display[1],
            "eligible_claim_count": claim_counts[site_uuid],
            "record_interval_count": feature_counts[site_uuid],
            "phase_count": len(phases),
            "gap_count": len(gaps),
            "phases_json": json.dumps(phases, separators=(",", ":")),
            "gaps_json": json.dumps(gaps, separators=(",", ":")),
        }
        rows.append(row)
        if gaps and len(disjoint_examples) < 5:
            disjoint_examples.append(
                {
                    **row,
                    "native_claims": sorted(
                        native_claims_by_site[site_uuid],
                        key=lambda claim: str(claim["chronology_claim_id"]),
                    ),
                }
            )
    report: dict[str, Any] = {
        "schema_version": "sead-interval-set-review.v1",
        "requirement_id": "SEAD-004",
        "source_run_id": SOURCE_RUN_ID,
        "source_build_id": index["source_build_id"],
        "denominators": {
            "native_reviewed_claims": len(claims),
            "eligible_record_claims": len(eligible),
            "refused_or_contextual_claims_excluded": len(claims) - len(eligible),
            "exported_record_intervals": len(features),
            "exported_sites": len(site_features),
            "sites_with_record_intervals": sum(
                bool(intervals_by_site[site_uuid]) for site_uuid in sites_by_uuid
            ),
            "sites_with_display_envelope": sites_with_display_envelope,
            "display_bounds_different_from_eligible_extent": display_bounds_differ,
            "sites_by_disjoint_phase_count": dict(sorted(phase_counts.items())),
        },
        "gold_disjoint_sites": disjoint_examples,
        "input_hashes": {
            "claim_index_sha256": index_sha,
            "claim_parts": part_hashes,
            "native_age_review_inputs": age_review["input_hashes"],
            "temporal_geojson_sha256": temporal_sha,
            "site_geojson_sha256": sites_sha,
        },
        "analytic_posture": {
            "record_intervals_are_distinct": True,
            "site_display_envelope_is_analytic_interval": False,
            "qualified_or_contextual_claims_admitted": False,
            "event_propagation_approved": False,
        },
    }
    return report, rows


def write_sead_interval_set_review(data_root: Path, output: Path) -> dict[str, Any]:
    """Write deterministic full-site inventory and content-bound review."""
    if output.exists():
        raise ValueError("SEAD interval review output must be absent")
    report, rows = build_sead_interval_set_review(data_root)
    output.mkdir(parents=True)
    with (output / "sites.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=_SITE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report["site_review_csv"] = {
        "path": "sites.csv",
        "sha256": sha256((output / "sites.csv").read_bytes()).hexdigest(),
        "row_count": len(rows),
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    return report
