"""Build a reviewable, non-accepting SEAD classification packet."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
    governed_sead_evidence_root,
    read_validated_sead_evidence_documents,
)

JsonObject = dict[str, object]


def build_sead_scientific_classification_review(data_root: Path) -> JsonObject:
    """Build the complete pending-review packet from pinned governed artifacts."""
    root = Path(data_root).resolve()
    acquisition_root = (
        root / "sead" / "raw" / "acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID
    )
    evidence_root = governed_sead_evidence_root(root)
    documents = read_validated_sead_evidence_documents(
        evidence_root,
        (
            "chronology_claims.json",
            "evidence_events.json",
            "observation_relation_index.json",
        ),
        expected_run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
        expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )
    claims = documents["chronology_claims.json"]
    events = documents["evidence_events.json"]
    relations = documents["observation_relation_index.json"]
    evidence_manifest_bytes = _regular_bytes(
        evidence_root / "evidence_materialization_manifest.json"
    )
    evidence_manifest = _json_object(evidence_manifest_bytes, "evidence manifest")
    admission = _read_governed_admission(acquisition_root)
    _validate_common_identity(admission, evidence_manifest, claims, events, relations)

    raw_tables = _read_bound_raw_tables(
        acquisition_root,
        admission,
        relations,
        tables=(
            "tbl_biblio",
            "tbl_ecocodes",
            "tbl_ecocode_definitions",
            "tbl_ecocode_groups",
            "tbl_ecocode_systems",
        ),
    )
    taxon_relations = _object_rows(relations, "taxon_relations")
    candidates, ecocode_summary = _classification_candidates(
        taxon_relations,
        ecocodes=raw_tables["tbl_ecocodes"],
        definitions=raw_tables["tbl_ecocode_definitions"],
        groups=raw_tables["tbl_ecocode_groups"],
        systems=raw_tables["tbl_ecocode_systems"],
    )
    citations = _citation_audit(
        raw_tables["tbl_ecocode_systems"], raw_tables["tbl_biblio"]
    )
    source_table_counts = _mapping(
        relations.get("source_table_counts"), "source table counts"
    )
    claim_relation_summary = _mapping(
        claims.get("relation_summary"), "chronology relation summary"
    )
    packet: JsonObject = {
        "schema_version": "sead-scientific-classification-review.v1",
        "source_family": "sead",
        "lineage": {
            "source_run_id": admission["run_id"],
            "build_id": admission["build_id"],
            "acquisition_manifest_sha256": admission["acquisition_manifest_sha256"],
            "parent_admission_sha256": admission["parent_admission_sha256"],
            "evidence_manifest_sha256": hashlib.sha256(
                evidence_manifest_bytes
            ).hexdigest(),
            "evidence_file_set_sha256": evidence_manifest["file_set_sha256"],
        },
        "review_posture": {
            "review_status": "pending_qualified_scientific_review",
            "derived_classification_status": "not_accepted",
            "accepted_mapping_count": 0,
            "accepted_qualified_mapping_count": 0,
            "propagation_allowed": False,
            "propagation_reason_code": "source_classification_not_accepted",
            "reviewer_id": None,
            "decision_date": None,
        },
        "taxonomic_inventory": {
            "taxon_relation_count": len(taxon_relations),
            "taxon_candidate_count": len(candidates),
            "source_taxonomy_table_counts": {
                key: source_table_counts[key]
                for key in (
                    "tbl_taxa_tree_master",
                    "tbl_taxa_tree_genera",
                    "tbl_taxa_tree_families",
                    "tbl_taxa_tree_orders",
                    "tbl_taxa_tree_authors",
                )
            },
        },
        "ecocode_inventory": ecocode_summary,
        "citation_audit": {
            "captured_bibliography_source_row_count": source_table_counts["tbl_biblio"],
            "chronology_bibliography_source_row_count": claim_relation_summary[
                "bibliography_source_row_count"
            ],
            "chronology_bibliography_relation_count": claim_relation_summary[
                "bibliography_row_count"
            ],
            "accepted_classification_authority_count": 0,
            "systems": citations,
        },
        "chronology_authority_gaps": {
            "claim_count": claims["claim_count"],
            "claim_type_counts": claims["claim_type_counts"],
            "comparability_counts": claims["comparability_counts"],
            "chronology_eligibility_counts": claims["chronology_eligibility_counts"],
            "refusal_reason_counts": claims["refusal_reason_counts"],
            "reason_count_semantics": (
                "chronology_not_comparable is an umbrella reason; specific authority "
                "reasons overlap it and must not be added to it"
            ),
        },
        "event_refusal_posture": {
            "observation_denominator": events["observation_denominator"],
            "eligible_event_count": events["eligible_event_count"],
            "refused_event_count": events["refused_event_count"],
            "refusal_reason_counts": events["refusal_reason_counts"],
            "reason_count_semantics": "reason populations overlap",
        },
        "review_requirements": [
            "Verify source-supported rank without increasing taxonomic resolution.",
            "Provide a citation or governed authority for every accepted mapping.",
            "Keep direct crops, qualified crop types, and indicators distinct.",
            "Review multi-role membership with observation-ID deduplication.",
            "Record reviewer identity, decision date, rationale, confidence, and evidence references.",
            "Accept no mapping by omission, label similarity, or batch default.",
        ],
        "candidates": candidates,
    }
    from .validation import validate_sead_scientific_classification_review

    validate_sead_scientific_classification_review(packet)
    return packet


def _classification_candidates(
    taxon_relations: list[Mapping[str, object]],
    *,
    ecocodes: list[Mapping[str, object]],
    definitions: list[Mapping[str, object]],
    groups: list[Mapping[str, object]],
    systems: list[Mapping[str, object]],
) -> tuple[list[JsonObject], JsonObject]:
    ecocodes_by_id = _unique_integer_index(ecocodes, "ecocode_id", "ecocodes")
    definitions_by_id = _unique_integer_index(
        definitions, "ecocode_definition_id", "ecocode definitions"
    )
    groups_by_id = _unique_integer_index(groups, "ecocode_group_id", "ecocode groups")
    systems_by_id = _unique_integer_index(
        systems, "ecocode_system_id", "ecocode systems"
    )
    candidates: list[JsonObject] = []
    system_row_counts: Counter[str] = Counter()
    system_taxa: dict[str, set[int]] = {}
    system_definitions: dict[str, set[int]] = {}
    pair_ids: set[tuple[int, int]] = set()
    observed_ecocode_ids: set[int] = set()
    taxa_with_ecocode = 0
    for relation in sorted(taxon_relations, key=lambda row: _integer(row, "taxon_id")):
        if relation.get("derived_classification_status") != "not_accepted":
            raise ValueError("SEAD derived classification was accepted before review")
        taxon_id = _integer(relation, "taxon_id")
        native_rows = relation.get("source_ecocodes")
        if not isinstance(native_rows, list):
            raise TypeError("SEAD source_ecocodes must be a list")
        compact_ecocodes: list[JsonObject] = []
        for raw in native_rows:
            ecocode = _mapping(raw, "source ecocode relation")
            source_ecocode = _mapping(ecocode.get("ecocode"), "ecocode")
            ecocode_id = _integer(source_ecocode, "ecocode_id")
            if ecocodes_by_id.get(ecocode_id) != source_ecocode:
                raise ValueError("SEAD ecocode relation diverges from raw authority")
            if ecocode_id in observed_ecocode_ids:
                raise ValueError("SEAD ecocode relation is duplicated")
            observed_ecocode_ids.add(ecocode_id)
            definition = _mapping(ecocode.get("definition"), "ecocode definition")
            group = _mapping(ecocode.get("group"), "ecocode group")
            system = _mapping(ecocode.get("system"), "ecocode system")
            definition_id = _integer(definition, "ecocode_definition_id")
            group_id = _integer(group, "ecocode_group_id")
            system_id = _integer(system, "ecocode_system_id")
            if definitions_by_id.get(definition_id) != definition:
                raise ValueError("SEAD ecocode definition diverges from raw authority")
            if groups_by_id.get(group_id) != group:
                raise ValueError("SEAD ecocode group diverges from raw authority")
            if systems_by_id.get(system_id) != system:
                raise ValueError("SEAD ecocode system diverges from raw authority")
            system_name = _text(system, "name")
            system_row_counts[system_name] += 1
            system_taxa.setdefault(system_name, set()).add(taxon_id)
            system_definitions.setdefault(system_name, set()).add(definition_id)
            pair_ids.add((taxon_id, definition_id))
            compact_ecocodes.append(
                {
                    "ecocode_id": ecocode_id,
                    "ecocode_definition_id": definition_id,
                    "abbreviation": definition.get("abbreviation"),
                    "name": definition.get("name"),
                    "ecocode_group_id": group_id,
                    "group_name": group.get("name"),
                    "ecocode_system_id": system_id,
                    "system_name": system_name,
                }
            )
        if compact_ecocodes:
            taxa_with_ecocode += 1
        taxon = _mapping(relation.get("taxon"), "SEAD taxon")
        genus = _optional_mapping(relation.get("genus"))
        candidates.append(
            {
                "candidate_id": f"sead-classification-candidate:{taxon_id}",
                "taxon_relation_id": _text(relation, "taxon_relation_id"),
                "taxon_id": taxon_id,
                "source_order_id": _nested_value(relation, "order", "order_id"),
                "source_order_name": _nested_value(relation, "order", "order_name"),
                "source_family_id": _nested_value(relation, "family", "family_id"),
                "source_family_name": _nested_value(relation, "family", "family_name"),
                "source_genus_id": genus.get("genus_id") if genus else None,
                "source_genus_name": genus.get("genus_name") if genus else None,
                "source_species": taxon.get("species"),
                "source_author_id": _nested_value(relation, "author", "author_id"),
                "source_author_name": _nested_value(relation, "author", "author_name"),
                "source_ecocode_count": len(compact_ecocodes),
                "source_ecocodes": compact_ecocodes,
                "review_priority": (
                    "plant_ecocode_candidate"
                    if any(row["ecocode_system_id"] == 4 for row in compact_ecocodes)
                    else "source_taxon_candidate"
                ),
                "review_status": "pending_qualified_scientific_review",
                "current_classification_status": "not_accepted",
                "proposed_accepted_taxon_concept_id": None,
                "proposed_accepted_taxon_name": None,
                "proposed_accepted_rank": None,
                "proposed_primary_group_id": None,
                "proposed_primary_subgroup_id": None,
                "proposed_role_ids": None,
                "evidence_reference_ids": [],
                "reviewer_id": None,
                "decision_date": None,
                "review_rationale": None,
                "review_confidence": None,
                "propagation_allowed": False,
            }
        )
    if observed_ecocode_ids != set(ecocodes_by_id):
        raise ValueError("SEAD ecocode relations do not exhaust raw authority rows")
    system_rows = [
        {
            "ecocode_system_id": system_id,
            "system_name": _text(system, "name"),
            "ecocode_row_count": system_row_counts[_text(system, "name")],
            "taxon_count": len(system_taxa.get(_text(system, "name"), set())),
            "definition_count": len(
                system_definitions.get(_text(system, "name"), set())
            ),
        }
        for system_id, system in sorted(systems_by_id.items())
    ]
    return candidates, {
        "ecocode_row_count": sum(system_row_counts.values()),
        "unique_taxon_definition_pair_count": len(pair_ids),
        "taxa_with_ecocode_count": taxa_with_ecocode,
        "taxa_without_ecocode_count": len(candidates) - taxa_with_ecocode,
        "ecocode_definition_count": len(definitions),
        "ecocode_group_count": len(groups),
        "ecocode_system_count": len(systems),
        "systems": system_rows,
    }


def _citation_audit(
    systems: list[Mapping[str, object]], bibliography: list[Mapping[str, object]]
) -> list[JsonObject]:
    bibliography_by_id = _unique_integer_index(
        bibliography, "biblio_id", "SEAD bibliography"
    )
    result: list[JsonObject] = []
    for system in sorted(systems, key=lambda row: _integer(row, "ecocode_system_id")):
        system_id = _integer(system, "ecocode_system_id")
        biblio_id = system.get("biblio_id")
        citation = (
            bibliography_by_id.get(biblio_id) if isinstance(biblio_id, int) else None
        )
        if biblio_id is None:
            status = "missing"
            reason = "ecocode_system_has_no_bibliography_authority"
        elif system_id == 4 and biblio_id == 5555:
            status = "conflicting"
            reason = "plant_system_points_to_beetle_reference"
        else:
            status = "pending_review"
            reason = "classification_authority_not_accepted"
        result.append(
            {
                "ecocode_system_id": system_id,
                "system_name": _text(system, "name"),
                "biblio_id": biblio_id,
                "citation_title": citation.get("title") if citation else None,
                "citation_doi": citation.get("doi") if citation else None,
                "citation_url": citation.get("url") if citation else None,
                "citation_status": status,
                "reason_code": reason,
                "accepted_for_classification": False,
            }
        )
    return result


def _validate_common_identity(*documents: Mapping[str, object]) -> None:
    admission, evidence_manifest, claims, events, relations = documents
    run_id = admission.get("run_id")
    build_id = admission.get("build_id")
    acquisition = admission.get("acquisition_manifest_sha256")
    for document in (evidence_manifest, claims, events, relations):
        if document.get("source_run_id") != run_id:
            raise ValueError("SEAD scientific-review source runs diverge")
        candidate_build = document.get("source_build_id", document.get("build_id"))
        if candidate_build != build_id:
            raise ValueError("SEAD scientific-review build identities diverge")
        if document.get("acquisition_manifest_sha256") != acquisition:
            raise ValueError("SEAD scientific-review acquisition identities diverge")
    if evidence_manifest.get("parent_admission_sha256") != admission.get(
        "parent_admission_sha256"
    ):
        raise ValueError("SEAD scientific-review parent admissions diverge")


def _read_bound_raw_tables(
    acquisition_root: Path,
    admission: Mapping[str, object],
    relations: Mapping[str, object],
    *,
    tables: tuple[str, ...],
) -> dict[str, list[Mapping[str, object]]]:
    copied = admission.get("copied_files")
    if not isinstance(copied, list):
        raise TypeError("SEAD governed admission copied_files must be rows")
    copied_by_path = {
        _text(_mapping(row, "copied-file record"), "path"): _mapping(
            row, "copied-file record"
        )
        for row in copied
    }
    source_digests = _mapping(
        relations.get("source_table_sha256"), "source table digests"
    )
    result: dict[str, list[Mapping[str, object]]] = {}
    for table in tables:
        relative_path = f"payloads/{table}.json"
        record = copied_by_path.get(relative_path)
        if record is None:
            raise ValueError(f"SEAD review input is not admitted: {table}")
        payload = _regular_bytes(acquisition_root / relative_path)
        payload_sha256 = hashlib.sha256(payload).hexdigest()
        if (
            record.get("byte_count") != len(payload)
            or record.get("sha256") != payload_sha256
            or source_digests.get(table) != payload_sha256
        ):
            raise ValueError(f"SEAD review input lineage changed: {table}")
        document = _json_object(payload, table)
        if document.get("table") != table:
            raise ValueError(f"SEAD review input table identity changed: {table}")
        result[table] = _object_rows(document, "rows")
    return result


def _read_governed_admission(acquisition_root: Path) -> JsonObject:
    payload = _regular_bytes(acquisition_root / "admission.json")
    if hashlib.sha256(payload).hexdigest() != SEAD_GOVERNED_ADMISSION_SHA256:
        raise ValueError("SEAD governed admission identity changed")
    admission = _json_object(payload, "SEAD governed admission")
    expected = {
        "run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        "parent_admission_sha256": SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
    }
    if any(admission.get(field) != value for field, value in expected.items()):
        raise ValueError("SEAD governed admission lineage changed")
    return admission


def _object_rows(
    document: Mapping[str, object], field: str
) -> list[Mapping[str, object]]:
    value = document.get(field)
    if not isinstance(value, list) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise TypeError(f"SEAD {field} must be object rows")
    return cast(list[Mapping[str, object]], value)


def _unique_integer_index(
    rows: list[Mapping[str, object]], field: str, label: str
) -> dict[int, Mapping[str, object]]:
    result: dict[int, Mapping[str, object]] = {}
    for row in rows:
        key = _integer(row, field)
        if key in result:
            raise ValueError(f"{label} contains duplicate {field}: {key}")
        result[key] = row
    return result


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return cast(Mapping[str, object], value)


def _optional_mapping(value: object) -> Mapping[str, object] | None:
    return cast(Mapping[str, object], value) if isinstance(value, Mapping) else None


def _integer(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"SEAD {field} must be an integer")
    return value


def _text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"SEAD {field} must be nonempty text")
    return value.strip()


def _nested_value(row: Mapping[str, object], object_key: str, field: str) -> object:
    nested = _optional_mapping(row.get(object_key))
    return nested.get(field) if nested else None


def _json_object(payload: bytes, label: str) -> JsonObject:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a JSON object")
    return cast(JsonObject, value)


def _regular_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"SEAD review input is missing or unsafe: {path}")
    return path.read_bytes()
