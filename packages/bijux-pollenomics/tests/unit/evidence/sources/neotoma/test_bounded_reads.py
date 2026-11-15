"""Relational evidence decoding follows a closed source-byte preflight."""

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.evidence.sources.neotoma import validation
from tests.unit.collection.sources.neotoma.materialization.native_snapshot import (
    _snapshot,
)


def test_relational_file_has_an_explicit_format_specific_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.json"
    source.write_bytes(b"1234")
    monkeypatch.setattr(
        validation, "RELATIONAL_MATERIALIZATION_MAX_BYTES", 3, raising=False
    )
    with pytest.raises(ValueError, match="budget|bound"):
        validation._read_regular_file(source)


def test_relational_aggregate_limit_refuses_before_json_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    materialize_neotoma_relational_snapshot(output, _snapshot())
    total = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
    monkeypatch.setattr(
        validation, "RELATIONAL_MATERIALIZATION_MAX_BYTES", total - 1, raising=False
    )
    monkeypatch.setattr(
        validation,
        "_decode_json_object",
        lambda *a: pytest.fail("Decoded before aggregate preflight"),
    )
    with pytest.raises(ValueError, match="budget|bound"):
        validation.validate_neotoma_relational_materialization(output)
