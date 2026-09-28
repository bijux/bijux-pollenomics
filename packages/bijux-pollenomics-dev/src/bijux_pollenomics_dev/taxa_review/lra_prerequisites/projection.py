"""Outcome-free Neotoma chronology and basin prerequisite projection."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, ClassVar, cast

from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization.neotoma.candidate_groups import (
    summarize_neotoma_candidate_groups,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.frontier import (
    assess_neotoma_lra_frontier,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.lakeparameters import (
    assess_neotoma_lakeparameters,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.pollen_screen import (
    assess_neotoma_pollen_screen,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.site_evidence import (
    assess_neotoma_candidate_site_evidence,
)
from bijux_pollenomics.analysis.lra.materialization.reading import NeotomaEvidence

NORDIC_COUNTRY_CODES = ("DK", "FI", "NO", "SE")
_AUTHORITY = object()


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _with_digest(value: dict[str, Any]) -> dict[str, Any]:
    return {**value, "source_row_sha256": _digest(value)}


@dataclass(frozen=True, init=False)
class NeotomaPrerequisiteProjection:
    """Factory-authenticated review projection, never executable eligibility."""

    canonical_json: bytes
    result_digest: str
    _authority: object
    _TOKEN: ClassVar[object] = _AUTHORITY

    def __init__(self, canonical_json: bytes, authority: object) -> None:
        """Initialize a projection from factory-owned canonical bytes."""
        if authority is not self._TOKEN:
            raise ValueError("Projection must be rebuilt from original authorities")
        object.__setattr__(self, "canonical_json", canonical_json)
        object.__setattr__(
            self, "result_digest", hashlib.sha256(canonical_json).hexdigest()
        )
        object.__setattr__(self, "_authority", authority)

    def as_dict(self) -> dict[str, Any]:
        """Return a detached copy of the canonical outcome-free projection."""
        return cast(dict[str, Any], json.loads(self.canonical_json))

    def assert_authenticated(self) -> None:
        """Refuse copied dataclass-shaped values and altered canonical bytes."""
        if (
            self._authority is not self._TOKEN
            or hashlib.sha256(self.canonical_json).hexdigest() != self.result_digest
        ):
            raise ValueError("Projection authority or canonical bytes differ")


def _chronology_rows(
    evidence: NeotomaEvidence,
    decisions: list[dict[str, Any]],
    necessary_ids: list[str],
) -> list[dict[str, Any]]:
    claims: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for item in evidence.rows("age_claims"):
        row = item.payload()
        claim_id = row.get("chronology_claim_id")
        if not isinstance(claim_id, str) or not claim_id or claim_id in claims:
            raise ValueError("Source chronology claim identity is missing or repeated")
        claims[claim_id] = (row, item.locator())
    by_sample = {row.get("sample_id"): row for row in decisions}
    if len(by_sample) != len(decisions):
        raise ValueError("Pollen screen sample identities are missing or repeated")
    rows = []
    for sample_id in necessary_ids:
        screen = by_sample.get(sample_id)
        if not isinstance(screen, dict):
            raise TypeError("Necessary sample is absent from pollen screen")
        claim_ids = screen.get("owned_comparable_age_claim_ids")
        if not isinstance(claim_ids, list) or not claim_ids:
            raise ValueError("Necessary sample has no candidate age claims")
        candidates = []
        for claim_id in claim_ids:
            if not isinstance(claim_id, str) or claim_id not in claims:
                raise ValueError("Candidate age claim is absent from source authority")
            claim, locator = claims[claim_id]
            if claim.get("subject_id") != sample_id:
                raise ValueError("Candidate age claim is not owned by its sample")
            candidates.append(
                _with_digest(
                    {
                        "chronology_claim_id": claim_id,
                        "source_locator": locator,
                        "source_claim": claim,
                    }
                )
            )
        row = {
            "sample_id": sample_id,
            "site_id": screen.get("site_id"),
            "country_code": screen.get("country_code"),
            "source_screen_row_sha256": _digest(screen),
            "candidate_age_claims": sorted(
                candidates, key=lambda item: item["chronology_claim_id"]
            ),
            "chronology_disposition": "not_evaluated",
        }
        rows.append(_with_digest(row))
    return rows


def _value_status(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "not_numeric"
    if not math.isfinite(value):
        raise ValueError("Basin evidence contains a nonfinite value")
    return "positive" if value > 0 else "nonpositive"


def _basin_rows(
    site_report: dict[str, Any], lake_report: dict[str, Any]
) -> list[dict[str, Any]]:
    lake_by_site: dict[str, list[dict[str, Any]]] = {}
    for source in lake_report["source_rows"]:
        site_id = source.get("site_id")
        if not isinstance(site_id, str):
            raise TypeError("Lakeparameter row has no site identity")
        lake_by_site.setdefault(site_id, []).append(source)
    rows = []
    seen: set[str] = set()
    for site in site_report["site_rows"]:
        site_id = site.get("site_id")
        if not isinstance(site_id, str) or not site_id or site_id in seen:
            raise ValueError("Candidate site identity is missing or repeated")
        seen.add(site_id)
        candidates = []
        area = site.get("source_area")
        if area is not None:
            candidates.append(
                _with_digest(
                    {
                        "source_field": "sites.source_payload.area",
                        "source_value": area,
                        "source_unit": None,
                        "source_domain": "area",
                        "source_row_locator": site["source_locator"],
                        "value_status": _value_status(area),
                        "unit_status": "not_observed",
                    }
                )
            )
        for source in lake_by_site.pop(site_id, []):
            code = source.get("source_parameter_code")
            domain = "area" if code == "Area" else "other_lakeparameter"
            candidates.append(
                _with_digest(
                    {
                        "source_field": (
                            f"lakeparameters.value:{source['source_parameter_id']}"
                        ),
                        "source_value": source.get("source_value"),
                        "source_unit": source.get("source_parameter_label"),
                        "source_domain": domain,
                        "source_row_locator": source["source_row_locator"],
                        "source_parameter_code": code,
                        "value_status": _value_status(source.get("source_value")),
                        "unit_status": (
                            "source_parameter_label"
                            if source.get("source_parameter_label")
                            else "not_observed"
                        ),
                    }
                )
            )
        row = {
            "site_id": site_id,
            "country_code": site.get("country_code"),
            "candidate_sample_count": site.get("candidate_sample_count"),
            "source_site_row_sha256": _digest(site),
            "candidate_basin_evidence": sorted(
                candidates, key=lambda item: item["source_row_sha256"]
            ),
            "support_evidence": [],
            "basin_disposition": "not_evaluated",
        }
        rows.append(_with_digest(row))
    if lake_by_site:
        raise ValueError("Lakeparameter rows refer to sites outside source evidence")
    return sorted(rows, key=lambda item: item["site_id"])


def _country_denominators(
    screen_report: dict[str, Any],
    site_report: dict[str, Any],
    chronology_rows: list[dict[str, Any]],
    basin_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    screen_countries = screen_report.get("country_denominators")
    site_countries = site_report.get("country_denominators")
    if not isinstance(screen_countries, dict) or not isinstance(site_countries, dict):
        raise TypeError("Source country denominators are missing")
    expected_codes = {*NORDIC_COUNTRY_CODES, "UNASSIGNED"}
    if set(screen_countries) != expected_codes or set(site_countries) != expected_codes:
        raise ValueError("Neotoma country universe differs from Nordic plus unassigned")
    chronology_counts = Counter(row["country_code"] for row in chronology_rows)
    basin_counts = Counter(row["country_code"] for row in basin_rows)
    countries: dict[str, dict[str, Any]] = {}
    for country in sorted(expected_codes):
        chronology_count = chronology_counts[country]
        basin_count = basin_counts[country]
        if (
            chronology_count != screen_countries[country]["screen_candidate_samples"]
            or chronology_count != site_countries[country]["candidate_samples"]
            or basin_count != site_countries[country]["candidate_source_sites"]
        ):
            raise ValueError(
                "Country prerequisite rows do not close source denominators"
            )
        countries[country] = {
            "chronology_samples": chronology_count,
            "basin_sites": basin_count,
            "coverage_status": (
                "refused_unassigned_country"
                if country == "UNASSIGNED" and (chronology_count or basin_count)
                else (
                    "no_necessary_candidates"
                    if not chronology_count and not basin_count
                    else "prerequisite_review_only"
                )
            ),
        }
    return countries


def build_neotoma_prerequisite_projection(
    evidence: NeotomaEvidence,
    *,
    lakeparameter_capture_root: Path,
    expected_lakeparameter_capture_sha256: str,
) -> NeotomaPrerequisiteProjection:
    """Rebuild and bind an outcome-free projection from original authorities."""
    evidence.assert_unchanged()
    screen = assess_neotoma_pollen_screen(evidence)
    screen_report = screen.as_dict()
    necessary_ids = screen_report["candidate_sample_ids"]
    groups = summarize_neotoma_candidate_groups(screen)
    site_evidence = assess_neotoma_candidate_site_evidence(evidence, groups)
    site_report = site_evidence.as_dict()
    lakeparameters = assess_neotoma_lakeparameters(
        site_evidence,
        lakeparameter_capture_root,
        expected_lakeparameter_capture_sha256,
    )
    lake_report = lakeparameters.as_dict()
    frontier = assess_neotoma_lra_frontier(evidence, necessary_ids)
    frontier_report = frontier.as_dict()
    expected_samples = len(necessary_ids)
    expected_sites = len(
        {
            row["site_id"]
            for row in screen_report["sample_decisions"]
            if row["screen_status"] == "necessary_candidate"
        }
    )
    if (
        not expected_samples
        or not expected_sites
        or screen_report["screen_denominators"]["necessary_candidate_samples"]
        != expected_samples
        or frontier_report["selected_denominators"]["samples"] != expected_samples
        or site_report["denominators"]["candidate_samples"] != expected_samples
        or site_report["denominators"]["candidate_source_sites"] != expected_sites
        or lake_report["candidate_source_sites"] != expected_sites
    ):
        raise ValueError("Real Neotoma prerequisite denominators differ")
    chronology_rows = _chronology_rows(
        evidence, screen_report["sample_decisions"], necessary_ids
    )
    basin_rows = _basin_rows(site_report, lake_report)
    country_denominators = _country_denominators(
        screen_report, site_report, chronology_rows, basin_rows
    )
    payload = {
        "schema_version": "neotoma-lra-prerequisite-review-projection.v1",
        "source_family": "neotoma",
        "source_identities": {
            "source_snapshot_id": screen_report["source_snapshot_id"],
            "normalized_build_id": screen_report["normalized_build_id"],
            "raw_manifest_sha256": screen_report["raw_manifest_sha256"],
            "normalized_manifest_sha256": screen_report["normalized_manifest_sha256"],
            "frontier_sha256": frontier.result_digest,
            "chronology_screen_sha256": screen.result_digest,
            "site_evidence_sha256": site_evidence.result_digest,
            "lakeparameter_review_sha256": lakeparameters.result_digest,
            "lakeparameter_capture_sha256": expected_lakeparameter_capture_sha256,
        },
        "denominators": {
            "necessary_samples": len(chronology_rows),
            "source_sites": len(basin_rows),
            "chronology_decisions_required": len(chronology_rows),
            "basin_decisions_required": len(basin_rows),
            "accepted_samples": 0,
        },
        "intended_country_universe": list(NORDIC_COUNTRY_CODES),
        "country_denominators": country_denominators,
        "chronology_rows": chronology_rows,
        "basin_rows": basin_rows,
        "reviewer_authority": "declared_not_authenticated",
        "scientific_acceptance": "not_evaluated",
        "release_status": "not_evaluated",
        "executable_request": None,
    }
    evidence.assert_unchanged()
    return NeotomaPrerequisiteProjection(canonical_bytes(payload), _AUTHORITY)


__all__ = [
    "NORDIC_COUNTRY_CODES",
    "NeotomaPrerequisiteProjection",
    "build_neotoma_prerequisite_projection",
]
