"""Dataset inclusion in the pollen study is separate from LRA readiness."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion import neotoma_entity_decisions as account

build = account.build

REPOSITORY = Path(__file__).resolve().parents[4]


def test_source_bound_dataset_decisions_replay_governed_result() -> None:
    result = build(REPOSITORY)
    governed = json.loads(
        (
            REPOSITORY
            / "docs/report/regions/nordic/source-capability/neotoma-entities/report.json"
        ).read_text()
    )
    assert result == governed
    assert result["dataset_count"] == 209
    assert result["sample_count"] == 12388
    assert result["direct_pollen_included_datasets"] == 85
    assert result["direct_pollen_excluded_datasets"] == 124
    assert (
        sum(
            row["count_and_comparable_age_candidate_samples"]
            for row in result["decisions"]
        )
        == 10637
    )
    assert all(
        row["lra_disposition"] == "unresolved_source_requirements"
        for row in result["decisions"]
    )
    assert result["country_denominators"]["SE"]["direct_pollen_included"] == 3
    assert result["country_denominators"]["DK"]["direct_pollen_included"] == 2
    assert result["country_denominators"]["NO"]["direct_pollen_included"] == 52
    assert result["country_denominators"]["FI"]["direct_pollen_included"] == 28


def _source_fixture(repository: Path) -> None:
    (repository / "artifacts").mkdir()
    for source in (
        account.DATASETS,
        account.MANIFEST,
        account.RAW_MANIFEST,
        account.SCREEN,
        account.COHORT,
        account.TRAINING,
    ):
        (repository / source).parent.mkdir(parents=True, exist_ok=True)
    datasets = {
        "rows": [
            {
                "dataset_id": "neotoma:dataset:1",
                "site_id": "neotoma:site:1",
                "country_code": "DK",
            }
        ]
    }
    dataset_bytes = json.dumps(datasets).encode()
    (repository / account.DATASETS).write_bytes(dataset_bytes)
    (repository / account.RAW_MANIFEST).write_text("{}")
    manifest = {
        "surfaces": {
            "datasets": {
                "parts": [
                    {
                        "path": "surfaces/datasets/part-00001.json",
                        "sha256": sha256(dataset_bytes).hexdigest(),
                        "row_count": 1,
                    }
                ]
            }
        }
    }
    manifest_bytes = json.dumps(manifest).encode()
    (repository / account.MANIFEST).write_bytes(manifest_bytes)
    screen = {
        "normalized_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "raw_manifest_sha256": sha256(b"{}").hexdigest(),
        "sample_decisions": [
            {
                "dataset_id": "neotoma:dataset:1",
                "screen_status": "necessary_candidate",
                "lra_admission_status": "refused",
            }
        ],
        "source_denominators": {"available_samples": 1},
        "screen_denominators": {"necessary_candidate_samples": 1},
    }
    (repository / account.SCREEN).write_text(json.dumps(screen))
    (repository / account.COHORT).write_text(
        "dataset_ids,site_id,country\n1,neotoma:site:1,DK\n"
    )
    (repository / account.TRAINING).write_text(
        "dataset_id,site_id,training_country,held_out_country\n1,neotoma:site:1,DK,FI\n"
    )


def test_atomic_publication_preserves_existing_bundle_and_source_identity(
    tmp_path: Path,
) -> None:
    _source_fixture(tmp_path)
    output = tmp_path / "artifacts/entity-account.json"
    result = account.run(tmp_path, output)
    assert output.read_bytes() == (json.dumps(result, indent=2) + "\n").encode()
    assert result["dataset_count"] == 1
    assert result["direct_pollen_included_datasets"] == 1
    before = output.read_bytes()
    with pytest.raises(ReportRebuildError, match="absent"):
        account.run(tmp_path, output)
    assert output.read_bytes() == before
    assert not output.with_name(output.name + ".stage").exists()


def test_source_change_after_snapshot_refuses_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _source_fixture(tmp_path)
    original = account._read
    changed = False

    def read_and_change(repository: Path, relative: Path) -> tuple[bytes, str]:
        nonlocal changed
        result = original(repository, relative)
        if relative == account.DATASETS and not changed:
            changed = True
            (repository / relative).write_bytes(result[0] + b" ")
        return result

    monkeypatch.setattr(account, "_read", read_and_change)
    output = tmp_path / "artifacts/entity-account.json"
    with pytest.raises(ValueError, match="source changed before publication"):
        account.run(tmp_path, output)
    assert changed
    assert not output.exists()
    assert not output.with_name(output.name + ".stage").exists()


def test_linked_source_refuses_even_with_matching_bytes(tmp_path: Path) -> None:
    _source_fixture(tmp_path)
    source = tmp_path / account.DATASETS
    original = source.with_name("original.json")
    source.rename(original)
    source.symlink_to(original)
    with pytest.raises(ValueError, match="symlink"):
        account.build(tmp_path)


def test_competing_output_cannot_be_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _source_fixture(tmp_path)
    output = tmp_path / "artifacts/entity-account.json"
    original_link = os.link

    def competing_link(source: Path, destination: Path) -> None:
        staged = json.loads(source.read_bytes())
        assert staged["dataset_count"] == 1
        destination.write_bytes(b"competing owner")
        original_link(source, destination)

    monkeypatch.setattr(os, "link", competing_link)
    with pytest.raises(FileExistsError):
        account.run(tmp_path, output)
    assert output.read_bytes() == b"competing owner"
    assert not output.with_name(output.name + ".stage").exists()


def test_competing_staging_file_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _source_fixture(tmp_path)
    output = tmp_path / "artifacts/entity-account.json"
    stage = output.with_name(output.name + ".stage")
    original_open = Path.open

    def competing_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == stage and args and args[0] == "x":
            with original_open(path, "wb") as writer:
                writer.write(b"competing staging owner")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", competing_open)
    with pytest.raises(FileExistsError):
        account.run(tmp_path, output)
    assert not output.exists()
    assert stage.read_bytes() == b"competing staging owner"
