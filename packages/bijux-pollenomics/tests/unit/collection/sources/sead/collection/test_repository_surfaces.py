from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces import (
    SEAD_REPOSITORY_SURFACE_PATHS,
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
