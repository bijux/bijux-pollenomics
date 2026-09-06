from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

__all__ = [
    "AnimalComparisonContract",
    "build_animal_comparison_contract_payload",
    "govern_animal_comparison_payload",
]


@dataclass(frozen=True)
class AnimalComparisonContract:
    contract_id: str
    contract_version: str
    output_schema_version: str
    left_evidence_class: str
    right_evidence_class: str
    input_surface_patterns: tuple[str, ...]
    comparison_unit: str
    identity_rule: str
    temporal_rule: str
    spatial_rule: str
    denominator_rule: str
    uncertainty_rule: str
    lineage_rule: str
    coverage_limitations: tuple[str, ...]
    output_metrics: tuple[str, ...]
    interpretation_posture: str
    allowed_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    qualified_scientific_review_required: bool


_CONTRACTS = (
    AnimalComparisonContract(
        contract_id="animal-human-chronology-overlap",
        contract_version="1.1.0",
        output_schema_version="animal-human-chronology-overlap.v1",
        left_evidence_class="animal_ancient_dna_locality",
        right_evidence_class="human_ancient_dna_locality",
        input_surface_patterns=(
            "data/adna/final/countries/country_publication_index.json",
            "docs/report/countries/<country>/<country>_aadr_v66_bundle.json",
        ),
        comparison_unit="country-partitioned locality chronology interval",
        identity_rule=(
            "Animal localities retain species and sample-owned locality identity; "
            "human localities retain AADR genetic and locality identity."
        ),
        temporal_rule=(
            "Compare only valid closed [younger_bp, older_bp] intervals; endpoint "
            "contact counts as overlap and missing or reversed bounds are non-comparable."
        ),
        spatial_rule=(
            "Rows are compared only within the same governed modern-country partition; "
            "this contract performs no distance or site-coincidence inference."
        ),
        denominator_rule=(
            "For each animal country/species row, every governed human locality is "
            "exactly one of overlapping, non-overlapping, or non-comparable. The "
            "reported right-record comparison denominator sums those row-scoped "
            "partitions and is not a unique-human-locality count."
        ),
        uncertainty_rule=(
            "Interval overlap is descriptive and does not propagate calibration or "
            "sampling uncertainty beyond the stored bounds."
        ),
        lineage_rule=(
            "Source-family identities remain distinct; repeated locality names do not "
            "create independent corroboration."
        ),
        coverage_limitations=(
            "Only countries with admitted animal publication rows are evaluated.",
            "Country-level interval overlap is not spatial co-location.",
            "Source ascertainment and recovery differ between species and countries.",
        ),
        output_metrics=(
            "animal_locality_count",
            "human_locality_count",
            "overlapping_human_localities",
            "non_overlapping_human_localities",
            "noncomparable_human_localities",
            "right_record_comparison_denominator",
            "comparable_right_record_comparison_denominator",
        ),
        interpretation_posture="exploratory_descriptive_implemented_unverified",
        allowed_claims=("country-partitioned chronology intervals overlap",),
        prohibited_claims=(
            "co-occurrence proves migration or causation",
            "country-level overlap proves site co-location",
            "the compared sources have equal sampling completeness",
        ),
        qualified_scientific_review_required=True,
    ),
    AnimalComparisonContract(
        contract_id="animal-pollen-chronology-overlap",
        contract_version="1.1.0",
        output_schema_version="animal-pollen-chronology-overlap.v1",
        left_evidence_class="animal_ancient_dna_locality",
        right_evidence_class="pollen_context_record",
        input_surface_patterns=(
            "data/adna/final/countries/country_publication_index.json",
            "docs/report/regions/nordic/nordic_bundle.json",
        ),
        comparison_unit="country-partitioned locality and pollen chronology interval",
        identity_rule=(
            "Animal sample/locality identities and pollen source-record identities "
            "remain separate throughout the comparison."
        ),
        temporal_rule=(
            "Compare only valid closed [younger_bp, older_bp] intervals; endpoint "
            "contact counts as overlap and missing or reversed bounds are non-comparable."
        ),
        spatial_rule=(
            "Rows are compared only within the same governed modern-country partition; "
            "this contract performs no distance or site-coincidence inference."
        ),
        denominator_rule=(
            "For each animal country/species row, every available pollen record is "
            "exactly one of overlapping, non-overlapping, or non-comparable. The "
            "reported right-record comparison denominator sums those row-scoped "
            "partitions and is not a unique-pollen-record count."
        ),
        uncertainty_rule=(
            "Interval overlap is descriptive; source uncertainty and observation-unit "
            "differences are not converted into a shared quantitative measure."
        ),
        lineage_rule=(
            "Animal and pollen evidence never merge identities, totals, ecological "
            "classes, or event domains."
        ),
        coverage_limitations=(
            "Only admitted pollen-context rows with numeric intervals are comparable.",
            "Country-level interval overlap is not spatial co-location.",
            "Absence of admitted pollen rows is unavailable evidence, not zero pollen.",
        ),
        output_metrics=(
            "animal_locality_count",
            "pollen_record_count",
            "overlapping_pollen_records",
            "non_overlapping_pollen_records",
            "noncomparable_pollen_records",
            "right_record_comparison_denominator",
            "comparable_right_record_comparison_denominator",
        ),
        interpretation_posture="exploratory_descriptive_implemented_unverified",
        allowed_claims=("country-partitioned chronology intervals overlap",),
        prohibited_claims=(
            "animal evidence is pollen evidence",
            "co-occurrence proves cultivation, migration, or causation",
            "no admitted context rows means observed absence",
        ),
        qualified_scientific_review_required=True,
    ),
)


def build_animal_comparison_contract_payload() -> dict[str, object]:
    """Return the exact versioned contracts for published animal comparisons."""
    contracts = []
    for contract in _CONTRACTS:
        record = asdict(contract)
        record["contract_digest"] = _digest(record)
        contracts.append(record)
    return {
        "schema_version": "animal-comparison-contract-registry.v1",
        "contract_count": len(contracts),
        "contracts": contracts,
    }


def govern_animal_comparison_payload(
    payload: dict[str, object],
    *,
    contract_id: str,
) -> dict[str, object]:
    """Bind one comparison result to its contract and truthful disposition."""
    contract = _contract(contract_id)
    if payload.get("schema_version") != contract.output_schema_version:
        raise ValueError(
            f"comparison output schema does not match {contract.contract_id}"
        )
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("comparison output rows must be a list of objects")
    _validate_denominators(contract, rows)
    right_record_denominator = _right_record_comparison_denominator(contract, rows)
    comparable_record_denominator = _comparable_right_record_denominator(contract, rows)
    reasons = ["qualified_comparison_review_missing"]
    status = "implemented_unverified"
    if not rows:
        status = "refused"
        reasons.insert(0, "no_comparison_rows")
    elif comparable_record_denominator == 0:
        status = "refused"
        reasons.insert(0, "required_comparison_dimension_unavailable")

    contract_record = asdict(contract)
    contract_record["contract_digest"] = _digest(contract_record)
    return {
        **payload,
        "comparison_contract": contract_record,
        "comparison_disposition": {
            "status": status,
            "reason_codes": reasons,
            "right_record_comparison_denominator": right_record_denominator,
            "comparable_right_record_comparison_denominator": (
                comparable_record_denominator
            ),
            "qualified_scientific_review_required": True,
        },
    }


def _contract(contract_id: str) -> AnimalComparisonContract:
    for contract in _CONTRACTS:
        if contract.contract_id == contract_id:
            return contract
    raise ValueError(f"unknown animal comparison contract: {contract_id}")


def _validate_denominators(
    contract: AnimalComparisonContract, rows: list[object]
) -> None:
    if contract.contract_id == "animal-human-chronology-overlap":
        total_key = "human_locality_count"
        partition_keys = (
            "overlapping_human_localities",
            "non_overlapping_human_localities",
            "noncomparable_human_localities",
        )
    else:
        total_key = "pollen_record_count"
        partition_keys = (
            "overlapping_pollen_records",
            "non_overlapping_pollen_records",
            "noncomparable_pollen_records",
        )
    for value in rows:
        if not isinstance(value, dict):
            raise ValueError("comparison row must be an object")
        total = _non_negative_int(value.get(total_key), field=total_key)
        partition_total = sum(
            _non_negative_int(value.get(key), field=key) for key in partition_keys
        )
        if total != partition_total:
            raise ValueError("comparison denominator does not reconcile")


def _comparable_right_record_denominator(
    contract: AnimalComparisonContract, rows: list[object]
) -> int:
    noncomparable_key = (
        "noncomparable_human_localities"
        if contract.contract_id == "animal-human-chronology-overlap"
        else "noncomparable_pollen_records"
    )
    return sum(
        _right_row_count(contract, row)
        - _non_negative_int(row.get(noncomparable_key), field=noncomparable_key)
        for row in rows
        if isinstance(row, dict)
    )


def _right_record_comparison_denominator(
    contract: AnimalComparisonContract, rows: list[object]
) -> int:
    return sum(_right_row_count(contract, row) for row in rows if isinstance(row, dict))


def _right_row_count(contract: AnimalComparisonContract, row: dict[str, object]) -> int:
    key = (
        "human_locality_count"
        if contract.contract_id == "animal-human-chronology-overlap"
        else "pollen_record_count"
    )
    return _non_negative_int(row.get(key), field=key)


def _non_negative_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"comparison field must be a non-negative integer: {field}")
    return value


def _digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
