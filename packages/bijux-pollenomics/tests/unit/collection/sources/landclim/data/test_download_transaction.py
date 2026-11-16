"""Interrupted collection preserves the previous complete source tree."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.landclim import catalog, collection
from tests.unit.collection.sources.landclim.data.test_native_payload_validation import (
    workbook_bytes,
)

FIRST = "landclim_i_land_cover_types.xlsx"
SECOND = "landclim_i_plant_functional_types.xlsx"


@pytest.mark.parametrize("owner", [catalog, collection])
def test_later_fetch_failure_preserves_existing_raw_capture(
    tmp_path: Path, owner: object
) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / FIRST).write_bytes(b"previous source")
    (raw / "landclim_sources.json").write_text("previous receipt")
    (raw / "unrelated.txt").write_text("user work")
    before = {p.name: p.read_bytes() for p in raw.iterdir()}
    with (
        patch.object(
            owner,
            "resolve_landclim_asset_urls",
            return_value={
                FIRST: "https://example.test/first",
                SECOND: "https://example.test/second",
            },
        ),
        patch.object(
            owner,
            "fetch_binary",
            side_effect=[workbook_bytes(), OSError("interrupted provider")],
        ),
        pytest.raises(OSError, match="interrupted provider"),
    ):
        owner.download_landclim_raw_assets(raw)
    assert {p.name: p.read_bytes() for p in raw.iterdir()} == before


@pytest.mark.parametrize("owner", [catalog, collection])
def test_valid_download_replaces_selected_assets_and_keeps_other_files(
    tmp_path: Path, owner: object
) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / FIRST).write_bytes(b"previous source")
    (raw / "unrelated.txt").write_text("user work")
    payload = workbook_bytes()
    with (
        patch.object(
            owner,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test/first"},
        ),
        patch.object(owner, "fetch_binary", return_value=payload),
    ):
        result = owner.download_landclim_raw_assets(raw)
    assert result.paths[FIRST] == raw / FIRST
    assert (raw / FIRST).read_bytes() == payload
    assert (raw / "unrelated.txt").read_text() == "user work"


@pytest.mark.parametrize("owner", [catalog, collection])
def test_source_html_does_not_replace_existing_workbook(
    tmp_path: Path, owner: object
) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / FIRST).write_bytes(b"previous source")
    with (
        patch.object(
            owner,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test/first"},
        ),
        patch.object(owner, "fetch_binary", return_value=b"<html>challenge</html>"),
        pytest.raises(ValueError),
    ):
        owner.download_landclim_raw_assets(raw)
    assert (raw / FIRST).read_bytes() == b"previous source"


def test_normalization_failure_preserves_raw_and_normalized_outputs(
    tmp_path: Path,
) -> None:
    root = tmp_path / "landclim"
    (root / "raw").mkdir(parents=True)
    (root / "normalized").mkdir()
    (root / "raw" / FIRST).write_bytes(b"previous source")
    (root / "normalized" / "result.json").write_text("previous result")
    before = {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test/first"},
        ),
        patch.object(collection, "fetch_binary", return_value=workbook_bytes()),
        patch(
            "bijux_pollenomics.collection.sources.landclim.collection.surfaces.build_landclim_site_records",
            side_effect=ValueError("normalization failed"),
        ),
        pytest.raises(ValueError, match="normalization failed"),
    ):
        collection.collect_landclim_data(root, {}, (0, 0, 1, 1))
    assert {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    } == before


def test_candidate_replacement_during_fetch_never_writes_foreign_tree(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction

    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / FIRST).write_bytes(b"previous source")
    real = transaction.transact
    foreign = None
    current = None

    def intercepted(destination: Path, producer: object, **kwargs: object) -> object:
        def wrap(candidate: Path) -> object:
            nonlocal current
            current = candidate
            return producer(candidate)

        return real(destination, wrap, **kwargs)

    def fetch(url: str) -> bytes:
        nonlocal foreign
        assert current is not None
        current.rename(current.with_name("owned-displaced"))
        current.mkdir()
        foreign = current
        (current / "foreign.txt").write_text("keep foreign")
        return workbook_bytes()

    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test"},
        ),
        patch.object(collection, "fetch_binary", side_effect=fetch),
        patch(
            "bijux_pollenomics.collection.sources.landclim.raw_assets.transact",
            side_effect=intercepted,
        ),
        pytest.raises(ValueError, match="namespace changed"),
    ):
        collection.download_landclim_raw_assets(raw)
    assert (raw / FIRST).read_bytes() == b"previous source"
    assert (
        foreign is not None and (foreign / "foreign.txt").read_text() == "keep foreign"
    )
    assert not (foreign / FIRST).exists()


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_unsafe_existing_entries_are_refused_before_fetch(
    tmp_path: Path, kind: str
) -> None:
    import os

    raw = tmp_path / "raw"
    raw.mkdir()
    protected = tmp_path / "protected"
    protected.write_bytes(b"protected")
    if kind == "symlink":
        (raw / FIRST).symlink_to(protected)
    elif kind == "hardlink":
        os.link(protected, raw / FIRST)
    else:
        os.mkfifo(raw / FIRST)

    def fetch(url: str) -> bytes:
        raise AssertionError("unsafe tree reached provider")

    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test"},
        ),
        patch.object(collection, "fetch_binary", side_effect=fetch),
        pytest.raises(ValueError, match="links or special"),
    ):
        collection.download_landclim_raw_assets(raw)
    assert protected.read_bytes() == b"protected"


def test_publication_failure_restores_predecessor(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction

    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / FIRST).write_bytes(b"previous source")
    rename = transaction._rename_no_replace

    def fail_candidate(source: str, target: str, **kwargs: object) -> None:
        if source == "candidate":
            raise OSError("synthetic publication refusal")
        rename(source, target, **kwargs)

    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test"},
        ),
        patch.object(collection, "fetch_binary", return_value=workbook_bytes()),
        patch.object(transaction, "_rename_no_replace", side_effect=fail_candidate),
        pytest.raises(OSError, match="publication refusal"),
    ):
        collection.download_landclim_raw_assets(raw)
    assert (raw / FIRST).read_bytes() == b"previous source"


def test_foreign_candidate_at_publication_is_retained_and_prior_restored(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction

    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / FIRST).write_bytes(b"previous source")
    rename = transaction.os.rename
    publish = transaction._rename_no_replace

    def substitute(source: str, target: str, **kwargs: object) -> None:
        if source == "candidate":
            run_fd = kwargs["src_dir_fd"]
            rename("candidate", "owned-displaced", src_dir_fd=run_fd, dst_dir_fd=run_fd)
            transaction.os.mkdir("candidate", dir_fd=run_fd)
            handle = transaction.os.open(
                "candidate/foreign.txt",
                transaction.os.O_WRONLY
                | transaction.os.O_CREAT
                | transaction.os.O_EXCL,
                0o600,
                dir_fd=run_fd,
            )
            transaction.os.write(handle, b"foreign")
            transaction.os.close(handle)
        publish(source, target, **kwargs)

    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test"},
        ),
        patch.object(collection, "fetch_binary", return_value=workbook_bytes()),
        patch.object(transaction, "_rename_no_replace", side_effect=substitute),
        pytest.raises(ValueError, match="rename source changed"),
    ):
        collection.download_landclim_raw_assets(raw)
    assert (raw / FIRST).read_bytes() == b"previous source"


@pytest.mark.parametrize("fail_writer", [False, True])
def test_complete_collection_preserves_previous_products_until_all_writers_finish(
    tmp_path: Path, fail_writer: bool
) -> None:
    from bijux_pollenomics.collection.sources.landclim.collection import surfaces

    root = tmp_path / "landclim"
    (root / "normalized").mkdir(parents=True)
    (root / "normalized" / "prior.txt").write_text("previous result")
    (root / "user.txt").write_text("user work")
    before = {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test"},
        ),
        patch.object(collection, "fetch_binary", return_value=workbook_bytes()),
        patch.object(
            collection,
            "_build_landclim_raw_receipt",
            return_value={"role": "synthetic fixture"},
        ),
        patch.object(collection, "validate_landclim_raw_receipt", return_value={}),
        patch.object(surfaces, "build_landclim_site_records", return_value=[]),
        patch.object(
            surfaces,
            "build_landclim_grid_geojson",
            return_value={"type": "FeatureCollection", "features": []},
        ),
        patch.object(
            surfaces,
            "build_landclim_temporal_grid_geojson",
            return_value={"type": "FeatureCollection", "features": []},
        ),
    ):
        if fail_writer:
            with (
                patch.object(
                    surfaces,
                    "write_context_points_geojson",
                    side_effect=ValueError("writer failed"),
                ),
                pytest.raises(ValueError, match="writer failed"),
            ):
                collection.collect_landclim_data(root, {}, (0, 0, 1, 1))
            assert {
                str(p.relative_to(root)): p.read_bytes()
                for p in root.rglob("*")
                if p.is_file()
            } == before
        else:
            report = collection.collect_landclim_data(root, {}, (0, 0, 1, 1))
            assert report.output_dir == root
            assert report.raw_manifest_path == root / "raw" / "landclim_sources.json"
            assert report.summary_path.is_file()
            assert report.normalized_sites_csv_path.is_file()
            assert (root / "normalized" / "prior.txt").read_text() == "previous result"
            assert (root / "user.txt").read_text() == "user work"
            for product in root.rglob("*"):
                if product.is_file() and product.suffix in (".json", ".csv", ".md"):
                    assert (
                        "artifacts/landclim-collection/capture-"
                        not in product.read_text()
                    )


@pytest.mark.parametrize("prior", [False, True])
def test_foreign_final_replacement_is_never_moved_during_recovery(
    tmp_path: Path, prior: bool
) -> None:
    from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction

    root = tmp_path / "destination"
    if prior:
        root.mkdir()
        (root / "previous.txt").write_text("previous")
    rename = transaction._rename_no_replace
    foreign_inode = None

    def substitute(source: str, target: str, **kwargs: object) -> None:
        nonlocal foreign_inode
        rename(source, target, **kwargs)
        if source == "candidate":
            root.rename(tmp_path / "owned-displaced")
            root.mkdir()
            (root / "foreign.txt").write_text("foreign user work")
            foreign_inode = root.stat().st_ino

    with (
        patch.object(transaction, "_rename_no_replace", side_effect=substitute),
        pytest.raises(ValueError, match="publication changed"),
    ):
        transaction.transact(
            root, lambda candidate: (candidate / "new.txt").write_text("new")
        )
    assert root.stat().st_ino == foreign_inode
    assert (root / "foreign.txt").read_text() == "foreign user work"


def test_growing_source_reads_only_declared_size_and_sentinel(tmp_path: Path) -> None:
    import os

    from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction

    source = tmp_path / "source.bin"
    source.write_bytes(b"x")
    read = os.read
    observed = 0

    def growing(fd: int, size: int) -> bytes:
        nonlocal observed
        if observed == 0:
            with source.open("r+b") as stream:
                stream.truncate(257 * 1024 * 1024)
        block = read(fd, size)
        observed += len(block)
        return block

    directory = os.open(tmp_path, transaction.DIRECTORY)
    try:
        with (
            patch.object(transaction.os, "read", side_effect=growing),
            pytest.raises(ValueError),
        ):
            transaction._tree(directory)
    finally:
        os.close(directory)
        source.unlink()
    assert observed <= 2


@pytest.mark.parametrize("prior", [False, True])
def test_foreign_empty_destination_at_publication_is_never_replaced(
    tmp_path: Path, prior: bool
) -> None:
    from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction

    root = tmp_path / "destination"
    if prior:
        root.mkdir()
        (root / "previous.txt").write_text("previous")
    rename = transaction._rename_no_replace
    foreign_inode = None

    def inject(source: str, target: str, **kwargs: object) -> None:
        nonlocal foreign_inode
        if source == "candidate":
            root.mkdir()
            foreign_inode = root.stat().st_ino
        rename(source, target, **kwargs)

    with (
        patch.object(transaction, "_rename_no_replace", side_effect=inject),
        pytest.raises(FileExistsError),
    ):
        transaction.transact(
            root, lambda candidate: (candidate / "new.txt").write_text("new")
        )
    assert root.stat().st_ino == foreign_inode
    assert not (root / "new.txt").exists()
