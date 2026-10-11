"""Preserve qualified input identity and atomic site-taxon-support publication."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import (
    SCHEMA as AUTHOR_SCHEMA,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.essd_reproduction.author_taxon_support import (
    CROSSWALK,
    FORMAT_SCRIPT,
    GRIDS,
    PARAMETERS,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import (
    LOOKUP,
)
from bijux_pollenomics_dev.source_completion.pollen_taxonomy import (
    author_site_support as account,
)


@pytest.fixture
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    descriptor = repository / account.DESCRIPTOR
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text(
        json.dumps({"schema_version": AUTHOR_SCHEMA, "source_id": account.SOURCE_ID}),
        encoding="utf-8",
    )
    root = tmp_path / "store"
    directory = root / account.SOURCE_ID
    rows = [
        {
            "grid_id": grid,
            "site_id": f"SOURCE{grid}{index}",
            "prepared_target_row_count": 31,
            "all_targets_measured_admitted": False,
        }
        for grid, count in GRIDS.items()
        for index in range(count)
    ]
    sources = [LOOKUP, PARAMETERS, CROSSWALK, FORMAT_SCRIPT]
    sources.extend(
        Path(f"author/run.REVEALS.files/site.list.{grid}.csv") for grid in GRIDS
    )
    for row in rows:
        sources.extend(
            (
                Path(f"author/input/{row['site_id']}.csv"),
                Path(f"author/run.REVEALS.files/LRAready_{row['site_id']}.csv"),
            )
        )
    inputs = {account.DESCRIPTOR.as_posix(): descriptor}
    declared = []
    for relative in sources:
        path = directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"qualified fixture source\n")
        inputs[f"external/{account.SOURCE_ID}/{relative.as_posix()}"] = path
        declared.append(
            {
                "source_root_role": "external_landclim_author_reference",
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    qualified = QualifiedReportSources(
        directory, inputs, hashlib.sha256(descriptor.read_bytes()).hexdigest()
    )
    report = {
        "schema_version": "landclim-author-example-taxon-support.v1",
        "site_count": 17,
        "author_target_count": 31,
        "grid_site_counts": GRIDS,
        "all_targets_measured_admitted": False,
        "reviewed_reveals_profile_admitted": False,
        "rows": rows,
        "inputs": declared,
    }
    calls: list[tuple[str, Path]] = []

    def qualify(
        repo: Path, source_root: Path, source_descriptor: Path
    ) -> QualifiedReportSources:
        assert (
            repo == repository
            and source_root == root
            and source_descriptor == account.DESCRIPTOR
        )
        calls.append(("qualify", source_root))
        return qualified

    def publish(source_directory: Path, output: Path) -> dict[str, Any]:
        assert source_directory == directory
        calls.append(("produce", output))
        return report

    monkeypatch.setattr(account, "validated_external_report_sources", qualify)
    monkeypatch.setattr(account, "publish", publish)
    return {
        "repository": repository,
        "root": root,
        "qualified": qualified,
        "report": report,
        "calls": calls,
        "publish": publish,
        "qualify": qualify,
        "output": repository / "artifacts/result",
    }


def _run(packet: dict[str, Any]) -> dict[str, Any]:
    return account.run(
        packet["repository"], packet["root"], account.DESCRIPTOR, packet["output"]
    )


def _no_publication(packet: dict[str, Any]) -> None:
    assert not packet["output"].exists()
    assert list((packet["repository"] / "artifacts").iterdir()) == []


def test_qualified_account_publishes_atomically_without_copying_source(
    packet: dict[str, Any],
) -> None:
    inputs = packet["qualified"].inputs
    before = {name: path.read_bytes() for name, path in inputs.items()}
    assert _run(packet) == packet["report"]
    assert [name for name, _ in packet["calls"]] == ["qualify", "produce", "qualify"]
    assert {path.name for path in packet["output"].iterdir()} == {
        "report.json",
    }
    assert {name: path.read_bytes() for name, path in inputs.items()} == before
    assert (
        json.loads((packet["output"] / "report.json").read_bytes()) == packet["report"]
    )


@pytest.mark.parametrize(
    "placement", ["existing", "escape", "symlink-leaf", "symlink-ancestor", "traversal"]
)
def test_invalid_output_refuses_before_source_consumption(
    packet: dict[str, Any], placement: str
) -> None:
    output = packet["output"]
    if placement == "existing":
        output.mkdir()
        (output / "user.txt").write_bytes(b"preserve")
    elif placement == "escape":
        packet["output"] = packet["repository"].parent / "escaped"
    elif placement == "symlink-leaf":
        output.symlink_to(packet["root"], target_is_directory=True)
    elif placement == "symlink-ancestor":
        ancestor = output.parent / "linked"
        ancestor.symlink_to(packet["root"], target_is_directory=True)
        packet["output"] = ancestor / "result"
    else:
        packet["output"] = output.parent / ".." / "artifacts" / "result"
    with pytest.raises(ReportRebuildError):
        _run(packet)
    assert packet["calls"] == []
    if placement == "existing":
        assert (output / "user.txt").read_bytes() == b"preserve"


@pytest.mark.parametrize(
    "mutation", ["schema", "source-id", "missing-descriptor", "missing-source"]
)
def test_wrong_qualified_contract_refuses_before_producer(
    packet: dict[str, Any], mutation: str
) -> None:
    qualified = packet["qualified"]
    descriptor = qualified.inputs[account.DESCRIPTOR.as_posix()]
    if mutation in {"schema", "source-id"}:
        payload = json.loads(descriptor.read_bytes())
        payload["schema_version" if mutation == "schema" else "source_id"] = "wrong"
        descriptor.write_text(json.dumps(payload), encoding="utf-8")
    else:
        name = (
            account.DESCRIPTOR.as_posix()
            if mutation == "missing-descriptor"
            else next(name for name in qualified.inputs if name.startswith("external/"))
        )
        qualified.inputs.pop(name)
    with pytest.raises(
        ReportRebuildError, match="missing|contract differs|coverage differs"
    ):
        _run(packet)
    assert [name for name, _ in packet["calls"]] == ["qualify"]
    _no_publication(packet)


def test_failed_source_qualification_never_executes_producer(
    packet: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_args: object) -> QualifiedReportSources:
        raise ReportRebuildError("source bytes differ")

    monkeypatch.setattr(account, "validated_external_report_sources", refuse)
    with pytest.raises(ReportRebuildError, match="source bytes differ"):
        _run(packet)
    assert packet["calls"] == []
    _no_publication(packet)


@pytest.mark.parametrize("target", ["external-source", "descriptor"])
def test_changed_input_during_production_refuses_and_removes_stage(
    packet: dict[str, Any], monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    original = cast(Callable[[Path, Path], dict[str, Any]], packet["publish"])
    qualified = packet["qualified"]
    path = (
        next(
            path
            for name, path in qualified.inputs.items()
            if name.startswith("external/")
        )
        if target == "external-source"
        else packet["repository"] / account.DESCRIPTOR
    )

    def mutate(directory: Path, output: Path) -> dict[str, Any]:
        report = original(directory, output)
        with path.open("ab") as stream:
            stream.write(b" ")
        return report

    monkeypatch.setattr(account, "publish", mutate)
    with pytest.raises(ReportRebuildError, match="inputs changed"):
        _run(packet)
    _no_publication(packet)


def test_changed_qualified_declaration_refuses_before_publish(
    packet: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0
    qualified = cast(QualifiedReportSources, packet["qualified"])

    def changed(*_args: object) -> QualifiedReportSources:
        nonlocal calls
        calls += 1
        return (
            qualified if calls == 1 else replace(qualified, descriptor_sha256="0" * 64)
        )

    monkeypatch.setattr(account, "validated_external_report_sources", changed)
    with pytest.raises(ReportRebuildError, match="inputs changed"):
        _run(packet)
    _no_publication(packet)


@pytest.mark.parametrize(
    "mutation",
    [
        "exception",
        "extra-output",
        "altered-output",
        "admitted-report",
        "output-appears",
    ],
)
def test_producer_failure_never_publishes_or_overwrites(
    packet: dict[str, Any], monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    original = cast(Callable[[Path, Path], dict[str, Any]], packet["publish"])

    def mutate(directory: Path, output: Path) -> dict[str, Any]:
        report = original(directory, output)
        if mutation == "exception":
            raise ValueError("producer refused")
        if mutation == "extra-output":
            (output / "extra.json").write_text("{}", encoding="utf-8")
        elif mutation == "altered-output":
            (output / "report.json").write_text("{}", encoding="utf-8")
        elif mutation == "admitted-report":
            report = {**report, "reviewed_reveals_profile_admitted": True}
        else:
            packet["output"].mkdir()
            (packet["output"] / "user.txt").write_bytes(b"preserve")
        return report

    monkeypatch.setattr(account, "publish", mutate)
    with pytest.raises((ValueError, ReportRebuildError)):
        _run(packet)
    if mutation == "output-appears":
        assert (packet["output"] / "user.txt").read_bytes() == b"preserve"
        assert {path.name for path in packet["output"].parent.iterdir()} == {"result"}
    else:
        _no_publication(packet)


@pytest.mark.parametrize(
    "mutation",
    [
        "size",
        "digest",
        "missing",
        "duplicate",
        "role",
        "traversal",
        "unqualified",
        "extra-field",
    ],
)
def test_unbound_producer_source_account_refuses(
    packet: dict[str, Any], monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    original = cast(Callable[[Path, Path], dict[str, Any]], packet["publish"])

    def mutate(directory: Path, output: Path) -> dict[str, Any]:
        report = deepcopy(original(directory, output))
        entry = report["inputs"][0]
        if mutation == "size":
            entry["bytes"] = True
        elif mutation == "digest":
            entry["sha256"] = "0" * 64
        elif mutation == "missing":
            report["inputs"].pop()
        elif mutation == "duplicate":
            report["inputs"][-1] = entry
        elif mutation == "role":
            entry["source_root_role"] = "wrong"
        elif mutation == "traversal":
            entry["path"] = "../outside.csv"
        elif mutation == "unqualified":
            entry["path"] = "author/input/unqualified.csv"
        else:
            entry["license"] = "invented"
        return report

    monkeypatch.setattr(account, "publish", mutate)
    with pytest.raises(ReportRebuildError):
        _run(packet)
    _no_publication(packet)


@pytest.mark.parametrize(
    "mutation",
    [
        "measured-admission",
        "profile-admission",
        "site-admission",
        "grid-counts",
        "site-grid",
        "duplicate-site",
        "target-count",
        "missing-site",
    ],
)
def test_changed_support_scope_refuses(
    packet: dict[str, Any], monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    original = cast(Callable[[Path, Path], dict[str, Any]], packet["publish"])

    def mutate(directory: Path, output: Path) -> dict[str, Any]:
        report = deepcopy(original(directory, output))
        row = report["rows"][0]
        if mutation == "measured-admission":
            report["all_targets_measured_admitted"] = True
        elif mutation == "profile-admission":
            report["reviewed_reveals_profile_admitted"] = True
        elif mutation == "site-admission":
            row["all_targets_measured_admitted"] = True
        elif mutation == "grid-counts":
            report["grid_site_counts"] = {"512": 8, "562": 9}
        elif mutation == "site-grid":
            row["grid_id"] = "562"
        elif mutation == "duplicate-site":
            report["rows"][-1]["site_id"] = row["site_id"]
        elif mutation == "target-count":
            row["prepared_target_row_count"] = 30
        else:
            report["rows"].pop()
        return report

    monkeypatch.setattr(account, "publish", mutate)
    with pytest.raises(ReportRebuildError):
        _run(packet)
    _no_publication(packet)
