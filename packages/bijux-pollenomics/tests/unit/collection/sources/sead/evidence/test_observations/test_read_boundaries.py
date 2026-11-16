"""Refuse unowned evidence and manifest members before their file bodies open."""

from hashlib import sha256
import io
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.admission.validation.manifests import (
    _validate_manifest_files,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import validation
from bijux_pollenomics.collection.sources.sead.evidence.bundle.constants import (
    EVIDENCE_MANIFEST_SCHEMA_VERSION,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle.serialization import (
    _canonical_bytes,
)

NAMES = (
    "chronology_claims.json",
    "source_native_observations.json",
    "observation_relation_index.json",
    "evidence_events.json",
    "source_key_ledger.json",
)


def _record(name: str, raw: bytes) -> dict[str, object]:
    return {"path": name, "sha256": sha256(raw).hexdigest(), "byte_count": len(raw)}


def _evidence(root: Path, raw: bytes = b"{}\n") -> None:
    root.mkdir()
    for name in NAMES:
        (root / name).write_bytes(raw)
    (root / "evidence_materialization_manifest.json").write_bytes(
        _canonical_bytes(
            {
                "schema_version": EVIDENCE_MANIFEST_SCHEMA_VERSION,
                "files": [_record(name, raw) for name in NAMES],
                "multipart_documents": {},
            }
        )
    )


def _watch_opens(monkeypatch: pytest.MonkeyPatch, watched: set[str]) -> list[str]:
    native_io_open, native_os_open = io.open, os.open
    observed: list[str] = []

    def io_open(path: Any, *args: Any, **kwargs: Any) -> Any:
        if (
            isinstance(path, (str, bytes, os.PathLike))
            and Path(os.fsdecode(path)).name in watched
        ):
            observed.append(Path(os.fsdecode(path)).name)
        return native_io_open(path, *args, **kwargs)

    def os_open(path: Any, *args: Any, **kwargs: Any) -> int:
        if (
            isinstance(path, (str, bytes, os.PathLike))
            and Path(os.fsdecode(path)).name in watched
        ):
            observed.append(Path(os.fsdecode(path)).name)
        return native_os_open(path, *args, **kwargs)

    monkeypatch.setattr(io, "open", io_open)
    monkeypatch.setattr(os, "open", os_open)
    return observed


def test_unlisted_namespace_refuses_before_any_record_body_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "evidence"
    _evidence(root)
    unexpected = root / "unlisted-body.json"
    unexpected.write_bytes(b'{"generated":"not declared"}\n')
    opens = _watch_opens(monkeypatch, {*NAMES, unexpected.name})
    with pytest.raises(ValueError):
        validation.validate_sead_source_native_evidence_materialization(root)
    assert opens == []


def test_member_size_cap_precedes_member_body_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "evidence"
    _evidence(root, b" " * 4096)
    monkeypatch.setattr(validation, "_MAX_GOVERNED_FILE_BYTES", 2048)
    assert (root / "evidence_materialization_manifest.json").stat().st_size < 2048
    opens = _watch_opens(monkeypatch, set(NAMES))
    with pytest.raises(ValueError):
        validation.validate_sead_source_native_evidence_materialization(root)
    assert opens == []


def test_manifest_cap_precedes_manifest_body_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "evidence"
    _evidence(root)
    name = "evidence_materialization_manifest.json"
    (root / name).write_bytes(b" " * 4096)
    monkeypatch.setattr(validation, "_MAX_GOVERNED_FILE_BYTES", 2048)
    opens = _watch_opens(monkeypatch, {name})
    with pytest.raises(ValueError):
        validation.validate_sead_source_native_evidence_materialization(root)
    assert opens == []


def test_acquisition_manifest_cannot_authorize_an_unowned_file_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "acquisition"
    (root / "reconciliation").mkdir(parents=True)
    names = (
        "reconciliation/countries.json",
        "reconciliation/joins.json",
        "unowned-body.json",
    )
    for name in names:
        (root / name).write_bytes(b"{}\n")
    manifest = {"files": [_record(name, b"{}\n") for name in names]}
    raw = _canonical_bytes(manifest)
    (root / "manifest.json").write_bytes(raw)
    opens = _watch_opens(monkeypatch, {Path(name).name for name in names})
    with pytest.raises(ValueError):
        _validate_manifest_files(
            root, manifest, raw, tables=(), allowed_extra_paths=set()
        )
    assert opens == []


def test_current_namespace_drift_stops_before_the_next_record_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.sead.evidence.bundle import reading

    root = tmp_path / "evidence"
    _evidence(root)
    from bijux_pollenomics.collection.sources.sead.evidence.bundle.serialization import (
        _verify_record,
    )

    real_verify = _verify_record

    def verified(raw: bytes, record: Any, label: str) -> None:
        real_verify(raw, record, label)
        (root / "unexpected-during-read.json").write_bytes(b"{}\n")

    monkeypatch.setattr(reading, "_verify_record", verified)
    opens = _watch_opens(monkeypatch, set(NAMES))
    with pytest.raises(ValueError):
        validation.validate_sead_source_native_evidence_materialization(root)
    assert opens == [NAMES[0]]


def test_equal_bytes_manifest_inode_drift_refuses_before_record_bodies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.sead.evidence.bundle import reading

    root = tmp_path / "evidence"
    _evidence(root)
    from bijux_pollenomics.collection.sources.sead.evidence.bundle.serialization import (
        _decode_object,
    )

    real_decode = _decode_object

    def decoded(raw: bytes, label: str) -> dict[str, object]:
        result = real_decode(raw, label)
        replacement = tmp_path / "equal-manifest.json"
        replacement.write_bytes(raw)
        os.replace(replacement, root / "evidence_materialization_manifest.json")
        return result

    monkeypatch.setattr(reading, "_decode_object", decoded)
    opens = _watch_opens(monkeypatch, set(NAMES))
    with pytest.raises(ValueError):
        validation.validate_sead_source_native_evidence_materialization(root)
    assert opens == []


@pytest.mark.parametrize("alias", ["symlink", "hardlink", "ancestor"])
def test_aliases_refuse_before_record_body_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alias: str
) -> None:
    root = tmp_path / "evidence"
    _evidence(root)
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"{}\n")
    if alias == "ancestor":
        linked = tmp_path / "linked"
        linked.symlink_to(root, target_is_directory=True)
        root = linked
    else:
        member = root / NAMES[0]
        member.unlink()
        if alias == "symlink":
            member.symlink_to(outside)
        else:
            os.link(outside, member)
    opens = _watch_opens(monkeypatch, set(NAMES))
    with pytest.raises(ValueError):
        validation.validate_sead_source_native_evidence_materialization(root)
    assert opens == []


def test_refused_overlap_does_not_create_an_unowned_source_directory(
    tmp_path: Path,
) -> None:
    from tests.unit.collection.sources.sead.acquisition.test_admission.fixtures import (
        _materialize,
        _write_fixture,
    )

    root, decisions = _write_fixture(tmp_path)
    destination = root / "admitted"
    with pytest.raises(ValueError, match="overlaps acquisition source"):
        _materialize(root, decisions, destination)
    assert not destination.exists()


def test_evidence_manifest_record_alone_cannot_authorize_an_unreferenced_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "evidence"
    _evidence(root)
    unexpected = root / "declared-but-unreferenced.json"
    unexpected.write_bytes(b"{}\n")
    manifest_path = root / "evidence_materialization_manifest.json"
    from bijux_pollenomics.collection.sources.sead.evidence.bundle.serialization import (
        _decode_object,
    )

    manifest = _decode_object(manifest_path.read_bytes(), "generated manifest")
    records = manifest["files"]
    assert isinstance(records, list)
    records.append(_record(unexpected.name, b"{}\n"))
    manifest_path.write_bytes(_canonical_bytes(manifest))
    opens = _watch_opens(monkeypatch, {unexpected.name})
    with pytest.raises(ValueError):
        validation.validate_sead_source_native_evidence_materialization(root)
    assert opens == []


def test_positive_literal_reads_are_finite_and_all_file_descriptors_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.sead.evidence.bundle.reading import (
        open_evidence_files,
    )

    root = tmp_path / "evidence"
    _evidence(root)
    files = list(root.iterdir())
    inodes = {path.stat().st_ino for path in files}
    expected_bytes = sum(path.stat().st_size for path in files)
    real_open, real_read = os.open, os.read
    descriptors: list[int] = []
    counts: list[int] = []

    def opened(name: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = real_open(name, flags, *args, **kwargs)
        if os.fstat(descriptor).st_ino in inodes:
            assert flags & os.O_NOFOLLOW and flags & os.O_NONBLOCK
            descriptors.append(descriptor)
        return descriptor

    def read(descriptor: int, count: int) -> bytes:
        raw = real_read(descriptor, count)
        if os.fstat(descriptor).st_ino in inodes:
            counts.append(len(raw))
        return raw

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "read", read)
    with open_evidence_files(root, max_member_bytes=2048) as (
        _manifest,
        records,
        contents,
    ):
        assert set(records) == set(NAMES)
        assert contents == dict.fromkeys(NAMES, b"{}\n")
    assert len(descriptors) == 6 and sum(counts) == expected_bytes
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_digest_failure_remains_primary_when_namespace_also_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.sead.evidence.bundle import reading
    from bijux_pollenomics.collection.sources.sead.evidence.bundle.serialization import (
        _decode_object,
        _verify_record,
    )

    root = tmp_path / "evidence"
    _evidence(root)
    path = root / "evidence_materialization_manifest.json"
    manifest = _decode_object(path.read_bytes(), "generated manifest")
    records = manifest["files"]
    assert isinstance(records, list) and isinstance(records[0], dict)
    records[0]["sha256"] = "0" * 64
    path.write_bytes(_canonical_bytes(manifest))

    def verified(raw: bytes, record: Any, label: str) -> None:
        try:
            _verify_record(raw, record, label)
        finally:
            (root / "secondary-namespace-change.json").write_bytes(b"{}\n")

    monkeypatch.setattr(reading, "_verify_record", verified)
    with pytest.raises(ValueError, match="admitted digest changed"):
        validation.validate_sead_source_native_evidence_materialization(root)


def test_admission_recovery_never_opens_unowned_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.unit.collection.sources.sead.acquisition.test_admission.fixtures import (
        _materialize,
        _write_fixture,
    )

    snapshot, decisions = _write_fixture(tmp_path)
    admitted = _materialize(snapshot, decisions, tmp_path / "admitted")
    unknown = admitted.output_root / "unowned-recovery-body.json"
    unknown.write_bytes(b"{}\n")
    opens = _watch_opens(monkeypatch, {unknown.name})
    with pytest.raises(FileExistsError, match="Non-identical"):
        _materialize(snapshot, decisions, tmp_path / "admitted")
    assert opens == []


def test_evidence_recovery_never_opens_unowned_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import patch

    from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
        materialize_sead_full_evidence_admission,
        service,
    )
    from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
        write_sead_source_native_evidence_bundle,
    )

    from .support import _acquire, _full_admission_inputs, _FullEvidencePostgrestFixture

    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent, expected = _full_admission_inputs(snapshot, tmp_path)
    with (
        patch.object(
            service, "_load_validated_boundary_authority", return_value=object()
        ),
        patch.object(
            service, "_validate_country_accounting", return_value={"reconciles": True}
        ),
    ):
        admitted = materialize_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=decisions,
            parent_admission_path=parent,
            output_root=tmp_path / "admitted",
            expected_identity=expected,
        )
        output = tmp_path / "evidence"
        write_sead_source_native_evidence_bundle(
            admitted.output_root, expected_identity=expected, output_directory=output
        )
        unknown = output / "unowned-recovery-body.json"
        unknown.write_bytes(b"{}\n")
        opens = _watch_opens(monkeypatch, {unknown.name})
        with pytest.raises(FileExistsError, match="Non-identical"):
            write_sead_source_native_evidence_bundle(
                admitted.output_root,
                expected_identity=expected,
                output_directory=output,
            )
    assert opens == []


@pytest.mark.parametrize(
    "invalid",
    [
        "missing_manifest_owner",
        "different_manifest_owner",
        "noncanonical_index",
        "digest",
    ],
)
def test_invalid_multipart_authority_refuses_before_part_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: str
) -> None:
    """A part path needs matching canonical logical and materialization indexes."""
    import json

    from bijux_pollenomics.collection.sources.sead.evidence.bundle.serialization import (
        _decode_object,
    )

    root = tmp_path / "evidence"
    _evidence(root)
    part_name = "source_native_observations/observations-00001.json"
    part = b'{"generated":"part requires independent index agreement"}\n'
    part_path = root / part_name
    part_path.parent.mkdir()
    part_path.write_bytes(part)
    part_record = {
        **_record(part_name, part),
        "part_number": 1,
        "row_start": 0,
        "row_end": 1,
        "row_count": 1,
    }
    index = {
        "partitioned_fields": {
            "observations": {"part_count": 1, "row_count": 1, "parts": [part_record]}
        }
    }
    if invalid == "digest":
        part_record["sha256"] = "0" * 64
    raw = (
        json.dumps(index, indent=2).encode()
        if invalid == "noncanonical_index"
        else _canonical_bytes(index)
    )
    index_name = "source_native_observations.json"
    (root / index_name).write_bytes(raw)
    manifest_path = root / "evidence_materialization_manifest.json"
    manifest = _decode_object(manifest_path.read_bytes(), "generated manifest")
    manifest["files"] = [
        _record(name, raw if name == index_name else b"{}\n") for name in NAMES
    ] + [_record(part_name, part)]
    owner = (
        "evidence_events.json" if invalid == "different_manifest_owner" else index_name
    )
    manifest["multipart_documents"] = (
        {}
        if invalid == "missing_manifest_owner"
        else {
            owner: {
                "partitioned_fields": ["observations"],
                "part_count": 1,
                "parts": [part_name],
            }
        }
    )
    manifest_path.write_bytes(_canonical_bytes(manifest))
    opens = _watch_opens(monkeypatch, {part_path.name})
    with pytest.raises((ValueError, TypeError, KeyError)):
        validation.validate_sead_source_native_evidence_materialization(root)
    assert opens == []
