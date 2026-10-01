"""Check the Lilla Gloppsjön metadata-only prediction boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion import (
    lilla_gloppsjon_direct_pollen as study,
)
from bijux_pollenomics_dev.source_completion.nordic_direct_pollen import _sha

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = REPOSITORY / study.PROTOCOL.parent


def test_prepared_metadata_and_predictions_replay_without_observation_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_open = Path.open

    def guarded_open(path: Path, *args: object, **kwargs: object):
        if "observations" in path.parts:
            raise AssertionError("target observation partition opened before freeze")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    prepared = tmp_path / "inputs"
    frozen = tmp_path / "frozen"
    study.prepare(REPOSITORY, prepared)
    study.predict(REPOSITORY, prepared, frozen)

    for relative in (
        "inputs/metadata.json",
        "inputs/input-manifest.json",
        "frozen/predictions.json",
        "frozen/freeze.json",
    ):
        assert _sha(tmp_path / relative) == _sha(GOVERNED / relative)
    metadata = json.loads((prepared / "metadata.json").read_text())
    predictions = json.loads((frozen / "predictions.json").read_text())
    assert len(metadata["all_source_sample_ids"]) == 86
    assert len(metadata["selected_age_claims"]) == 84
    assert len(metadata["refused_age_claims"]) == 2
    assert not (
        set(metadata["selected_age_claims"]) & set(metadata["refused_age_claims"])
    )
    assert set(metadata["selected_age_claims"]) | set(
        metadata["refused_age_claims"]
    ) == set(metadata["all_source_sample_ids"])
    assert len(predictions["predictions"]) == 69
    assert predictions["refusals"] == []
    assert all(
        study.SITE not in row["training_site_ids"] for row in predictions["predictions"]
    )


def test_prepare_refuses_changed_selected_age_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(study, "_verify_publication", lambda *_: None)
    original_surface = study._surface

    def changed_surface(repository: Path, name: str):
        rows = original_surface(repository, name)
        if name == "age_claims":
            rows = [dict(row) for row in rows]
            for row in rows:
                if (
                    row["site_id"] == study.SITE
                    and row["chronology_id"] == study.CHRONOLOGY
                ):
                    row["source_age_value"] = row["source_age_value"] + 1
                    break
        return rows

    monkeypatch.setattr(study, "_surface", changed_surface)
    with pytest.raises(ValueError, match="predeclared.*age claims changed"):
        study.prepare(REPOSITORY, tmp_path / "prepared")
    assert not (tmp_path / "prepared").exists()


def test_training_refuses_target_site_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    protocol, _ = study._protocol(REPOSITORY)
    original_read = study._compressed_read

    def leaked_training(path: Path):
        training = original_read(path)
        training[next(iter(training))]["site_id"] = study.SITE
        return training

    monkeypatch.setattr(study, "_compressed_read", leaked_training)
    with pytest.raises(ValueError, match="target physical site or alias entered"):
        study._training(REPOSITORY, protocol)
