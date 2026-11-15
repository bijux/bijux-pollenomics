"""Scoring retains the prepared source epoch across valid chronology changes."""

from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.metrics import score_pollen
from bijux_pollenomics_dev.source_completion import nordic_direct_pollen as nordic

from .test_point_age_consumers import normalized_claim, normalized_sources


def refresh_part(root: Path, surface: str, rows: list[dict[str, Any]]) -> None:
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    part = manifest["surfaces"][surface]["parts"][0]
    path = root / part["path"]
    document = json.loads(path.read_bytes())
    document["rows"] = rows
    body = json.dumps(document).encode()
    path.write_bytes(body)
    part["sha256"] = hashlib.sha256(body).hexdigest()
    manifest["surfaces"][surface]["row_count"] = len(rows)
    manifest_path.write_text(json.dumps(manifest))


def part_rows(root: Path, surface: str) -> list[dict[str, Any]]:
    path = root / f"surfaces/{surface}/part-00001.json"
    return [dict(row) for row in json.loads(path.read_bytes())["rows"]]


@pytest.fixture
def scoring_sources(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, Any]]:
    root, work, published = (
        tmp_path / name for name in ("relational", "work", "published")
    )
    claim = normalized_claim()
    claim["older_bp"] = claim["source_age_older"] = 900
    normalized_sources(root, claim)
    for surface in ("samples", "age_claims", "observations"):
        rows = part_rows(root, surface)
        second = deepcopy(rows[0])
        if surface == "age_claims":
            second.update(
                subject_id="sample:two",
                chronology_claim_id="age:two",
                source_age_value=750,
                younger_bp=700,
                source_age_younger=700,
            )
        else:
            second["sample_id"] = "sample:two"
        refresh_part(root, surface, [*rows, second])
    manifest = json.loads((root / "manifest.json").read_bytes())
    pins = {
        "manifest.json": hashlib.sha256(
            (root / "manifest.json").read_bytes()
        ).hexdigest()
    }
    pins.update(
        {
            part["path"]: part["sha256"]
            for spec in manifest["surfaces"].values()
            for part in spec["parts"]
        }
    )
    metadata = {
        "candidate_samples": 2,
        "selected_age_claim_ids": {"sample:one": "age:one", "sample:two": "age:two"},
        "sites": [
            {
                "site_id": "site:one",
                "site_name": "synthetic",
                "candidate_sample_ids": ["sample:one", "sample:two"],
                "candidate_bin_ids": ["0", "1"],
                "dataset_details": {
                    "dataset:one": {
                        "dataset_name": "synthetic",
                        "source_dois": [],
                        "contributors": [],
                    }
                },
            }
        ],
    }
    work.mkdir()
    (work / "inputs").mkdir()
    (work / "input-manifest.json").write_text(
        json.dumps({"relational_file_sha256": pins})
    )
    all_metadata = {
        country: metadata
        if country == "DK"
        else {"candidate_samples": 0, "selected_age_claim_ids": {}, "sites": []}
        for country in nordic.COUNTRIES
    }
    (work / "target-metadata.json").write_text(json.dumps(all_metadata))
    for country in nordic.COUNTRIES:
        predictions = (
            [
                {
                    "target_site_id": "site:one",
                    "target_site_name": "synthetic",
                    "bin_id": index,
                    "method": "training_mean",
                    "prediction_fractions": {
                        name: int(name == "Alnus") for name in nordic.TAXA
                    },
                    "training_site_ids": ["site:training"],
                }
                for index in (0, 1)
            ]
            if country == "DK"
            else []
        )
        (work / f"predictions-{country}.json").write_text(
            json.dumps({"country": country, "predictions": predictions})
        )
        training = {
            "training": {
                "country": "SE",
                "site_id": "site:training",
                "site_name": "synthetic training",
                "dataset_id": "training",
                "dataset_name": "synthetic",
                "source_dois": [],
                "contributors": [],
                "sample_count": 1,
                "bins": {"0": {"closed_nisp": 1}},
            }
        }
        (work / "inputs" / f"training-{country}.json").write_text(json.dumps(training))
    return root, work, published, metadata


def test_unchanged_scoring_keeps_both_hand_counted_source_bins(
    scoring_sources: tuple[Path, Path, Path, dict[str, Any]],
) -> None:
    root, work, published, _ = scoring_sources
    nordic.score(root, work, published)
    with (published / "scores.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [
        (r["bin_id"], r["target_sample_count"], r["target_closed_nisp"]) for r in rows
    ] == [("0", "1", "1"), ("1", "1", "1")]


@pytest.mark.parametrize("surface", ["samples", "age_claims", "observations"])
def test_scoring_refuses_stale_manifest_part_before_using_changed_rows(
    scoring_sources: tuple[Path, Path, Path, dict[str, Any]], surface: str
) -> None:
    root, _, _, metadata = scoring_sources
    path = root / f"surfaces/{surface}/part-00001.json"
    document = json.loads(path.read_bytes())
    if surface == "samples":
        document["rows"][0]["site_id"] = "site:changed"
    elif surface == "age_claims":
        document["rows"][0]["source_age_value"] = 850
    else:
        document["rows"][0]["source_value"] = 7
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="digest mismatch"):
        nordic._nordic_target_outcomes(root, "DK", metadata)


def test_republished_valid_age_cannot_replace_the_prepared_source_epoch(
    scoring_sources: tuple[Path, Path, Path, dict[str, Any]],
) -> None:
    root, work, published, metadata = scoring_sources
    ages = part_rows(root, "age_claims")
    ages[0]["source_age_value"] = 850
    refresh_part(root, "age_claims", ages)
    # The new source is internally consistent and its point remains bounded.
    current = nordic._nordic_target_outcomes(root, "DK", metadata)
    assert list(current["sites"]) == ["site:one:1"]
    assert current["sites"]["site:one:1"]["closed_nisp"] == 2
    with pytest.raises(ValueError, match="digest mismatch"):
        nordic.score(root, work, published)
    assert not (work / "scores.csv").exists()
    assert not published.exists()


def test_source_changed_during_evaluation_refuses_result_publication(
    scoring_sources: tuple[Path, Path, Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, work, published, _ = scoring_sources
    changed = False

    def mutate_source(*args: Any, **kwargs: Any) -> Any:
        nonlocal changed
        result = score_pollen(*args, **kwargs)
        if not changed:
            changed = True
            ages = part_rows(root, "age_claims")
            ages[0]["source_age_value"] = 850
            refresh_part(root, "age_claims", ages)
        return result

    monkeypatch.setattr(nordic, "score_pollen", mutate_source)
    with pytest.raises(ValueError, match="digest mismatch"):
        nordic.score(root, work, published)
    assert not (work / "scores.csv").exists()
    assert not published.exists()


@pytest.mark.parametrize("pins", [{}, {"manifest.json": "0" * 64}])
def test_scoring_refuses_missing_or_false_prepared_source_pins(
    scoring_sources: tuple[Path, Path, Path, dict[str, Any]], pins: dict[str, str]
) -> None:
    root, work, published, _ = scoring_sources
    (work / "input-manifest.json").write_text(
        json.dumps({"relational_file_sha256": pins})
    )
    with pytest.raises(ValueError, match="Neotoma"):
        nordic.score(root, work, published)
    assert not published.exists()


def test_prepared_pins_must_cover_samples_ages_and_observations(
    scoring_sources: tuple[Path, Path, Path, dict[str, Any]],
) -> None:
    root, work, published, _ = scoring_sources
    pins = {
        "manifest.json": hashlib.sha256(
            (root / "manifest.json").read_bytes()
        ).hexdigest()
    }
    (work / "input-manifest.json").write_text(
        json.dumps({"relational_file_sha256": pins})
    )
    with pytest.raises(ValueError, match="omit a scoring surface"):
        nordic.score(root, work, published)
    assert not published.exists()


@pytest.mark.parametrize("surface", ["samples", "age_claims"])
def test_target_owner_metadata_spanning_parts_remains_complete(
    scoring_sources: tuple[Path, Path, Path, dict[str, Any]], surface: str
) -> None:
    root, _, _, metadata = scoring_sources
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    spec = manifest["surfaces"][surface]
    original = json.loads((root / spec["parts"][0]["path"]).read_bytes())
    spec["parts"] = []
    for number, row in enumerate(original["rows"], start=1):
        relative = f"surfaces/{surface}/part-{number:05d}.json"
        body = json.dumps({**original, "rows": [row]}).encode()
        (root / relative).write_bytes(body)
        spec["parts"].append(
            {"path": relative, "sha256": hashlib.sha256(body).hexdigest()}
        )
    manifest_path.write_text(json.dumps(manifest))
    outcomes = nordic._nordic_target_outcomes(root, "DK", metadata)
    assert list(outcomes["sites"]) == ["site:one:0", "site:one:1"]
    assert all(row["closed_nisp"] == 1 for row in outcomes["sites"].values())
