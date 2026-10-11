"""Keep the Sämbosjön prediction boundary independent of target counts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion import sambosjon_direct_pollen as study
from bijux_pollenomics_dev.source_completion.nordic_author_target_pollen import (
    _compressed_read,
    _compressed_write,
)
from bijux_pollenomics_dev.source_completion.nordic_direct_pollen import (
    BASELINE_METHODS,
    TAXA,
    _sha,
)


def _prepared(tmp_path: Path, *, leaked_site: bool = False) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    protocol = repository / study.PROTOCOL
    protocol.parent.mkdir(parents=True)
    protocol.write_text("{}", encoding="utf-8")
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    training = {}
    for index in range(84):
        site = (
            study.SITE if leaked_site and index == 0 else f"neotoma:site:{1000 + index}"
        )
        counts = dict.fromkeys(TAXA, 0)
        counts[TAXA[index % 2]] = 10
        training[f"training:{index}"] = {
            "site_id": site,
            "group_id": site,
            "record_id": f"record:{index}",
            "coordinate": {"latitude": 56.0 + index / 1000, "longitude": 12.0},
            "bins": {"1": {"counts": counts, "closed_nisp": 10}} if index < 2 else {},
        }
    metadata = {
        "sites": [
            {
                "site_id": study.SITE,
                "group_id": study.SITE,
                "coordinate": {"latitude": 57.0, "longitude": 12.0},
                "candidate_bin_ids": ["1"],
            }
        ]
    }
    _compressed_write(prepared / "training.json.gz", training)
    (prepared / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (prepared / "input-manifest.json").write_text(
        json.dumps(
            {
                "protocol_sha256": _sha(protocol),
                "training_sha256": _sha(prepared / "training.json.gz"),
                "metadata_sha256": _sha(prepared / "metadata.json"),
            }
        ),
        encoding="utf-8",
    )
    return repository, prepared


def test_prediction_freezes_three_fixed_methods_without_target_profile(
    tmp_path: Path,
) -> None:
    repository, prepared = _prepared(tmp_path)
    frozen = tmp_path / "frozen"
    assert len(_compressed_read(prepared / "training.json.gz")) == 84

    study.predict(repository, prepared, frozen)

    prediction = json.loads((frozen / "predictions.json").read_text())
    freeze = json.loads((frozen / "freeze.json").read_text())
    assert {row["method"] for row in prediction["predictions"]} == set(BASELINE_METHODS)
    assert {row["bin_id"] for row in prediction["predictions"]} == {1}
    assert all(row["training_site_count"] == 2 for row in prediction["predictions"])
    assert all(
        study.SITE not in row["training_site_ids"] for row in prediction["predictions"]
    )
    assert freeze["predictions_sha256"] == _sha(frozen / "predictions.json")
    assert freeze["target_observations_used_for_prediction"] is False


def test_prediction_refuses_target_site_alias_in_training(tmp_path: Path) -> None:
    repository, prepared = _prepared(tmp_path, leaked_site=True)

    with pytest.raises(ValueError, match="target physical site leaked"):
        study.predict(repository, prepared, tmp_path / "frozen")


def test_score_refuses_changed_prediction_before_reading_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, prepared = _prepared(tmp_path)
    frozen = tmp_path / "frozen"
    study.predict(repository, prepared, frozen)
    freeze_digest = _sha(frozen / "freeze.json")
    (frozen / "predictions.json").write_text("{}", encoding="utf-8")

    def unexpected_target_read(*_: object) -> None:
        raise AssertionError("target counts opened before freeze verification")

    monkeypatch.setattr(study, "_nordic_target_outcomes", unexpected_target_read)

    with pytest.raises(ValueError, match="prediction freeze or inputs changed"):
        study.score(repository, prepared, frozen, freeze_digest, tmp_path / "scored")


def test_score_refuses_source_part_drift_before_reading_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, prepared = _prepared(tmp_path)
    relational = repository / study.RELATIONAL
    surfaces = {}
    recorded = {}
    for surface in ("samples", "age_claims", "observations"):
        relative = f"surfaces/{surface}/part-00001.json"
        path = relational / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"rows":[]}', encoding="utf-8")
        recorded[relative] = _sha(path)
        surfaces[surface] = {"parts": [{"path": relative}]}
    source_manifest = relational / "manifest.json"
    source_manifest.write_text(json.dumps({"surfaces": surfaces}), encoding="utf-8")
    recorded["manifest.json"] = _sha(source_manifest)
    input_manifest = prepared / "input-manifest.json"
    value = json.loads(input_manifest.read_text())
    value["source_surface_sha256"] = recorded
    input_manifest.write_text(json.dumps(value), encoding="utf-8")
    frozen = tmp_path / "frozen"
    study.predict(repository, prepared, frozen)

    (relational / "surfaces/observations/part-00001.json").write_text(
        '{"rows":[{}]}', encoding="utf-8"
    )

    def unexpected_target_read(*_: object) -> None:
        raise AssertionError("target counts opened before source verification")

    monkeypatch.setattr(study, "_nordic_target_outcomes", unexpected_target_read)
    with pytest.raises(
        ValueError, match="prepared Neotoma source drift: surfaces/observations"
    ):
        study.score(
            repository,
            prepared,
            frozen,
            _sha(frozen / "freeze.json"),
            tmp_path / "scored",
        )
