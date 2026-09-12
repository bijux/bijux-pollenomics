"""Keep scalar, absolute-count and pollen eligibility as distinct source facts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from ..counts import assess_nonnegative_integer
from ..models import SourceRow, canonical_bytes
from .reading import SeadEvidence

_ABSOLUTE_COUNT_DEFINITION = "The absolute number of the counted element (e.g. seeds, fossils) present in the sample."


@dataclass
class SeadAccounting:
    """Source-owned relation indexes and occurrence counts, never merged pollen."""

    evidence: SeadEvidence
    entities: dict[str, SourceRow]
    datasets: dict[str, SourceRow]
    taxa: dict[str, SourceRow]
    values: dict[str, SourceRow]
    methods: dict[int, dict[str, Any]]
    elements: dict[int, dict[str, Any]]
    analysis_values: dict[int, dict[str, Any]]
    observation_counts: Counter[str] = field(default_factory=Counter)
    count_candidates: Counter[str] = field(default_factory=Counter)
    pollen_methods: Counter[str] = field(default_factory=Counter)

    def observation(self, source: SourceRow) -> dict[str, Any]:
        row = source.payload()
        native = row["source_row"]
        value_field = row["source_value_field"]
        presence = (
            "absent"
            if value_field not in native
            else "null"
            if native[value_field] is None
            else "reported"
        )
        scalar, scalar_reason = assess_nonnegative_integer(row.get("source_value"))
        entity_id = row["entity_relation_id"]
        entity_source = self.entities.get(entity_id)
        entity = entity_source.payload() if entity_source else None
        semantics = row["source_semantics"]
        dataset_source = self.datasets.get(semantics.get("dataset_semantics_id"))
        dataset = dataset_source.payload() if dataset_source else None
        value_source = self.values.get(semantics.get("value_semantics_id"))
        value_semantics = value_source.payload() if value_source else None
        taxon_id = row.get("taxon_relation_id")
        taxon_source = self.taxa.get(taxon_id) if isinstance(taxon_id, str) else None
        taxon = taxon_source.payload() if taxon_source else None
        method_id = dataset["dataset"].get("method_id") if dataset else None
        method = self.methods.get(method_id) if type(method_id) is int else None
        data_type = dataset.get("source_data_type") if dataset else None
        element_id = native.get("abundance_element_id")
        element = self.elements.get(element_id) if type(element_id) is int else None
        ownership_reasons = []
        if canonical_bytes(row.get("source_value")) != canonical_bytes(
            native.get(value_field)
        ):
            ownership_reasons.append("source_value_projection_mismatch")
        owner_native = native
        if row["source_table"] == "tbl_analysis_taxon_counts":
            owner_native = self.analysis_values.get(native.get("analysis_value_id"), {})
        if entity is None:
            ownership_reasons.append("source_analysis_entity_relation_missing")
        elif (
            type(owner_native.get("analysis_entity_id")) is not int
            or canonical_bytes(owner_native["analysis_entity_id"])
            != canonical_bytes(entity["analysis_entity_id"])
            or row["country_code"] != entity["country_code"]
        ):
            ownership_reasons.append("source_analysis_entity_ownership_mismatch")
        if (
            dataset is None
            or entity is None
            or canonical_bytes(dataset["dataset"]["dataset_id"])
            != canonical_bytes(entity["dataset_id"])
        ):
            ownership_reasons.append("source_dataset_relation_missing_or_mismatched")
        count_reasons = list(ownership_reasons)
        if presence != "reported":
            count_reasons.append(f"source_value_{presence}")
        if scalar_reason is not None:
            count_reasons.append(scalar_reason)
        declared_absolute_count = (
            isinstance(data_type, dict)
            and type(data_type.get("data_type_id")) is int
            and data_type["data_type_id"] == 5
            and data_type.get("data_type_name") == "Abundance"
            and data_type.get("definition") == _ABSOLUTE_COUNT_DEFINITION
        )
        if not declared_absolute_count:
            count_reasons.append("source_absolute_count_declaration_unavailable")
        if semantics.get("source_unit_id") is not None:
            count_reasons.append("source_unit_not_admitted_as_count")
        pollen_method = (
            method is not None
            and type(method_id) is int
            and method_id == 14
            and method.get("method_name") == "Palynology"
            and method.get("description") == "Pollen analysis."
        )
        scientific_reasons = {
            "source_pollen_identity_not_accepted",
            "lra_chronology_decision_not_supplied",
            "parameter_binding_not_supplied",
            "basin_geometry_not_supplied",
            *ownership_reasons,
        }
        if not pollen_method:
            scientific_reasons.add("source_method_not_admitted_as_pollen")
        if taxon is None:
            scientific_reasons.add("source_taxon_relation_unavailable")
        if element is None:
            scientific_reasons.add("source_element_metadata_unavailable")
        self.observation_counts[entity_id] += 1
        self.count_candidates[entity_id] += int(not count_reasons)
        self.pollen_methods[entity_id] += int(pollen_method)
        return {
            "source_locator": source.locator(),
            "source_observation": row,
            "source_value_presence": presence,
            "numeric_scalar_compatibility": "compatible"
            if scalar_reason is None
            else "refused",
            "numeric_scalar_reason": scalar_reason,
            "exact_nonnegative_integer": scalar,
            "source_count_compatibility": "source_absolute_count_candidate"
            if not count_reasons
            else "refused",
            "source_count_reason_codes": sorted(set(count_reasons)),
            "source_count_basis": "dataset_data_type_declares_absolute_count"
            if declared_absolute_count
            else None,
            "source_pollen_method_candidate": pollen_method,
            "source_entity_relation": entity,
            "source_dataset_semantics": dataset,
            "source_method": method,
            "source_value_semantics": value_semantics,
            "source_taxon_relation": taxon,
            "source_element": element,
            "pollen_grain_count_eligibility": "not_admitted",
            "lra_admission_status": "refused",
            "lra_reason_codes": sorted(scientific_reasons),
        }


def sead_accounting(evidence: SeadEvidence) -> SeadAccounting:
    def indexed(field_name: str, identity: str) -> dict[str, SourceRow]:
        result = {}
        for row in evidence.rows("observation_relation_index.json", field_name):
            key = row.payload()[identity]
            if not isinstance(key, str) or not key or key in result:
                raise ValueError("SEAD relation identity is missing or duplicated")
            result[key] = row
        return result

    return SeadAccounting(
        evidence,
        indexed("entity_relations", "entity_relation_id"),
        indexed("dataset_semantics", "dataset_semantics_id"),
        indexed("taxon_relations", "taxon_relation_id"),
        indexed("value_semantics", "value_semantics_id"),
        {row["method_id"]: row for row in evidence.raw_rows("tbl_methods")},
        {
            row["abundance_element_id"]: row
            for row in evidence.raw_rows("tbl_abundance_elements")
        },
        {
            row["analysis_value_id"]: row
            for row in evidence.raw_rows("tbl_analysis_values")
        },
    )
