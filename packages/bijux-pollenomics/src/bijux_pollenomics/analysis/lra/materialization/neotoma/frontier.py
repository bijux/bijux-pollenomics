"""Compact source-authenticated Neotoma LRA prerequisite accounting."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
from typing import Any, cast

from bijux_pollenomics.evidence.sources.neotoma.contract import COUNTRY_CODES

from ..models import canonical_bytes
from ..reading import NeotomaEvidence
from .accounting import MISSING_LRA_EVIDENCE, source_accounting


@dataclass(frozen=True)
class NeotomaLraFrontier:
    """Immutable prerequisite projection; never an executable LRA request."""

    canonical_json: bytes
    result_digest: str

    def as_dict(self) -> dict[str, Any]:
        """Return an independent copy of the canonical projection."""
        return cast(dict[str, Any], json.loads(self.canonical_json))


def assess_neotoma_lra_frontier(
    evidence: NeotomaEvidence,
    selected_sample_ids: Sequence[str] | None = None,
) -> NeotomaLraFrontier:
    """Partition actual source prerequisites without supplying scientific decisions.

    The existing admission audit is deliberately conservative and complete, but its
    four scientific blockers are global manifest fields.  This projection makes the
    affected sample, observation, chronology, variable and site denominators
    machine-readable while retaining the exact source selection.  It cannot accept
    classification, choose an age, bind a parameter, infer basin geometry or create
    a numerical request.
    """
    evidence.assert_unchanged()
    accounting = source_accounting(evidence, selected_sample_ids)
    manifest = evidence.manifest()
    available_observations = 0
    selected_observations = 0
    selected_count_candidates = 0
    selected_count_refusals = 0
    candidate_variables: set[str] = set()
    countries: dict[str, Counter[str]] = {
        country: Counter() for country in COUNTRY_CODES
    }
    for source in evidence.rows("observations"):
        available_observations += 1
        record = accounting.observation(source)
        if record["selected"] is not True:
            continue
        selected_observations += 1
        observation = cast(dict[str, Any], record["source_observation"])
        country = str(observation["country_code"])
        country_counts = countries[country]
        country_counts["selected_observations"] += 1
        if record["count_status"] == "count_candidate":
            selected_count_candidates += 1
            country_counts["count_candidate_observations"] += 1
            candidate_variables.add(str(observation["variable_id"]))
        else:
            selected_count_refusals += 1
            country_counts["refused_count_observations"] += 1

    selected_samples = 0
    samples_with_count_candidates = 0
    selected_sites: set[str] = set()
    selected_datasets: set[str] = set()
    selected_collection_units: set[str] = set()
    samples_with_age_claims = 0
    samples_without_age_claims = 0
    selected_age_claims = 0
    samples_with_count_and_age_claims = 0
    samples_with_count_and_comparable_age_claims = 0
    chronology_postures: Counter[str] = Counter()
    country_chronology_postures: dict[str, Counter[str]] = {
        country: Counter() for country in COUNTRY_CODES
    }
    for source in accounting.indexes["samples"].values():
        record = accounting.sample(source)
        if record["selected"] is not True:
            continue
        selected_samples += 1
        sample = cast(dict[str, Any], record["source_sample"])
        country = str(sample["country_code"])
        country_counts = countries[country]
        country_counts["selected_samples"] += 1
        if cast(int, record["count_candidate_observations"]) > 0:
            samples_with_count_candidates += 1
            country_counts["samples_with_count_candidates"] += 1
        else:
            country_counts["samples_without_count_candidates"] += 1
        selected_sites.add(str(sample["site_id"]))
        selected_datasets.add(str(sample["dataset_id"]))
        selected_collection_units.add(str(sample["collection_unit_id"]))
        chronology = cast(dict[str, Any], record["chronology"])
        claim_count = cast(int, chronology["claim_count"])
        projected_claims = cast(list[dict[str, Any]], chronology["claims"])
        selected_age_claims += claim_count
        country_counts["age_claims"] += claim_count
        if claim_count:
            samples_with_age_claims += 1
            country_counts["samples_with_age_claims"] += 1
            if cast(int, record["count_candidate_observations"]) > 0:
                samples_with_count_and_age_claims += 1
                country_counts["samples_with_count_and_age_claims"] += 1
                if any(
                    projected["source_claim"].get("comparability_status")
                    == "comparable"
                    for projected in projected_claims
                ):
                    samples_with_count_and_comparable_age_claims += 1
                    country_counts["samples_with_count_and_comparable_age_claims"] += 1
        else:
            samples_without_age_claims += 1
            country_counts["samples_without_age_claims"] += 1
        for projected in projected_claims:
            claim = cast(dict[str, Any], projected["source_claim"])
            posture = claim.get("comparability_status")
            chronology_postures[
                posture if isinstance(posture, str) else "missing_status"
            ] += 1
            country_chronology_postures[country][
                posture if isinstance(posture, str) else "missing_status"
            ] += 1

    expected_observations = cast(int, manifest["surfaces"]["observations"]["row_count"])
    if available_observations != expected_observations:
        raise ValueError("Observation frontier does not cover the source denominator")
    if selected_count_candidates + selected_count_refusals != selected_observations:
        raise ValueError("Selected count frontier is not a complete partition")
    if selected_samples != len(accounting.selected_samples):
        raise ValueError("Selected sample frontier is not a complete partition")
    if (
        sum(counts["age_claims"] for counts in countries.values())
        != selected_age_claims
    ):
        raise ValueError("Country age-claim frontier is not a complete partition")
    if (
        sum(
            counts["samples_with_count_and_age_claims"] for counts in countries.values()
        )
        != samples_with_count_and_age_claims
    ):
        raise ValueError("Country count/age intersection is not a complete partition")
    if (
        sum(
            counts["samples_with_count_and_comparable_age_claims"]
            for counts in countries.values()
        )
        != samples_with_count_and_comparable_age_claims
    ):
        raise ValueError(
            "Country comparable-age intersection is not a complete partition"
        )

    selection_ids = sorted(accounting.selected_samples)
    blocker_denominator = {
        "selected_samples": selected_samples,
        "selected_observations": selected_observations,
        "selected_count_candidate_observations": selected_count_candidates,
    }
    country_fields = (
        "selected_samples",
        "samples_with_count_candidates",
        "samples_without_count_candidates",
        "samples_with_count_and_age_claims",
        "samples_with_count_and_comparable_age_claims",
        "samples_with_age_claims",
        "samples_without_age_claims",
        "age_claims",
        "selected_observations",
        "count_candidate_observations",
        "refused_count_observations",
    )
    empty = selected_samples == 0
    payload: dict[str, Any] = {
        "schema_version": "neotoma-lra-prerequisite-frontier.v3",
        "source_family": "neotoma",
        "source_snapshot_id": manifest["source_snapshot_id"],
        "normalized_build_id": manifest["build_id"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "selection": {
            "mode": (
                "all_source_samples"
                if selected_sample_ids is None
                else "explicit_sample_ids"
            ),
            "sample_ids": selection_ids,
            "sample_ids_sha256": hashlib.sha256(
                canonical_bytes(selection_ids)
            ).hexdigest(),
        },
        "source_denominators": {
            "available_samples": len(accounting.indexes["samples"]),
            "available_observations": available_observations,
            "source_age_claims": len(accounting.indexes["age_claims"]),
            "source_conflicts": len(accounting.indexes["conflicts"]),
            "source_orphans": len(accounting.indexes["orphans"]),
        },
        "selected_denominators": {
            "samples": selected_samples,
            "observations": selected_observations,
            "count_candidate_observations": selected_count_candidates,
            "refused_count_observations": selected_count_refusals,
            "samples_with_count_candidates": samples_with_count_candidates,
            "samples_without_count_candidates": (
                selected_samples - samples_with_count_candidates
            ),
            "sites": len(selected_sites),
            "datasets": len(selected_datasets),
            "collection_units": len(selected_collection_units),
            "candidate_source_variables": len(candidate_variables),
            "age_claims": selected_age_claims,
            "samples_with_age_claims": samples_with_age_claims,
            "samples_without_age_claims": samples_without_age_claims,
            "samples_with_count_and_age_claims": samples_with_count_and_age_claims,
            "samples_with_count_and_comparable_age_claims": (
                samples_with_count_and_comparable_age_claims
            ),
            "age_claim_comparability_counts": dict(sorted(chronology_postures.items())),
        },
        "country_denominators": {
            country: {
                **{field: counts[field] for field in country_fields},
                "age_claim_comparability_counts": dict(
                    sorted(country_chronology_postures[country].items())
                ),
            }
            for country, counts in sorted(countries.items())
        },
        "prerequisites": [
            {
                "prerequisite": reason,
                "status": "not_supplied",
                **blocker_denominator,
            }
            for reason in (() if empty else MISSING_LRA_EVIDENCE)
        ],
        "frontier_status": "empty_selection" if empty else "refused",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "reason_codes": (
            ["empty_source_sample_selection"] if empty else list(MISSING_LRA_EVIDENCE)
        ),
        "claims_not_made": [
            "classification_review_acceptance",
            "chronology_selection",
            "ppe_or_fall_speed_binding",
            "basin_geometry_admission",
            "known_pollen_denominator",
            "numerical_lra_execution",
            "scientific_acceptance",
        ],
    }
    evidence.assert_unchanged()
    content = canonical_bytes(payload)
    return NeotomaLraFrontier(content, hashlib.sha256(content).hexdigest())
