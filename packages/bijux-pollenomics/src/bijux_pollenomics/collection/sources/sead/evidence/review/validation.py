"""Fail-closed validation for the SEAD classification review packet."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import cast

JsonObject = dict[str, object]

_EXPECTED_SYSTEMS = {
    "Bugs Ecocodes": (2_535, 1_286, 22),
    "Koch Ecology Codes": (6_552, 866, 201),
    "Arnolds & van der Maarel (plants)": (173, 173, 30),
}
_EXPECTED_LINEAGE = {
    "source_run_id": "sead-full-evidence-39bfff6a-ce80714e",
    "build_id": (
        "sha256:ce80714e4c9e9974b24913e5da50f49854670ed642879c1ca5076499e1d56725"
    ),
    "acquisition_manifest_sha256": (
        "6fc2428046d148f9ce6c158f982afbbbbaea39de2132850a4fb8f41acf8a4c14"
    ),
    "parent_admission_sha256": (
        "168ad1efe6fa68cdb7789246a6cce16670377cdbacd14d1673beaab8ddd1ebd1"
    ),
    "evidence_manifest_sha256": (
        "c5ec51e8e7360e4f47cffceeb7a907e022da4445caf853317cbcc908269b0093"
    ),
    "evidence_file_set_sha256": (
        "3a18b6e11ccccdc61f3c1fcbc5f301fd1132313ad14c8dba2fa87c6a9b3174cf"
    ),
}
_EXPECTED_TAXONOMY_TABLE_COUNTS = {
    "tbl_taxa_tree_master": 1_974,
    "tbl_taxa_tree_genera": 925,
    "tbl_taxa_tree_families": 207,
    "tbl_taxa_tree_orders": 30,
    "tbl_taxa_tree_authors": 285,
}
_EXPECTED_CITATION_SYSTEMS = {
    "Bugs Ecocodes": {
        "ecocode_system_id": 2,
        "biblio_id": None,
        "citation_title": None,
        "citation_doi": None,
        "citation_url": None,
        "citation_status": "missing",
        "reason_code": "ecocode_system_has_no_bibliography_authority",
        "accepted_for_classification": False,
    },
    "Koch Ecology Codes": {
        "ecocode_system_id": 3,
        "biblio_id": None,
        "citation_title": None,
        "citation_doi": None,
        "citation_url": None,
        "citation_status": "missing",
        "reason_code": "ecocode_system_has_no_bibliography_authority",
        "accepted_for_classification": False,
    },
    "Arnolds & van der Maarel (plants)": {
        "ecocode_system_id": 4,
        "biblio_id": 5_555,
        "citation_title": (
            "Beetles of the family Ptinidae of Central Europe. Prague, Academia."
        ),
        "citation_doi": None,
        "citation_url": None,
        "citation_status": "conflicting",
        "reason_code": "plant_system_points_to_beetle_reference",
        "accepted_for_classification": False,
    },
}
_NULL_REVIEW_FIELDS = (
    "proposed_accepted_taxon_concept_id",
    "proposed_accepted_taxon_name",
    "proposed_accepted_rank",
    "proposed_primary_group_id",
    "proposed_primary_subgroup_id",
    "proposed_role_ids",
    "reviewer_id",
    "decision_date",
    "review_rationale",
    "review_confidence",
)
_PACKET_FIELDS = {
    "schema_version",
    "source_family",
    "lineage",
    "review_posture",
    "taxonomic_inventory",
    "ecocode_inventory",
    "citation_audit",
    "chronology_authority_gaps",
    "event_refusal_posture",
    "review_requirements",
    "candidates",
}
_CANDIDATE_FIELDS = {
    "candidate_id",
    "taxon_relation_id",
    "taxon_id",
    "source_order_id",
    "source_order_name",
    "source_family_id",
    "source_family_name",
    "source_genus_id",
    "source_genus_name",
    "source_species",
    "source_author_id",
    "source_author_name",
    "source_ecocode_count",
    "source_ecocodes",
    "review_priority",
    "review_status",
    "current_classification_status",
    "proposed_accepted_taxon_concept_id",
    "proposed_accepted_taxon_name",
    "proposed_accepted_rank",
    "proposed_primary_group_id",
    "proposed_primary_subgroup_id",
    "proposed_role_ids",
    "evidence_reference_ids",
    "reviewer_id",
    "decision_date",
    "review_rationale",
    "review_confidence",
    "propagation_allowed",
}
_SOURCE_ECOCODE_FIELDS = {
    "ecocode_id",
    "ecocode_definition_id",
    "abbreviation",
    "name",
    "ecocode_group_id",
    "group_name",
    "ecocode_system_id",
    "system_name",
}
_REVIEW_REQUIREMENTS = [
    "Verify source-supported rank without increasing taxonomic resolution.",
    "Provide a citation or governed authority for every accepted mapping.",
    "Keep direct crops, qualified crop types, and indicators distinct.",
    "Review multi-role membership with observation-ID deduplication.",
    "Record reviewer identity, decision date, rationale, confidence, and evidence references.",
    "Accept no mapping by omission, label similarity, or batch default.",
]


def validate_sead_scientific_classification_review(packet: JsonObject) -> None:
    """Require exact governed denominators and a wholly non-accepting review queue."""
    if packet.get("schema_version") != "sead-scientific-classification-review.v1":
        raise ValueError("unsupported SEAD scientific-review schema")
    if set(packet) != _PACKET_FIELDS:
        raise ValueError("SEAD scientific-review packet fields changed")
    if packet.get("source_family") != "sead":
        raise ValueError("SEAD scientific-review source family changed")
    lineage = _mapping(packet.get("lineage"), "lineage")
    if dict(lineage) != _EXPECTED_LINEAGE:
        raise ValueError("SEAD scientific-review lineage changed from governed inputs")
    posture = _mapping(packet.get("review_posture"), "review posture")
    expected_posture = {
        "review_status": "pending_qualified_scientific_review",
        "derived_classification_status": "not_accepted",
        "accepted_mapping_count": 0,
        "accepted_qualified_mapping_count": 0,
        "propagation_allowed": False,
        "propagation_reason_code": "source_classification_not_accepted",
        "reviewer_id": None,
        "decision_date": None,
    }
    if dict(posture) != expected_posture:
        raise ValueError("SEAD scientific-review posture must remain pending")

    candidates = packet.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 1_974:
        raise ValueError("SEAD review must contain exactly 1,974 taxon candidates")
    candidate_ids: list[str] = []
    taxon_ids: list[int] = []
    taxa_with_ecocode = 0
    ecocode_rows = 0
    taxon_definition_pairs: set[tuple[int, int]] = set()
    system_row_counts: Counter[str] = Counter()
    system_taxa: dict[str, set[int]] = {}
    system_definitions: dict[str, set[int]] = {}
    plant_priority_count = 0
    for raw in candidates:
        candidate = _mapping(raw, "candidate")
        if set(candidate) != _CANDIDATE_FIELDS:
            raise ValueError("SEAD candidate fields changed")
        if candidate.get("review_status") != "pending_qualified_scientific_review":
            raise ValueError("SEAD candidate review status was accepted")
        if candidate.get("current_classification_status") != "not_accepted":
            raise ValueError("SEAD candidate classification status was accepted")
        if candidate.get("propagation_allowed") is not False:
            raise ValueError("SEAD candidate incorrectly permits propagation")
        if any(candidate.get(field) is not None for field in _NULL_REVIEW_FIELDS):
            raise ValueError("SEAD candidate contains a prefilled review decision")
        if candidate.get("evidence_reference_ids") != []:
            raise ValueError("SEAD candidate contains unreviewed evidence references")
        candidate_id = candidate.get("candidate_id")
        taxon_id = candidate.get("taxon_id")
        if (
            not isinstance(candidate_id, str)
            or not isinstance(taxon_id, int)
            or isinstance(taxon_id, bool)
            or candidate_id != f"sead-classification-candidate:{taxon_id}"
        ):
            raise TypeError("SEAD candidate identity is invalid")
        if candidate.get("taxon_relation_id") != f"sead-taxon:{taxon_id}":
            raise ValueError("SEAD candidate relation identity changed")
        source_ecocodes = candidate.get("source_ecocodes")
        if not isinstance(source_ecocodes, list):
            raise TypeError("SEAD candidate source ecocodes must be a list")
        if candidate.get("source_ecocode_count") != len(source_ecocodes):
            raise ValueError("SEAD candidate ecocode count does not reconcile")
        candidate_ids.append(candidate_id)
        taxon_ids.append(taxon_id)
        taxa_with_ecocode += int(bool(source_ecocodes))
        ecocode_rows += len(source_ecocodes)
        has_plant_ecocode = False
        for raw_ecocode in source_ecocodes:
            ecocode = _mapping(raw_ecocode, "candidate source ecocode")
            if set(ecocode) != _SOURCE_ECOCODE_FIELDS:
                raise ValueError("SEAD candidate ecocode fields changed")
            system_name = ecocode.get("system_name")
            system_id = ecocode.get("ecocode_system_id")
            definition_id = ecocode.get("ecocode_definition_id")
            if (
                not isinstance(system_name, str)
                or system_name not in _EXPECTED_SYSTEMS
                or not isinstance(system_id, int)
                or isinstance(system_id, bool)
                or not isinstance(definition_id, int)
                or isinstance(definition_id, bool)
            ):
                raise ValueError("SEAD candidate ecocode identity is invalid")
            expected_system_id = {
                "Bugs Ecocodes": 2,
                "Koch Ecology Codes": 3,
                "Arnolds & van der Maarel (plants)": 4,
            }[system_name]
            if system_id != expected_system_id:
                raise ValueError("SEAD candidate ecocode system identity changed")
            system_row_counts[system_name] += 1
            system_taxa.setdefault(system_name, set()).add(taxon_id)
            system_definitions.setdefault(system_name, set()).add(definition_id)
            taxon_definition_pairs.add((taxon_id, definition_id))
            has_plant_ecocode |= system_id == 4
        expected_priority = (
            "plant_ecocode_candidate" if has_plant_ecocode else "source_taxon_candidate"
        )
        if candidate.get("review_priority") != expected_priority:
            raise ValueError("SEAD candidate review priority is not source-derived")
        plant_priority_count += int(has_plant_ecocode)
    if len(candidate_ids) != len(set(candidate_ids)) or len(taxon_ids) != len(
        set(taxon_ids)
    ):
        raise ValueError("SEAD review candidate identities must be unique")
    if taxon_ids != sorted(taxon_ids):
        raise ValueError("SEAD review candidates must be ordered by taxon_id")

    taxonomy = _mapping(packet.get("taxonomic_inventory"), "taxonomic inventory")
    if (
        taxonomy.get("taxon_relation_count") != 1_974
        or taxonomy.get("taxon_candidate_count") != 1_974
    ):
        raise ValueError("SEAD taxon denominators changed")
    if taxonomy.get("source_taxonomy_table_counts") != _EXPECTED_TAXONOMY_TABLE_COUNTS:
        raise ValueError("SEAD source taxonomy table counts changed")
    ecocodes = _mapping(packet.get("ecocode_inventory"), "ecocode inventory")
    if (
        ecocodes.get("ecocode_row_count") != ecocode_rows
        or ecocode_rows != 9_260
        or ecocodes.get("unique_taxon_definition_pair_count")
        != len(taxon_definition_pairs)
        or len(taxon_definition_pairs) != 9_251
        or ecocodes.get("taxa_with_ecocode_count") != taxa_with_ecocode
        or taxa_with_ecocode != 1_466
        or ecocodes.get("taxa_without_ecocode_count") != 508
    ):
        raise ValueError("SEAD ecocode denominators do not reconcile")
    systems = ecocodes.get("systems")
    if not isinstance(systems, list) or len(systems) != 3:
        raise TypeError("SEAD ecocode systems must be rows")
    observed_systems = {
        cast(str, row["system_name"]): (
            row["ecocode_row_count"],
            row["taxon_count"],
            row["definition_count"],
        )
        for raw in systems
        for row in [_mapping(raw, "ecocode system")]
    }
    if observed_systems != _EXPECTED_SYSTEMS:
        raise ValueError("SEAD ecocode-system denominators changed")
    recomputed_systems = {
        name: (
            system_row_counts[name],
            len(system_taxa.get(name, set())),
            len(system_definitions.get(name, set())),
        )
        for name in _EXPECTED_SYSTEMS
    }
    if recomputed_systems != _EXPECTED_SYSTEMS or plant_priority_count != 173:
        raise ValueError("SEAD candidate ecocode systems do not reconcile")
    if (
        ecocodes.get("ecocode_definition_count") != 253
        or ecocodes.get("ecocode_group_count") != 17
        or ecocodes.get("ecocode_system_count") != 3
    ):
        raise ValueError("SEAD ecocode authority inventory changed")

    citation = _mapping(packet.get("citation_audit"), "citation audit")
    if (
        citation.get("captured_bibliography_source_row_count") != 1_114
        or citation.get("chronology_bibliography_source_row_count") != 1_113
        or citation.get("chronology_bibliography_relation_count") != 39_024
        or citation.get("accepted_classification_authority_count") != 0
    ):
        raise ValueError("SEAD citation authority was accepted without review")
    citation_rows = citation.get("systems")
    if not isinstance(citation_rows, list) or len(citation_rows) != 3:
        raise ValueError("SEAD citation-system accounting changed")
    observed_citations = {
        cast(str, row["system_name"]): {
            key: value for key, value in row.items() if key != "system_name"
        }
        for raw in citation_rows
        for row in [_mapping(raw, "citation system")]
    }
    if observed_citations != _EXPECTED_CITATION_SYSTEMS:
        raise ValueError("SEAD citation audit no longer fails closed")

    chronology = _mapping(
        packet.get("chronology_authority_gaps"), "chronology authority gaps"
    )
    if chronology.get("claim_count") != 25_109:
        raise ValueError("SEAD chronology claim denominator changed")
    if chronology.get("reason_count_semantics") != (
        "chronology_not_comparable is an umbrella reason; specific authority "
        "reasons overlap it and must not be added to it"
    ):
        raise ValueError("SEAD chronology nested-reason semantics changed")
    if chronology.get("claim_type_counts") != {
        "analysis_entity_age": 641,
        "dating_range": 7_377,
        "dendrochronology": 6_947,
        "geochronology": 87,
        "relative_period": 10_057,
    }:
        raise ValueError("SEAD chronology claim types changed")
    if chronology.get("comparability_counts") != {
        "comparable": 14_264,
        "context_only": 10_144,
        "refused": 60,
        "unresolved": 641,
    }:
        raise ValueError("SEAD chronology comparability changed")
    if chronology.get("chronology_eligibility_counts") != {
        "eligible": 14_264,
        "refused": 10_845,
    }:
        raise ValueError("SEAD chronology eligibility changed")
    if chronology.get("refusal_reason_counts") != {
        "analysis_entity_age_basis_unspecified": 641,
        "chronology_not_comparable": 10_845,
        "geochronology_calibration_posture_unknown": 87,
        "negative_bp": 60,
        "relative_period_requires_governed_mapping": 10_057,
    }:
        raise ValueError("SEAD chronology authority gaps changed")

    events = _mapping(packet.get("event_refusal_posture"), "event refusal posture")
    if (
        events.get("observation_denominator") != 177_763
        or events.get("eligible_event_count") != 0
        or events.get("refused_event_count") != 177_763
    ):
        raise ValueError("SEAD event refusal partition changed")
    if events.get("reason_count_semantics") != "reason populations overlap":
        raise ValueError("SEAD event refusal overlap semantics changed")
    reasons = _mapping(events.get("refusal_reason_counts"), "event refusal reasons")
    if dict(reasons) != {
        "eligible_chronology_claim_unavailable_at_analysis_entity": 166_386,
        "source_classification_not_accepted": 177_763,
        "source_taxon_unavailable": 154_107,
        "source_unit_unavailable": 160_825,
    }:
        raise ValueError("SEAD classification refusal denominator changed")
    if packet.get("review_requirements") != _REVIEW_REQUIREMENTS:
        raise ValueError("SEAD qualified-review requirements changed")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"SEAD scientific-review {label} must be an object")
    return cast(Mapping[str, object], value)
