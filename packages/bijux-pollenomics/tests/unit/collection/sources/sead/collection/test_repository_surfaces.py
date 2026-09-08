from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces import (
    SEAD_REPOSITORY_SURFACE_PATHS,
    RepositorySurfaceCandidate,
    prepare_repository_surface_transaction,
    publish_repository_surface_candidate,
    validate_repository_surface_candidate,
)
from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces import (
    validation as surface_validation,
)


def _write_population(root: Path, *, prefix: str) -> dict[Path, bytes]:
    population: dict[Path, bytes] = {}
    for index, relative_path in enumerate(SEAD_REPOSITORY_SURFACE_PATHS):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            b'{"value": "' + prefix.encode() + str(index).encode() + b'"}\n'
            if path.suffix in {".json", ".geojson"}
            else f"{prefix}-{index}\n".encode()
        )
        path.write_bytes(content)
        population[relative_path] = content
    return population


def test_repository_surface_publication_replaces_the_exact_population(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    baseline = _write_population(data_root, prefix="old")
    transaction = prepare_repository_surface_transaction(
        data_root, artifacts_root=tmp_path / "artifacts"
    )
    candidate = _write_population(transaction.candidate_data_root, prefix="new")
    monkeypatch.setattr(
        surface_validation, "validate_cross_format_counts", lambda _: None
    )

    outcome = publish_repository_surface_candidate(transaction)

    assert outcome == "replaced"
    assert baseline != candidate
    assert all(
        (data_root / path).read_bytes() == content
        for path, content in candidate.items()
    )
    journal = json.loads(
        (transaction.transaction_root / "journal.json").read_text(encoding="utf-8")
    )
    assert journal["state"] == "replaced"
    assert not transaction.lock_path.exists()
    assert not (transaction.transaction_root / "candidate").exists()
    assert not (transaction.transaction_root / "recovery").exists()


@pytest.mark.parametrize("failure_index", range(len(SEAD_REPOSITORY_SURFACE_PATHS)))
def test_repository_surface_publication_failure_restores_every_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_index: int,
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    baseline = _write_population(data_root, prefix="old")
    transaction = prepare_repository_surface_transaction(
        data_root, artifacts_root=tmp_path / "artifacts"
    )
    candidate = _write_population(transaction.candidate_data_root, prefix="new")
    monkeypatch.setattr(
        surface_validation, "validate_cross_format_counts", lambda _: None
    )
    real_replace = os.replace
    candidate_installs = 0

    def failing_replace(source: Path | str, target: Path | str) -> None:
        nonlocal candidate_installs
        source_path = Path(source)
        if transaction.candidate_data_root in source_path.parents:
            if candidate_installs == failure_index:
                raise OSError("injected candidate installation failure")
            candidate_installs += 1
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError, match="injected"):
        publish_repository_surface_candidate(transaction)

    assert all(
        (data_root / path).read_bytes() == content for path, content in baseline.items()
    )
    assert all(
        (transaction.candidate_data_root / path).read_bytes() == content
        for path, content in candidate.items()
    )
    journal = json.loads(
        (transaction.transaction_root / "journal.json").read_text(encoding="utf-8")
    )
    assert journal["state"] == "rolled_back"
    assert not transaction.lock_path.exists()


@pytest.mark.parametrize("failure_index", (0, 7, 23))
def test_repository_surface_baseline_move_failure_leaves_every_target_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_index: int,
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    baseline = _write_population(data_root, prefix="old")
    transaction = prepare_repository_surface_transaction(
        data_root, artifacts_root=tmp_path / "artifacts"
    )
    candidate = _write_population(transaction.candidate_data_root, prefix="new")
    monkeypatch.setattr(
        surface_validation, "validate_cross_format_counts", lambda _: None
    )
    real_replace = os.replace
    baseline_moves = 0

    def failing_replace(source: Path | str, target: Path | str) -> None:
        nonlocal baseline_moves
        source_path = Path(source)
        target_path = Path(target)
        if (
            transaction.data_root in source_path.parents
            and transaction.recovery_root in target_path.parents
        ):
            if baseline_moves == failure_index:
                raise OSError("injected baseline preservation failure")
            baseline_moves += 1
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError, match="baseline preservation"):
        publish_repository_surface_candidate(transaction)

    assert all(
        (data_root / path).read_bytes() == content for path, content in baseline.items()
    )
    assert all(
        (transaction.candidate_data_root / path).read_bytes() == content
        for path, content in candidate.items()
    )
    assert not transaction.lock_path.exists()


def test_repository_surface_candidate_refuses_partial_or_extra_population(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    transaction = prepare_repository_surface_transaction(
        data_root, artifacts_root=tmp_path / "artifacts"
    )
    _write_population(transaction.candidate_data_root, prefix="new")
    (transaction.candidate_data_root / SEAD_REPOSITORY_SURFACE_PATHS[0]).unlink()
    extra = transaction.candidate_data_root / "sead" / "review" / "extra.json"
    extra.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="inventory differs"):
        validate_repository_surface_candidate(transaction)


def test_repository_surface_baseline_refuses_partial_population(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    path = data_root / SEAD_REPOSITORY_SURFACE_PATHS[0]
    path.parent.mkdir(parents=True)
    path.write_text("partial\n", encoding="utf-8")

    with pytest.raises(ValueError, match="baseline is partial"):
        prepare_repository_surface_transaction(
            data_root, artifacts_root=tmp_path / "artifacts"
        )


def test_cross_format_validation_requires_direct_uuid_reconciliation(
    tmp_path: Path,
) -> None:
    site_uuid = "16fd2706-8baf-433b-82eb-8c7fada847da"
    root = tmp_path / "candidate" / "data" / "sead"
    normalized = root / "normalized"
    derived = root / "derived"
    review = root / "review"
    for directory in (normalized, derived, review):
        directory.mkdir(parents=True)
    for stem in ("nordic_environmental_sites", "nordic_temporal_evidence"):
        (normalized / f"{stem}.csv").write_text(
            f"record_id,site_uuid\n1,{site_uuid}\n", encoding="utf-8"
        )
        (normalized / f"{stem}.geojson").write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": None,
                            "properties": {
                                "record_id": "1",
                                "site_uuid": site_uuid,
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
    for stem in (
        "access_model",
        "evidence_legibility_review",
        "recovery_requirements",
        "temporal_review",
    ):
        (review / f"{stem}.csv").write_text("record_id\n", encoding="utf-8")
        (review / f"{stem}.json").write_text(
            json.dumps({"row_count": 0}), encoding="utf-8"
        )
    (derived / "sweden_archaeology_site_discovery.csv").write_text(
        f"site_id,site_uuid\n1,{site_uuid}\n", encoding="utf-8"
    )
    (derived / "sweden_archaeology_site_discovery.json").write_text(
        json.dumps(
            {
                "summary": {"site_count": 1, "map_feature_count": 1},
                "sites": [{"site_id": "1", "site_uuid": site_uuid}],
            }
        ),
        encoding="utf-8",
    )
    discovery_geojson = derived / "sweden_archaeology_site_discovery.geojson"
    discovery_geojson.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": None,
                        "properties": {
                            "record_id": "1:unresolved:discovery",
                            "site_uuid": site_uuid,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (review / "scientific_classification_candidates.csv").write_text(
        "candidate_id\n", encoding="utf-8"
    )
    (review / "scientific_classification_review.json").write_text(
        json.dumps({"candidates": []}), encoding="utf-8"
    )
    candidate = RepositorySurfaceCandidate(
        data_root=root.parent,
        transaction_root=tmp_path / "transaction",
        candidate_data_root=root.parent,
        recovery_root=tmp_path / "recovery",
        lock_path=tmp_path / "lock",
        baseline=(),
    )

    surface_validation.validate_cross_format_counts(candidate)

    value = json.loads(discovery_geojson.read_text(encoding="utf-8"))
    value["features"][0]["properties"]["site_uuid"] = (
        "6c39f57c-31a9-4a44-b8b7-c5b2798045dc"
    )
    discovery_geojson.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="feature UUID differs"):
        surface_validation.validate_cross_format_counts(candidate)

    value["features"][0]["properties"]["site_uuid"] = "uuid-1"
    discovery_geojson.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="not a UUID"):
        surface_validation.validate_cross_format_counts(candidate)
