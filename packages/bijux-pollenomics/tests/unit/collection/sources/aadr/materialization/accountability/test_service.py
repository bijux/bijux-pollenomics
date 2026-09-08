"""End-to-end service tests for compact AADR source accountability."""

from __future__ import annotations

from hashlib import md5, sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION,
    materialize_aadr_source_accountability,
    service,
)

from .support import HEADER


def _write_release(
    data_root: Path,
    *,
    downloaded_files: list[str] | None = None,
    source: str = "AADR",
    requested_version: str = "v66",
) -> tuple[Path, bytes]:
    release_dir = data_root / "aadr" / "v66"
    panels = (
        (
            "ho",
            "v66.HO.aadr.PUB.anno",
            (
                "ID-SE",
                "Sweden",
                "Direct",
                "100",
                "10",
                "110-90 BP",
                "59",
                "18",
                "HO",
            ),
        ),
        (
            "1240k",
            "v66.1240K.aadr.PUB.anno",
            (
                "ID-DK",
                "Denmark",
                "Context",
                "200",
                "20",
                "220-180 BP",
                "56",
                "12",
                "1240K",
            ),
        ),
    )
    anno_files: list[dict[str, object]] = []
    for file_id, (dataset_name, filename, row) in enumerate(panels, start=1):
        payload = (HEADER + "\n" + "\t".join(row) + "\n").encode()
        path = release_dir / dataset_name / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        anno_files.append(
            {
                "dataset_name": dataset_name,
                "filename": filename,
                "file_id": file_id,
                "md5": md5(payload, usedforsecurity=False).hexdigest(),
                "filesize": len(payload),
            }
        )
    inventory = [f"{row['dataset_name']}/{row['filename']}" for row in anno_files]
    manifest = {
        "source": source,
        "requested_version": requested_version,
        "downloaded_files": inventory if downloaded_files is None else downloaded_files,
        "anno_files": anno_files,
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    manifest_path = release_dir / "release_manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    return manifest_path, manifest_bytes


def test_service_validates_reconciles_and_publishes_only_compact_receipt(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    _manifest_path, manifest_bytes = _write_release(data_root)

    first = materialize_aadr_source_accountability(data_root, "v66")
    second = materialize_aadr_source_accountability(data_root, "v66")

    expected_path = (
        data_root
        / "adna/species/homo_sapiens/review"
        / "aadr_v66_source_accountability.json"
    )
    assert first == second
    assert first.output_path == expected_path
    assert first.output_path.read_bytes().endswith(b"\n")
    assert first.byte_count == first.output_path.stat().st_size
    assert first.sha256 == sha256(first.output_path.read_bytes()).hexdigest()
    assert first.receipt["schema_version"] == (
        AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION
    )
    assert first.receipt["release_manifest"] == {
        "logical_path": "data/aadr/v66/release_manifest.json",
        "sha256": sha256(manifest_bytes).hexdigest(),
        "byte_count": len(manifest_bytes),
    }
    summary = first.receipt["accountability_projection"]["summary"]
    assert [row["dataset_name"] for row in summary["source_files"]] == [
        "1240k",
        "ho",
    ]
    assert [row["source_path"] for row in summary["source_files"]] == [
        "data/aadr/v66/1240k/v66.1240K.aadr.PUB.anno",
        "data/aadr/v66/ho/v66.HO.aadr.PUB.anno",
    ]
    assert summary["denominators"] == {
        "source_file_count": 2,
        "source_row_count": 2,
        "keyed_source_row_count": 2,
        "unkeyed_source_row_count": 0,
        "genetic_id_count": 2,
        "coordinate_evidence_group_count": 2,
        "chronology_evidence_group_count": 2,
    }
    stream = first.receipt["accountability_projection"]["stream"]
    assert stream["materialized"] is False
    assert stream["tracked"] is False
    assert not tuple(data_root.rglob("*.jsonl"))
    assert not tuple(expected_path.parent.glob("*.writing"))


@pytest.mark.parametrize(
    ("downloaded_files", "message"),
    (
        (
            [
                "ho/v66.HO.aadr.PUB.anno",
                "ho/v66.HO.aadr.PUB.anno",
            ],
            "downloaded_files must be unique",
        ),
        (
            [
                "ho/v66.HO.aadr.PUB.anno",
                "1240k/not-the-declared-panel.anno",
            ],
            "inventory must exactly match",
        ),
        (
            [
                "ho/v66.HO.aadr.PUB.anno",
                "../v66.1240K.aadr.PUB.anno",
            ],
            "not a canonical panel path",
        ),
    ),
)
def test_service_refuses_untrustworthy_downloaded_file_inventory(
    tmp_path: Path,
    downloaded_files: list[str],
    message: str,
) -> None:
    data_root = tmp_path / "data"
    _write_release(data_root, downloaded_files=downloaded_files)

    with pytest.raises(ValueError, match=message):
        materialize_aadr_source_accountability(data_root, "v66")

    assert not (data_root / "adna/species/homo_sapiens/review").exists()


def test_service_refuses_release_identity_before_publication(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    _write_release(data_root, requested_version="v65")

    with pytest.raises(ValueError, match="does not match its release directory"):
        materialize_aadr_source_accountability(data_root, "v66")

    assert not (data_root / "adna/species/homo_sapiens/review").exists()


def test_service_refuses_panel_changed_after_manifest_capture(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    _write_release(data_root)
    panel = data_root / "aadr/v66/ho/v66.HO.aadr.PUB.anno"
    panel.write_bytes(panel.read_bytes() + b"changed\n")

    with pytest.raises(ValueError, match="filesize mismatch"):
        materialize_aadr_source_accountability(data_root, "v66")

    assert not (data_root / "adna/species/homo_sapiens/review").exists()


def test_service_refuses_panel_mutation_between_manifest_validation_and_parse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_root = tmp_path / "data"
    _write_release(data_root)
    panel = data_root / "aadr/v66/ho/v66.HO.aadr.PUB.anno"
    validate_manifest = service.validate_release_manifest_identity

    def validate_then_mutate(payload: object, release_dir: Path) -> None:
        validate_manifest(payload, release_dir)
        original = panel.read_bytes()
        panel.write_bytes(original.replace(b"ID-SE", b"ID-XX", 1))

    monkeypatch.setattr(
        service,
        "validate_release_manifest_identity",
        validate_then_mutate,
    )

    with pytest.raises(ValueError, match="AADR source digest mismatch"):
        materialize_aadr_source_accountability(data_root, "v66")

    assert not (data_root / "adna/species/homo_sapiens/review").exists()


def test_service_requires_manifest_size_and_digest_for_every_panel(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    manifest_path, _manifest_bytes = _write_release(data_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["anno_files"][0].pop("md5")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="requires a valid MD5 digest"):
        materialize_aadr_source_accountability(data_root, "v66")

    assert not (data_root / "adna/species/homo_sapiens/review").exists()


def test_service_refuses_symlinked_panel_ancestor(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    _write_release(data_root)
    panel_dir = data_root / "aadr/v66/ho"
    panel = panel_dir / "v66.HO.aadr.PUB.anno"
    outside_dir = tmp_path / "outside-ho"
    outside_dir.mkdir()
    (outside_dir / panel.name).write_bytes(panel.read_bytes())
    panel.unlink()
    panel_dir.rmdir()
    panel_dir.symlink_to(outside_dir, target_is_directory=True)

    with pytest.raises(ValueError, match="AADR panel cannot use a symlink path"):
        materialize_aadr_source_accountability(data_root, "v66")

    assert not (data_root / "adna/species/homo_sapiens/review").exists()


def test_service_refuses_symlinked_output_ancestor(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    _write_release(data_root)
    outside_dir = tmp_path / "outside-adna"
    outside_dir.mkdir()
    (data_root / "adna").symlink_to(outside_dir, target_is_directory=True)

    with pytest.raises(ValueError, match="output cannot use a symlink"):
        materialize_aadr_source_accountability(data_root, "v66")

    assert not tuple(outside_dir.rglob("aadr_v66_source_accountability.json"))


def test_service_refuses_symlinked_data_root(tmp_path: Path) -> None:
    physical_root = tmp_path / "physical-data"
    _write_release(physical_root)
    data_root = tmp_path / "linked-data"
    data_root.symlink_to(physical_root, target_is_directory=True)

    with pytest.raises(ValueError, match="data root must be a non-symlink directory"):
        materialize_aadr_source_accountability(data_root, "v66")

    assert not (physical_root / "adna/species/homo_sapiens/review").exists()


@pytest.mark.parametrize("version", ("", "../v66", "v66/ho", " v66", "v66\\ho"))
def test_service_refuses_unsafe_release_version(tmp_path: Path, version: str) -> None:
    with pytest.raises(ValueError, match="safe path component"):
        materialize_aadr_source_accountability(tmp_path / "data", version)
