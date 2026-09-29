"""Review rows and exact-unit occurrence accounting, without inferred taxonomy."""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any

from ..source_completion.evidence import digest


def review_row(
    *,
    row_id: str,
    source: str,
    native_id: object,
    label: object,
    domain: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Create an unresolved review row with source identity and explicit nulls."""
    return {
        "review_row_id": row_id,
        "source_family": source,
        "source_native_id": native_id,
        "source_reported_name": label,
        "source_rank": None,
        "source_domain": domain,
        "source_element_type": None,
        "source_units": [],
        "source_groups": [],
        "current_mapping_status": "unmapped",
        "current_mapping_status_namespace": "review_projection_mapping_posture",
        "qualifier_markers": [],
        "proposed_accepted_taxon_concept_id": None,
        "proposed_accepted_taxon_name": None,
        "proposed_accepted_rank": None,
        "proposed_primary_group_id": None,
        "proposed_primary_subgroup_id": None,
        "proposed_role_ids": [],
        "proposed_lra_model_taxon": None,
        "proposed_pft_group_id": None,
        "proposed_ppe_parameter_id": None,
        "proposed_fall_speed_parameter_id": None,
        "source_pft": None,
        "source_lct": None,
        "parameter_candidates": [],
        "observation_count": None,
        "sample_count": None,
        "country_counts": {},
        "value_totals_by_exact_unit": [],
        "pollen_mass_coverage": None,
        "pollen_mass_coverage_reason": "No reviewed retained-pollen denominator is established by this inventory.",
        "example_observation_ids": [],
        "supporting_evidence": evidence,
        "review_state": "needs_discussion",
        "reviewer_id": None,
        "decision_date": None,
        "review_rationale": None,
        "review_confidence": "unresolved",
        "publication_allowed": False,
        "source_identity_sha256": digest(evidence),
    }


class Occurrences:
    """Count every source observation once; never add incompatible values."""

    def __init__(self) -> None:
        """Initialize identity, country and exact-unit occurrence counters."""
        self.ids: set[str] = set()
        self.countries: dict[str, Counter[str]] = defaultdict(Counter)
        self.counts: Counter[str] = Counter()
        self.totals: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
        self.value_states: Counter[tuple[str, str | None, str]] = Counter()
        self.examples: dict[str, list[str]] = defaultdict(list)

    def add(
        self,
        key: str,
        observation_id: str,
        *,
        country: str | None,
        unit: str | None,
        value: object,
    ) -> None:
        """Count one observation and retain its value state within its source unit."""
        if observation_id in self.ids:
            raise ValueError(f"Duplicate observation identity: {observation_id}")
        self.ids.add(observation_id)
        self.counts[key] += 1
        self.countries[key][country or "UNASSIGNED"] += 1
        self.examples[key].append(observation_id)
        unit_key = unit
        country_key = country or "UNASSIGNED"
        state = "missing_or_non_numeric"
        if not isinstance(value, bool) and isinstance(value, (int, float, str)):
            try:
                number = Decimal(str(value))
                if number.is_finite():
                    if unit is not None and unit != "":
                        total_key = (key, unit, country_key)
                        previous = self.totals[total_key]
                        with localcontext() as context:
                            context.prec = (
                                max(previous.adjusted(), number.adjusted())
                                - min(
                                    int(previous.as_tuple().exponent),
                                    int(number.as_tuple().exponent),
                                )
                                + 2
                            )
                            self.totals[total_key] = previous + number
                        state = (
                            "reported_zero"
                            if number == 0
                            else "reported_nonzero_numeric"
                        )
                    else:
                        state = "reported_numeric_unit_unresolved"
            except InvalidOperation:
                pass
        self.value_states[(key, unit_key, state)] += 1

    def annotate(self, row: dict[str, Any], key: str) -> None:
        """Attach reconciled counts and unit-separated totals to a review row."""
        row["observation_count"] = self.counts[key]
        row["country_counts"] = dict(sorted(self.countries[key].items()))
        row["example_observation_ids"] = sorted(self.examples[key])[:3]
        row["value_totals_by_exact_unit"] = [
            {
                "source_unit": unit,
                "country_code": country,
                "reported_value_sum": str(value),
                "interpretation": "Exact source-unit sum; not an accepted pollen denominator or LRA input.",
            }
            for (owner, unit, country), value in sorted(self.totals.items())
            if owner == key
        ]
        row["source_value_state_counts"] = [
            {"source_unit": unit, "value_state": state, "count": count}
            for (owner, unit, state), count in sorted(
                self.value_states.items(),
                key=lambda item: (
                    item[0][0],
                    item[0][1] is not None,
                    item[0][1] or "",
                    item[0][2],
                ),
            )
            if owner == key
        ]
