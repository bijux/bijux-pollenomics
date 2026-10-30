"""Scoring population, source-label custody and closed-member workflow controls."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    reopen as reopen_member,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning import (
    outcomes,
    scoring,
    study,
)


def _pin(path: Path, relative: str) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "path": relative,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _source_fixture(
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, int]], Path]:
    archive = root / "archive"
    archive.mkdir()
    taxa = [f"taxon-{i}" for i in range(30)]
    owners = [f"author:S{i:02}" for i in range(15)]
    refs, geometries, geometry_refs, counts = {}, {}, {}, {}

    def capture(name: str, body: dict[str, Any]) -> dict[str, Any]:
        raw = json.dumps(body, sort_keys=True).encode()
        sha = hashlib.sha256(raw).hexdigest()
        path = archive / "objects" / sha[:2] / sha
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {"path": name, "bytes": len(raw), "sha256": sha}

    for index, owner in enumerate(owners):
        metadata = {
            "sample_id": owner,
            "site_id": owner,
            "bin_id": "author-TW5",
            "age_type": "calendar_bp",
            "age_support_bp": [[1250, 1750]],
        }
        geometry = {"sample_metadata": metadata}
        geometries[owner] = geometry
        geometry_refs[owner] = capture(f"S{index:02}-geometry.json", geometry)
        vector = [index + 1, *([0] * 29)]
        counts[owner] = dict(zip(taxa, vector, strict=True))
        refs[owner] = {
            **capture(
                f"S{index:02}-raw.json",
                {
                    "data_kind": "source_observations",
                    "taxa": taxa,
                    "sample": {**metadata, "counts": vector},
                },
            ),
            "record_id": owner,
        }
    selected = owners[:10]
    packet = {
        "taxa": taxa,
        "groups": {owner: "group:" + owner for owner in owners},
        "cohort": {"selected": selected},
        "geometries": geometries,
        "geometry_refs": geometry_refs,
        "observation_refs": [refs[owner] for owner in selected],
        "contexts": [
            {"context_id": "context:" + owner, "target": owner} for owner in selected
        ],
        "retained_reference_predictions": [{} for _ in range(40)],
        "sources": [],
    }
    zero = dict.fromkeys(scoring.METRICS, 0.0)
    old = [
        {
            "outer_target": owner,
            "status": "scored",
            "selected_scale_km": 20.0,
            "observed_count": sum(counts[owner].values()),
            "observed_reference": refs[owner],
            "metrics": dict(zero),
            "matched_baselines": {method: dict(zero) for method in scoring.BASELINES},
        }
        for owner in owners
    ]
    old_path = root / "retained.json"
    old_path.write_text(json.dumps(old))
    protocol = {
        "schema_version": "author-lra-geographic-thinning.v1",
        "cohort": {"size": 10},
        "models": {"hellinger_scales_km": [20.0, 100.0]},
        "qualified_sources": {"outer_scores": _pin(old_path, old_path.name)},
        "limits": {
            "producer_wall_seconds": 60,
            "observer_wall_seconds": 60,
            "max_rss_bytes": 512 * 1024**2,
            "max_output_bytes": 16 * 1024**2,
        },
    }
    return packet, protocol, {owner: counts[owner] for owner in selected}, archive


def _predictions(packet: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "target": context["target"],
            "context_id": context["context_id"],
            "method_id": method,
            "status": "predicted",
            "scientific_input_sha256": "a" * 64,
            "pollen_fraction": [1.0, *([0.0] * 29)],
        }
        for context in packet["contexts"]
        for method in scoring.METHODS
    ]


def test_reader_retains_ten_exact_once_scoring_roles(tmp_path: Path) -> None:
    packet, _, counts, archive = _source_fixture(tmp_path)
    reader = outcomes.OutcomeReader(archive, packet, "f" * 64)
    assert {
        owner: reader.read(owner) for owner in packet["cohort"]["selected"]
    } == counts
    assert len(reader.accesses) == 10
    assert {row["prediction_freeze_sha256"] for row in reader.accesses} == {"f" * 64}
    with pytest.raises(ValueError, match="already accessed"):
        reader.read(packet["cohort"]["selected"][0])
    with pytest.raises(ValueError, match="unselected"):
        reader.read("author:S10")


def test_reader_refuses_a_different_valid_owner_geometry(tmp_path: Path) -> None:
    packet, _, _, archive = _source_fixture(tmp_path)
    first, second = packet["cohort"]["selected"][:2]
    packet["geometry_refs"][first] = packet["geometry_refs"][second]
    reader = outcomes.OutcomeReader(archive, packet, "f" * 64)
    with pytest.raises(ValueError, match="target geometry"):
        reader.read(first)
    assert reader.accesses == []


@pytest.mark.parametrize("bad", [True, 1.5, -1, 2**53 + 1])
def test_reader_refuses_invalid_native_count_representations(
    tmp_path: Path, bad: Any
) -> None:
    packet, _, _, archive = _source_fixture(tmp_path)
    ref = packet["observation_refs"][0]
    body = json.loads(
        (archive / "objects" / ref["sha256"][:2] / ref["sha256"]).read_text()
    )
    body["sample"]["counts"][0] = bad
    raw = json.dumps(body).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = archive / "objects" / sha[:2] / sha
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(raw)
    packet["observation_refs"][0] = {**ref, "bytes": len(raw), "sha256": sha}
    reader = outcomes.OutcomeReader(archive, packet, "f" * 64)
    with pytest.raises(ValueError, match="integer N"):
        reader.read(ref["record_id"])
    assert not reader.accesses


def test_scores_count_grains_once_and_keep_impossible_loss(tmp_path: Path) -> None:
    packet, protocol, counts, _ = _source_fixture(tmp_path)
    predictions = _predictions(packet)
    row = next(r for r in predictions if r["method_id"] == "hellinger_20km")
    row["pollen_fraction"] = [0.0, 1.0, *([0.0] * 28)]
    prior = scoring.retained_metrics(tmp_path, protocol, packet, counts)
    report = scoring.score_targets(packet, predictions, counts, prior, "f" * 64)
    assert report["unique_observed_total_count"] == 55
    assert len(report["targets"]) == 10
    assert all(len(target["methods"]) == 5 for target in report["targets"])
    assert all(len(target["comparisons"]) == 11 for target in report["targets"])
    summary = report["method_summaries"]["hellinger_20km"]
    assert summary["mean_count_deviance"] == {
        "status": "infinite_positive_count_loss",
        "value": None,
    }
    assert summary["mean_bounded_metrics_on_scored_targets"][
        "hellinger"
    ] == pytest.approx(0.1)
    assert summary["impossible_positive_count_target_ids"] == [row["target"]]
    assert len(report["comparison_summaries"]) == 11
    json.dumps(report, allow_nan=False)


def test_method_refusal_retains_row_and_exact_paired_mask(tmp_path: Path) -> None:
    packet, protocol, counts, _ = _source_fixture(tmp_path)
    predictions = _predictions(packet)
    failed = predictions[0]
    failed.update(status="refused", reason="source_domain")
    failed.pop("pollen_fraction")
    original = deepcopy(predictions)
    prior = scoring.retained_metrics(tmp_path, protocol, packet, counts)
    report = scoring.score_targets(packet, predictions, counts, prior, "f" * 64)
    assert predictions == original
    summary = report["method_summaries"]["training_mean"]
    assert summary["refused_target_ids"] == [failed["target"]]
    assert len(summary["scored_target_ids"]) == 9
    comparison = next(
        row
        for row in report["comparison_summaries"]
        if row["model_method_id"] == "hellinger_20km"
        and row["reference_method_id"] == "training_mean"
        and row["reference_channel"] == "within_thinned"
    )
    assert comparison["excluded_target_ids"] == [failed["target"]]
    assert len(comparison["common_target_ids"]) == 9
    assert len(report["targets"][0]["methods"]) == 5


def test_retained_scores_refuse_another_count_or_source_revision(
    tmp_path: Path,
) -> None:
    packet, protocol, counts, _ = _source_fixture(tmp_path)
    counts[packet["cohort"]["selected"][0]][packet["taxa"][0]] += 1
    with pytest.raises(ValueError, match="outcome/support"):
        scoring.retained_metrics(tmp_path, protocol, packet, counts)
    (tmp_path / "retained.json").write_text("[]")
    with pytest.raises(ValueError, match="absent or redirected"):
        scoring.retained_metrics(tmp_path, protocol, packet, counts)


@pytest.mark.parametrize("damage_predictions", [False, True])
def test_workflow_requires_member_readback_before_any_scoring_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage_predictions: bool
) -> None:
    packet, protocol, counts, archive = _source_fixture(tmp_path)
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    output = artifact_root / "result"
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol))
    monkeypatch.setattr(study, "load_inputs", lambda *_: packet)
    monkeypatch.setattr(study, "check_sources", lambda *_: None)
    monkeypatch.setattr(
        study,
        "code_state",
        lambda *_: {"head": "c" * 40, "index_sha256": "d" * 64, "python_files": {}},
    )
    rows = _predictions(packet)
    monkeypatch.setattr(
        study,
        "predict_context",
        lambda context, *_: [row for row in rows if row["target"] == context["target"]],
    )
    opened = []

    class GuardedReader(outcomes.OutcomeReader):
        def read(self, target: str) -> dict[str, int]:
            frozen = json.loads((output / "prediction-manifest.json").read_text())
            for pin in frozen["files"].values():
                raw = (output / pin["path"]).read_bytes()
                assert len(raw) == pin["bytes"]
                assert hashlib.sha256(raw).hexdigest() == pin["sha256"]
            opened.append(target)
            return super().read(target)

    monkeypatch.setattr(study, "OutcomeReader", GuardedReader)

    def reopen(directory: Path, pin: dict[str, Any]) -> Any:
        if damage_predictions and pin["path"] == "prediction-manifest.json":
            with (directory / "predictions.json").open("ab") as stream:
                stream.write(b"\n")
        return reopen_member(directory, pin)

    monkeypatch.setattr(study, "reopen", reopen)
    if damage_predictions:
        with pytest.raises(ValueError, match="member changed"):
            study.produce(tmp_path, archive, protocol_path, output)
        assert opened == []
    else:
        result = study.produce(tmp_path, archive, protocol_path, output)
        assert opened == packet["cohort"]["selected"]
        assert result["source_guards_passed"] is True
        scores = json.loads((output / "scores.json").read_text())
        assert scores["unique_observed_total_count"] == sum(
            sum(value.values()) for value in counts.values()
        )
