"""Context byte custody never grants ownership of an equal-byte competing tree."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
    publication,
)
from bijux_pollenomics.core.filesystem import OwnedTreeWriter


@pytest.mark.parametrize(
    "boundary", ["after_attachment_check", "after_final_validator"]
)
def test_publication_refuses_equal_byte_foreign_root(
    site_context_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    inputs = site_context_products()
    final, staging = tmp_path / "published", tmp_path / ".published.staging"
    retained = tmp_path / "retained-owned-inode"
    stage_validated = replaced = False
    load = publication.load_neotoma_context_resource_archive
    attachment = OwnedTreeWriter.validate_attachment

    def swap(path: Path) -> None:
        nonlocal replaced
        path.rename(retained)
        shutil.copytree(retained, path)
        replaced = True
        assert retained.stat().st_ino != path.stat().st_ino
        assert (retained / "manifest.json").read_bytes() == (
            path / "manifest.json"
        ).read_bytes()

    def validated(path: Path, **kwargs: Any) -> dict[str, Any]:
        nonlocal stage_validated
        result = load(path, **kwargs)
        if path == staging:
            stage_validated = True
        elif path == final and boundary == "after_final_validator":
            swap(path)
        return result

    def attached(writer: OwnedTreeWriter) -> None:
        attachment(writer)
        if (
            writer.root == staging
            and stage_validated
            and not replaced
            and boundary == "after_attachment_check"
        ):
            swap(staging)

    monkeypatch.setattr(publication, "load_neotoma_context_resource_archive", validated)
    monkeypatch.setattr(OwnedTreeWriter, "validate_attachment", attached)
    with pytest.raises(ValueError, match="identity|inode|attachment"):
        publication.write_neotoma_context_resource_archive(final, **inputs["writer"])
    assert replaced and retained.is_dir()
    foreign = staging if boundary == "after_attachment_check" else final
    assert foreign.is_dir()
    if boundary == "after_attachment_check":
        assert not final.exists()
