"""Chronological node construction from admitted source observations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import cast

from .admission import canonical_claim_interval, source_coordinate
from .identity import digest, optional_text
from .models import SourceChronologyNode, SourceNodeContext, SourceNodeFacetRefusal

_Feature = tuple[str, str, int | str | None, str | None, str | None]
_Admitted = tuple[
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
]


def _source_taxon_id(value: object) -> int | str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return optional_text(value)


def _features(
    observation: Mapping[str, object],
) -> tuple[tuple[_Feature, ...], tuple[tuple[str, str], ...]]:
    code = optional_text(observation.get("source_ecological_group"))
    taxon_id = _source_taxon_id(observation.get("source_taxon_id"))
    taxon_name = optional_text(observation.get("source_reported_name"))
    variable_id = optional_text(observation.get("variable_id"))
    features: list[_Feature] = [
        (
            "source_sample_presence",
            "source:neotoma:pollen-presence",
            None,
            None,
            None,
        )
    ]
    refusals: list[tuple[str, str]] = []
    if code is None:
        refusals.append(("source_ecological_code", "source_ecological_code_missing"))
    else:
        features.append(
            (
                "source_ecological_code",
                f"source:neotoma:ecological-code:{code}",
                None,
                None,
                code,
            )
        )
    if taxon_id is None or taxon_name is None or variable_id is None:
        refusals.append(("source_taxon", "source_taxon_identity_incomplete"))
    else:
        features.append(
            (
                "source_taxon",
                f"source:neotoma:taxon:{taxon_id}",
                taxon_id,
                taxon_name,
                code,
            )
        )
    return tuple(features), tuple(refusals)


def build_source_chronology_nodes(
    admitted: Sequence[_Admitted],
    context: SourceNodeContext,
) -> tuple[tuple[SourceChronologyNode, ...], tuple[SourceNodeFacetRefusal, ...]]:
    """Build sample, source-code, and exact-source-taxon chronology nodes."""
    groups: dict[tuple[object, ...], list[Mapping[str, object]]] = defaultdict(list)
    relations: dict[tuple[object, ...], tuple[Mapping[str, object], ...]] = {}
    facet_refusals: list[SourceNodeFacetRefusal] = []
    for observation, sample, site, claim in admitted:
        point = source_coordinate(site)
        interval = canonical_claim_interval(claim)
        source_unit = optional_text(observation.get("source_unit"))
        if point is None or interval is None or source_unit is None:
            raise AssertionError("admitted source node input lost governed semantics")
        longitude, latitude, coordinate_quality = point
        younger_bp, older_bp = interval
        common = (
            observation["sample_id"],
            observation["site_id"],
            observation["country_code"],
            latitude,
            longitude,
            coordinate_quality,
            claim["chronology_claim_id"],
            younger_bp,
            older_bp,
            observation["source_snapshot_id"],
            observation["build_id"],
            source_unit,
            claim["provenance_record_id"],
        )
        features, feature_refusals = _features(observation)
        for level, reason in feature_refusals:
            facet_refusals.append(
                SourceNodeFacetRefusal(
                    observation_id=str(observation["observation_id"]),
                    country_code=str(observation["country_code"]),
                    node_level=level,
                    reason_code=reason,
                )
            )
        for feature in features:
            key = (*common, *feature)
            groups[key].append(observation)
            relations[key] = sample, site, claim

    nodes = tuple(
        _build_node(key, groups[key], relations[key], context)
        for key in sorted(groups, key=lambda value: tuple(str(item) for item in value))
    )
    return (
        tuple(
            sorted(
                nodes,
                key=lambda node: (-node.older_bp, -node.younger_bp, node.node_id),
            )
        ),
        tuple(
            sorted(
                facet_refusals,
                key=lambda row: (row.country_code, row.observation_id, row.node_level),
            )
        ),
    )


def _build_node(
    key: tuple[object, ...],
    observations: Sequence[Mapping[str, object]],
    relations: tuple[Mapping[str, object], ...],
    context: SourceNodeContext,
) -> SourceChronologyNode:
    sample, site, claim = relations
    observation_ids = tuple(sorted(str(row["observation_id"]) for row in observations))
    node_level = str(key[13])
    feature_key = str(key[14])
    refusal_reason = {
        "source_sample_presence": "reviewed_pollen_sum_not_available",
        "source_ecological_code": "source_ecological_equivalence_not_reviewed",
        "source_taxon": "source_taxon_equivalence_not_reviewed",
    }[node_level]
    node_id = f"source-chronology-node:{digest(('neotoma', key[0], key[1], key[6], key[7], key[8], node_level, feature_key, key[15], key[16], key[17], key[11], context.producer_version))[:24]}"
    taxon_id = key[15]
    if taxon_id is not None and not isinstance(taxon_id, (int, str)):
        raise AssertionError("source taxon identity lost validated type")
    return SourceChronologyNode(
        node_id=node_id,
        source_family="neotoma",
        source_snapshot_id=str(key[9]),
        source_record_id=str(key[0]),
        site_id=str(key[1]),
        observation_ids=observation_ids,
        node_level=node_level,
        feature_key=feature_key,
        source_variable_ids=(
            tuple(
                sorted(
                    {
                        value
                        for row in observations
                        if (value := optional_text(row.get("variable_id"))) is not None
                    }
                )
            )
            if node_level == "source_taxon"
            else ()
        ),
        source_taxon_id=taxon_id,
        source_reported_name=None if key[16] is None else str(key[16]),
        source_ecological_group=None if key[17] is None else str(key[17]),
        source_unit=str(key[11]),
        country_code=str(key[2]),
        latitude=float(cast(float | int, key[3])),
        longitude=float(cast(float | int, key[4])),
        coordinate_quality=str(key[5]),
        chronology_claim_id=str(key[6]),
        younger_bp=cast(float | int, key[7]),
        older_bp=cast(float | int, key[8]),
        provenance_record_id=str(key[12]),
        input_digest=digest(
            {
                "observations": observations,
                "sample": sample,
                "site": site,
                "chronology": claim,
            }
        ),
        config_digest=context.config_digest,
        producer_version=context.producer_version,
        build_id=str(key[10]),
        candidate_refusal_reason=refusal_reason,
    )


__all__ = ["build_source_chronology_nodes"]
