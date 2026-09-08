"""Source-native observation projection and semantic reconciliation."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import cast

from ..constants import _SEAD_OBSERVATION_FIELDS
from ..io import _identifier_text, _mapping, _required_text
from ..records import _unique_rows
from ..sead_records import _compact_sead_entity, _compact_sead_observation
from .admission import object_rows
from .chronology import reconcile_claim_entity_links
from .models import ClaimIndex, EvidenceBundle, ObservationIndex, RelationIndex


def index_observations(
    bundle: EvidenceBundle,
    claims: ClaimIndex,
    relations: RelationIndex,
) -> ObservationIndex:
    """Validate observations, refusals, counts, and all referenced relations."""
    refusal_rows = object_rows(bundle.events, "refusals", "SEAD event refusals")
    refusal_by_observation = _unique_rows(
        refusal_rows, "observation_id", "SEAD event refusals"
    )
    if (
        bundle.events.get("events") != []
        or bundle.events.get("eligible_event_count") != 0
    ):
        raise ValueError("SEAD evidence unexpectedly contains eligible events")
    if bundle.events.get("refused_event_count") != len(refusal_rows):
        raise ValueError("SEAD event refusal count does not reconcile")

    rows = object_rows(bundle.observations, "observations", "SEAD observations")
    if bundle.observations.get("observation_count") != len(rows):
        raise ValueError("SEAD observation count does not reconcile")
    if bundle.events.get("observation_denominator") != len(rows):
        raise ValueError("SEAD event denominator does not reconcile")
    for field, expected in (
        ("chronology_claim_count", len(claims.rows)),
        ("observation_count", len(rows)),
        ("eligible_event_count", 0),
        ("refused_event_count", len(refusal_rows)),
    ):
        if bundle.manifest.get(field) != expected:
            raise ValueError(f"SEAD evidence manifest {field} does not reconcile")

    by_site: dict[str, list[list[object]]] = defaultdict(list)
    entities_by_site: dict[str, dict[str, list[object]]] = defaultdict(dict)
    taxon_ids_by_site: dict[str, set[str]] = defaultdict(set)
    dimension_ids_by_site: dict[str, set[str]] = defaultdict(set)
    dataset_semantic_ids_by_site: dict[str, set[str]] = defaultdict(set)
    value_semantic_ids_by_site: dict[str, set[str]] = defaultdict(set)
    observation_ids: set[str] = set()
    referenced_taxon_ids: set[str] = set()
    referenced_dimension_ids: set[str] = set()
    referenced_dataset_semantic_ids: set[str] = set()
    referenced_value_semantic_ids: set[str] = set()
    observation_count_by_entity: Counter[str] = Counter()
    country_counts: Counter[str] = Counter()
    table_counts: Counter[str] = Counter()
    refusal_reason_counts: Counter[str] = Counter()
    for observation in rows:
        if observation.get("build_id") != bundle.observations.get("build_id"):
            raise ValueError("SEAD observation build identity changed")
        if observation.get("acquisition_manifest_sha256") != bundle.observations.get(
            "acquisition_manifest_sha256"
        ):
            raise ValueError("SEAD observation acquisition identity changed")
        compact, site_id, references = _compact_sead_observation(
            observation,
            entity_by_id=relations.entity_by_id,
            refusal_by_observation=refusal_by_observation,
            taxon_by_id=relations.taxon_by_id,
            dimension_by_id=relations.dimension_by_id,
            dataset_semantic_by_id=relations.dataset_semantic_by_id,
            value_semantic_by_id=relations.value_semantic_by_id,
        )
        observation_id = cast(str, compact[0])
        if observation_id in observation_ids:
            raise ValueError(f"SEAD observation ID is duplicated: {observation_id}")
        observation_ids.add(observation_id)
        by_site[site_id].append(compact)
        entity_id = cast(str, compact[3])
        observation_count_by_entity[entity_id] += 1
        country_counts[
            _required_text(observation.get("country_code"), "SEAD observation country")
        ] += 1
        table_counts[
            _required_text(observation.get("source_table"), "SEAD observation table")
        ] += 1
        refusal_reason_counts.update(
            cast(
                list[str],
                compact[_SEAD_OBSERVATION_FIELDS.index("event_refusal_reason_codes")],
            )
        )
        entities_by_site[site_id][entity_id] = _compact_sead_entity(
            relations.entity_by_id[entity_id]
        )
        taxon_id, dimension_ids, dataset_id, value_id = references
        if taxon_id is not None:
            taxon_ids_by_site[site_id].add(taxon_id)
            referenced_taxon_ids.add(taxon_id)
        dimension_ids_by_site[site_id].update(dimension_ids)
        referenced_dimension_ids.update(dimension_ids)
        if dataset_id is not None:
            dataset_semantic_ids_by_site[site_id].add(dataset_id)
            referenced_dataset_semantic_ids.add(dataset_id)
        if value_id is not None:
            value_semantic_ids_by_site[site_id].add(value_id)
            referenced_value_semantic_ids.add(value_id)

    _assign_owned_dimensions(relations, dimension_ids_by_site, referenced_dimension_ids)
    if observation_ids != set(refusal_by_observation):
        raise ValueError("SEAD observations and event refusals do not reconcile")
    _reconcile_declared_counts(
        bundle,
        country_counts=country_counts,
        table_counts=table_counts,
        refusal_reason_counts=refusal_reason_counts,
    )
    eligible_country_counts = _mapping(
        bundle.events.get("country_eligible_event_counts"),
        "SEAD eligible event country counts",
    )
    if set(eligible_country_counts) != set(country_counts) or any(
        count != 0 for count in eligible_country_counts.values()
    ):
        raise ValueError("SEAD eligible event country counts do not reconcile")
    reconcile_claim_entity_links(claims, relations, observation_count_by_entity)
    for dimension_id in referenced_dimension_ids:
        semantics_id = _required_text(
            relations.dimension_by_id[dimension_id].get("dimension_semantics_id"),
            "SEAD dimension semantics ID",
        )
        if semantics_id not in relations.dimension_semantic_by_id:
            raise ValueError("SEAD dimension relation references unknown semantics")

    return ObservationIndex(
        rows=rows,
        refusal_rows=refusal_rows,
        by_site=by_site,
        entities_by_site=entities_by_site,
        taxon_ids_by_site=taxon_ids_by_site,
        dimension_ids_by_site=dimension_ids_by_site,
        dataset_semantic_ids_by_site=dataset_semantic_ids_by_site,
        value_semantic_ids_by_site=value_semantic_ids_by_site,
        referenced_taxon_ids=referenced_taxon_ids,
        referenced_dimension_ids=referenced_dimension_ids,
        referenced_dataset_semantic_ids=referenced_dataset_semantic_ids,
        referenced_value_semantic_ids=referenced_value_semantic_ids,
        country_counts=country_counts,
        eligible_country_counts=eligible_country_counts,
    )


def _assign_owned_dimensions(
    relations: RelationIndex,
    dimension_ids_by_site: dict[str, set[str]],
    referenced_dimension_ids: set[str],
) -> None:
    owner_sites = {
        "analysis_entity": relations.site_by_owner["analysis_entity_id"],
        "physical_sample": relations.site_by_owner["physical_sample_id"],
        "sample_group": relations.site_by_owner["sample_group_id"],
    }
    for dimension_id, dimension in relations.dimension_by_id.items():
        owner_kind = _required_text(
            dimension.get("owner_kind"), "SEAD dimension owner kind"
        )
        sites = owner_sites.get(owner_kind)
        if sites is None:
            raise ValueError(f"SEAD dimension owner kind is unsupported: {owner_kind}")
        owner_id = _identifier_text(
            dimension.get("owner_id"), "SEAD dimension owner ID"
        )
        site_id = sites.get(owner_id)
        if site_id is None:
            raise ValueError("SEAD dimension owner has no governed site relation")
        dimension_ids_by_site[site_id].add(dimension_id)
        referenced_dimension_ids.add(dimension_id)


def _reconcile_declared_counts(
    bundle: EvidenceBundle,
    *,
    country_counts: Counter[str],
    table_counts: Counter[str],
    refusal_reason_counts: Counter[str],
) -> None:
    for label, actual, declared in (
        ("country counts", country_counts, bundle.observations.get("country_counts")),
        (
            "observation table counts",
            table_counts,
            bundle.observations.get("observation_table_counts"),
        ),
        (
            "event refusal reason counts",
            refusal_reason_counts,
            bundle.events.get("refusal_reason_counts"),
        ),
        (
            "event country observation counts",
            country_counts,
            bundle.events.get("country_observation_counts"),
        ),
    ):
        declared_counts = _mapping(declared, f"SEAD {label}")
        nonzero_declared = {
            str(key): value for key, value in declared_counts.items() if value != 0
        }
        if dict(sorted(actual.items())) != nonzero_declared:
            raise ValueError(f"SEAD {label} do not reconcile")
