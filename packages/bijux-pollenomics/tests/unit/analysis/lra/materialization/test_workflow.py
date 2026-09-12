"""Complete source denominators, exact sums and atomic publication refusals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.materialization import (
    audit_neotoma_lra_source,
    workflow,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from .support import authorities


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def test_full_source_ledger_preserves_values_alternatives_and_denominators(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    outputs = []
    for name in ("first", "second"):
        report = audit_neotoma_lra_source(
            raw_root=raw,
            normalized_root=normalized,
            output_directory=tmp_path / name,
            selected_sample_ids=("neotoma:sample:100",),
        )
        outputs.append(report.output_directory)
        manifest = json.loads((report.output_directory / "manifest.json").read_bytes())
        assert (report.available_samples, report.selected_samples) == (9, 1)
        assert (report.available_observations, report.selected_observations) == (45, 5)
        assert manifest["lra_accepted_samples"] == 0
        assert manifest["executable_request"] is None
        assert (
            sum(
                row["available_observations"]
                for row in manifest["country_accounting"].values()
            )
            == 45
        )
        assert manifest["source_orphans"] == 18
        for artifact in manifest["artifacts"]:
            assert (
                hashlib.sha256(
                    (report.output_directory / artifact["path"]).read_bytes()
                ).hexdigest()
                == artifact["sha256"]
            )
    assert {p.name: p.read_bytes() for p in outputs[0].iterdir()} == {
        p.name: p.read_bytes() for p in outputs[1].iterdir()
    }
    samples = _rows(outputs[0] / "samples.jsonl")
    sample = next(row for row in samples if row["selected"])
    assert sample["observation_count"] == 5
    assert sample["count_candidate_observations"] == 2
    assert sample["count_candidate_sums_by_exact_unit"] == [
        {"source_unit": "NISP", "exact_sum": 9007199254740993}
    ]
    assert sample["chronology"]["claim_count"] == 2
    assert sample["chronology"]["selected_claim_id"] is None
    observations = _rows(outputs[0] / "observations.jsonl")
    selected = [row for row in observations if row["selected"]]
    assert len(selected) == 5
    assert sum(row["typed_count"] == 0 for row in selected) == 1
    assert {row["source_observation"]["detection_status"] for row in selected} == {
        "reported_value",
        "source_null",
        "not_provided_by_source",
    }


def test_publication_refuses_existing_output_and_source_overlap(tmp_path: Path) -> None:
    raw, normalized = authorities(tmp_path)
    destination = tmp_path / "existing"
    destination.mkdir()
    (destination / "sentinel").write_text("preserve")
    with pytest.raises(FileExistsError):
        audit_neotoma_lra_source(
            raw_root=raw, normalized_root=normalized, output_directory=destination
        )
    bridge = tmp_path / "bridge"
    bridge.mkdir()
    before = sorted(str(p.relative_to(normalized)) for p in normalized.rglob("*"))
    with pytest.raises(ValueError, match="overlap"):
        audit_neotoma_lra_source(
            raw_root=raw,
            normalized_root=normalized,
            output_directory=bridge / ".." / "normalized" / "nested",
        )
    assert before == sorted(
        str(p.relative_to(normalized)) for p in normalized.rglob("*")
    )
    assert (destination / "sentinel").read_text() == "preserve"


def test_competing_final_directory_is_never_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw, normalized = authorities(tmp_path)
    publish = publish_new_output_tree

    def compete(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        publish(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(workflow, "publish_new_output_tree", compete)
    destination = tmp_path / "competing"
    with pytest.raises(FileExistsError):
        audit_neotoma_lra_source(
            raw_root=raw, normalized_root=normalized, output_directory=destination
        )
    assert destination.is_dir() and not list(destination.iterdir())
    assert len(list(tmp_path.glob(".competing.pending-*"))) == 1
