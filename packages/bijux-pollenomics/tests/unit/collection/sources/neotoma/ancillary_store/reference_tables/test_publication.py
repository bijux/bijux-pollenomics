"""Closed portable reference archives do not depend on an acquisition folder."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import importlib
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.reference_tables import (
    DEFAULT_REFERENCE_LIMITS,
    NeotomaReferenceTablePlan,
    capture_neotoma_reference_tables,
    replay_neotoma_reference_tables,
)
from bijux_pollenomics.collection.sources.neotoma.capture.transport import (
    NeotomaHttpResponse,
)


@pytest.mark.parametrize(
    "reference_source", ["complete", "incomplete", "http"], indirect=True
)
def test_archive_restores_without_original_capture(
    reference_archive: dict[str, Any],
) -> None:
    archive = reference_archive
    shutil.rmtree(archive["source_directory"])
    assert (
        archive["owner"].load_neotoma_reference_archive(
            archive["directory"], expected_manifest_sha256=archive["sha256"]
        )
        == archive["manifest"]
    )
    assert archive["manifest"]["scientific_admission"] == "not_asserted"
    assert archive["manifest"]["table_population_complete"] is False
    for table, body in archive["bodies"].items():
        path = (
            archive["directory"]
            / "capture"
            / f"reference-table-{table}-current-attempt-1.body"
        )
        assert path.read_bytes() == body


@pytest.mark.parametrize(
    "damage", ["extra", "missing", "changed", "symlink", "hardlink"]
)
def test_closed_namespace_and_full_source_validation_refuse_damage(
    reference_archive: dict[str, Any], damage: str, tmp_path: Path
) -> None:
    archive = reference_archive
    root = archive["directory"]
    body = root / "capture/reference-table-variableunits-current-attempt-1.body"
    if damage == "extra":
        (root / "caller-note.json").write_text("{}")
    elif damage == "missing":
        body.unlink()
    elif damage == "changed":
        raw = body.read_bytes()
        body.write_bytes(raw.replace(b'"m"', b'"x"'))
    else:
        outside = tmp_path / "outside-entity"
        outside.write_bytes(body.read_bytes())
        body.unlink()
        if damage == "symlink":
            body.symlink_to(outside)
        else:
            body.hardlink_to(outside)
    with pytest.raises(ValueError):
        archive["owner"].load_neotoma_reference_archive(
            root, expected_manifest_sha256=archive["sha256"]
        )


def test_wrong_anchor_and_existing_output_are_refused(
    reference_archive: dict[str, Any],
) -> None:
    archive = reference_archive
    with pytest.raises(ValueError):
        archive["owner"].load_neotoma_reference_archive(
            archive["directory"], expected_manifest_sha256="f" * 64
        )
    before = sha256((archive["directory"] / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        archive["owner"].write_neotoma_reference_archive(
            archive["directory"],
            capture_directory=archive["source_directory"],
            expected_capture_manifest_sha256=archive["capture"].manifest_sha256,
        )
    assert (
        sha256((archive["directory"] / "manifest.json").read_bytes()).hexdigest()
        == before
    )


def test_original_final_incomplete_sentinel_survives_portable_roundtrip(
    tmp_path: Path,
) -> None:
    bounds: list[int] = []

    def fetch(url: str, *, max_bytes: int, **_: Any) -> NeotomaHttpResponse:
        bounds.append(max_bytes)
        return NeotomaHttpResponse(
            url, 200, (("Content-Length", "11"),), b"0123456789", False
        )

    source = tmp_path / "sentinel-source"
    limits = replace(
        DEFAULT_REFERENCE_LIMITS, max_response_bytes=10, max_total_bytes=19
    )
    original = capture_neotoma_reference_tables(
        source,
        plan=NeotomaReferenceTablePlan(("variableunits", "geopoliticalunits")),
        limits=limits,
        fetch=fetch,
    )
    assert bounds == [10, 9]
    assert original.response_bytes == 20
    assert (
        replay_neotoma_reference_tables(
            source, expected_manifest_sha256=original.manifest_sha256
        )
        == original
    )
    owner = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.ancillary_store.reference_tables"
    )
    archive = tmp_path / "sentinel-archive"
    manifest = owner.write_neotoma_reference_archive(
        archive,
        capture_directory=source,
        expected_capture_manifest_sha256=original.manifest_sha256,
    )
    anchor = sha256((archive / "manifest.json").read_bytes()).hexdigest()
    assert (
        owner.load_neotoma_reference_archive(archive, expected_manifest_sha256=anchor)
        == manifest
    )
    assert all(
        row["terminal_status"] == "refused_incomplete_body"
        for row in owner.read_neotoma_reference_archive_inventory(
            archive, expected_manifest_sha256=anchor
        ).index["tables"]
    )


@pytest.mark.parametrize("anchor", [None, True, "invalid"])
def test_publication_requires_capture_anchor_before_source_entity_access(
    reference_source: dict[str, Any],
    tmp_path: Path,
    anchor: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.ancillary_store.reference_tables"
    )
    actual_open = Path.open

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            pytest.fail("missing independent capture anchor reached a source entity")
        return actual_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    with pytest.raises(ValueError):
        owner.write_neotoma_reference_archive(
            tmp_path / "unanchored-archive",
            capture_directory=reference_source["directory"],
            expected_capture_manifest_sha256=anchor,
        )
    assert not (tmp_path / "unanchored-archive").exists()
