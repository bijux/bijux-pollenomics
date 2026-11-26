"""Historical source selection binds both the predecessor and current custody."""

from pathlib import Path
import shutil

import pytest

from bijux_pollenomics.collection.sources.landclim.collection.receipt.predecessor import (
    capture_predecessor_assets,
)
from bijux_pollenomics.collection.sources.landclim.published_inventory import (
    LandClimPublishedInventoryRefusal,
    read_landclim_published_inventory,
    reopen_landclim_published_inventory,
)
from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    LandClimStudyInventoryRefusal,
    read_landclim_study_inventory,
    reopen_landclim_study_inventory,
)
from tests.support.repository import REPOSITORY_ROOT

RAW = REPOSITORY_ROOT / "data/landclim/raw"
PREDECESSOR = REPOSITORY_ROOT / "data/landclim/provenance/landclim-raw-predecessor.json"
READERS = (read_landclim_study_inventory, read_landclim_published_inventory)


def test_explicit_predecessor_reproduces_retained_inventories() -> None:
    study = read_landclim_study_inventory(RAW, predecessor_receipt=PREDECESSOR)
    published = read_landclim_published_inventory(RAW, predecessor_receipt=PREDECESSOR)
    assert (
        study.receipt_sha256
        == published.receipt_sha256
        == ("eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677")
    )
    assert not study.scientifically_accepted
    assert not study.publication_allowed
    assert not published.scientifically_accepted
    assert not published.publication_allowed
    assert (
        study.sha256
        == "8b9ed4fa38d895cd4a83e8ee50d9b0eedd1be5d3a21009928fa9c1d88618b83a"
    )
    assert (
        published.sha256
        == "0333fec471bcf4c0fcd173de006a2efebe3f9fda545c4f0893bf10e288417c23"
    )
    assert len(study.records) == 1128
    assert len(published.records) == 10500
    assert (
        reopen_landclim_study_inventory(
            study.canonical_bytes, RAW, predecessor_receipt=PREDECESSOR
        )
        == study
    )
    assert (
        reopen_landclim_published_inventory(
            published.canonical_bytes, RAW, predecessor_receipt=PREDECESSOR
        )
        == published
    )


@pytest.mark.parametrize("reader", READERS)
def test_default_does_not_implicitly_select_predecessor(reader: object) -> None:
    with pytest.raises(
        (LandClimStudyInventoryRefusal, LandClimPublishedInventoryRefusal)
    ):
        reader(RAW)  # type: ignore[operator]


@pytest.mark.parametrize(
    "member",
    [
        "landclim_ii_contributors.xlsx",
        "landclim_ii_site_metadata.xlsx",
        "landclim_sources.json",
    ],
)
def test_predecessor_selection_refuses_changed_current_members(
    tmp_path: Path, member: str
) -> None:
    root = tmp_path / "raw"
    shutil.copytree(RAW, root)
    path = root / member
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError):
        read_landclim_study_inventory(root, predecessor_receipt=PREDECESSOR)


def test_predecessor_selection_refuses_changed_historical_receipt(
    tmp_path: Path,
) -> None:
    predecessor = tmp_path / "receipt.json"
    predecessor.write_bytes(PREDECESSOR.read_bytes() + b" ")
    with pytest.raises(ValueError):
        read_landclim_study_inventory(RAW, predecessor_receipt=predecessor)


def test_predecessor_selection_refuses_aliased_receipt(tmp_path: Path) -> None:
    predecessor = tmp_path / "receipt.json"
    predecessor.symlink_to(PREDECESSOR)
    with pytest.raises(LandClimStudyInventoryRefusal):
        read_landclim_study_inventory(RAW, predecessor_receipt=predecessor)


def test_predecessor_selection_refuses_unlisted_current_member(tmp_path: Path) -> None:
    root = tmp_path / "raw"
    shutil.copytree(RAW, root)
    (root / "unlisted.json").write_text("{}")
    with pytest.raises(ValueError):
        read_landclim_study_inventory(root, predecessor_receipt=PREDECESSOR)


def test_legacy_seven_asset_root_still_uses_default_reader(tmp_path: Path) -> None:
    root = tmp_path / "raw"
    shutil.copytree(RAW, root)
    (root / "landclim_ii_contributors.xlsx").unlink()
    (root / "landclim_sources.json").write_bytes(PREDECESSOR.read_bytes())
    assert (
        read_landclim_study_inventory(root).sha256
        == "8b9ed4fa38d895cd4a83e8ee50d9b0eedd1be5d3a21009928fa9c1d88618b83a"
    )
    assert (
        read_landclim_published_inventory(root).sha256
        == "0333fec471bcf4c0fcd173de006a2efebe3f9fda545c4f0893bf10e288417c23"
    )


@pytest.mark.parametrize("kind", ["study", "published"])
def test_consumer_parses_captured_bytes_after_source_is_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    from bijux_pollenomics.collection.sources.landclim.published_inventory import (
        reading as published,
    )
    from bijux_pollenomics.collection.sources.landclim.study_inventory import (
        reading as study,
    )

    root = tmp_path / "raw"
    shutil.copytree(RAW, root)
    owner = study if kind == "study" else published

    def capture(raw_dir: Path, predecessor: Path) -> dict[str, bytes]:
        retained = capture_predecessor_assets(raw_dir, predecessor)
        member = (
            "landclim_ii_site_metadata.xlsx"
            if kind == "study"
            else "landclim_ii_reveals_results.zip"
        )
        (root / member).write_bytes(b"replacement")
        return retained

    monkeypatch.setattr(owner, "capture_predecessor_assets", capture)
    result = (
        owner.read_landclim_study_inventory(root, predecessor_receipt=PREDECESSOR)
        if kind == "study"
        else owner.read_landclim_published_inventory(
            root, predecessor_receipt=PREDECESSOR
        )
    )
    expected = (
        "8b9ed4fa38d895cd4a83e8ee50d9b0eedd1be5d3a21009928fa9c1d88618b83a"
        if kind == "study"
        else "0333fec471bcf4c0fcd173de006a2efebe3f9fda545c4f0893bf10e288417c23"
    )
    assert result.sha256 == expected
