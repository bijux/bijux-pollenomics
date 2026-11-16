"""Evidence derivation keeps the exact bytes returned by admission validation."""

from hashlib import sha256
import io
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition import (
    admission as admission_api,
)
from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    materialize_sead_full_evidence_admission,
    service,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import derivation
from bijux_pollenomics.collection.sources.sead.evidence.source_keys.derivation import (
    _read_bound_object,
)

from .support import _acquire, _full_admission_inputs, _FullEvidencePostgrestFixture


@pytest.mark.parametrize(
    "changed_member",
    [
        "payloads/tbl_sites.json",
        "receipts/tbl_sites.json",
        "country-decisions.json",
        "admission.json",
    ],
)
def test_evidence_uses_authenticated_buffers_after_admission_handoff(
    tmp_path: Path, monkeypatch: Any, changed_member: str
) -> None:
    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    decisions, parent, expected = _full_admission_inputs(
        result.manifest_path.parent.resolve(), tmp_path
    )
    with (
        patch.object(
            service, "_load_validated_boundary_authority", return_value=object()
        ),
        patch.object(
            service, "_validate_country_accounting", return_value={"reconciles": True}
        ),
    ):
        admitted = materialize_sead_full_evidence_admission(
            result.manifest_path.parent.resolve(),
            country_decisions_path=decisions,
            parent_admission_path=parent,
            output_root=(tmp_path / "admitted").resolve(),
            expected_identity=expected,
        )
        root = admitted.output_root
        baseline = derivation.build_sead_source_native_evidence_bundle(
            root, expected_identity=expected
        )
        read_snapshot = service.read_materialized_sead_full_evidence_admission
        read_bytes = Path.read_bytes
        handed_off: list[str] = []
        late_reads: list[str] = []

        def read_and_change(*args: Any, **kwargs: Any) -> Any:
            snapshot = read_snapshot(*args, **kwargs)
            (root / changed_member).write_bytes(b'{"changed_after_validation":true}\n')
            handed_off.append(changed_member)
            return snapshot

        def observe_read(path: Path) -> bytes:
            if handed_off and path.is_relative_to(root):
                late_reads.append(path.relative_to(root).as_posix())
                raise AssertionError(
                    "Evidence reopened a file after authenticated admission"
                )
            return read_bytes(path)

        monkeypatch.setattr(
            service, "read_materialized_sead_full_evidence_admission", read_and_change
        )
        monkeypatch.setattr(
            admission_api,
            "read_materialized_sead_full_evidence_admission",
            read_and_change,
        )
        if hasattr(derivation, "read_materialized_sead_full_evidence_admission"):
            monkeypatch.setattr(
                derivation,
                "read_materialized_sead_full_evidence_admission",
                read_and_change,
            )
        monkeypatch.setattr(Path, "read_bytes", observe_read)
        observed = derivation.build_sead_source_native_evidence_bundle(
            root, expected_identity=expected
        )
        assert handed_off == [changed_member]
        assert late_reads == []
        assert observed == baseline


@pytest.mark.parametrize("relative", ["receipts/native.json", "country-decisions.json"])
def test_ledger_refuses_oversized_declared_source_before_open(
    tmp_path: Path, monkeypatch: Any, relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b" " * 64)
    record = {"byte_count": 3, "sha256": sha256(b"{}\n").hexdigest()}
    opened: list[str] = []
    native_io, native_os = io.open, os.open

    def open_io(value: Any, *args: Any, **kwargs: Any) -> Any:
        if (
            isinstance(value, (str, bytes, os.PathLike))
            and Path(os.fsdecode(value)) == path
        ):
            opened.append(relative)
        return native_io(value, *args, **kwargs)

    def open_os(value: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if not flags & os.O_DIRECTORY and Path(os.fsdecode(value)).name == path.name:
            opened.append(relative)
        return native_os(value, flags, *args, **kwargs)

    monkeypatch.setattr(io, "open", open_io)
    monkeypatch.setattr(os, "open", open_os)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {open_os})
    with pytest.raises(ValueError, match="byte count changed"):
        _read_bound_object(tmp_path, relative, record)
    assert opened == []


@pytest.mark.parametrize(
    "buffers,expected_error",
    [
        ({}, ValueError),
        ({"receipt.json": bytearray(b"{}\n")}, TypeError),
        ({"receipt.json": b"{}"}, ValueError),
        ({"receipt.json": b"[]\n"}, ValueError),
    ],
)
def test_ledger_authenticates_supplied_buffers_without_path_reads(
    tmp_path: Path, buffers: Any, expected_error: type[Exception]
) -> None:
    record = {"byte_count": 3, "sha256": sha256(b"{}\n").hexdigest()}
    absent_root = tmp_path / "absent-source"
    with pytest.raises(expected_error):
        _read_bound_object(absent_root, "receipt.json", record, source_files=buffers)
    assert (
        _read_bound_object(
            absent_root, "receipt.json", record, source_files={"receipt.json": b"{}\n"}
        )
        == {}
    )
    assert not absent_root.exists()
