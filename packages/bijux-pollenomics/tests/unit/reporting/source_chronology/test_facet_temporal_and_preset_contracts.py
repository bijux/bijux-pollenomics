"""Four-country and literal source-label facet accountability tests."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)
from bijux_pollenomics.reporting.source_chronology.facet_accountability import (
    validate_facet_accountability,
)

from .support import BUILD, SNAPSHOT, projection, source_result


def _node(level: str) -> SourceChronologyNode:
    return next(node for node in source_result().nodes if node.node_level == level)


@pytest.mark.parametrize(
    ("global_field", "global_value", "country_field", "country_value"),
    [
        ("time_min_bp", 99, None, None),
        ("time_max_bp", 126, None, None),
        (None, None, "time_min_bp", 99),
        (None, None, "time_max_bp", 126),
    ],
)
def test_facet_time_extent_must_reconcile_to_nonempty_country_rows(
    global_field: str | None,
    global_value: int | None,
    country_field: str | None,
    country_value: int | None,
) -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    )
    if global_field is not None:
        metadata[global_field] = global_value
    else:
        countries = cast(list[dict[str, object]], metadata["country_counts"])
        assert country_field is not None
        countries[0][country_field] = country_value

    with pytest.raises(ValueError, match="time bounds do not reconcile"):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_sample_presence",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "catalog_definition_digest",
        "accountability_schema",
        "catalog_content_binding",
        "catalog_counts",
        "accountability_refusal",
        "preset_key",
        "preset_membership",
        "preset_refusal",
        "union_membership",
        "union_refusal",
    ],
)
def test_preset_accountability_rejects_identity_and_semantic_tampering(
    mutation: str,
) -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[2]["facet_metadata"])
    )
    catalog = cast(dict[str, object], metadata["source_label_preset_catalog"])
    accountability = cast(
        dict[str, object], metadata["source_label_preset_accountability"]
    )
    presets = cast(list[dict[str, object]], accountability["presets"])
    union = cast(dict[str, object], accountability["union"])

    if mutation == "catalog_definition_digest":
        catalog["definition_sha256"] = "sha256:" + "0" * 64
    elif mutation == "accountability_schema":
        accountability["schema_version"] = "neotoma-source-label-accountability.v0"
    elif mutation == "catalog_content_binding":
        accountability["catalog_content_sha256"] = "sha256:" + "0" * 64
    elif mutation == "catalog_counts":
        accountability["membership_count"] = 23
    elif mutation == "accountability_refusal":
        accountability["accepted_classification"] = True
    elif mutation == "preset_key":
        presets[0]["key"] = "inferred-avena"
    elif mutation == "preset_membership":
        presets[0]["member_taxon_ids"] = [4140]
    elif mutation == "preset_refusal":
        presets[0]["propagation_allowed"] = True
    elif mutation == "union_membership":
        union["member_taxon_ids"] = cast(list[int], union["member_taxon_ids"])[1:]
    else:
        union["aggregation_is_abundance"] = True

    with pytest.raises(ValueError):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_taxon",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )
