"""Exercise source-bound publication without interpreting real scientific inputs."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics.core import owned_tree
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts import (
    pangaea_abbo_profile as profile_contract,
)
from bijux_pollenomics_dev.source_completion import (
    abbo_profile_lineage as profile_retained,
)
from bijux_pollenomics_dev.source_completion.neotoma import abbo_profile
from bijux_pollenomics_dev.source_completion.neotoma import (
    native_correspondence as native,
)
from bijux_pollenomics_dev.source_completion.neotoma import (
    source_bound_reports as custody,
)


@pytest.fixture
def inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, QualifiedReportSources]:
    """Provide inputs for the retained source contract."""
    repository, store = tmp_path / "repository", tmp_path / "store"
    (repository / "artifacts").mkdir(parents=True)
    store.mkdir()
    supplied = store / "source"
    supplied.write_bytes(b"explicit synthetic source")
    descriptor = Path("configs/source.json")
    (repository / descriptor).parent.mkdir(parents=True)
    (repository / descriptor).write_text("{}")
    qualified = QualifiedReportSources(
        store,
        {descriptor.as_posix(): repository / descriptor, "external/source": supplied},
        "a" * 64,
    )
    monkeypatch.setattr(
        custody, "validated_external_report_sources", lambda *_: qualified
    )
    return repository, store, descriptor, qualified


def publish(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
    mutation: str = "",
    retained_artifacts_root: Path | None = None,
) -> dict[str, Any]:
    """Provide publish for the retained source contract."""
    repository, store, descriptor, qualified = inputs

    def producer(_: QualifiedReportSources, raw: Path) -> None:
        raw.mkdir()
        (raw / "report.json").write_text('{"scope":"synthetic"}\n')
        (raw / "cells.csv").write_bytes(b"synthetic sidecar\n")
        if mutation == "input":
            qualified.inputs["external/source"].write_bytes(b"changed")
        elif mutation == "alias":
            source = qualified.inputs["external/source"]
            replacement = source.parent / "replacement"
            source.rename(replacement)
            source.symlink_to(replacement)
        elif mutation == "extra":
            (raw / "unexpected").write_bytes(b"extra")

    return custody.publish(
        repository,
        store,
        descriptor,
        repository / "artifacts/output",
        (),
        lambda _: None,
        producer,
        frozenset({"report.json", "cells.csv"}),
        lambda _: None,
        retained_artifacts_root=retained_artifacts_root,
    )


def test_raw_sidecars_are_retained_and_only_fresh_report_is_mapped(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
) -> None:
    """Verify raw sidecars are retained and only fresh report is mapped."""
    repository, _, _, _ = inputs
    assert publish(inputs) == {"scope": "synthetic"}
    assert {p.name for p in (repository / "artifacts/output").iterdir()} == {
        "report.json"
    }
    retained = list((repository / "artifacts").glob(".output-retained-*"))
    assert len(retained) == 1
    assert (
        retained[0] / "source-products/cells.csv"
    ).read_bytes() == b"synthetic sidecar\n"
    assert (retained[0] / "source-products/report.json").read_bytes() == (
        repository / "artifacts/output/report.json"
    ).read_bytes()
    assert json.loads((retained[0] / "source-custody.json").read_bytes())["inputs"][
        "external/source"
    ]["sha256"]


@pytest.mark.parametrize("mutation", ["input", "alias", "extra"])
def test_mutated_source_and_unexpected_members_never_publish(
    inputs: tuple[Path, Path, Path, QualifiedReportSources], mutation: str
) -> None:
    """Verify mutated source and unexpected members never publish."""
    with pytest.raises(ReportRebuildError):
        publish(inputs, mutation)
    assert not (inputs[0] / "artifacts/output").exists()


def test_input_hardlink_and_existing_output_refuse(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
) -> None:
    """Verify input hardlink and existing output refuse."""
    repository, _, _, qualified = inputs
    source = qualified.inputs["external/source"]
    link = source.parent / "link"
    os.link(source, link)
    with pytest.raises(ReportRebuildError, match="physical alias"):
        publish(inputs)
    link.unlink()
    (repository / "artifacts/output").mkdir()
    with pytest.raises(ReportRebuildError, match="absent"):
        publish(inputs)


@pytest.mark.parametrize("descriptor", list(native.CASES))
def test_native_cli_preserves_exact_arguments_return_argv_and_report_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, descriptor: Path
) -> None:
    """Verify native cli preserves exact arguments return argv and report bytes."""
    case = native.CASES[descriptor]
    repository, store = tmp_path / "repository", tmp_path / "store"
    (repository / "artifacts").mkdir(parents=True)
    (repository / case.raw).parent.mkdir(parents=True)
    (repository / case.raw).write_bytes(b"synthetic native source")
    directory = store / native.SOURCE_ID
    directory.mkdir(parents=True)
    labels = {
        native.BASE_DESCRIPTOR.as_posix(): repository / native.BASE_DESCRIPTOR,
        f"external/{native.SOURCE_ID}/manifest.json": directory / "manifest.json",
        f"external/{native.SOURCE_ID}/rootsi/BOKE.xls": directory / "rootsi/BOKE.xls",
    }
    if descriptor != native.BASE_DESCRIPTOR:
        labels.update(
            {
                descriptor.as_posix(): repository / descriptor,
                f"external/{native.SOURCE_ID}/{case.workbook}": directory
                / case.workbook,
            }
        )
    for path in labels.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic qualified input")
    qualified = QualifiedReportSources(directory, labels, "a" * 64)
    monkeypatch.setattr(
        custody, "validated_external_report_sources", lambda *_: qualified
    )
    expected = {
        "schema_version": case.schema,
        "neotoma_dataset_id": case.dataset,
        "neotoma_site_id": case.site,
        "rootsi_archive_member": case.workbook,
        "lra_admitted_samples": 0,
        "input_sha256": {
            "neotoma_raw_part": hashlib.sha256(
                (repository / case.raw).read_bytes()
            ).hexdigest(),
            "rootsi_workbook": hashlib.sha256(
                (directory / case.workbook).read_bytes()
            ).hexdigest(),
        },
        "basin_radius_transfer": "refused",
        "scientific_detail": "unchanged",
    }
    wire = json.dumps(expected, indent=2, ensure_ascii=False).encode() + b"\n"
    original_argv = sys.argv

    def retained_main() -> int:
        assert sys.argv[1:5] == [
            "--workbook",
            str(directory / case.workbook),
            "--raw-part",
            str(repository / case.raw),
        ]
        raw = Path(sys.argv[-1])
        raw.mkdir()
        (raw / "report.json").write_bytes(wire)
        (raw / case.csv).write_bytes(b"synthetic cells")
        (raw / "REPORT.md").write_bytes(b"synthetic report")
        return 0

    monkeypatch.setitem(native.CASES, descriptor, replace(case, main=retained_main))
    result = native.run(repository, store, descriptor, repository / "artifacts/output")
    assert result == expected
    assert sys.argv is original_argv
    assert (repository / "artifacts/output/report.json").read_bytes() == wire


def test_unknown_native_and_profile_descriptors_refuse(tmp_path: Path) -> None:
    """Verify unknown native and profile descriptors refuse."""
    with pytest.raises(ReportRebuildError, match="maintained case"):
        native.run(tmp_path, tmp_path, Path("unknown.json"), tmp_path)
    with pytest.raises(ReportRebuildError, match="maintained source"):
        abbo_profile.run(tmp_path, tmp_path, Path("unknown.json"), tmp_path)


def test_profile_adapter_uses_four_declared_sequence_inputs_and_unchanged_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify profile adapter uses four declared sequence inputs and unchanged build."""
    repository, store = tmp_path / "repository", tmp_path / "store"
    (repository / "artifacts").mkdir(parents=True)
    for path in (*abbo_profile.INPUTS, abbo_profile.DESCRIPTOR):
        (repository / path).parent.mkdir(parents=True, exist_ok=True)
        (repository / path).write_bytes(b"synthetic sequence input")
    table = store / profile_contract.SOURCE_ID / profile_contract.TABLE
    table.parent.mkdir(parents=True)
    table.write_bytes(b"synthetic source profile")
    qualified = QualifiedReportSources(
        table.parent,
        {
            abbo_profile.DESCRIPTOR.as_posix(): repository / abbo_profile.DESCRIPTOR,
            f"external/{profile_contract.SOURCE_ID}/{profile_contract.TABLE}": table,
        },
        "a" * 64,
    )
    monkeypatch.setattr(
        custody, "validated_external_report_sources", lambda *_: qualified
    )
    expected = {
        "schema_version": "neotoma-abbo-pangaea-lineage.v1",
        "dataset_id": "19913",
        "site_id": "13338",
        "historical_basin_geometry_admitted": False,
        "lra_input_admitted": False,
        "source_profile_doi": profile_contract.DOI,
        "source_profile_url": "https://doi.pangaea.de/" + profile_contract.DOI,
        "source_profile_license": "CC-BY-NC-3.0",
        "source_profile_sha256": hashlib.sha256(table.read_bytes()).hexdigest(),
        "governed_sequence_manifest_sha256": hashlib.sha256(
            (repository / abbo_profile.SEQUENCE / "manifest.json").read_bytes()
        ).hexdigest(),
        "pangaea_area_temporal_support": "source_event_metadata_only",
        "source_core_handle": "ABBO",
        "source_depth_unit": "m",
        "neotoma_depth_source_unit": None,
    }

    def build(repo: Path, profile: Path, output: Path) -> dict[str, object]:
        assert repo == repository and profile == table
        output.mkdir()
        (output / "report.json").write_text(
            json.dumps(expected, indent=2, sort_keys=True) + "\n"
        )
        return expected

    monkeypatch.setattr(profile_retained, "build", build)
    assert (
        abbo_profile.run(
            repository, store, abbo_profile.DESCRIPTOR, repository / "artifacts/output"
        )
        == expected
    )


@pytest.mark.parametrize("descriptor", list(native.CASES))
@pytest.mark.parametrize(
    "field",
    ["schema_version", "neotoma_dataset_id", "neotoma_site_id", "lra_admitted_samples"],
)
def test_native_report_scope_and_boolean_counts_refuse(
    monkeypatch: pytest.MonkeyPatch, descriptor: Path, field: str
) -> None:
    """Verify native report scope and boolean counts refuse."""
    case = native.CASES[descriptor]
    report = {
        "schema_version": case.schema,
        "neotoma_dataset_id": case.dataset,
        "neotoma_site_id": case.site,
        "rootsi_archive_member": case.workbook,
        "lra_admitted_samples": 0,
    }
    report[field] = False if field != "schema_version" else "unrelated.v1"

    def publication(*args: Any) -> dict[str, Any]:
        args[-1](report)
        return report

    monkeypatch.setattr(native, "publish", publication)
    with pytest.raises(ReportRebuildError, match="report scope differs"):
        native.run(Path("repository"), Path("store"), descriptor, Path("output"))


@pytest.mark.parametrize(
    "field",
    ["schema_version", "historical_basin_geometry_admitted", "lra_input_admitted"],
)
def test_profile_scope_false_is_typed_and_never_admitted(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    """Verify profile scope false is typed and never admitted."""
    report = {
        "schema_version": "neotoma-abbo-pangaea-lineage.v1",
        "dataset_id": "19913",
        "site_id": "13338",
        "historical_basin_geometry_admitted": False,
        "lra_input_admitted": False,
    }
    report[field] = 0 if field != "schema_version" else "unrelated.v1"

    def publication(*args: Any) -> dict[str, Any]:
        args[-1](report)
        return report

    monkeypatch.setattr(abbo_profile, "publish", publication)
    with pytest.raises(ReportRebuildError, match="report scope differs"):
        abbo_profile.run(
            Path("repository"), Path("store"), abbo_profile.DESCRIPTOR, Path("output")
        )


def test_native_main_exception_restores_original_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify native main exception restores original argv."""
    descriptor = native.BASE_DESCRIPTOR
    case = native.CASES[descriptor]
    original = sys.argv

    def refuse() -> int:
        raise ValueError("synthetic retained producer refusal")

    def publication(*args: Any) -> dict[str, Any]:
        args[-3](QualifiedReportSources(Path("store"), {}, "a" * 64), Path("raw"))
        raise AssertionError("producer refusal must propagate")

    monkeypatch.setitem(native.CASES, descriptor, replace(case, main=refuse))
    monkeypatch.setattr(native, "publish", publication)
    with pytest.raises(ValueError, match="synthetic retained producer refusal"):
        native.run(Path("repository"), Path("store"), descriptor, Path("output"))
    assert sys.argv is original


@pytest.mark.parametrize("competitor", ["file", "symlink"])
def test_competing_final_report_is_never_overwritten(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
    monkeypatch: pytest.MonkeyPatch,
    competitor: str,
) -> None:
    """Verify competing final report is never overwritten."""
    repository, _, _, _ = inputs
    destination = repository / "artifacts/output"
    victim = repository / "artifacts/competitor.json"
    victim.write_bytes(b"competitor evidence")
    original = owned_tree.publish_new_output_tree
    raced = False

    def race(*, final_output_root: Path, staging_output_root: Path) -> None:
        nonlocal raced
        raced = True
        final_output_root.mkdir()
        if competitor == "symlink":
            (final_output_root / "report.json").symlink_to(victim)
        else:
            (final_output_root / "report.json").write_bytes(b"competitor evidence")
        original(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(custody, "publish_new_output_tree", race)
    with pytest.raises((ReportRebuildError, FileExistsError)):
        publish(inputs)
    assert raced
    assert victim.read_bytes() == b"competitor evidence"
    if competitor == "file":
        assert (destination / "report.json").read_bytes() == b"competitor evidence"


@pytest.mark.parametrize("boundary", ["directory_open", "file_open"])
def test_reserved_directory_replacement_refuses_without_writing_payload(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    """Verify reserved directory replacement refuses without writing payload."""
    repository, _, _, _ = inputs
    destination = repository / "artifacts/output"
    displaced = repository / "artifacts/displaced-reservation"
    original_open = os.open
    changed = False
    stage: Path | None = None

    def racing_open(
        path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        nonlocal changed, stage
        if isinstance(path, Path) and path.name.startswith(".mapped-report-"):
            stage = path
        matches = (
            path == stage
            if boundary == "directory_open"
            else path == "report.json" and dir_fd is not None
        )
        if matches and stage is not None and not changed:
            changed = True
            stage.rename(displaced)
            stage.mkdir()
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", racing_open)
    with pytest.raises(ReportRebuildError, match="directory"):
        publish(inputs)
    assert changed
    assert not destination.exists()
    assert (
        not (displaced / "report.json").exists()
        or (displaced / "report.json").read_bytes() == b""
    )
    assert any(
        (p / "source-products/report.json").is_file()
        for p in (repository / "artifacts").glob(".output-retained-*")
    )


@pytest.mark.parametrize("boundary", ["before_publication", "after_publication"])
def test_replaced_visible_destination_never_binds_competitor_inode(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    """Verify replaced visible destination never binds competitor inode."""
    repository, _, _, _ = inputs
    destination = repository / "artifacts/output"
    saved = repository / "artifacts/original-reservation"
    original = owned_tree.publish_new_output_tree
    raced = False

    def race(*, final_output_root: Path, staging_output_root: Path) -> None:
        nonlocal raced
        raced = True
        if boundary == "before_publication":
            final_output_root.mkdir()
        else:
            original(
                final_output_root=final_output_root,
                staging_output_root=staging_output_root,
            )
        final_output_root.rename(saved)
        final_output_root.mkdir()
        (final_output_root / "competitor-marker").write_bytes(b"competitor directory")
        if boundary == "before_publication":
            original(
                final_output_root=final_output_root,
                staging_output_root=staging_output_root,
            )

    monkeypatch.setattr(custody, "publish_new_output_tree", race)
    with pytest.raises((ReportRebuildError, FileExistsError)):
        publish(inputs)
    assert raced
    assert not (destination / "report.json").exists()
    assert (destination / "competitor-marker").read_bytes() == b"competitor directory"


def test_unavailable_atomic_publication_refuses_without_fallback(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify unavailable atomic publication refuses without fallback."""

    def refuse(*, final_output_root: Path, staging_output_root: Path) -> None:
        raise OSError("synthetic unavailable atomic publication")

    monkeypatch.setattr(custody, "publish_new_output_tree", refuse)
    with pytest.raises(OSError, match="unavailable atomic publication"):
        publish(inputs)
    assert not (inputs[0] / "artifacts/output").exists()
    assert any(
        (p / "source-products/report.json").is_file()
        for p in (inputs[0] / "artifacts").glob(".output-retained-*")
    )


def test_explicit_retained_artifacts_stay_outside_mapped_report_tree(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
) -> None:
    """Verify explicit retained artifacts stay outside mapped report tree."""
    repository, _, _, _ = inputs
    retained = repository / "artifacts/producer-artifacts"
    assert publish(inputs, retained_artifacts_root=retained) == {"scope": "synthetic"}
    assert {p.name for p in (repository / "artifacts/output").iterdir()} == {
        "report.json"
    }
    raw = list(retained.glob(".output-retained-*"))
    assert len(raw) == 1
    assert (raw[0] / "source-products/cells.csv").read_bytes() == b"synthetic sidecar\n"
    assert (raw[0] / "source-custody.json").is_file()


@pytest.mark.parametrize("mutation", ["input", "alias", "extra"])
def test_explicit_artifacts_keep_source_and_raw_member_refusals(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
    mutation: str,
) -> None:
    """Verify explicit artifacts keep source and raw member refusals."""
    root = inputs[0]
    with pytest.raises(ReportRebuildError):
        publish(inputs, mutation, root / "artifacts/producer-artifacts")
    assert not (root / "artifacts/output").exists()


@pytest.mark.parametrize(
    "name", ["artifacts/retained", "outside", "artifacts/output/private"]
)
def test_retained_artifact_root_refuses_existing_escaping_or_overlap(
    inputs: tuple[Path, Path, Path, QualifiedReportSources],
    name: str,
) -> None:
    """Verify retained artifact root refuses existing escaping or overlap."""
    root = inputs[0]
    selected = root / name
    if name == "artifacts/retained":
        selected.mkdir()
        (selected / "original").write_bytes(b"preserve")
    with pytest.raises(ReportRebuildError):
        publish(inputs, retained_artifacts_root=selected)
    assert not (root / "artifacts/output").exists()
    if name == "artifacts/retained":
        assert (selected / "original").read_bytes() == b"preserve"
