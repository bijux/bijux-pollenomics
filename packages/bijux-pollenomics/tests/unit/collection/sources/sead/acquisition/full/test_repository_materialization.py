from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.sead import collection as production_sead

from .support import _REPOSITORY_ROOT


def test_production_archive_is_deterministic_and_refuses_changed_overwrite(
    tmp_path: Path,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    rows = [{"site_id": 1, "site_name": "A"}]
    path = production_sead._write_sead_site_archive(
        raw_dir,
        bbox=(4.0, 54.0, 35.0, 72.0),
        rows=rows,
        inventory_summary={"site_row_count": 1},
    )
    original = path.read_bytes()
    payload = json.loads(original)

    assert payload["schema_version"] == "sead-site-archive.v2"
    assert "generated_on" not in payload
    assert payload["source_snapshot_id"].startswith("sha256:")
    assert (
        production_sead._write_sead_site_archive(
            raw_dir,
            bbox=(4.0, 54.0, 35.0, 72.0),
            rows=rows,
            inventory_summary={"site_row_count": 1},
        ).read_bytes()
        == original
    )
    with pytest.raises(FileExistsError, match="Non-identical"):
        production_sead._write_sead_site_archive(
            raw_dir,
            bbox=(4.0, 54.0, 35.0, 72.0),
            rows=[{"site_id": 2, "site_name": "B"}],
            inventory_summary={"site_row_count": 1},
        )


def test_production_archive_canonicalizes_site_order(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    rows = [{"site_id": 2}, {"site_id": 1}]

    first = production_sead._write_sead_site_archive(
        first_dir,
        bbox=(4.0, 54.0, 35.0, 72.0),
        rows=rows,  # type: ignore[arg-type]
        inventory_summary={"site_row_count": 2},
    )
    second = production_sead._write_sead_site_archive(
        second_dir,
        bbox=(4.0, 54.0, 35.0, 72.0),
        rows=list(reversed(rows)),  # type: ignore[arg-type]
        inventory_summary={"site_row_count": 2},
    )

    assert first.read_bytes() == second.read_bytes()


def test_repository_materializer_rejects_non_object_raw_rows(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "sead" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "nordic_sites.json").write_text(
        json.dumps({"rows": [{"site_id": 1}, "not-an-object"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="contains a non-object row"):
        production_sead.materialize_sead_repository_surfaces(tmp_path / "data")


def test_repository_materializer_rejects_unbound_governed_admission(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    raw_dir = data_root / "sead" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "nordic_sites.json").write_text(
        json.dumps({"rows": []}), encoding="utf-8"
    )
    admission_path = (
        raw_dir
        / "acquisitions"
        / production_sead.SEAD_GOVERNED_ACQUISITION_ID
        / "admission.json"
    )
    admission_path.parent.mkdir(parents=True)
    admission_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="admission identity changed"):
        production_sead.materialize_sead_repository_surfaces(data_root)


def test_governed_admission_rejects_symlinked_raw_payload_tree(
    tmp_path: Path,
) -> None:
    source = (
        _REPOSITORY_ROOT
        / "data/sead/raw/acquisitions"
        / production_sead.SEAD_GOVERNED_ACQUISITION_ID
    )
    data_root = tmp_path / "data"
    mirror = (
        data_root
        / "sead/raw/acquisitions"
        / production_sead.SEAD_GOVERNED_ACQUISITION_ID
    )
    mirror.mkdir(parents=True)
    (mirror / "admission.json").write_bytes((source / "admission.json").read_bytes())
    (mirror / "country-decisions.json").symlink_to(source / "country-decisions.json")

    with pytest.raises(ValueError, match="symlink"):
        production_sead.validate_governed_sead_admission(  # type: ignore[attr-defined]
            mirror,
            data_root=data_root,
        )
