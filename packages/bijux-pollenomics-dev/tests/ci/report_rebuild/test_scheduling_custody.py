"""Keep scheduling validation reuse confined to its inputs and lifetime."""

from __future__ import annotations

from collections.abc import Callable
import contextvars
import json
import os
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner, scheduling
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)

MODULE = "bijux_pollenomics_dev.source_completion.example"
PRODUCER = "packages/bijux-pollenomics-dev/src/" + MODULE.replace(".", "/") + ".py"
DATA = "data/input.json"
INVENTORY = "configs/ci/report-ownership.json"
CONFIGURATION = "configs/ci/report-owner-execution.json"
DESCRIPTOR = "configs/ci/qualified-report-sources/example.json"


def _write(root: Path, name: str, content: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _modify(root: Path, name: str, change: Callable[[dict[str, Any]], None]) -> None:
    path = root / name
    value = json.loads(path.read_bytes())
    change(value)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repository"
    _write(root, PRODUCER, "# synthetic configured producer\n")
    _write(root, DATA, "{}\n")
    inventory, configuration = [], []
    for key in ("a", "b"):
        output = "docs/report/domain/" + key + ".json"
        _write(root, output, "{}\n")
        inventory.append(
            {
                "owner_id": "domain/" + key,
                "role": "generated_owner",
                "paths": [output],
                "producer_paths": [PRODUCER],
                "producer_inputs": [DATA],
            }
        )
        configuration.append(
            {
                "owner_id": "domain/" + key,
                "module": MODULE,
                "source_paths": {key + ".json": output},
                "source_arguments": [],
                "output_mode": "single_file",
                "timeout_seconds": 30,
            }
        )
    _write(root, INVENTORY, json.dumps({"owners": inventory}))
    _write(
        root,
        CONFIGURATION,
        json.dumps(
            {"schema_version": configured_owner.SCHEMA, "owners": configuration}
        ),
    )
    monkeypatch.setattr(configured_owner, "check_report_ownership", lambda *_args: None)
    return root


def test_schedule_validates_inventory_once_and_preserves_public_callbacks(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checks: list[Path] = []
    callbacks: list[str] = []
    copied: list[contextvars.Context] = []
    original = configured_owner.resolve_configured_owner

    def observe(
        root: Path, owner: str, **kwargs: Any
    ) -> configured_owner.ConfiguredOwner:
        callbacks.append(owner)
        copied.append(contextvars.copy_context())
        return original(root, owner, **kwargs)

    monkeypatch.setattr(
        configured_owner,
        "check_report_ownership",
        lambda root, _inventory: checks.append(root),
    )
    monkeypatch.setattr(scheduling, "resolve_configured_owner", observe)
    report = scheduling.configured_owner_schedule(repository)
    assert report["owner_ids"] == "domain/a domain/b"
    assert callbacks == ["domain/a", "domain/b"]
    assert checks == [repository]
    copied[0].run(original, repository, "domain/a")
    assert checks == [repository, repository]
    original(repository, "domain/b")
    assert checks == [repository] * 3


def test_active_schedule_does_not_validate_another_repository(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = repository.parent / "other-repository"
    shutil.copytree(repository, other)
    checks: list[Path] = []
    original = configured_owner.resolve_configured_owner

    def observe(root: Path, owner: str) -> configured_owner.ConfiguredOwner:
        value = original(root, owner)
        original(other, owner)
        return value

    monkeypatch.setattr(
        configured_owner,
        "check_report_ownership",
        lambda root, _inventory: checks.append(root),
    )
    monkeypatch.setattr(scheduling, "resolve_configured_owner", observe)
    scheduling.configured_owner_schedule(repository)
    assert checks == [repository, other, other]


@pytest.mark.parametrize(
    "name", [INVENTORY, CONFIGURATION, DATA, PRODUCER, "docs/report/domain/a.json"]
)
def test_schedule_refuses_changed_controls_and_declared_sources(
    repository: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    original = configured_owner.resolve_configured_owner

    def changed(root: Path, owner: str) -> configured_owner.ConfiguredOwner:
        value = original(root, owner)
        path = root / name
        path.write_bytes(path.read_bytes() + b"\n")
        return value

    monkeypatch.setattr(scheduling, "resolve_configured_owner", changed)
    with pytest.raises(ReportRebuildError, match="changed during scheduling"):
        scheduling.configured_owner_schedule(repository)
    # An unsuccessful schedule must not leave cached validation behind.
    checks: list[Path] = []
    monkeypatch.setattr(
        configured_owner,
        "check_report_ownership",
        lambda root, _inventory: checks.append(root),
    )
    configured_owner.resolve_configured_owner(repository, "domain/b")
    assert checks == [repository]


def test_schedule_refuses_replaced_source_ancestor(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = configured_owner.resolve_configured_owner
    replaced: list[Path] = []

    def changed(root: Path, owner: str) -> configured_owner.ConfiguredOwner:
        value = original(root, owner)
        if not replaced:
            parent = (root / PRODUCER).parent
            moved = root / "moved-producer"
            parent.rename(moved)
            parent.symlink_to(moved)
            replaced.append(parent)
        return value

    monkeypatch.setattr(scheduling, "resolve_configured_owner", changed)
    with pytest.raises(ReportRebuildError, match="non-real ancestor"):
        scheduling.configured_owner_schedule(repository)


def _external(repository: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    _write(repository, DESCRIPTOR, "{}\n")

    def declare(value: dict[str, Any]) -> None:
        for row in value["owners"]:
            row["producer_inputs"].append(DESCRIPTOR)

    _modify(repository, INVENTORY, declare)

    def configure(value: dict[str, Any]) -> None:
        for row in value["owners"]:
            row.update(external_source_descriptor=DESCRIPTOR)

    _modify(repository, CONFIGURATION, configure)
    root = repository.parent / "qualified-synthetic-source"
    _write(root, "input.json", "{}\n")
    leaf = root / "input.json"
    monkeypatch.setattr(
        configured_owner,
        "validated_external_report_sources",
        lambda *_args: QualifiedReportSources(
            root,
            {DESCRIPTOR: repository / DESCRIPTOR, "external/example/input.json": leaf},
            "a" * 64,
        ),
    )
    return root, leaf


def test_external_source_still_requires_ordinary_qualification(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _external(repository, monkeypatch)
    with pytest.raises(ReportRebuildError, match="requires --source-root"):
        scheduling.configured_owner_schedule(repository)

    def refused(*_args: object) -> QualifiedReportSources:
        raise ReportRebuildError("synthetic qualification refused")

    monkeypatch.setattr(configured_owner, "validated_external_report_sources", refused)
    with pytest.raises(ReportRebuildError, match="synthetic qualification refused"):
        scheduling.configured_owner_schedule(repository, source_root=root)


def test_schedule_allows_repeated_identical_external_bytes(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, leaf = _external(repository, monkeypatch)
    original = configured_owner.resolve_configured_owner
    callbacks: list[str] = []

    def unchanged(
        repository: Path, owner: str, **kwargs: Any
    ) -> configured_owner.ConfiguredOwner:
        value = original(repository, owner, **kwargs)
        leaf.write_bytes(leaf.read_bytes())
        callbacks.append(owner)
        return value

    monkeypatch.setattr(scheduling, "resolve_configured_owner", unchanged)
    scheduling.configured_owner_schedule(repository, source_root=root)
    assert callbacks == ["domain/a", "domain/b"]


def test_schedule_refuses_external_bytes_with_same_size_and_restored_mtime(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, leaf = _external(repository, monkeypatch)
    original = configured_owner.resolve_configured_owner

    def changed(
        repository: Path, owner: str, **kwargs: Any
    ) -> configured_owner.ConfiguredOwner:
        value = original(repository, owner, **kwargs)
        info = leaf.stat()
        leaf.write_text("[]\n", encoding="utf-8")
        os.utime(leaf, ns=(info.st_atime_ns, info.st_mtime_ns))
        return value

    monkeypatch.setattr(scheduling, "resolve_configured_owner", changed)
    with pytest.raises(ReportRebuildError, match="external input changed"):
        scheduling.configured_owner_schedule(repository, source_root=root)


def test_schedule_does_not_suppress_ordinary_ownership_refusal(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refused(*_args: object) -> None:
        raise ReportOwnershipError("synthetic ownership refused")

    monkeypatch.setattr(configured_owner, "check_report_ownership", refused)
    with pytest.raises(ReportRebuildError, match="ownership is invalid"):
        scheduling.configured_owner_schedule(repository)
