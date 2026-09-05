"""Source-owned chronology-node level and namespace tests."""

from __future__ import annotations

from copy import deepcopy

from .support import derive, source_rows


def test_source_levels_preserve_literal_identity_without_propagation() -> None:
    result = derive(source_rows())
    by_level = {node.node_level: node for node in result.nodes}

    assert set(by_level) == {
        "source_sample_presence",
        "source_ecological_code",
        "source_taxon",
    }
    assert by_level["source_ecological_code"].feature_key == (
        "source:neotoma:ecological-code:TRSH"
    )
    assert by_level["source_ecological_code"].source_ecological_group == "TRSH"
    assert by_level["source_taxon"].feature_key == "source:neotoma:taxon:1"
    assert by_level["source_taxon"].source_taxon_id == 1
    assert by_level["source_taxon"].source_reported_name == "Abies"
    assert all(node.source_family == "neotoma" for node in result.nodes)
    assert all(node.source_element_type == "pollen" for node in result.nodes)
    assert all(node.comparability_status == "comparable" for node in result.nodes)
    assert all(node.propagation_eligible is False for node in result.nodes)
    assert by_level["source_sample_presence"].candidate_refusal_reason == (
        "reviewed_pollen_sum_not_available"
    )
    assert by_level["source_ecological_code"].candidate_refusal_reason == (
        "source_ecological_equivalence_not_reviewed"
    )
    assert by_level["source_taxon"].candidate_refusal_reason == (
        "source_taxon_equivalence_not_reviewed"
    )
    assert result.reconciliation.propagation_eligible_event_count == 0


def test_observations_group_by_durable_sample_code_and_taxon_levels() -> None:
    rows = source_rows()
    second = deepcopy(rows["observations"][0])
    second["observation_id"] = "observation-2"
    second["variable_id"] = "variable-2"
    second["source_taxon_id"] = 2
    second["source_reported_name"] = "Betula"
    second_variable = deepcopy(rows["variables"][0])
    second_variable["variable_id"] = "variable-2"
    second_variable["source_taxon_id"] = 2
    second_variable["source_reported_name"] = "Betula"
    rows["observations"].append(second)
    rows["variables"].append(second_variable)

    result = derive(rows)
    by_level: dict[str, list[object]] = {}
    for node in result.nodes:
        by_level.setdefault(node.node_level, []).append(node)

    assert len(by_level["source_sample_presence"]) == 1
    assert len(by_level["source_ecological_code"]) == 1
    assert len(by_level["source_taxon"]) == 2
    assert len(result.nodes) == 4
    assert result.reconciliation.eligible_observation_count == 2
    assert dict(result.reconciliation.node_counts_by_level) == {
        "source_ecological_code": 1,
        "source_sample_presence": 1,
        "source_taxon": 2,
    }


def test_stable_node_identity_does_not_depend_on_observation_membership() -> None:
    original_rows = source_rows()
    original = derive(original_rows)
    expanded_rows = deepcopy(original_rows)
    second = deepcopy(expanded_rows["observations"][0])
    second["observation_id"] = "observation-2"
    expanded_rows["observations"].append(second)

    expanded = derive(expanded_rows)

    assert {node.node_id for node in original.nodes} == {
        node.node_id for node in expanded.nodes
    }
    assert {node.input_digest for node in original.nodes} != {
        node.input_digest for node in expanded.nodes
    }
    assert all(
        node.observation_ids == ("observation-1", "observation-2")
        for node in expanded.nodes
    )


def test_source_taxon_groups_variables_with_the_same_exact_taxon_identity() -> None:
    rows = source_rows()
    second = deepcopy(rows["observations"][0])
    second["observation_id"] = "observation-2"
    second["variable_id"] = "variable-2"
    second_variable = deepcopy(rows["variables"][0])
    second_variable["variable_id"] = "variable-2"
    rows["observations"].append(second)
    rows["variables"].append(second_variable)

    result = derive(rows)
    taxon = next(node for node in result.nodes if node.node_level == "source_taxon")

    assert len(result.nodes) == 3
    assert taxon.source_variable_ids == ("variable-1", "variable-2")
    assert taxon.observation_ids == ("observation-1", "observation-2")


def test_taxon_node_identity_distinguishes_literal_source_codes() -> None:
    rows = source_rows()
    second = deepcopy(rows["observations"][0])
    second["observation_id"] = "observation-2"
    second["variable_id"] = "variable-2"
    second["source_ecological_group"] = "UPHE"
    second_variable = deepcopy(rows["variables"][0])
    second_variable["variable_id"] = "variable-2"
    second_variable["source_semantics"] = [
        {"source_element_type": "pollen", "source_ecological_group": "UPHE"}
    ]
    rows["observations"].append(second)
    rows["variables"].append(second_variable)

    result = derive(rows)
    taxa = [node for node in result.nodes if node.node_level == "source_taxon"]

    assert len(taxa) == 2
    assert len({node.node_id for node in taxa}) == 2
    assert {node.source_ecological_group for node in taxa} == {"TRSH", "UPHE"}


def test_null_source_facets_remain_null_and_are_reconciled() -> None:
    rows = source_rows(source_code=None, taxon_id=None, taxon_name=None)
    result = derive(rows)

    assert len(result.nodes) == 1
    node = result.nodes[0]
    assert node.node_level == "source_sample_presence"
    assert node.source_ecological_group is None
    assert node.source_taxon_id is None
    assert node.source_reported_name is None
    assert "None" not in node.feature_key
    assert {(row.node_level, row.reason_code) for row in result.facet_refusals} == {
        ("source_ecological_code", "source_ecological_code_missing"),
        ("source_taxon", "source_taxon_identity_incomplete"),
    }


def test_nullable_observation_identity_is_enriched_from_matching_variable() -> None:
    rows = source_rows()
    observation = rows["observations"][0]
    observation["source_ecological_group"] = None
    observation["source_taxon_id"] = None
    observation["source_reported_name"] = None

    result = derive(rows)
    taxon = next(node for node in result.nodes if node.node_level == "source_taxon")

    assert len(result.nodes) == 3
    assert not result.facet_refusals
    assert taxon.source_taxon_id == 1
    assert taxon.source_reported_name == "Abies"
    assert taxon.source_ecological_group == "TRSH"
    assert result.reconciliation.source_taxon_identity_enrichment_count == 1
