"""Evidence publication must preserve the admitted acquisition and foreign owners."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
    materialize_sead_full_evidence_admission,
    service,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
    build_sead_source_native_evidence_bundle,
    publication,
    write_sead_source_native_evidence_bundle,
)

from .support import _acquire, _full_admission_inputs, _FullEvidencePostgrestFixture


@pytest.fixture
def admitted(tmp_path: Path) -> Iterator[tuple[Path, SeadAdmissionExpectedIdentity]]:
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
        acquisition = materialize_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=decisions,
            parent_admission_path=parent,
            output_root=tmp_path / "admitted",
            expected_identity=expected,
        )
        yield acquisition.output_root, expected


def _namespace(root: Path) -> dict[str, tuple[int, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.stat().st_dev,
            path.stat().st_ino,
            path.stat().st_size,
        )
        for path in [root, *root.rglob("*")]
    }


@pytest.mark.parametrize("placement", ["same", "child", "parent", "ancestor"])
def test_overlapping_output_refuses_before_source_lookup_and_preserves_namespace(
    admitted: tuple[Path, SeadAdmissionExpectedIdentity],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    placement: str,
) -> None:
    source, expected = admitted
    output = {
        "same": source,
        "child": source / "evidence",
        "parent": source.parent,
        "ancestor": source.parent.parent,
    }[placement]
    foreign = tmp_path / "foreign-owner.json"
    foreign.write_bytes(b'{"owner":"generated foreign owner"}\n')
    before = _namespace(tmp_path)
    original = build_sead_source_native_evidence_bundle
    lookups = []

    def looked_up(*args: Any, **kwargs: Any) -> Any:
        lookups.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(
        publication, "build_sead_source_native_evidence_bundle", looked_up
    )
    with pytest.raises(ValueError, match="overlap"):
        write_sead_source_native_evidence_bundle(
            source, output, expected_identity=expected
        )
    assert lookups == []
    assert _namespace(tmp_path) == before
    assert foreign.read_bytes() == b'{"owner":"generated foreign owner"}\n'


def test_nonoverlapping_output_uses_real_source_lookup_and_preserves_acquisition(
    admitted: tuple[Path, SeadAdmissionExpectedIdentity],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, expected = admitted
    before = _namespace(source)
    original = build_sead_source_native_evidence_bundle
    lookups = []

    def looked_up(*args: Any, **kwargs: Any) -> Any:
        lookups.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(
        publication, "build_sead_source_native_evidence_bundle", looked_up
    )
    output = tmp_path / "evidence"
    files = write_sead_source_native_evidence_bundle(
        source, output, expected_identity=expected
    )
    assert (
        len(lookups) == 1 and output / "evidence_materialization_manifest.json" in files
    )
    assert _namespace(source) == before
