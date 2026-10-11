"""Retain every native SEAD chronology claim at its analysis-entity owner."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from ..models import SourceRow, canonical_bytes
from .observations import SeadAccounting


@dataclass
class ChronologyAccounting:
    """No default claim, midpoint or conversion is chosen by this audit."""

    observations: SeadAccounting
    claim_counts: Counter[str] = field(default_factory=Counter)
    comparable_counts: Counter[str] = field(default_factory=Counter)
    claimed_ids: set[str] = field(default_factory=set)

    def claim(self, source: SourceRow) -> dict[str, Any]:
        row = source.payload()
        claim_id = row["chronology_claim_id"]
        if (
            not isinstance(claim_id, str)
            or not claim_id
            or claim_id in self.claimed_ids
        ):
            raise ValueError("SEAD chronology identity is missing or duplicated")
        self.claimed_ids.add(claim_id)
        entity_id = row["observation_relation_id"]
        source_entity = self.observations.entities.get(entity_id)
        entity = source_entity.payload() if source_entity else None
        reasons = ["lra_chronology_decision_not_supplied"]
        if entity is None:
            reasons.append("source_analysis_entity_relation_missing")
        else:
            for key in (
                "analysis_entity_id",
                "physical_sample_id",
                "sample_group_id",
                "dataset_id",
            ):
                if canonical_bytes(row[key]) != canonical_bytes(entity[key]):
                    reasons.append("source_chronology_owner_mismatch")
            if (
                row["site_uuid"] != entity["site_uuid"]
                or row["country_code"] != entity["country_code"]
            ):
                reasons.append("source_chronology_owner_mismatch")
            if claim_id not in entity["chronology_link"]["claim_ids"]:
                reasons.append("source_chronology_link_missing")
        self.claim_counts[entity_id] += 1
        self.comparable_counts[entity_id] += int(
            row["comparability_status"] == "comparable"
        )
        return {
            "source_locator": source.locator(),
            "source_claim": row,
            "source_entity_locator": source_entity.locator() if source_entity else None,
            "observation_count_at_analysis_entity": self.observations.observation_counts[
                entity_id
            ],
            "lra_chronology_admission": "refused",
            "reason_codes": sorted(set(reasons)),
            "selected": False,
        }

    def entity(self, source: SourceRow) -> dict[str, Any]:
        row = source.payload()
        key = row["entity_relation_id"]
        expected = row["chronology_link"]["claim_ids"]
        if self.claim_counts[key] != len(expected) or any(
            claim not in self.claimed_ids for claim in expected
        ):
            raise ValueError("SEAD claim accounting does not cover the analysis entity")
        return {
            "source_locator": source.locator(),
            "source_entity_relation": row,
            "observation_count": self.observations.observation_counts[key],
            "source_absolute_count_candidates": self.observations.count_candidates[key],
            "source_pollen_method_candidates": self.observations.pollen_methods[key],
            "chronology_claim_count": self.claim_counts[key],
            "source_comparable_claim_count": self.comparable_counts[key],
            "multiple_claims_retained": self.claim_counts[key] > 1,
            "lra_admission_status": "refused",
            "selected_chronology_claim": None,
        }
