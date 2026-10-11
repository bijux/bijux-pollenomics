"""Check the Lilla Gloppsjön metadata-only prediction boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import IO

import pytest

from bijux_pollenomics_dev.source_completion import (
    lilla_gloppsjon_direct_pollen as study,
)
from bijux_pollenomics_dev.source_completion import (
    lilla_gloppsjon_direct_pollen_scoring as scoring_study,
)
from bijux_pollenomics_dev.source_completion.nordic_author_target_pollen import (
    _compressed_read,
)
from bijux_pollenomics_dev.source_completion.nordic_direct_pollen import (
    BASELINE_METHODS,
    TAXA,
    _sha,
)
from bijux_pollenomics_dev.source_completion.sambosjon_direct_pollen import _surface

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = REPOSITORY / study.PROTOCOL.parent
PUBLICATION_LOCATOR = (
    "bijux-pollenomics-data/neotoma/publication-links/2026-09-29/"
    "responses/dataset-4200-publications.json"
)
PUBLICATION_SHA256 = "1a13124e576effcbd1f95d5db4b9b7cbda65baf92ab679381b161f209319d471"


def _publication_fixture(
    tmp_path: Path, publication_ids: tuple[int, ...] = (16060,)
) -> tuple[Path, dict[str, str], Path]:
    """Exercise the production publication guard with a test-owned response."""
    repository = tmp_path / "repository"
    repository.mkdir()
    response = tmp_path / "publications.json"
    response.write_text(
        json.dumps(
            {
                "data": [
                    {
                        "publication": {
                            "publicationid": publication_id,
                            "datasets": [
                                {"siteid": 3234, "datasetid": 4200, "primary": True}
                            ],
                        }
                    }
                    for publication_id in publication_ids
                ]
            }
        ),
        encoding="utf-8",
    )
    return (
        repository,
        {
            "publication_response_locator": response.name,
            "publication_response_sha256": _sha(response),
        },
        response,
    )


def test_prepared_metadata_and_predictions_replay_without_observation_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol, _ = study._protocol(REPOSITORY)
    assert protocol["publication_response_locator"] == PUBLICATION_LOCATOR
    assert protocol["publication_response_sha256"] == PUBLICATION_SHA256
    source_guard = study._verify_publication
    fixture_repository, fixture_protocol, _ = _publication_fixture(tmp_path)

    def portable_publication_guard(repository: Path, actual: dict[str, object]) -> None:
        assert repository == REPOSITORY
        assert actual["publication_response_locator"] == PUBLICATION_LOCATOR
        assert actual["publication_response_sha256"] == PUBLICATION_SHA256
        source_guard(fixture_repository, fixture_protocol)

    monkeypatch.setattr(study, "_verify_publication", portable_publication_guard)
    original_open = Path.open

    def guarded_open(
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[str] | IO[bytes]:
        if "observations" in path.parts:
            raise AssertionError("target observation partition opened before freeze")
        return original_open(path, mode, buffering, encoding, errors, newline)

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


@pytest.mark.parametrize("publication_ids", [(), (16061,), (16060, 16060)])
def test_publication_guard_refuses_missing_wrong_or_duplicate_primary(
    tmp_path: Path, publication_ids: tuple[int, ...]
) -> None:
    repository, protocol, _ = _publication_fixture(tmp_path, publication_ids)
    with pytest.raises(ValueError, match="primary publication changed"):
        study._verify_publication(repository, protocol)


def test_publication_guard_refuses_response_byte_drift(tmp_path: Path) -> None:
    repository, protocol, response = _publication_fixture(tmp_path)
    response.write_text('{"data":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="publication response changed"):
        study._verify_publication(repository, protocol)


def test_prepare_refuses_changed_selected_age_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(study, "_verify_publication", lambda *_: None)
    original_surface = _surface

    def changed_surface(repository: Path, name: str) -> list[dict[str, object]]:
        rows = original_surface(repository, name)
        if name == "age_claims":
            rows = [dict(row) for row in rows]
            for row in rows:
                if (
                    row["site_id"] == study.SITE
                    and row["chronology_id"] == study.CHRONOLOGY
                ):
                    value = row["source_age_value"]
                    assert isinstance(value, (int, float))
                    row["source_age_value"] = value + 1
                    break
        return rows

    monkeypatch.setattr(study, "_surface", changed_surface)
    with pytest.raises(ValueError, match="predeclared.*age claims changed"):
        study.prepare(REPOSITORY, tmp_path / "prepared")
    assert not (tmp_path / "prepared").exists()


def test_training_refuses_target_site_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    protocol, _ = study._protocol(REPOSITORY)
    original_read = _compressed_read

    def leaked_training(path: Path) -> object:
        training = original_read(path)
        assert isinstance(training, dict)
        assert all(isinstance(profile, dict) for profile in training.values())
        training[next(iter(training))]["site_id"] = study.SITE
        return training

    monkeypatch.setattr(study, "_compressed_read", leaked_training)
    with pytest.raises(ValueError, match="target physical site or alias entered"):
        study._training(REPOSITORY, protocol)


def test_scoring_source_guard_refuses_observation_drift(tmp_path: Path) -> None:
    relational = tmp_path / study.RELATIONAL
    surfaces = {}
    recorded = {}
    for name in (
        "sites",
        "collection_units",
        "datasets",
        "samples",
        "age_claims",
        "chronologies",
        "chronology_controls",
        "observations",
    ):
        relative = f"surfaces/{name}/part-00001.json"
        path = relational / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"rows":[]}', encoding="utf-8")
        digest = _sha(path)
        recorded[relative] = digest
        surfaces[name] = {"parts": [{"path": relative, "sha256": digest}]}
    manifest_path = relational / "manifest.json"
    manifest_path.write_text(json.dumps({"surfaces": surfaces}), encoding="utf-8")
    recorded["manifest.json"] = _sha(manifest_path)
    scoring = {
        "source_relational_manifest_sha256": _sha(manifest_path),
        "source_surface_sha256": recorded,
        "source_additional_metadata_sha256": {},
    }
    scoring_study._verify_scoring_source(tmp_path, scoring)

    (relational / "surfaces/observations/part-00001.json").write_text(
        '{"rows":[{"sample_id":"target"}]}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="source drift: surfaces/observations"):
        scoring_study._verify_scoring_source(tmp_path, scoring)


def test_synthetic_score_retains_refusals_and_all_sample_mass() -> None:
    counts = dict.fromkeys(TAXA, 0)
    counts["Alnus"] = 6
    counts["Betula"] = 4
    absent = dict.fromkeys(TAXA, 0)
    scoring = {
        "selected_age_sample_count": 2,
        "refused_age_sample_count": 1,
        "candidate_bin_ids": [0, 1],
        "target_dataset_doi": "10.21233/vpnw-pv89",
        "primary_method": "inverse_distance_squared",
        "frozen_predictions_sha256": "synthetic-prediction",
        "prediction_freeze_sha256": "synthetic-freeze",
        "source_relational_manifest_sha256": "synthetic-source",
        "scoring_protocol_sha256": "synthetic-protocol",
    }
    metadata = {
        "all_source_sample_ids": ["sample:a", "sample:b", "sample:c"],
        "selected_age_claims": {
            "sample:a": {"claim_id": "age:a", "point_cal_bp": 100, "bin_id": 0},
            "sample:b": {"claim_id": "age:b", "point_cal_bp": 600, "bin_id": 1},
        },
        "refused_age_claims": {"sample:c": {"claim_id": "age:c", "point_cal_bp": -10}},
    }
    fractions = dict.fromkeys(TAXA, 0.0)
    fractions["Alnus"] = 0.5
    fractions["Betula"] = 0.5
    predictions = {
        "predictions": [
            {
                "bin_id": bin_id,
                "method": method,
                "fractions": fractions,
                "training_site_count": 2,
            }
            for bin_id in (0, 1)
            for method in BASELINE_METHODS
        ],
        "refusals": [],
    }
    sample_counts: dict[str, scoring_study._SampleCounts] = {
        "sample:a": {
            "native_nisp": 10,
            "counts": counts,
            "direct_count_rows": 2,
            "other_observation_rows": 0,
        },
        "sample:b": {
            "native_nisp": 5,
            "counts": absent,
            "direct_count_rows": 1,
            "other_observation_rows": 0,
        },
        "sample:c": {
            "native_nisp": 7,
            "counts": absent,
            "direct_count_rows": 1,
            "other_observation_rows": 0,
        },
    }

    samples, scores, coverage, report = scoring_study._score_records(
        scoring, metadata, predictions, sample_counts
    )

    assert len(samples) == 3
    assert len(scores) == 6
    assert [row["status"] for row in coverage] == ["scored", "refused_zero_closed_axis"]
    assert report["scored_common_bins"] == 1
    assert report["mass"]["all_source_native_nisp"] == 22
    assert report["mass"]["all_source_closed_nisp"] == 10
    assert report["mass"]["all_source_outside_axis_nisp"] == 12
    assert report["mass"]["refused_native_nisp"] == 7
    assert all(
        row["mae_fraction"] == pytest.approx(0.0125)
        for row in scores
        if row["status"] == "scored"
    )
    assert all(
        row["mae_fraction"] is None for row in scores if row["status"] != "scored"
    )


def test_score_refuses_freeze_change_before_target_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_target_read(*_: object) -> None:
        raise AssertionError("target observations opened before freeze verification")

    monkeypatch.setattr(scoring_study, "_target_sample_counts", unexpected_target_read)
    with pytest.raises(ValueError, match="prediction freeze changed"):
        scoring_study.score(
            REPOSITORY,
            GOVERNED / "inputs",
            GOVERNED / "frozen",
            "0" * 64,
            tmp_path / "scored",
        )


def test_scoring_replays_governed_source_bound_result(tmp_path: Path) -> None:
    output = tmp_path / "scored"
    scoring_study.score(
        REPOSITORY,
        GOVERNED / "inputs",
        GOVERNED / "frozen",
        "bc89f334d95b727d2a051efaa794a131f1d13eee0613f1c32f6e6ace67a6e997",
        output,
    )
    for filename in ("sample-counts.csv", "scores.csv", "coverage.csv", "report.json"):
        assert _sha(output / filename) == _sha(GOVERNED / "scored" / filename)
    report = json.loads((output / "report.json").read_text())
    assert report["source_samples"] == 86
    assert report["age_selected_samples"] == 84
    assert report["age_refused_samples"] == 2
    assert report["scored_common_bins"] == 23
    assert report["refused_or_failed_bins"] == 0
    assert report["mass"]["all_source_native_nisp"] == (
        report["mass"]["selected_native_nisp"] + report["mass"]["refused_native_nisp"]
    )
