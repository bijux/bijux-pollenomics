"""Chronology-node bundle materialization tests."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.analysis.propagation.source_chronology import (
    materialize_source_chronology_nodes,
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
    assert not (output_root / "primary_scenario_candidates.json").exists()
