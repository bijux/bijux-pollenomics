"""Native Neotoma site fields for basin review, without geometry admission."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from typing import Any, cast

from bijux_pollenomics.evidence.sources.neotoma.contract import COUNTRY_CODES

from ..models import canonical_bytes
from ..reading import NeotomaEvidence, json_object
from .candidate_groups import NeotomaCandidateGroups


@dataclass(frozen=True)
class NeotomaSiteEvidence:
    """Source-bound review rows; no row is an accepted basin or LRA input."""

    canonical_json: bytes
    result_digest: str

    def as_dict(self) -> dict[str, Any]:
        """Return a separate copy of the review projection."""
        return cast(dict[str, Any], json.loads(self.canonical_json))


def _geometry_type(value: object) -> tuple[str | None, str]:
    if not isinstance(value, str) or not value:
        return None, "missing_source_geography"
    try:
        parsed = json_object(value.encode("utf-8"))
    except (ValueError, UnicodeError):
        return None, "unparseable_source_geography"
    kind = parsed.get("type")
    if not isinstance(kind, str) or not kind:
        return None, "untyped_source_geography"
    return kind, "source_geometry_type_only"


def assess_neotoma_candidate_site_evidence(
    evidence: NeotomaEvidence, groups: NeotomaCandidateGroups
) -> NeotomaSiteEvidence:
    """Project source site fields for exact candidate IDs and refuse basin inference."""
    if hashlib.sha256(groups.canonical_json).hexdigest() != groups.result_digest:
        raise ValueError("Candidate source-group bytes differ from their digest")
    evidence.assert_unchanged()
    source = evidence.manifest()
    report = groups.as_dict()
    candidates = report.get("site_rows")
    if (
        report.get("schema_version") != "neotoma-prerequisite-source-groups.v1"
        or report.get("source_family") != "neotoma"
        or report.get("source_snapshot_id") != source["source_snapshot_id"]
        or report.get("normalized_build_id") != source["build_id"]
        or report.get("raw_manifest_sha256")
        != dict(evidence.raw_files)["manifest.json"]
        or report.get("normalized_manifest_sha256")
        != hashlib.sha256(evidence.manifest_bytes).hexdigest()
        or report.get("lra_admission_status") != "refused"
        or report.get("denominators", {}).get("lra_accepted_samples") != 0
        or not isinstance(candidates, list)
    ):
        raise ValueError("Candidate groups are not bound to this refused source")
    by_id = {row["site_id"]: row for row in candidates}
    if (
        len(by_id) != len(candidates)
        or len(by_id) != report["denominators"]["source_sites"]
        or sum(row["candidate_sample_count"] for row in candidates)
        != report["denominators"]["candidate_samples"]
    ):
        raise ValueError("Candidate source sites do not reconcile")

    rows = []
    seen: set[str] = set()
    for item in evidence.rows("sites"):
        row = item.payload()
        site_id = row["site_id"]
        if site_id not in by_id:
            continue
        if site_id in seen:
            raise ValueError("Candidate site has repeated source rows")
        seen.add(site_id)
        country = row["country_code"]
        if country != by_id[site_id]["country_code"] or country not in COUNTRY_CODES:
            raise ValueError("Candidate site country differs from source groups")
        native = row["source_payload"]
        if (
            not isinstance(native, dict)
            or native.get("siteid") != row["source_site_id"]
        ):
            raise ValueError("Candidate source site payload is malformed")
        kind, geometry_status = _geometry_type(native.get("geography"))
        rows.append(
            {
                "site_id": site_id,
                "country_code": country,
                "candidate_sample_count": by_id[site_id]["candidate_sample_count"],
                "collection_unit_ids": by_id[site_id]["collection_unit_ids"],
                "dataset_ids": by_id[site_id]["dataset_ids"],
                "source_locator": item.locator(),
                "source_site_name": native.get("sitename"),
                "source_site_description": native.get("sitedescription"),
                "source_notes": native.get("notes"),
                "source_area": native.get("area"),
                "source_geography": native.get("geography"),
                "source_geometry_type": kind,
                "source_geometry_status": geometry_status,
                "basin_type_status": "not_reviewed",
                "basin_dimensions_status": "not_reviewed",
                "independence_status": "not_reviewed",
                "lra_admission_status": "refused",
            }
        )
    if seen != set(by_id):
        raise ValueError("Candidate source site is missing from authenticated surface")
    rows.sort(key=lambda row: row["site_id"])
    unit_to_site = {
        unit_id: site_id
        for site_id, group in by_id.items()
        for unit_id in group["collection_unit_ids"]
    }
    if len(unit_to_site) != report["denominators"]["source_collection_units"]:
        raise ValueError("Candidate collection units do not reconcile")
    unit_rows = []
    seen_units: set[str] = set()
    for item in evidence.rows("collection_units"):
        row = item.payload()
        unit_id = row["collection_unit_id"]
        if unit_id not in unit_to_site:
            continue
        if unit_id in seen_units:
            raise ValueError("Candidate collection unit has repeated source rows")
        seen_units.add(unit_id)
        site_id = unit_to_site[unit_id]
        if (
            row["site_id"] != site_id
            or row["country_code"] != by_id[site_id]["country_code"]
        ):
            raise ValueError("Candidate collection unit differs from source groups")
        native = row["source_payload"]
        if (
            not isinstance(native, dict)
            or native.get("collectionunitid") != row["source_collection_unit_id"]
        ):
            raise ValueError("Candidate collection-unit payload is malformed")
        unit_rows.append(
            {
                "collection_unit_id": unit_id,
                "site_id": site_id,
                "country_code": row["country_code"],
                "source_locator": item.locator(),
                "source_depositional_environment": native.get(
                    "depositionalenvironment"
                ),
                "source_collection_unit_type": native.get("collunittype"),
                "source_water_depth": native.get("waterdepth"),
                "source_collection_date": native.get("colldate"),
                "source_collection_location": native.get("location"),
                "source_gps_location": native.get("gpslocation"),
                "source_notes": native.get("notes"),
                "basin_type_status": "not_reviewed",
                "basin_dimensions_status": "not_reviewed",
                "lra_admission_status": "refused",
            }
        )
    if seen_units != set(unit_to_site):
        raise ValueError(
            "Candidate collection unit is missing from authenticated surface"
        )
    unit_rows.sort(key=lambda row: row["collection_unit_id"])
    countries: dict[str, dict[str, int]] = {}
    for country in COUNTRY_CODES:
        selected = [row for row in rows if row["country_code"] == country]
        selected_units = [row for row in unit_rows if row["country_code"] == country]
        shapes = Counter(row["source_geometry_type"] for row in selected)
        countries[country] = {
            "candidate_source_sites": len(selected),
            "candidate_collection_units": len(selected_units),
            "candidate_samples": sum(row["candidate_sample_count"] for row in selected),
            "source_description_present": sum(
                row["source_site_description"] is not None for row in selected
            ),
            "source_area_present": sum(
                row["source_area"] is not None for row in selected
            ),
            "source_point_geometries": shapes["Point"],
            "source_polygon_geometries": shapes["Polygon"],
            "other_or_missing_geometries": len(selected)
            - shapes["Point"]
            - shapes["Polygon"],
            "depositional_environment_present": sum(
                row["source_depositional_environment"] is not None
                for row in selected_units
            ),
            "collection_unit_type_present": sum(
                row["source_collection_unit_type"] is not None for row in selected_units
            ),
            "water_depth_present": sum(
                row["source_water_depth"] is not None for row in selected_units
            ),
        }
        expected = report["country_denominators"][country]
        if (
            countries[country]["candidate_source_sites"] != expected["source_sites"]
            or countries[country]["candidate_collection_units"]
            != expected["source_collection_units"]
            or countries[country]["candidate_samples"] != expected["candidate_samples"]
        ):
            raise ValueError("Candidate site evidence country does not reconcile")
    if sum(value["candidate_source_sites"] for value in countries.values()) != len(
        rows
    ):
        raise ValueError("Candidate source site total does not reconcile")
    if sum(value["candidate_collection_units"] for value in countries.values()) != len(
        unit_rows
    ):
        raise ValueError("Candidate collection unit total does not reconcile")
    evidence.assert_unchanged()
    payload = {
        "schema_version": "neotoma-candidate-site-evidence.v1",
        "source_family": "neotoma",
        "candidate_groups_sha256": groups.result_digest,
        "source_snapshot_id": source["source_snapshot_id"],
        "normalized_build_id": source["build_id"],
        "raw_manifest_sha256": report["raw_manifest_sha256"],
        "normalized_manifest_sha256": report["normalized_manifest_sha256"],
        "denominators": {
            "candidate_source_sites": len(rows),
            "candidate_collection_units": len(unit_rows),
            "candidate_samples": report["denominators"]["candidate_samples"],
            "lra_accepted_samples": 0,
        },
        "country_denominators": countries,
        "site_rows": rows,
        "collection_unit_rows": unit_rows,
        "source_area_semantics": "not_verified_as_basin_area_or_dimension",
        "basin_admission_status": "not_reviewed",
        "lra_admission_status": "refused",
    }
    content = canonical_bytes(payload)
    return NeotomaSiteEvidence(content, hashlib.sha256(content).hexdigest())
