"""Bounded, source-owned Neotoma pollen series for scientific review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
from typing import Any, cast

from bijux_pollenomics.evidence.sources.neotoma.contract import COUNTRY_CODES

from ...models import canonical_bytes
from ...reading import NeotomaEvidence
from ..accounting import MISSING_LRA_EVIDENCE, source_accounting

MAX_SAMPLES = 16
MAX_OBSERVATIONS = 4096


@dataclass(frozen=True)
class NeotomaCandidateSeries:
    """Canonical review export with no selected chronology or LRA admission."""

    canonical_json: bytes
    result_digest: str

    def as_dict(self) -> dict[str, Any]:
        """Return an independent copy of the source-bound export."""
        return cast(dict[str, Any], json.loads(self.canonical_json))


def source_element_status(value: object, element_type: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return "source_element_missing"
    if not isinstance(element_type, str) or not element_type.strip():
        return "source_element_type_missing"
    if value.strip().casefold() != element_type.strip().casefold():
        return "source_element_labels_disagree"
    return (
        "source_label_pollen"
        if value.strip().casefold() == "pollen"
        else "source_element_not_pollen"
    )


def build_neotoma_candidate_series(
    evidence: NeotomaEvidence,
    selected_sample_ids: Sequence[str],
) -> NeotomaCandidateSeries:
    """Export explicit sample slices while retaining source alternatives and refusals.

    A source element labelled pollen and a numeric count are necessary review leads,
    not a taxon classification or a known compatible pollen denominator.  The
    caller must supply a bounded, explicit set of source sample identities.
    """
    if (
        isinstance(selected_sample_ids, (str, bytes))
        or not 1 <= len(selected_sample_ids) <= MAX_SAMPLES
    ):
        raise ValueError(f"Select between 1 and {MAX_SAMPLES} source samples")
    evidence.assert_unchanged()
    accounting = source_accounting(evidence, selected_sample_ids)
    observations: dict[str, list[dict[str, Any]]] = {
        sample_id: [] for sample_id in accounting.selected_samples
    }
    countries: dict[str, Counter[str]] = {
        country: Counter() for country in COUNTRY_CODES
    }
    selected_observations = 0
    for source in evidence.rows("observations"):
        source_row = source.payload()
        sample_id = source_row.get("sample_id")
        if sample_id not in accounting.selected_samples:
            continue
        selected_observations += 1
        if selected_observations > MAX_OBSERVATIONS:
            raise ValueError(f"Selected slice exceeds {MAX_OBSERVATIONS} observations")
        record = accounting.observation(source)
        observation = cast(dict[str, Any], record["source_observation"])
        country = str(observation["country_code"])
        counts = countries[country]
        counts["observations"] += 1
        element_status = source_element_status(
            observation.get("source_element"),
            observation.get("source_element_type"),
        )
        count_candidate = record["count_status"] == "count_candidate"
        review_candidate = count_candidate and element_status == "source_label_pollen"
        counts[
            "count_candidate_observations"
            if count_candidate
            else "refused_count_observations"
        ] += 1
        if review_candidate:
            counts["pollen_labelled_count_candidates"] += 1
        observations[cast(str, sample_id)].append(
            {
                **record,
                "source_element_status": element_status,
                "pollen_count_review_candidate": review_candidate,
                "pollen_review_reason_codes": (
                    []
                    if review_candidate
                    else [
                        *cast(list[str], record["count_reason_codes"]),
                        *(
                            []
                            if element_status == "source_label_pollen"
                            else [element_status]
                        ),
                    ]
                ),
            }
        )

    series = []
    for sample_id in sorted(accounting.selected_samples):
        source = accounting.indexes["samples"][sample_id]
        sample_record = accounting.sample(source)
        sample = cast(dict[str, Any], sample_record["source_sample"])
        country = str(sample["country_code"])
        counts = countries[country]
        counts["samples"] += 1
        counts["lra_refused_samples"] += 1
        chronology = cast(dict[str, Any], sample_record["chronology"])
        claims = cast(list[dict[str, Any]], chronology["claims"])
        counts["age_claims"] += len(claims)
        comparable = sum(
            claim["source_claim"].get("comparability_status") == "comparable"
            for claim in claims
        )
        counts["comparable_age_claims"] += comparable
        if comparable:
            counts["samples_with_comparable_age_claims"] += 1
        sample_observations = sorted(
            observations[sample_id],
            key=lambda row: str(row["source_observation"]["observation_id"]),
        )
        pollen_candidates = [
            row for row in sample_observations if row["pollen_count_review_candidate"]
        ]
        exact_units = sorted(
            {
                canonical_bytes(row["source_observation"].get("source_unit"))
                for row in pollen_candidates
            }
        )
        reasons = list(MISSING_LRA_EVIDENCE)
        if not pollen_candidates:
            reasons.append("no_pollen_labelled_count_candidates")
        if len(exact_units) > 1:
            reasons.append("pollen_candidate_source_units_differ")
        if sample_record["duplicate_variable_unit_groups"]:
            reasons.append("duplicate_source_variable_exact_unit")
        if not comparable:
            reasons.append("no_comparable_sample_age_claim")
        if any(row["source_conflict_ids"] for row in sample_observations):
            reasons.append("source_identity_conflict")
        series.append(
            {
                "sample_id": sample_id,
                "source_sample": sample,
                "source_locator": source.locator(),
                "chronology": chronology,
                "observations": sample_observations,
                "observation_count": len(sample_observations),
                "pollen_labelled_count_candidates": len(pollen_candidates),
                "candidate_exact_source_units": [
                    json.loads(unit) for unit in exact_units
                ],
                "duplicate_variable_unit_groups": sample_record[
                    "duplicate_variable_unit_groups"
                ],
                "lra_admission_status": "refused",
                "lra_reason_codes": reasons,
            }
        )

    if sum(row["observation_count"] for row in series) != selected_observations:
        raise ValueError("Sample series does not reconcile selected observations")
    if sum(counts["samples"] for counts in countries.values()) != len(series):
        raise ValueError("Country series does not reconcile selected samples")
    if (
        sum(counts["observations"] for counts in countries.values())
        != selected_observations
    ):
        raise ValueError("Country series does not reconcile selected observations")
    manifest = evidence.manifest()
    payload: dict[str, Any] = {
        "schema_version": "neotoma-candidate-sample-series.v1",
        "source_family": "neotoma",
        "source_snapshot_id": manifest["source_snapshot_id"],
        "normalized_build_id": manifest["build_id"],
        "raw_manifest_sha256": dict(evidence.raw_files)["manifest.json"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "selection": {
            "mode": "explicit_sample_ids",
            "sample_ids": sorted(accounting.selected_samples),
        },
        "source_denominators": {
            "available_samples": len(accounting.indexes["samples"]),
            "available_observations": manifest["surfaces"]["observations"]["row_count"],
            "source_age_claims": len(accounting.indexes["age_claims"]),
        },
        "selected_denominators": {
            "samples": len(series),
            "lra_refused_samples": len(series),
            "observations": selected_observations,
            "count_candidate_observations": sum(
                counts["count_candidate_observations"] for counts in countries.values()
            ),
            "pollen_labelled_count_candidates": sum(
                counts["pollen_labelled_count_candidates"]
                for counts in countries.values()
            ),
            "age_claims": sum(counts["age_claims"] for counts in countries.values()),
        },
        "country_denominators": {
            country: {
                field: counts[field]
                for field in (
                    "samples",
                    "observations",
                    "count_candidate_observations",
                    "refused_count_observations",
                    "pollen_labelled_count_candidates",
                    "age_claims",
                    "comparable_age_claims",
                    "samples_with_comparable_age_claims",
                    "lra_refused_samples",
                )
            }
            for country, counts in sorted(countries.items())
        },
        "series": series,
        "series_scope": "explicit_samples_not_asserted_shared_core",
        "temporal_order_status": "not_established_without_chronology_selection",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "claims_not_made": [
            "approved_taxon_or_ppe_mapping",
            "selected_chronology",
            "compatible_pollen_denominator",
            "basin_geometry_admission",
            "numerical_lra_execution",
            "scientific_acceptance",
        ],
    }
    evidence.assert_unchanged()
    content = canonical_bytes(payload)
    return NeotomaCandidateSeries(content, hashlib.sha256(content).hexdigest())
