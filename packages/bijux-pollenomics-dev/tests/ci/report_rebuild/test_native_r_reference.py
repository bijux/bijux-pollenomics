"""Admit native raw evidence independently from generated comparison records."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.r_reference import native, selection
from bijux_pollenomics_dev.lra_validation.native_reference.capture import (
    REPORT_PREFIX,
    NativeCapture,
)
from bijux_pollenomics_dev.lra_validation.reference_replay import CERTIFICATE_SHA256


@pytest.fixture
def report_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, NativeCapture]:
    root = tmp_path / "repository"
    directory = root / REPORT_PREFIX
    directory.mkdir(parents=True)
    digests = {}
    for index in range(129):
        name = f"oracle/C{index:04d}.csv"
        path = directory / name
        path.parent.mkdir(exist_ok=True)
        payload = f"value\n{index}\n".encode()
        path.write_bytes(payload)
        digests[name] = hashlib.sha256(payload).hexdigest()
    for name in native._MAINTAINED_SOURCE_MEMBERS:
        path = directory / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("maintained code, separate owner")
    for name in ("report.json", "source-replay.json"):
        (directory / name).write_text(
            "deliberately invalid owned output; must not consume"
        )
    accepted = NativeCapture(
        root / "source",
        root / "archives",
        "a" * 40,
        "b" * 64,
        tuple(sorted(digests)),
        digests,
        {},
    )
    monkeypatch.setattr(native, "validated_native_capture", lambda _: accepted)
    return root, accepted


def _policy() -> dict[str, Any]:
    return {
        "tracked_report_root": "docs/report",
        "volatile_text_rules": [],
        "allowed_input_symlinks": {},
        "excluded_input_globs": [],
    }


def test_admission_reads_raw129_and_excludes_owned2(
    report_source: tuple[Path, NativeCapture],
) -> None:
    root, _ = report_source
    inventory = native.validated_native_r_reference(root, _policy())
    assert len(inventory) == 129
    assert all(
        entry.path.startswith("method-certification/current-r-oracle/oracle/")
        for entry in inventory
    )
    assert not any(
        entry.path.endswith(("report.json", "source-replay.json"))
        for entry in inventory
    )


@pytest.mark.parametrize(
    "operation", ["missing", "extra", "mutated", "symlink", "hardlink"]
)
def test_retained_report_refuses_unqualified_members(
    report_source: tuple[Path, NativeCapture], operation: str
) -> None:
    import os

    root, _ = report_source
    path = root / REPORT_PREFIX / "oracle/C0000.csv"
    if operation == "missing":
        path.unlink()
    elif operation == "extra":
        path.with_name("unrelated.csv").write_bytes(b"extra")
    elif operation == "mutated":
        path.write_bytes(b"changed")
    elif operation == "symlink":
        path.unlink()
        path.symlink_to(path.with_name("C0001.csv"))
    else:
        os.link(path, root / "other.csv")
    with pytest.raises(ReportRebuildError):
        native.validated_native_r_reference(root, _policy())


def test_final_capture_mutation_refuses(
    report_source: tuple[Path, NativeCapture], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, before = report_source
    calls = 0

    def changed(_: Path) -> NativeCapture:
        nonlocal calls
        calls += 1
        return (
            before
            if calls == 1
            else NativeCapture(
                before.directory,
                before.source_archives,
                "c" * 40,
                before.manifest_sha256,
                before.report_source_members,
                before.raw_sha256,
                before.input_sha256,
            )
        )

    monkeypatch.setattr(native, "validated_native_capture", changed)
    with pytest.raises(ReportRebuildError, match="changed during"):
        native.validated_native_r_reference(root, _policy())


def test_disabled_source_selection_never_reads_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_: object) -> None:
        raise AssertionError("disabled source must not read")

    monkeypatch.setattr(selection, "validated_native_r_reference", refuse)
    monkeypatch.setattr(selection, "validated_original_r_reference", refuse)
    result = selection.validated_r_references(
        tmp_path, _policy(), original=False, native=False
    )
    assert result.inventory == ()
    assert result.evidence == result.retained_evidence == {}


def test_source_family_identity_and_overlap_refusal(
    report_source: tuple[Path, NativeCapture], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = report_source
    accepted = selection.validated_r_references(
        root, _policy(), original=False, native=True
    )
    assert set(accepted.evidence) == {"native_r_reference"}
    assert (
        len(cast(Any, accepted.retained_evidence["native_r_reference"])["paths"]) == 129
    )
    monkeypatch.setattr(
        selection, "validated_original_r_reference", lambda *_: accepted.inventory
    )
    with pytest.raises(ReportRebuildError, match="overlap"):
        selection.validated_r_references(root, _policy(), original=True, native=True)


def test_original_retained_receipt_contract_is_preserved(
    report_source: tuple[Path, NativeCapture], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = report_source
    entries = native.validated_native_r_reference(root, _policy())[:1]
    monkeypatch.setattr(selection, "validated_original_r_reference", lambda *_: entries)
    selected = selection.validated_r_references(
        root, _policy(), original=True, native=False
    )
    assert selected.retained_evidence == {
        "original_r_reference": {
            "certificate_sha256": CERTIFICATE_SHA256,
            "paths": [entry.path for entry in entries],
        }
    }
    assert len(cast(Any, selected.evidence["original_r_reference"])["inventory"]) == 1
