"""Byte and validation contracts for animal governance payloads."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.contracts import (
    _render_adna_governance_role_registry_markdown,
    build_adna_governance_role_registry,
    build_source_library_project_surface_contract,
    validate_source_library_project_surfaces,
)

REPOSITORY_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "data/adna/governance/surface_role_registry.json").is_file()
)


def test_governance_payloads_match_tracked_publication_bytes() -> None:
    governance_root = REPOSITORY_ROOT / "data" / "adna" / "governance"
    for relative_path, payload in (
        ("surface_role_registry.json", build_adna_governance_role_registry()),
        (
            "source_library/project_surface_contract.json",
            build_source_library_project_surface_contract(),
        ),
    ):
        expected = (governance_root / relative_path).read_bytes()
        assert json.dumps(payload, indent=2, ensure_ascii=False).encode() == expected
    assert (
        _render_adna_governance_role_registry_markdown().encode()
        == (governance_root / "surface_role_registry.md").read_bytes()
    )


def test_project_surface_contract_refuses_a_missing_required_file(
    tmp_path: Path,
) -> None:
    project_root = (
        tmp_path / "adna" / "governance" / "source_library" / "projects" / "P123"
    )
    project_root.mkdir(parents=True)
    contract = build_source_library_project_surface_contract()
    required_files = tuple(
        filename
        for group in contract["artifact_groups"]
        for filename in group["required_files"]
    )
    for filename in required_files:
        (project_root / filename).touch()
    validate_source_library_project_surfaces(tmp_path)
    (project_root / required_files[0]).unlink()
    with pytest.raises(
        ValueError, match="source-library project surface contract violation"
    ):
        validate_source_library_project_surfaces(tmp_path)
