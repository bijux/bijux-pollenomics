"""Sample-owned source accounting with explicit unresolved LRA admission."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
import json
from typing import Any

from bijux_pollenomics.evidence.sources.neotoma.contract import SURFACE_ID_FIELDS

from ..chronology import chronology_projection
from ..counts import assess_count
from ..models import SourceRow, canonical_bytes
from ..reading import NeotomaEvidence

MISSING_LRA_EVIDENCE = (
    "classification_decision_not_supplied",
    "lra_chronology_decision_not_supplied",
    "parameter_binding_not_supplied",
    "basin_geometry_not_supplied",
)
PARENT_SURFACES = {
    "sample_id": "samples",
    "dataset_id": "datasets",
    "collection_unit_id": "collection_units",
    "site_id": "sites",
    "variable_id": "variables",
}


@dataclass
class SourceAccounting:
    """Per-run accumulators; totals retain units and occurrence denominators."""

    evidence: NeotomaEvidence
    indexes: dict[str, dict[str, SourceRow]]
    selected_samples: frozenset[str]
    claims: dict[str, list[SourceRow]]
    conflicts_by_subject: dict[str, tuple[str, ...]]
    observations: Counter[str] = field(default_factory=Counter)
    count_candidates: Counter[str] = field(default_factory=Counter)
    value_statuses: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    sums: dict[str, dict[bytes, tuple[object, int]]] = field(
        default_factory=lambda: defaultdict(dict)
    )
    components: dict[str, Counter[tuple[str, bytes]]] = field(
        default_factory=lambda: defaultdict(Counter)
    )

    def observation(self, source: SourceRow) -> dict[str, Any]:
        row = source.payload()
        sample_id = row["sample_id"]
        selected = sample_id in self.selected_samples
        assessment = assess_count(row)
        reasons = []
        for identifier, surface in PARENT_SURFACES.items():
            parent_id = row.get(identifier)
            parent = (
                self.indexes[surface].get(parent_id)
                if isinstance(parent_id, str)
                else None
            )
            if parent is None:
                reasons.append(f"missing_parent_{identifier}")
                continue
            parent_row = parent.payload()
            for owner_field in (
                "dataset_id",
                "collection_unit_id",
                "site_id",
                "country_code",
            ):
                if (
                    owner_field in parent_row
                    and row.get(owner_field) != parent_row[owner_field]
                ):
                    reasons.append(f"{surface}_ownership_mismatch_{owner_field}")
        if assessment.reason is not None:
            reasons.append(assessment.reason)
        conflicts = sorted(
            {
                conflict
                for key in (*PARENT_SURFACES, "observation_id")
                for subject in (row.get(key),)
                if isinstance(subject, str)
                for conflict in self.conflicts_by_subject.get(subject, ())
            }
        )
        if conflicts:
            reasons.append("source_identity_conflict")
        self.observations[sample_id] += 1
        self.value_statuses[sample_id][assessment.source_value_status] += 1
        unit_key = canonical_bytes(row.get("source_unit"))
        self.components[sample_id][(row["variable_id"], unit_key)] += 1
        if assessment.exact_count is not None and not reasons:
            self.count_candidates[sample_id] += 1
            unit, total = self.sums[sample_id].get(
                unit_key, (row.get("source_unit"), 0)
            )
            self.sums[sample_id][unit_key] = (unit, total + assessment.exact_count)
        return {
            "source_locator": source.locator(),
            "source_observation": row,
            "selected": selected,
            "count_status": "count_candidate" if not reasons else "refused",
            "typed_count": assessment.exact_count if not reasons else None,
            "count_reason_codes": sorted(reasons),
            "primary_count_reason": min(reasons) if reasons else None,
            "source_conflict_ids": sorted(conflicts),
            "lra_admission_status": "refused" if selected else "not_selected",
            "primary_lra_reason": MISSING_LRA_EVIDENCE[0]
            if selected
            else "not_selected",
            "lra_reason_codes": list(MISSING_LRA_EVIDENCE)
            if selected
            else ["not_selected"],
        }

    def sample(self, source: SourceRow) -> dict[str, Any]:
        row = source.payload()
        identity = row["sample_id"]
        selected = identity in self.selected_samples
        total = self.observations[identity]
        candidates = self.count_candidates[identity]
        duplicates = [
            {
                "variable_id": variable,
                "source_unit": json.loads(unit),
                "source_unit_json": unit.decode("utf-8").rstrip("\n"),
                "observation_count": count,
            }
            for (variable, unit), count in sorted(self.components[identity].items())
            if count > 1
        ]
        return {
            "source_locator": source.locator(),
            "source_sample": row,
            "selected": selected,
            "observation_count": total,
            "count_candidate_observations": candidates,
            "refused_count_observations": total - candidates,
            "source_value_status_counts": dict(
                sorted(self.value_statuses[identity].items())
            ),
            "count_candidate_sums_by_exact_unit": [
                {"source_unit": unit, "exact_sum": value}
                for _key, (unit, value) in sorted(self.sums[identity].items())
            ],
            "count_sum_scope": "count_candidate_observation_records_not_a_pollen_denominator",
            "pollen_denominator_status": "not_admitted",
            "duplicate_variable_unit_groups": duplicates,
            "chronology": chronology_projection(row, self.claims.get(identity, [])),
            "lra_admission_status": "refused" if selected else "not_selected",
            "primary_lra_reason": MISSING_LRA_EVIDENCE[0]
            if selected
            else "not_selected",
            "lra_reason_codes": list(MISSING_LRA_EVIDENCE)
            if selected
            else ["not_selected"],
        }


def source_accounting(
    evidence: NeotomaEvidence,
    selected_sample_ids: Sequence[str] | None,
) -> SourceAccounting:
    """Index declared source identities and partition an explicit sample selection."""
    indexes = {
        surface: {row.payload()[field]: row for row in evidence.rows(surface)}
        for surface, field in SURFACE_ID_FIELDS.items()
        if surface != "observations"
    }
    available = set(indexes["samples"])
    if selected_sample_ids is None:
        selected = available
    else:
        if isinstance(selected_sample_ids, (str, bytes)) or any(
            not isinstance(value, str) or not value for value in selected_sample_ids
        ):
            raise ValueError(
                "Selected sample IDs must be nonempty source identifier strings"
            )
        selected = set(selected_sample_ids)
        if len(selected) != len(selected_sample_ids):
            raise ValueError("Selected sample IDs must be unique")
        if selected - available:
            raise ValueError("Selected sample IDs are absent from the source inventory")
    claims: dict[str, list[SourceRow]] = defaultdict(list)
    for row in indexes["age_claims"].values():
        claims[row.payload()["subject_id"]].append(row)
    conflicts: dict[str, list[str]] = defaultdict(list)
    for identity, row in indexes["conflicts"].items():
        conflicts[row.payload()["subject_id"]].append(identity)
    return SourceAccounting(
        evidence,
        indexes,
        frozenset(selected),
        dict(claims),
        {subject: tuple(sorted(ids)) for subject, ids in conflicts.items()},
    )
