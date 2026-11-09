"""Chronology-node bundle materialization tests."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.analysis.propagation.source_chronology import (
    materialize_source_chronology_nodes,
)
from bijux_pollenomics.reporting.source_chronology import (
    build_source_chronology_atlas_projection,
)

from .support import derive, source_rows


def test_materialization_is_atomic_idempotent_and_propagation_refused(
    tmp_path: Path,
) -> None:
    result = derive(source_rows())
    output_root = tmp_path / "source-nodes"

    created = materialize_source_chronology_nodes(
        result, output_root=output_root, allowed_output_parent=tmp_path
    )
    unchanged = materialize_source_chronology_nodes(
        result, output_root=output_root, allowed_output_parent=tmp_path
    )

    assert created.disposition == "created"
    assert unchanged.disposition == "unchanged"
    assert created.manifest_sha256 == unchanged.manifest_sha256
    assert created.file_count == 5
    assert created.chronology_node_count == 3
    assert created.propagation_eligible_event_count == 0
    reconciliation = json.loads(
        (output_root / "reconciliation.json").read_text(encoding="utf-8")
    )
    nodes = json.loads((output_root / "chronology_nodes.json").read_text())
    assert nodes["source_snapshot_id"] == result.context.source_snapshot_id
    assert nodes["build_id"] == result.context.build_id
    assert nodes["config_digest"] == result.context.config_digest
    assert nodes["result_digest"] == result.result_digest
    assert reconciliation["candidate_generation_status"] == "refused"
    assert reconciliation["propagation_eligible_event_count"] == 0
    assert reconciliation["reconciliation"]["selected_sample_count"] == 1
    assert reconciliation["reconciliation"]["chronology_selection_posture_counts"] == {
        "selected_source_default": 1
    }
    assert nodes["records"][0]["chronology_id"] == "chronology-1"
    assert nodes["records"][0]["chronology_name"] == "Source chronology"
    assert nodes["records"][0]["is_default_chronology"] is True
    assert not (output_root / "primary_scenario_candidates.json").exists()


@pytest.mark.parametrize(
    "element", [None, "", " \t\n", "pollen", "Pollen", " POLLEN\t"]
)
def test_unknown_or_matching_element_preserves_source_context(element: object) -> None:
    rows = source_rows()
    expected = derive(rows)
    rows["observations"][0]["source_element"] = element
    semantics = cast(list[dict[str, object]], rows["variables"][0]["source_semantics"])
    semantics[0]["source_element"] = element

    result = derive(rows)

    assert len(result.nodes) == 3 and not result.admission_refusals
    assert [node.observation_ids for node in result.nodes] == [
        node.observation_ids for node in expected.nodes
    ]
    assert result.reconciliation == expected.reconciliation
    assert {(node.younger_bp, node.older_bp) for node in result.nodes} == {(100, 125)}
    assert all(node.propagation_eligible is False for node in result.nodes)


@pytest.mark.parametrize("element_type", [None, "Pollen", "POLLEN", "seed"])
def test_pollen_element_does_not_relax_canonical_element_type(
    element_type: object,
) -> None:
    rows = source_rows()
    rows["observations"][0].update(
        source_element="pollen", source_element_type=element_type
    )

    result = derive(rows)

    assert not result.nodes
    assert [row.reason_code for row in result.admission_refusals] == [
        "non_pollen_observation"
    ]


def test_mixed_element_population_keeps_refused_rows_out_of_map_and_bundle(
    tmp_path: Path,
) -> None:
    rows = source_rows(observation_id="accepted-pollen")
    observation = rows["observations"][0]
    observation["source_element"] = "pollen"
    semantics = cast(list[dict[str, object]], rows["variables"][0]["source_semantics"])
    semantics[0]["source_element"] = "pollen"
    for identity, element_type in (("contradictory-seed", "pollen"), ("seed", "seed")):
        refused = deepcopy(observation)
        refused.update(
            observation_id=identity,
            source_element="seed",
            source_element_type=element_type,
        )
        rows["observations"].append(refused)
        semantics.append(
            {
                **semantics[0],
                "source_element": "seed",
                "source_element_type": element_type,
            }
        )
    original = deepcopy(rows)

    result = derive(rows)
    atlas = build_source_chronology_atlas_projection(
        result, detail_record_ids={"neotoma:site:site-SE"}
    )
    published = materialize_source_chronology_nodes(
        result, output_root=tmp_path / "mixed", allowed_output_parent=tmp_path
    )

    assert rows == original
    assert len(result.nodes) == 3
    assert all(node.observation_ids == ("accepted-pollen",) for node in result.nodes)
    assert {row.observation_id for row in result.admission_refusals} == {
        "contradictory-seed",
        "seed",
    }
    assert {row.reason_code for row in result.admission_refusals} == {
        "non_pollen_observation"
    }
    country = next(
        row
        for row in result.reconciliation.country_reconciliations
        if row.country_code == "SE"
    )
    assert country.input_observation_count == 3
    assert country.pollen_observation_count == 2
    assert country.eligible_observation_count == 1
    assert country.refused_observation_count == 2
    assert result.reconciliation.propagation_eligible_event_count == 0
    assert atlas.reconciliation["eligible_observation_denominator"] == 1
    assert atlas.reconciliation["refused_observation_count"] == 2
    for layer in atlas.point_layers:
        features = cast(list[dict[str, object]], layer["features"])
        assert len(features) == 1
        assert features[0]["observation_denominator"] == 1
        assert features[0]["time_start_bp"] == 100
        assert features[0]["time_end_bp"] == 125
        assert layer["propagation_status"] == "refused" and layer["edge_count"] == 0
    output = Path(published.output_root)
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert len(manifest["files"]) == 4 and published.file_count == 5
    for item in manifest["files"]:
        body = (output / item["path"]).read_bytes()
        assert len(body) == item["byte_count"]
        assert hashlib.sha256(body).hexdigest() == item["sha256"]
    nodes = json.loads((output / "chronology_nodes.json").read_bytes())
    refusals = json.loads((output / "admission_refusals.json").read_bytes())
    reconciliation = json.loads((output / "reconciliation.json").read_bytes())
    assert nodes["records"] == [node.as_dict() for node in result.nodes]
    assert refusals["records"] == [row.as_dict() for row in result.admission_refusals]
    assert reconciliation["reconciliation"] == result.reconciliation.as_dict()
    assert reconciliation["propagation_eligible_event_count"] == 0
