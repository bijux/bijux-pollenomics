"""Source-wide Neotoma pollen/count/age prerequisites, without LRA admission."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, cast

from bijux_pollenomics.evidence.sources.neotoma.contract import COUNTRY_CODES

from ..models import canonical_bytes
from ..reading import NeotomaEvidence
from .accounting import source_accounting
from .series import source_element_status


@dataclass(frozen=True)
class NeotomaPollenScreen:
    """Canonical, source-bound prerequisite partition; no numerical request."""

    canonical_json: bytes
    result_digest: str

    def as_dict(self) -> dict[str, Any]:
        """Return an independent copy of the source-wide partition."""
        return cast(dict[str, Any], json.loads(self.canonical_json))


def _comparable_owned_claim(projected: dict[str, Any]) -> bool:
    """Use only a typed, bounded age claim owned by its source sample."""
    claim = cast(dict[str, Any], projected["source_claim"])
    younger, older = claim.get("younger_bp"), claim.get("older_bp")
    return (
        not projected["ownership_mismatches"]
        and claim.get("comparability_status") == "comparable"
        and isinstance(claim.get("source_age_type"), str)
        and bool(claim["source_age_type"].strip())
        and isinstance(younger, (int, float))
        and not isinstance(younger, bool)
        and isinstance(older, (int, float))
        and not isinstance(older, bool)
        and math.isfinite(younger)
        and math.isfinite(older)
        and younger <= older
    )


def assess_neotoma_pollen_screen(evidence: NeotomaEvidence) -> NeotomaPollenScreen:
    """Screen every source sample for necessary pollen/count/age evidence.

    A count with two agreeing source pollen labels and a separate comparable
    sample-owned age are leads for review, not a known pollen denominator or
    a selected chronology.  This projection keeps every refusal in its original
    source country partition, including unassigned source geography.
    """
    evidence.assert_unchanged()
    accounting = source_accounting(evidence, None)
    manifest = evidence.manifest()
    by_sample: dict[str, Counter[str]] = defaultdict(Counter)
    by_country: dict[str, Counter[str]] = {
        country: Counter() for country in COUNTRY_CODES
    }
    total_observations = 0
    label_statuses: Counter[str] = Counter()
    count_refusals: Counter[str] = Counter()
    for source in evidence.rows("observations"):
        record = accounting.observation(source)
        observation = cast(dict[str, Any], record["source_observation"])
        sample_id = str(observation["sample_id"])
        country = str(observation["country_code"])
        sample_counts = by_sample[sample_id]
        country_counts = by_country[country]
        total_observations += 1
        sample_counts["observations"] += 1
        country_counts["observations"] += 1
        if record["count_status"] != "count_candidate":
            sample_counts["refused_count_observations"] += 1
            country_counts["refused_count_observations"] += 1
            for reason in cast(list[str], record["count_reason_codes"]):
                count_refusals[reason] += 1
            continue
        sample_counts["count_candidate_observations"] += 1
        country_counts["count_candidate_observations"] += 1
        status = source_element_status(
            observation.get("source_element"),
            observation.get("source_element_type"),
        )
        label_statuses[status] += 1
        country_counts[f"count_label_{status}"] += 1
        if status == "source_label_pollen":
            sample_counts["pollen_count_observations"] += 1
            country_counts["pollen_count_observations"] += 1

    decisions = []
    candidate_ids = []
    old_count_age_leads = 0
    sample_refusals: Counter[str] = Counter()
    for sample_id, source in sorted(accounting.indexes["samples"].items()):
        record = accounting.sample(source)
        sample = cast(dict[str, Any], record["source_sample"])
        country = str(sample["country_code"])
        sample_counts = by_sample[sample_id]
        country_counts = by_country[country]
        country_counts["samples"] += 1
        projected_claims = cast(list[dict[str, Any]], record["chronology"]["claims"])
        owned_comparable = sorted(
            str(projected["source_claim"]["chronology_claim_id"])
            for projected in projected_claims
            if _comparable_owned_claim(projected)
        )
        count_lead = sample_counts["count_candidate_observations"] > 0
        pollen_lead = sample_counts["pollen_count_observations"] > 0
        age_lead = bool(owned_comparable)
        if count_lead:
            country_counts["samples_with_count_candidates"] += 1
        if age_lead:
            country_counts["samples_with_owned_comparable_age"] += 1
        if count_lead and age_lead:
            old_count_age_leads += 1
            country_counts["samples_with_count_and_comparable_age"] += 1
        if pollen_lead:
            country_counts["samples_with_pollen_count"] += 1
        reasons = []
        if not count_lead:
            reasons.append("no_numeric_count_candidate")
        elif not pollen_lead:
            reasons.append("no_agreeing_pollen_labelled_count")
        if not age_lead:
            reasons.append("no_sample_owned_comparable_typed_age")
        if reasons:
            country_counts["screen_refused_samples"] += 1
            for reason in reasons:
                sample_refusals[reason] += 1
                country_counts[f"reason_{reason}"] += 1
        else:
            candidate_ids.append(sample_id)
            country_counts["screen_candidate_samples"] += 1
        decisions.append(
            {
                "sample_id": sample_id,
                "country_code": country,
                "dataset_id": sample["dataset_id"],
                "collection_unit_id": sample["collection_unit_id"],
                "site_id": sample["site_id"],
                "source_locator": source.locator(),
                "observation_count": sample_counts["observations"],
                "count_candidate_observations": sample_counts[
                    "count_candidate_observations"
                ],
                "pollen_count_observations": sample_counts["pollen_count_observations"],
                "owned_comparable_age_claim_ids": owned_comparable,
                "screen_status": "necessary_candidate" if not reasons else "refused",
                "reason_codes": reasons,
                "lra_admission_status": "refused",
            }
        )

    available_samples = len(accounting.indexes["samples"])
    expected_observations = manifest["surfaces"]["observations"]["row_count"]
    if total_observations != expected_observations:
        raise ValueError("Observation screen does not cover the source denominator")
    if len(decisions) != available_samples:
        raise ValueError("Sample screen does not cover the source denominator")
    if sum(row["samples"] for row in by_country.values()) != available_samples:
        raise ValueError("Country sample screen does not reconcile")
    if sum(row["observations"] for row in by_country.values()) != total_observations:
        raise ValueError("Country observation screen does not reconcile")
    if sum(row["screen_candidate_samples"] for row in by_country.values()) != len(
        candidate_ids
    ):
        raise ValueError("Country candidate screen does not reconcile")
    if len(candidate_ids) > old_count_age_leads:
        raise ValueError("Pollen screen exceeds count/age prerequisite frontier")
    candidate_set = set(candidate_ids)
    if any(
        decision["sample_id"] in candidate_set
        and not (
            decision["count_candidate_observations"]
            and decision["owned_comparable_age_claim_ids"]
        )
        for decision in decisions
    ):
        raise ValueError("Pollen candidate lacks a count/age prerequisite")

    country_fields = (
        "samples",
        "observations",
        "count_candidate_observations",
        "refused_count_observations",
        "pollen_count_observations",
        "samples_with_count_candidates",
        "samples_with_owned_comparable_age",
        "samples_with_count_and_comparable_age",
        "samples_with_pollen_count",
        "screen_candidate_samples",
        "screen_refused_samples",
    )
    payload: dict[str, Any] = {
        "schema_version": "neotoma-pollen-prerequisite-screen.v1",
        "source_family": "neotoma",
        "source_snapshot_id": manifest["source_snapshot_id"],
        "normalized_build_id": manifest["build_id"],
        "raw_manifest_sha256": dict(evidence.raw_files)["manifest.json"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "source_denominators": {
            "available_samples": available_samples,
            "available_observations": total_observations,
            "source_age_claims": len(accounting.indexes["age_claims"]),
            "source_conflicts": len(accounting.indexes["conflicts"]),
            "source_orphans": len(accounting.indexes["orphans"]),
        },
        "screen_denominators": {
            "count_candidate_observations": sum(
                row["count_candidate_observations"] for row in by_country.values()
            ),
            "refused_count_observations": sum(
                row["refused_count_observations"] for row in by_country.values()
            ),
            "pollen_count_observations": sum(
                row["pollen_count_observations"] for row in by_country.values()
            ),
            "samples_with_count_and_comparable_age": old_count_age_leads,
            "necessary_candidate_samples": len(candidate_ids),
            "refused_samples": available_samples - len(candidate_ids),
            "count_candidate_source_label_statuses": dict(
                sorted(label_statuses.items())
            ),
            "count_refusal_reason_occurrences": dict(sorted(count_refusals.items())),
            "sample_refusal_reason_occurrences": dict(sorted(sample_refusals.items())),
        },
        "country_denominators": {
            country: {
                **{field: counts[field] for field in country_fields},
                "count_candidate_source_label_statuses": {
                    status: counts[f"count_label_{status}"]
                    for status in sorted(label_statuses)
                },
                "sample_refusal_reason_occurrences": {
                    reason: counts[f"reason_{reason}"]
                    for reason in sorted(sample_refusals)
                },
            }
            for country, counts in sorted(by_country.items())
        },
        "candidate_sample_ids": candidate_ids,
        "candidate_sample_ids_sha256": hashlib.sha256(
            canonical_bytes(candidate_ids)
        ).hexdigest(),
        "sample_decisions": decisions,
        "screen_status": "prerequisite_only",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "claims_not_made": [
            "reviewed_taxa_or_ppe",
            "selected_chronology",
            "compatible_pollen_denominator",
            "admitted_basin_geometry",
            "numerical_lra_input",
            "measured_vegetation_truth",
            "four_country_lra_admission",
        ],
    }
    evidence.assert_unchanged()
    content = canonical_bytes(payload)
    return NeotomaPollenScreen(content, hashlib.sha256(content).hexdigest())
