"""Prediction persistence, scoring identity and complete-cohort controls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward import (
    geometry,
    producer,
    scoring,
    sources,
)

from .test_predictions import controlled_geometry
from .test_sources import controlled_inputs


def publish_control(monkeypatch: pytest.MonkeyPatch, output: Path) -> dict[str, Any]:
    loaded = controlled_inputs()
    monkeypatch.setattr(producer, "source_revision", lambda _: "controlled-source")
    monkeypatch.setattr(sources, "load_sources", lambda *_: loaded)
    monkeypatch.setattr(sources, "bound_inputs", lambda *_: ({}, {}))
    monkeypatch.setattr(producer, "require_absent_artifact_output", lambda _, p: p)
    monkeypatch.setattr(
        geometry,
        "geometry_inputs",
        lambda *_: [
            controlled_geometry(
                name,
                sorted(other for other in ("BOKE", "BUS", "SOLSOE83") if other != name),
            )
            for name in ("BOKE", "BUS", "SOLSOE83")
        ],
    )
    actual = scoring.score_frozen

    def observe_closed_file(
        path: Path, observations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        # An independent reopen sees the complete persisted population.
        with path.open() as stream:
            packet = json.load(stream)
        assert len(packet["contexts"]) == len(observations) == 18
        assert all("counts" not in context["target"] for context in packet["contexts"])
        return actual(path, observations)

    monkeypatch.setattr(scoring, "score_frozen", observe_closed_file)
    return producer.publish(output.parent, output.parent, output)


def test_publish_closes_reopens_and_scores_all_requested_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = publish_control(monkeypatch, tmp_path / "published")
    assert len(result["scores"]) == 54
    assert all(r["status"] == "scored" for r in result["scores"])
    assert all(
        r["prediction_file_sha256"] == result["prediction_file"]["sha256"]
        for r in result["scores"]
    )
    assert (
        len(result["summaries"]["families"])
        == len(result["summaries"]["pairwise"])
        == 3
    )
    assert all(
        r["status"] == "complete_cohort" for r in result["summaries"]["families"]
    )
    assert json.loads((tmp_path / "published/result.json").read_bytes()) == json.loads(
        json.dumps(result)
    )


@pytest.mark.parametrize("corruption", ["duplicate", "owner", "support"])
def test_frozen_context_corruption_refuses_before_scoring(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, corruption: str
) -> None:
    result = publish_control(monkeypatch, tmp_path / "published")
    path = tmp_path / "published/prediction-freeze.json"
    packet = json.loads(path.read_bytes())
    if corruption == "duplicate":
        packet["contexts"][0] = packet["contexts"][1]
    elif corruption == "owner":
        packet["contexts"][0]["target"]["site_id"] = -1
    else:
        packet["contexts"][0]["target"]["sample_ids"] = [-1]
    path.write_text(json.dumps(packet))
    with pytest.raises(ValueError, match="identit|owner|support"):
        scoring.score_frozen(path, result["observations"])


def test_one_refusal_keeps_primary_cohort_denominator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = publish_control(monkeypatch, tmp_path / "published")
    scores = result["scores"]
    scores[0]["status"] = "refused_prediction"
    summaries = scoring.summarize(scores, ["BOKE", "BUS", "SOLSOE83"])
    assert summaries["families"][0]["status"] == "refused_incomplete_cohort"
    assert summaries["families"][0]["scored_contexts"] == 17
    assert summaries["families"][1]["status"] == "complete_cohort"
    assert summaries["pairwise"][0]["status"] == "refused_incomplete_cohort"
