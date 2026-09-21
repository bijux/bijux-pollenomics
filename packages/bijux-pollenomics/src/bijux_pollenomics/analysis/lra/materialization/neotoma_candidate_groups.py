"""Source-identity denominators for Neotoma pollen prerequisite samples."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from typing import Any, cast

from bijux_pollenomics.evidence.sources.neotoma.contract import COUNTRY_CODES

from .models import canonical_bytes
from .neotoma_pollen_screen import NeotomaPollenScreen


@dataclass(frozen=True)
class NeotomaCandidateGroups:
    """Canonical source groups for review, without independent-site admission."""

    canonical_json: bytes
    result_digest: str

    def as_dict(self) -> dict[str, Any]:
        """Return an independent copy of the source-group projection."""
        return cast(dict[str, Any], json.loads(self.canonical_json))


def summarize_neotoma_candidate_groups(
    screen: NeotomaPollenScreen,
) -> NeotomaCandidateGroups:
    """Count distinct source sites, collection units and datasets behind candidates.

    These are source grouping leads, not independent basins or admitted LRA sites.
    The caller retains the screen's authenticated raw and normalized manifests.
    """
    if hashlib.sha256(screen.canonical_json).hexdigest() != screen.result_digest:
        raise ValueError("Neotoma screen bytes differ from its digest")
    report = screen.as_dict()
    decisions = report.get("sample_decisions")
    selected = report.get("candidate_sample_ids")
    if (
        report.get("schema_version") != "neotoma-pollen-prerequisite-screen.v1"
        or report.get("source_family") != "neotoma"
        or report.get("screen_status") != "prerequisite_only"
        or report.get("lra_accepted_samples") != 0
        or report.get("executable_request") is not None
        or not isinstance(decisions, list)
        or not isinstance(selected, list)
        or not selected
        or any(not isinstance(value, str) or not value for value in selected)
        or selected != sorted(set(selected))
        or report.get("candidate_sample_ids_sha256")
        != hashlib.sha256(canonical_bytes(selected)).hexdigest()
        or len(decisions)
        != report.get("source_denominators", {}).get("available_samples")
        or len(selected)
        != report.get("screen_denominators", {}).get("necessary_candidate_samples")
    ):
        raise ValueError("Neotoma prerequisite screen is incomplete or executable")

    by_id: dict[str, dict[str, Any]] = {}
    for row in decisions:
        if not isinstance(row, dict):
            raise ValueError("Neotoma screen decision is malformed")
        sample_id = row.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id or sample_id in by_id:
            raise ValueError("Neotoma screen sample identity is missing or repeated")
        by_id[sample_id] = row
    if set(selected) != {
        sample_id
        for sample_id, row in by_id.items()
        if row.get("screen_status") == "necessary_candidate"
    }:
        raise ValueError("Candidate IDs differ from source decision partition")

    sites: dict[str, dict[str, Any]] = {}
    country_samples: dict[str, set[str]] = defaultdict(set)
    country_units: dict[str, set[str]] = defaultdict(set)
    country_datasets: dict[str, set[str]] = defaultdict(set)
    for sample_id in selected:
        row = by_id[sample_id]
        country = row.get("country_code")
        if country not in COUNTRY_CODES:
            raise ValueError("Candidate country is outside the source partition")
        for field in ("site_id", "collection_unit_id", "dataset_id"):
            value = row.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"Candidate {field} is missing")
        if (
            row.get("lra_admission_status") != "refused"
            or type(row.get("pollen_count_observations")) is not int
            or row["pollen_count_observations"] < 1
            or not isinstance(row.get("owned_comparable_age_claim_ids"), list)
            or not row["owned_comparable_age_claim_ids"]
        ):
            raise ValueError("Candidate lacks refused pollen/count/age prerequisites")
        site_id = row["site_id"]
        site = sites.setdefault(
            site_id,
            {
                "site_id": site_id,
                "country_code": country,
                "sample_ids": [],
                "collection_unit_ids": set(),
                "dataset_ids": set(),
            },
        )
        if site["country_code"] != country:
            raise ValueError("Source site crosses country partitions")
        site["sample_ids"].append(sample_id)
        site["collection_unit_ids"].add(row["collection_unit_id"])
        site["dataset_ids"].add(row["dataset_id"])
        country_samples[country].add(sample_id)
        country_units[country].add(row["collection_unit_id"])
        country_datasets[country].add(row["dataset_id"])

    site_rows = [
        {
            "site_id": site_id,
            "country_code": site["country_code"],
            "candidate_sample_count": len(site["sample_ids"]),
            "sample_ids": sorted(site["sample_ids"]),
            "collection_unit_ids": sorted(site["collection_unit_ids"]),
            "dataset_ids": sorted(site["dataset_ids"]),
        }
        for site_id, site in sorted(sites.items())
    ]
    countries = {
        country: {
            "candidate_samples": len(country_samples[country]),
            "source_sites": sum(row["country_code"] == country for row in site_rows),
            "source_collection_units": len(country_units[country]),
            "source_datasets": len(country_datasets[country]),
        }
        for country in COUNTRY_CODES
    }
    if sum(row["candidate_samples"] for row in countries.values()) != len(selected):
        raise ValueError("Country sample groups do not reconcile")
    if any(
        countries[country]["candidate_samples"]
        != report["country_denominators"][country]["screen_candidate_samples"]
        for country in COUNTRY_CODES
    ):
        raise ValueError("Country sample groups differ from source screen")
    payload = {
        "schema_version": "neotoma-prerequisite-source-groups.v1",
        "source_family": "neotoma",
        "source_screen_sha256": screen.result_digest,
        "source_snapshot_id": report["source_snapshot_id"],
        "normalized_build_id": report["normalized_build_id"],
        "raw_manifest_sha256": report["raw_manifest_sha256"],
        "normalized_manifest_sha256": report["normalized_manifest_sha256"],
        "denominators": {
            "candidate_samples": len(selected),
            "source_sites": len(sites),
            "source_collection_units": len(
                {unit for values in country_units.values() for unit in values}
            ),
            "source_datasets": len(
                {dataset for values in country_datasets.values() for dataset in values}
            ),
            "lra_accepted_samples": 0,
        },
        "country_denominators": countries,
        "site_rows": site_rows,
        "independence_status": "source_site_aliases_and_basins_not_reviewed",
        "lra_admission_status": "refused",
    }
    content = canonical_bytes(payload)
    return NeotomaCandidateGroups(content, hashlib.sha256(content).hexdigest())
