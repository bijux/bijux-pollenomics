"""Authenticate the exact parent bytes consumed by SEAD projection."""

import json
from pathlib import Path

import pytest

from bijux_pollenomics.core.filesystem import read_regular_file


def test_projection_refuses_reopened_manifest_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        sead as projection,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead import (
        admission,
    )
    from tests.support.sead_evidence import (
        install_sead_projection_fixture,
        sead_projection_layers,
    )

    root = tmp_path.absolute()
    install_sead_projection_fixture(root, monkeypatch)
    original = read_regular_file

    def swapped(path: Path, *, max_bytes: int) -> bytes:
        payload = original(path, max_bytes=max_bytes)
        if path.name == "evidence_materialization_manifest.json":
            value = json.loads(payload)
            value["file_set_sha256"] = "0" * 64
            return (
                json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
                + b"\n"
            )
        return payload

    monkeypatch.setattr(admission, "read_regular_file", swapped)
    with pytest.raises(ValueError, match="manifest"):
        projection._project_sead(root, sead_projection_layers()[1:])


@pytest.mark.parametrize("name", ["tbl_sites.json", "country-decisions.json"])
def test_projection_refuses_parent_swap_at_site_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        sead as projection,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead import sites
    from tests.support.sead_evidence import (
        install_sead_projection_fixture,
        sead_projection_layers,
    )

    root = tmp_path.absolute()
    install_sead_projection_fixture(root, monkeypatch)
    original = read_regular_file

    def swapped(path: Path, *, max_bytes: int) -> bytes:
        payload = original(path, max_bytes=max_bytes)
        if path.name == name:
            return payload + b" "
        return payload

    monkeypatch.setattr(sites, "read_regular_file", swapped)
    with pytest.raises(ValueError, match="digest"):
        projection._project_sead(root, sead_projection_layers()[1:])


def test_projection_refuses_admission_swap_before_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        sead as projection,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead import (
        admission,
    )
    from tests.support.sead_evidence import (
        install_sead_projection_fixture,
        sead_projection_layers,
    )

    root = tmp_path.absolute()
    install_sead_projection_fixture(root, monkeypatch)

    def swapped(path: Path, *, max_bytes: int) -> bytes:
        payload = read_regular_file(path, max_bytes=max_bytes)
        return payload + b" " if path.name == "admission.json" else payload

    monkeypatch.setattr(admission, "read_regular_file", swapped)
    with pytest.raises(ValueError, match="admission digest"):
        projection._project_sead(root, sead_projection_layers()[1:])
