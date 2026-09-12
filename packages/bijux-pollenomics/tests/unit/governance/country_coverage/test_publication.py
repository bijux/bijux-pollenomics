"""Country-coverage identity and fail-closed publication tests."""

from __future__ import annotations

from collections.abc import Iterator
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType
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
    _LEDGER_PATH,
    _READ_BYTES,
    _REPOSITORY_ROOT,
    _build,
    _cell,
)


def test_producer_identity_binds_the_recursive_package_source_closure() -> None:
    package_root = Path(country_coverage_service.__file__).resolve().parent
    source_records = [
        {
            "path": path.relative_to(_REPOSITORY_ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(package_root.rglob("*.py"))
    ]

    producer = country_coverage_service._producer_identity(_REPOSITORY_ROOT)

    assert any("/evidence/" in record["path"] for record in source_records)
    canonical_records = (
        json.dumps(
            source_records,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    assert producer["sha256"] == hashlib.sha256(canonical_records).hexdigest()


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


def test_atomic_writer_refuses_symlinked_or_overlapping_output(
    publication_workspace: tuple[Path, ModuleType],
) -> None:
    root, coverage = publication_workspace
    schema_path = root / "configs/scientific-contracts/country-coverage.schema.json"
    artifact_root = root / "artifacts/execution-control/country-coverage"
    artifact_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=artifact_root) as temporary_directory:
        directory = Path(temporary_directory)
        schema_copy = directory / "country-coverage.schema.json"
        schema_copy.write_bytes(schema_path.read_bytes())
        target = directory / "target.json"
        target.write_text("preserve\n", encoding="utf-8")
        alias = directory / "alias.json"
        alias.symlink_to(target.name)
        with pytest.raises(ValueError, match="must not contain symlinks"):
            coverage.write_country_dimension_coverage_ledger(
                root,
                cell_schema_path=schema_copy,
                output_path=alias,
            )

        real_parent = directory / "real-parent"
        real_parent.mkdir()
        parent_alias = directory / "parent-alias"
        parent_alias.symlink_to(real_parent.name, target_is_directory=True)
        with pytest.raises(ValueError, match="must not contain symlinks"):
            coverage.write_country_dimension_coverage_ledger(
                root,
                cell_schema_path=schema_copy,
                output_path=parent_alias / "ledger.json",
            )

        with pytest.raises(ValueError, match="overlaps a governed input"):
            coverage.write_country_dimension_coverage_ledger(
                root,
                cell_schema_path=schema_copy,
                output_path=schema_copy,
            )

        hardlink = directory / "schema-hardlink.json"
        hardlink.hardlink_to(schema_copy)
        with pytest.raises(ValueError, match="overlaps a governed input"):
            coverage.write_country_dimension_coverage_ledger(
                root,
                cell_schema_path=schema_copy,
                output_path=hardlink,
            )


def test_checked_ledger_and_atomic_writer_are_fixed_point(
    publication_workspace: tuple[Path, ModuleType],
) -> None:
    root, coverage = publication_workspace
    schema_path = root / "configs/scientific-contracts/country-coverage.schema.json"
    artifact_root = root / "artifacts/execution-control/country-coverage"
    first = coverage.build_country_dimension_coverage_ledger(
        root, cell_schema_path=schema_path
    )
    second = coverage.build_country_dimension_coverage_ledger(
        root, cell_schema_path=schema_path
    )
    assert first == second

    artifact_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=artifact_root) as temporary_directory:
        output = Path(temporary_directory) / "country_dimension_coverage.json"
        first_bytes = coverage.write_country_dimension_coverage_ledger(
            root,
            cell_schema_path=schema_path,
            output_path=output,
        )
        second_bytes = coverage.write_country_dimension_coverage_ledger(
            root,
            cell_schema_path=schema_path,
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
    publication_workspace: tuple[Path, ModuleType],
) -> None:
    root, coverage = publication_workspace
    schema_path = root / "configs/scientific-contracts/country-coverage.schema.json"
    artifact_root = root / "artifacts/execution-control/country-coverage"
    artifact_root.mkdir(parents=True, exist_ok=True)
    outside_root = root / "artifacts"
    outside_root.mkdir(exist_ok=True)
    with (
        tempfile.TemporaryDirectory(dir=artifact_root) as approved_directory,
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
            assert repository_root == root
            assert cell_schema_path == schema_path
            intermediate.rename(displaced)
            intermediate.symlink_to(outside, target_is_directory=True)
            return {"probe": "ancestor-swap"}

        monkeypatch.setattr(
            coverage.service,
            "build_country_dimension_coverage_ledger",
            swap_ancestor,
        )
        try:
            with pytest.raises(ValueError, match="must not contain symlinks"):
                coverage.write_country_dimension_coverage_ledger(
                    root,
                    cell_schema_path=schema_path,
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
    publication_workspace: tuple[Path, ModuleType],
) -> None:
    root, coverage = publication_workspace
    schema_path = root / "configs/scientific-contracts/country-coverage.schema.json"
    artifact_root = root / "artifacts/execution-control/country-coverage"
    artifact_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=artifact_root) as approved_directory:
        destination = (
            Path(approved_directory) / "nested" / "evidence" / "country-coverage.json"
        )

        def fixed_ledger(
            repository_root: Path, *, cell_schema_path: Path
        ) -> dict[str, object]:
            assert repository_root == root
            assert cell_schema_path == schema_path
            return {"probe": "approved-nested-output"}

        monkeypatch.setattr(
            coverage.service,
            "build_country_dimension_coverage_ledger",
            fixed_ledger,
        )
        payload = coverage.write_country_dimension_coverage_ledger(
            root,
            cell_schema_path=schema_path,
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


@pytest.fixture(scope="module")
def publication_workspace(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[Path, ModuleType]]:
    """Execute real copied authority code against privately owned governed inputs."""
    from bijux_pollenomics.evidence.sources.sead import governed_sead_evidence_root
    from bijux_pollenomics.governance.country_coverage import INPUT_PATHS

    root = tmp_path_factory.mktemp("country-publication-workspace")
    for relative in (
        *INPUT_PATHS,
        "configs/scientific-contracts/country-coverage.schema.json",
    ):
        source = _REPOSITORY_ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    original_sead = governed_sead_evidence_root(_REPOSITORY_ROOT / "data")
    shutil.copytree(
        original_sead, governed_sead_evidence_root(root / "data"), dirs_exist_ok=True
    )
    source_package = Path(country_coverage_service.__file__).resolve().parent
    package = root / source_package.relative_to(_REPOSITORY_ROOT)
    shutil.copytree(
        source_package, package, ignore=shutil.ignore_patterns("__pycache__")
    )
    name = "_isolated_country_coverage_publication"
    specification = importlib.util.spec_from_file_location(
        name, package / "__init__.py", submodule_search_locations=[str(package)]
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
        yield root, module
    finally:
        for key in tuple(sys.modules):
            if key == name or key.startswith(name + "."):
                del sys.modules[key]
