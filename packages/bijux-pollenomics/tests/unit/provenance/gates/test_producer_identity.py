"""Recorded-gate producer-closure identity tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.provenance import gates
from bijux_pollenomics.provenance.gates import producer
from bijux_pollenomics.provenance.release_evidence import ReleaseEvidenceError


def _digest(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _expected_source_files(package_root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for path in sorted(
        package_root.rglob("*.py"),
        key=lambda item: item.relative_to(package_root).as_posix(),
    ):
        relative = path.relative_to(package_root)
        components = list(relative.parts)
        if components[-1] == "__init__.py":
            components.pop()
        else:
            components[-1] = path.stem
        payload = path.read_bytes()
        result.append(
            {
                "module": ".".join((producer._PRODUCER_MODULE, *components)),
                "sha256": _digest(payload),
                "byte_count": len(payload),
            }
        )
    return result


def test_producer_identity_binds_complete_package_source_closure() -> None:
    package_root = Path(gates.__file__).parent

    source_files = producer._producer_source_files()

    assert source_files == _expected_source_files(package_root)
    assert len(source_files) > 1
    assert source_files[0]["module"] == "bijux_pollenomics.provenance.gates"
    assert [item["module"] for item in source_files] == sorted(
        item["module"] for item in source_files
    )


def test_producer_identity_changes_with_any_owned_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_root = tmp_path / "gates"
    package_root.mkdir()
    (package_root / "__init__.py").write_text('"""Facade."""\n', encoding="utf-8")
    (package_root / "execution.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.setattr(producer, "_PACKAGE_ROOT", package_root)

    before = producer._producer_record()
    (package_root / "execution.py").write_text("VALUE = 2\n", encoding="utf-8")
    after = producer._producer_record()

    assert before["source_files"] != after["source_files"]
    assert before["source_digest"] != after["source_digest"]
    assert before["digest"] != after["digest"]


def test_producer_identity_refuses_symlinked_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_root = tmp_path / "gates"
    package_root.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("VALUE = 1\n", encoding="utf-8")
    (package_root / "__init__.py").write_text('"""Facade."""\n', encoding="utf-8")
    (package_root / "execution.py").symlink_to(outside)
    monkeypatch.setattr(producer, "_PACKAGE_ROOT", package_root)

    with pytest.raises(ReleaseEvidenceError, match="producer source is unsafe"):
        producer._producer_source_files()
