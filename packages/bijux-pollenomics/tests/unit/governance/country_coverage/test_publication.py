"""Country-coverage identity and fail-closed publication tests."""

from __future__ import annotations

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
from typing import cast
import pytest
from bijux_pollenomics.governance.country_coverage import (
    CELL_SCHEMA_ID,
    build_country_dimension_coverage_ledger,
    write_country_dimension_coverage_ledger,
)
from bijux_pollenomics.governance.country_coverage import (
    service as country_coverage_service,
)
from .fixtures import (
    _CELL_SCHEMA_PATH,
    _COUNTRY_COVERAGE_ARTIFACT_ROOT,
    _LEDGER_PATH,
    _READ_BYTES,
    _REPOSITORY_ROOT,
    _build,
    _cell,
)


def test_input_bytes_are_read_once_for_identity_and_derivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = (_REPOSITORY_ROOT / "data/collection_summary.json").resolve()
    original = _READ_BYTES(target)
    changed = cast(dict[str, object], json.loads(original))
    source_hashes = cast(dict[str, object], changed["source_hashes"])
    landclim = cast(dict[str, object], source_hashes["landclim"])
    landclim["snapshot_sha256"] = "d" * 64
    replacement = json.dumps(changed, sort_keys=True).encode("utf-8")
    reads = 0

    def changing_read(path: Path) -> bytes:
        nonlocal reads
        if path.resolve() == target:
            reads += 1
            return original if reads == 1 else replacement
        return _READ_BYTES(path)

    monkeypatch.setattr(Path, "read_bytes", changing_read)

    ledger = _build()

    assert reads == 1
    recorded = next(
        item
        for item in cast(list[dict[str, object]], ledger["input_artifacts"])
        if item["path"] == "data/collection_summary.json"
    )
    assert recorded["sha256"] == hashlib.sha256(original).hexdigest()
    expected_snapshot = (
        "sha256:"
        + cast(dict[str, str], json.loads(original)["source_hashes"]["landclim"])[
            "snapshot_sha256"
        ]
    )
    assert (
        _cell(ledger, "landclim", "source_reported", "SE")["source_snapshot_id"]
        == expected_snapshot
    )


def test_substituted_schema_with_governed_identity_is_refused(tmp_path: Path) -> None:
    substitute = tmp_path / "country-coverage.schema.json"
    substitute.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": CELL_SCHEMA_ID,
                "type": "object",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema content is not governed"):
        build_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT, cell_schema_path=substitute
        )


def test_atomic_writer_refuses_symlinked_or_overlapping_output() -> None:
    _COUNTRY_COVERAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=_COUNTRY_COVERAGE_ARTIFACT_ROOT
    ) as temporary_directory:
        directory = Path(temporary_directory)
        schema_copy = directory / "country-coverage.schema.json"
        schema_copy.write_bytes(_CELL_SCHEMA_PATH.read_bytes())
        target = directory / "target.json"
        target.write_text("preserve\n", encoding="utf-8")
        alias = directory / "alias.json"
        alias.symlink_to(target.name)
        with pytest.raises(ValueError, match="must not contain symlinks"):
            write_country_dimension_coverage_ledger(
                _REPOSITORY_ROOT,
                cell_schema_path=schema_copy,
                output_path=alias,
            )

        real_parent = directory / "real-parent"
        real_parent.mkdir()
        parent_alias = directory / "parent-alias"
        parent_alias.symlink_to(real_parent.name, target_is_directory=True)
        with pytest.raises(ValueError, match="must not contain symlinks"):
            write_country_dimension_coverage_ledger(
                _REPOSITORY_ROOT,
                cell_schema_path=schema_copy,
                output_path=parent_alias / "ledger.json",
            )

        with pytest.raises(ValueError, match="overlaps a governed input"):
            write_country_dimension_coverage_ledger(
                _REPOSITORY_ROOT,
                cell_schema_path=schema_copy,
                output_path=schema_copy,
            )

        hardlink = directory / "schema-hardlink.json"
        hardlink.hardlink_to(schema_copy)
        with pytest.raises(ValueError, match="overlaps a governed input"):
            write_country_dimension_coverage_ledger(
                _REPOSITORY_ROOT,
                cell_schema_path=schema_copy,
                output_path=hardlink,
            )


def test_checked_ledger_and_atomic_writer_are_fixed_point() -> None:
    first = _build()
    second = _build()
    assert first == second

    _COUNTRY_COVERAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=_COUNTRY_COVERAGE_ARTIFACT_ROOT
    ) as temporary_directory:
        output = Path(temporary_directory) / "country_dimension_coverage.json"
        first_bytes = write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=output,
        )
        second_bytes = write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=output,
        )
        assert first_bytes == second_bytes == output.read_bytes()
        assert output.stat().st_mode & 0o777 == 0o644

    assert _LEDGER_PATH.read_bytes() == first_bytes


def test_atomic_writer_refuses_output_outside_repository() -> None:
    with pytest.raises(
        ValueError, match="country coverage output must remain inside the repository"
    ):
        write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=_REPOSITORY_ROOT.parent
            / "country_dimension_coverage-outside.json",
        )


def test_atomic_writer_refuses_lexical_output_alias() -> None:
    with pytest.raises(ValueError, match="must not use aliases"):
        write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=_REPOSITORY_ROOT
            / "data/../data/country_dimension_coverage.json",
        )


def test_atomic_writer_refuses_intermediate_ancestor_symlink_swap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _COUNTRY_COVERAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    outside_root = _REPOSITORY_ROOT / "artifacts"
    outside_root.mkdir(exist_ok=True)
    with (
        tempfile.TemporaryDirectory(
            dir=_COUNTRY_COVERAGE_ARTIFACT_ROOT
        ) as approved_directory,
        tempfile.TemporaryDirectory(dir=outside_root) as outside_directory,
    ):
        approved_root = Path(approved_directory)
        intermediate = approved_root / "stable-ancestor"
        intermediate.mkdir()
        displaced = approved_root / "displaced-ancestor"
        outside = Path(outside_directory)
        destination = intermediate / "nested" / "country-coverage.json"

        def swap_ancestor(
            repository_root: Path, *, cell_schema_path: Path
        ) -> dict[str, object]:
            assert repository_root == _REPOSITORY_ROOT
            assert cell_schema_path == _CELL_SCHEMA_PATH
            intermediate.rename(displaced)
            intermediate.symlink_to(outside, target_is_directory=True)
            return {"probe": "ancestor-swap"}

        monkeypatch.setattr(
            country_coverage_service,
            "build_country_dimension_coverage_ledger",
            swap_ancestor,
        )
        try:
            with pytest.raises(ValueError, match="must not contain symlinks"):
                write_country_dimension_coverage_ledger(
                    _REPOSITORY_ROOT,
                    cell_schema_path=_CELL_SCHEMA_PATH,
                    output_path=destination,
                )
            assert list(outside.iterdir()) == []
            assert not (displaced / "nested").exists()
            assert list(displaced.rglob("*.writing")) == []
            assert list(outside.rglob("*.writing")) == []
        finally:
            intermediate.unlink(missing_ok=True)


def test_atomic_writer_creates_approved_nested_artifact_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _COUNTRY_COVERAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=_COUNTRY_COVERAGE_ARTIFACT_ROOT
    ) as approved_directory:
        destination = (
            Path(approved_directory) / "nested" / "evidence" / "country-coverage.json"
        )

        def fixed_ledger(
            repository_root: Path, *, cell_schema_path: Path
        ) -> dict[str, object]:
            assert repository_root == _REPOSITORY_ROOT
            assert cell_schema_path == _CELL_SCHEMA_PATH
            return {"probe": "approved-nested-output"}

        monkeypatch.setattr(
            country_coverage_service,
            "build_country_dimension_coverage_ledger",
            fixed_ledger,
        )
        payload = write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=destination,
        )

        assert destination.read_bytes() == payload
        assert json.loads(payload) == {"probe": "approved-nested-output"}
        assert list(Path(approved_directory).rglob("*.writing")) == []


@pytest.mark.parametrize(
    "relative_output",
    (
        ".git/country-coverage.json",
        "pyproject.toml",
        "data/unrelated-country-output.json",
        "packages/bijux-pollenomics/src/bijux_pollenomics/governance/country_coverage.py",
        "packages/bijux-pollenomics/tests/unit/governance/test_country_coverage.py",
        "artifacts/unrelated-country-output.json",
    ),
)
def test_atomic_writer_refuses_unapproved_repository_paths(
    relative_output: str,
) -> None:
    with pytest.raises(ValueError, match="not an approved product or artifact path"):
        write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=_REPOSITORY_ROOT / relative_output,
        )
