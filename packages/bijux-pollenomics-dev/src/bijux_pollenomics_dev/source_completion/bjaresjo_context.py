"""Screen a named Swedish lake against source-bound SEAD display intervals."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km

from .nordic_direct_pollen import _coordinate, _json_write

REGISTRY = Path("data/svar/review/sweden_lake_candidate_registry.geojson")
SITE_LEDGER = Path(
    "docs/report/source-relations/neotoma/landclim-site-identity/site-comparison.csv"
)
SEAD = Path("data/sead/normalized/nordic_temporal_evidence.geojson")
SEAD_REVIEW = Path("docs/report/source-relations/sead/interval-sets/report.json")
CLAIMS = Path("docs/report/source-relations/sead/chronology-claim-review/claims.csv")
CLAIM_REVIEW = Path(
    "docs/report/source-relations/sead/chronology-claim-review/report.json"
)
SYNTHESIS = Path("docs/report/countries/sweden/sweden_land_use_synthesis_v66.json")
ADMISSION = Path(
    "data/sead/raw/acquisitions/sead-full-evidence-39bfff6a-ce80714e/admission.json"
)
RADIUS_KM = 20.0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("empty source-bound context result")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def produce(repository: Path, output: Path) -> None:
    """Retain spatial/nominal-time overlap without admitting an ecological join."""
    repository = repository.resolve()
    paths = {
        name: repository / relative
        for name, relative in {
            "registry": REGISTRY,
            "site_ledger": SITE_LEDGER,
            "sead_intervals": SEAD,
            "sead_interval_review": SEAD_REVIEW,
            "sead_claims": CLAIMS,
            "sead_claim_review": CLAIM_REVIEW,
            "land_use_synthesis": SYNTHESIS,
            "sead_admission": ADMISSION,
        }.items()
    }
    hashes = {name: _sha(path) for name, path in paths.items()}
    interval_review = json.loads(paths["sead_interval_review"].read_text())
    claim_review = json.loads(paths["sead_claim_review"].read_text())
    admission = json.loads(paths["sead_admission"].read_text())
    if (
        interval_review["input_hashes"]["temporal_geojson_sha256"]
        != hashes["sead_intervals"]
        or claim_review["claim_review_csv"]["sha256"] != hashes["sead_claims"]
        or interval_review["analytic_posture"]["event_propagation_approved"]
        is not False
        or admission["release_status"] != "refused"
    ):
        raise ValueError("SEAD source custody or review posture changed")
    registry = json.loads(paths["registry"].read_text())
    matches = [
        feature
        for feature in registry["features"]
        if feature["properties"]["record_id"] == "614958-137018"
    ]
    if len(matches) != 1:
        raise ValueError("named Bjäresjö official lake identity changed")
    lake = matches[0]
    props = lake["properties"]
    if (
        props["name"] != "Bjäresjö"
        or props["temporal_posture"] != "current_hydrographic_identity_only"
        or "neotoma-pollen:28871" not in props["matched_pollen_records"]
    ):
        raise ValueError("official lake and pollen candidate posture changed")
    with paths["site_ledger"].open(newline="", encoding="utf-8") as stream:
        source_leads = [
            row
            for row in csv.DictReader(stream)
            if row["neotoma_site_id"] == "neotoma:site:28871"
        ]
    if (
        len(source_leads) != 1
        or source_leads[0]["identity_decision"] != "not_established"
        or source_leads[0]["radius_transfer"] != "refused"
        or source_leads[0]["same_name_sequence"] != "BJARE"
    ):
        raise ValueError("Bjäresjösjön core identity decision changed")
    claims: dict[str, dict[str, str]] = {}
    with paths["sead_claims"].open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            key = row["chronology_claim_id"]
            if key in claims:
                raise ValueError("duplicate SEAD chronology claim")
            claims[key] = row
    if len(claims) != claim_review["claim_count"]:
        raise ValueError("SEAD chronology denominator changed")
    longitude, latitude = lake["geometry"]["coordinates"]
    center = _coordinate({"latitude": latitude, "longitude": longitude})
    nearby: list[dict[str, Any]] = []
    for feature in json.loads(paths["sead_intervals"].read_text())["features"]:
        if feature["geometry"]["type"] != "Point":
            raise ValueError("SEAD interval lacks a point location")
        lon, lat = feature["geometry"]["coordinates"]
        km = distance_km(center, _coordinate({"latitude": lat, "longitude": lon}))
        if km > RADIUS_KM:
            continue
        source = feature["properties"]
        semantics = source["temporal_semantics"]
        claim_ids = semantics["chronology_claim_ids"]
        if (
            source["country"] != "Sweden"
            or not claim_ids
            or source["time_start_bp"] > source["time_end_bp"]
            or any(key not in claims for key in claim_ids)
        ):
            raise ValueError("nearby SEAD record identity or interval changed")
        source_claims = [claims[key] for key in claim_ids]
        if any(
            row["chronology_eligibility"] != "eligible"
            or row["publication_role"] != "chronology_display_only"
            or row["propagation_eligibility"] != "refused"
            for row in source_claims
        ):
            raise ValueError("SEAD claim role differs from display-only review")
        nearby.append(
            {
                "source_record_id": source["record_id"],
                "site_uuid": source["site_uuid"],
                "source_site_id": source["record_id"].split(":", 1)[0],
                "distance_from_official_lake_center_km": f"{km:.6f}",
                "time_start_bp": source["time_start_bp"],
                "time_end_bp": source["time_end_bp"],
                "evidence_class": semantics["evidence_class"],
                "chronology_claim_ids": ";".join(claim_ids),
                "chronology_role": "display_only",
                "ecological_or_event_join": "refused",
            }
        )
    if len({row["source_record_id"] for row in nearby}) != len(nearby):
        raise ValueError("duplicate SEAD interval feature")
    nearby.sort(
        key=lambda row: (
            float(row["distance_from_official_lake_center_km"]),
            row["source_record_id"],
        )
    )
    synthesis = json.loads(paths["land_use_synthesis"].read_text())
    windows = [row for row in synthesis["rows"] if row["target_name"] == "Bjäresjösjön"]
    if len(windows) != 25:
        raise ValueError("published Bjäresjösjön window denominator changed")
    overlap_rows: list[dict[str, Any]] = []
    for window in sorted(windows, key=lambda row: row["time_start_bp"]):
        members = [
            row
            for row in nearby
            if row["time_start_bp"] <= window["time_end_bp"]
            and row["time_end_bp"] >= window["time_start_bp"]
        ]
        sites = {row["site_uuid"] for row in members}
        if (
            len(members) != window["sead_temporal_record_count_20km"]
            or len(sites) != window["sead_site_count_20km"]
        ):
            raise ValueError("published Bjäresjösjön SEAD display count differs")
        overlap_rows.append(
            {
                "landclim_record_id": window["landclim_record_id"],
                "time_start_bp": window["time_start_bp"],
                "time_end_bp": window["time_end_bp"],
                "display_interval_features_within_20km": len(members),
                "display_sites_within_20km": len(sites),
                "ecological_or_event_join": "refused",
            }
        )
    output.mkdir(parents=True, exist_ok=False)
    _csv(output / "nearby-sead.csv", nearby)
    _csv(output / "window-overlap.csv", overlap_rows)
    _json_write(
        output / "report.json",
        {
            "schema_version": "bjaresjo-context-screen.v1",
            "source_sha256": hashes,
            "lake": {
                "requested_name": "Bjäresjösjön",
                "official_name": props["name"],
                "official_registry_id": props["record_id"],
                "official_area_km2": props["area_km2"],
                "representative_point_lon_lat": [longitude, latitude],
                "source_temporal_posture": props["temporal_posture"],
                "neotoma_candidate_site_id": source_leads[0]["neotoma_site_id"],
                "same_name_landclim_sequence": "BJARE",
                "neotoma_to_landclim_km": float(
                    source_leads[0]["same_name_distance_km"]
                ),
                "core_identity_decision": "not_established",
                "radius_transfer": "refused",
            },
            "sead": {
                "radius_km": RADIUS_KM,
                "nearby_interval_features": len(nearby),
                "nearby_sites": len({row["site_uuid"] for row in nearby}),
                "chronology_role": "display_only",
                "source_release_status": admission["release_status"],
                "ecological_or_event_join": "refused",
            },
            "published_window_count": len(overlap_rows),
            "window_counts_match_published_synthesis": True,
            "nearby_sead_sha256": _sha(output / "nearby-sead.csv"),
            "window_overlap_sha256": _sha(output / "window-overlap.csv"),
            "interpretation": "Official modern lake identity and source-bound nearby SEAD display intervals are established. Physical pollen-core identity, selected source age model, scientific chronology admission, event propagation and ecological causation are not established.",
        },
    )


def main() -> None:
    """Export source-bound Bjäresjö context without promoting unadmitted evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    produce(args.repository, args.output)


if __name__ == "__main__":
    main()
