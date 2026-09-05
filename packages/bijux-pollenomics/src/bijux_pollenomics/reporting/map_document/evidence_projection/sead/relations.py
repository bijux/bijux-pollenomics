"""Source-native relation indexing for SEAD atlas evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..io import _identifier_text
from ..records import _unique_rows
from .admission import object_rows
from .models import EvidenceBundle, RelationIndex


def index_relations(bundle: EvidenceBundle) -> RelationIndex:
    """Validate all relation denominators and build stable ID indexes."""
    entity_rows = object_rows(
        bundle.relations, "entity_relations", "SEAD entity relations"
    )
    taxon_rows = object_rows(bundle.relations, "taxon_relations", "SEAD taxa")
    dimension_rows = object_rows(
        bundle.relations, "dimension_relations", "SEAD dimension relations"
    )
    dimension_semantic_rows = object_rows(
        bundle.relations, "dimension_semantics", "SEAD dimension semantics"
    )
    dataset_semantic_rows = object_rows(
        bundle.relations, "dataset_semantics", "SEAD dataset semantics"
    )
    value_semantic_rows = object_rows(
        bundle.relations, "value_semantics", "SEAD value semantics"
    )
    entity_by_id = _unique_rows(
        entity_rows, "entity_relation_id", "SEAD entity relations"
    )
    taxon_by_id = _unique_rows(taxon_rows, "taxon_relation_id", "SEAD taxa")
    dimension_by_id = _unique_rows(
        dimension_rows, "dimension_relation_id", "SEAD dimension relations"
    )
    dimension_semantic_by_id = _unique_rows(
        dimension_semantic_rows,
        "dimension_semantics_id",
        "SEAD dimension semantics",
    )
    dataset_semantic_by_id = _unique_rows(
        dataset_semantic_rows,
        "dataset_semantics_id",
        "SEAD dataset semantics",
    )
    value_semantic_by_id = _unique_rows(
        value_semantic_rows, "value_semantics_id", "SEAD value semantics"
    )
    site_by_owner = {
        owner_field: site_by_entity_owner(entity_rows, owner_field=owner_field)
        for owner_field in (
            "analysis_entity_id",
            "physical_sample_id",
            "sample_group_id",
        )
    }
    reconcile_relation_denominators(
        bundle.relations,
        entity_rows=entity_rows,
        taxon_rows=taxon_rows,
        dimension_rows=dimension_rows,
        dimension_semantic_rows=dimension_semantic_rows,
        dataset_semantic_rows=dataset_semantic_rows,
        value_semantic_rows=value_semantic_rows,
    )
    return RelationIndex(
        entity_rows=entity_rows,
        taxon_rows=taxon_rows,
        dimension_rows=dimension_rows,
        dimension_semantic_rows=dimension_semantic_rows,
        dataset_semantic_rows=dataset_semantic_rows,
        value_semantic_rows=value_semantic_rows,
        entity_by_id=entity_by_id,
        taxon_by_id=taxon_by_id,
        dimension_by_id=dimension_by_id,
        dimension_semantic_by_id=dimension_semantic_by_id,
        dataset_semantic_by_id=dataset_semantic_by_id,
        value_semantic_by_id=value_semantic_by_id,
        site_by_owner=site_by_owner,
    )


def reconcile_relation_denominators(
    relation_index: Mapping[str, object],
    *,
    entity_rows: Sequence[Mapping[str, object]],
    taxon_rows: Sequence[Mapping[str, object]],
    dimension_rows: Sequence[Mapping[str, object]],
    dimension_semantic_rows: Sequence[Mapping[str, object]],
    dataset_semantic_rows: Sequence[Mapping[str, object]],
    value_semantic_rows: Sequence[Mapping[str, object]],
) -> None:
    """Require declared relation counts to equal materialized row counts."""
    for field, rows in (
        ("entity_relation_count", entity_rows),
        ("taxon_relation_count", taxon_rows),
        ("dimension_relation_count", dimension_rows),
        ("dimension_semantic_count", dimension_semantic_rows),
        ("dataset_semantic_count", dataset_semantic_rows),
        ("value_semantic_count", value_semantic_rows),
    ):
        if relation_index.get(field) != len(rows):
            raise ValueError(f"SEAD {field} does not reconcile")


def site_by_entity_owner(
    entity_rows: Sequence[Mapping[str, object]], *, owner_field: str
) -> dict[str, str]:
    """Map one source owner identity to exactly one governed site."""
    sites_by_owner: dict[str, str] = {}
    for entity in entity_rows:
        owner_value = entity.get(owner_field)
        if owner_value is None:
            continue
        owner_id = _identifier_text(owner_value, f"SEAD {owner_field}")
        site_id = _identifier_text(entity.get("site_id"), "SEAD entity site ID")
        existing = sites_by_owner.setdefault(owner_id, site_id)
        if existing != site_id:
            raise ValueError(f"SEAD {owner_field} crosses governed sites")
    return sites_by_owner
