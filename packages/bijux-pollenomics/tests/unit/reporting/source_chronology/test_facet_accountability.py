"""Four-country and literal source-label facet accountability tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import cast

import pytest

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)
from bijux_pollenomics.reporting.source_chronology.facet_accountability import (
    validate_facet_accountability,
)
from bijux_pollenomics.reporting.source_chronology.facets import build_facet_metadata
from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    build_neotoma_source_label_preset_catalog,
)

from .support import BUILD, SNAPSHOT, projection, source_result


def _node(level: str) -> SourceChronologyNode:
    return next(node for node in source_result().nodes if node.node_level == level)


def test_layer_and_literal_facets_reconcile_unique_sites_by_country() -> None:
    base = _node("source_ecological_code")
    nodes = [
        replace(
            base,
            node_id="trsh-se-a",
            site_id="site-se",
            source_record_id="sample-se-a",
            observation_ids=("observation-se-a",),
            younger_bp=100,
            older_bp=200,
        ),
        replace(
            base,
            node_id="trsh-se-b",
            site_id="site-se",
            source_record_id="sample-se-b",
            observation_ids=("observation-se-b", "observation-se-c"),
            younger_bp=50,
            older_bp=150,
        ),
        replace(
            base,
            node_id="trsh-dk",
            site_id="site-dk",
            source_record_id="sample-dk",
            country_code="DK",
            observation_ids=("observation-dk",),
            younger_bp=300,
            older_bp=400,
        ),
    ]

    metadata = build_facet_metadata(
        nodes,
        node_level="source_ecological_code",
        source_snapshot_id=SNAPSHOT,
        build_id=BUILD,
    )

    assert metadata["site_count_semantics"] == "unique_site_union"
    assert (
        metadata["site_count"],
        metadata["node_count"],
        metadata["observation_denominator"],
        metadata["time_min_bp"],
        metadata["time_max_bp"],
    ) == (2, 3, 4, 50, 400)
    countries = cast(list[dict[str, object]], metadata["country_counts"])
    assert [row["country_code"] for row in countries] == ["SE", "DK", "NO", "FI"]
    assert countries[:2] == [
        {
            "country_code": "SE",
            "value": "Sweden",
            "site_count_semantics": "unique_site_union",
            "site_count": 1,
            "node_count": 2,
            "observation_denominator": 3,
            "time_min_bp": 50,
            "time_max_bp": 200,
        },
        {
            "country_code": "DK",
            "value": "Denmark",
            "site_count_semantics": "unique_site_union",
            "site_count": 1,
            "node_count": 1,
            "observation_denominator": 1,
            "time_min_bp": 300,
            "time_max_bp": 400,
        },
    ]
    assert all(
        (
            row["site_count"],
            row["node_count"],
            row["observation_denominator"],
            row["time_min_bp"],
            row["time_max_bp"],
        )
        == (0, 0, 0, None, None)
        for row in countries[2:]
    )
    literal = cast(list[dict[str, object]], metadata["source_ecological_codes"])[0]
    assert literal["country_counts"] == countries


def test_source_label_presets_are_identity_bound_and_deduplicate_overlaps() -> None:
    base = _node("source_taxon")
    taxon_rows = (
        (415, "Avena/Triticum", "SE", "site-se", ("observation-a",)),
        (
            3917,
            "Avena/Triticum-type",
            "DK",
            "site-dk",
            ("observation-b", "observation-c"),
        ),
        (3924, "Hordeum/Secale", "NO", "site-no", ("observation-d",)),
        (4150, "Avena/Triticum lookalike", "FI", "site-fi", ("observation-e",)),
    )
    nodes = [
        replace(
            base,
            node_id=f"taxon-{taxon_id}",
            feature_key=f"source:neotoma:taxon:{taxon_id}",
            source_taxon_id=taxon_id,
            source_reported_name=label,
            country_code=country_code,
            site_id=site_id,
            source_record_id=f"sample-{country_code.casefold()}",
            observation_ids=observation_ids,
        )
        for taxon_id, label, country_code, site_id, observation_ids in taxon_rows
    ]

    metadata = build_facet_metadata(
        nodes,
        node_level="source_taxon",
        source_snapshot_id=SNAPSHOT,
        build_id=BUILD,
    )
    catalog = cast(dict[str, object], metadata["source_label_preset_catalog"])
    accountability = cast(
        dict[str, object], metadata["source_label_preset_accountability"]
    )

    assert catalog["source_snapshot_id"] == SNAPSHOT
    assert catalog["build_id"] == BUILD
    assert accountability["catalog_content_sha256"] == catalog["content_sha256"]
    assert (
        accountability["source_taxon_count"],
        accountability["preset_count"],
        accountability["membership_count"],
    ) == (21, 5, 24)
    assert accountability["accepted_classification"] is False
    assert accountability["aggregation_is_abundance"] is False
    assert accountability["propagation_allowed"] is False

    presets = {
        cast(str, row["key"]): row
        for row in cast(list[dict[str, object]], accountability["presets"])
    }
    assert set(presets) == {"avena", "hordeum", "triticum", "secale", "cerealia"}
    assert all(row["accepted_classification"] is False for row in presets.values())
    assert all(row["aggregation_is_abundance"] is False for row in presets.values())
    assert all(row["propagation_allowed"] is False for row in presets.values())
    assert (
        presets["avena"]["node_count"],
        presets["avena"]["observation_denominator"],
        presets["avena"]["site_count"],
    ) == (2, 3, 2)
    assert (
        presets["triticum"]["node_count"],
        presets["hordeum"]["node_count"],
        presets["secale"]["node_count"],
    ) == (2, 1, 1)
    assert all(
        (
            row["site_count"],
            row["node_count"],
            row["observation_denominator"],
            row["time_min_bp"],
            row["time_max_bp"],
        )
        == (0, 0, 0, None, None)
        for row in cast(list[dict[str, object]], presets["cerealia"]["country_counts"])
    )

    union = cast(dict[str, object], accountability["union"])
    assert (
        union["member_taxon_count"],
        union["node_count"],
        union["observation_denominator"],
        union["site_count"],
    ) == (21, 3, 4, 3)
    assert union["accepted_classification"] is False
    assert union["aggregation_is_abundance"] is False
    assert union["propagation_allowed"] is False
    assert 4150 not in cast(list[int], union["member_taxon_ids"])

    exact_rows = cast(list[dict[str, object]], metadata["source_taxa"])
    assert {row["value"] for row in exact_rows} == {
        f"source:neotoma:taxon:{taxon_id}" for taxon_id, *_rest in taxon_rows
    }


def test_facet_catalog_rejects_identity_drift_from_result_context() -> None:
    with pytest.raises(ValueError, match="source identity differs"):
        build_facet_metadata(
            [_node("source_taxon")],
            node_level="source_taxon",
            source_snapshot_id="sha256:" + "c" * 64,
            build_id=BUILD,
        )


@pytest.mark.parametrize("bad_count", [True, 1.0, "1"])
def test_facet_accountability_rejects_non_integer_counts(bad_count: object) -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    )
    metadata["node_count"] = bad_count

    with pytest.raises(ValueError):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_sample_presence",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


@pytest.mark.parametrize("bad_count", [False, 1.0, "1"])
def test_facet_accountability_rejects_non_integer_country_counts(
    bad_count: object,
) -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    )
    countries = cast(list[dict[str, object]], metadata["country_counts"])
    countries[0]["node_count"] = bad_count

    with pytest.raises(ValueError):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_sample_presence",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


@pytest.mark.parametrize("mutation", ["duplicate", "omitted", "reordered"])
def test_facet_accountability_requires_complete_ordered_country_rows(
    mutation: str,
) -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    )
    countries = cast(list[dict[str, object]], metadata["country_counts"])
    if mutation == "duplicate":
        countries[1] = deepcopy(countries[0])
    elif mutation == "omitted":
        countries.pop()
    else:
        countries.reverse()

    with pytest.raises(ValueError):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_sample_presence",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "neotoma-source-chronology-facets.v3"),
        ("node_level", "source_taxon"),
    ],
)
def test_facet_accountability_rejects_contract_identity_drift(
    field: str, value: str
) -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    )
    metadata[field] = value

    with pytest.raises(ValueError, match="schema or node level"):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_sample_presence",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


def test_facet_accountability_rejects_country_name_drift() -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    )
    countries = cast(list[dict[str, object]], metadata["country_counts"])
    countries[0]["value"] = "Not Sweden"

    with pytest.raises(ValueError, match="country identity"):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_sample_presence",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


def test_facet_accountability_rejects_foreign_recomputed_catalog_identity() -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[2]["facet_metadata"])
    )
    catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "d" * 64,
    )
    metadata["source_label_preset_catalog"] = catalog
    accountability = cast(
        dict[str, object], metadata["source_label_preset_accountability"]
    )
    accountability["catalog_content_sha256"] = catalog["content_sha256"]

    with pytest.raises(ValueError, match="catalog identity"):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_taxon",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


@pytest.mark.parametrize("duplicate_kind", ["node", "observation"])
def test_facet_builder_rejects_duplicate_source_identities(
    duplicate_kind: str,
) -> None:
    base = _node("source_taxon")
    duplicate = replace(
        base,
        node_id=base.node_id if duplicate_kind == "node" else base.node_id + ":other",
    )

    with pytest.raises(ValueError, match=f"duplicate {duplicate_kind} identity"):
        build_facet_metadata(
            [base, duplicate],
            node_level="source_taxon",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


def test_facet_accountability_rejects_added_scientific_promotion_flag() -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    )
    metadata["propagation_allowed"] = True

    with pytest.raises(ValueError, match="scientific refusal"):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_sample_presence",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


def test_facet_accountability_rejects_density_denominator_drift() -> None:
    _result, atlas = projection()
    metadata = deepcopy(
        cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    )
    density = cast(dict[str, object], metadata["time_density"])
    density["observation_denominator"] = 2

    with pytest.raises(ValueError, match="time density"):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_sample_presence",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )


def test_preset_denominators_must_derive_from_exact_taxon_facets() -> None:
    base = _node("source_taxon")
    governed = replace(
        base,
        feature_key="source:neotoma:taxon:415",
        source_taxon_id=415,
        source_reported_name="Avena/Triticum",
    )
    metadata = build_facet_metadata(
        [governed],
        node_level="source_taxon",
        source_snapshot_id=SNAPSHOT,
        build_id=BUILD,
    )
    accountability = cast(
        dict[str, object], metadata["source_label_preset_accountability"]
    )
    presets = cast(list[dict[str, object]], accountability["presets"])
    avena = presets[0]
    avena.update(node_count=2, observation_denominator=2)
    countries = cast(list[dict[str, object]], avena["country_counts"])
    countries[0].update(node_count=2, observation_denominator=2)
    density = cast(dict[str, object], avena["time_density"])
    density.update(node_count=2, observation_denominator=2)
    bins = cast(list[dict[str, object]], density["bins"])
    for row in bins:
        row.update(node_count=2, observation_denominator=2)

    with pytest.raises(ValueError, match="preset denominator changed"):
        validate_facet_accountability(
            metadata,
            expected_node_level="source_taxon",
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )
