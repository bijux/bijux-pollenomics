"""Generated release mechanics retain independently frozen route authority."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import sys
from typing import Any
from unittest.mock import patch

import pytest

from bijux_pollenomics.adna.sources.library import build_project_registry
from bijux_pollenomics.core import repository
from bijux_pollenomics.reporting import generate_published_reports
from bijux_pollenomics.reporting.bundles.staging import publish_into_staging_dir
from bijux_pollenomics.reporting.presentation.report_portal.publication import (
    publish_report_portal,
)
from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    publish_scientific_routes,
)

from ..fixtures.aadr import write_anno
from ..fixtures.scientific_routes import (
    EXPECTED,
    assert_generated_route_views,
    expected_bytes,
    generated_route_authority,
    write_generated_readers,
)
from ..fixtures.source_library import generated_source_library


def test_stock_production_routes_refuse_generated_mechanical_fixture(
    tmp_path: Path,
) -> None:
    root = tmp_path / "report"
    root.mkdir()
    write_generated_readers(root)
    reader = root / "animal_atlas_exclusion_report.md"
    before = reader.read_bytes()
    with pytest.raises(ValueError, match="Scientific qualification evidence changed"):
        publish_scientific_routes(root)
    assert reader.read_bytes() == before


@pytest.mark.parametrize("damage", ["changed-byte", "foreign-owner"])
def test_same_frozen_authority_refuses_changed_candidate_and_preserves_prior(
    tmp_path: Path, damage: str
) -> None:
    output = tmp_path / "report"
    output.mkdir()
    (output / "prior-complete.txt").write_bytes(b"previous complete publication")
    candidates: list[Path] = []
    with generated_route_authority(output):
        before = {
            path.relative_to(output).as_posix(): path.read_bytes()
            for path in output.rglob("*")
            if path.is_file()
        }

        def publish(root: Path) -> None:
            candidates.append(root)
            write_generated_readers(root)
            evidence = root / "animal_atlas_exclusion_report.json"
            if damage == "changed-byte":
                evidence.write_bytes(evidence.read_bytes() + b" ")
            else:
                evidence.rename(root / "foreign-owner.json")
            publish_report_portal(root)

        with pytest.raises(
            ValueError, match="Scientific qualification evidence changed"
        ):
            publish_into_staging_dir(output, publish)

        assert len(candidates) == 1 and candidates[0] != output
        after = {
            path.relative_to(output).as_posix(): path.read_bytes()
            for path in output.rglob("*")
            if path.is_file()
        }
        assert after == before
        assert all(expected_bytes(name) for name in EXPECTED)


def test_ambient_source_library_body_is_never_opened_by_generated_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ambient = tmp_path / "ambient-workspace"
    metadata = (
        ambient
        / "data/adna/governance/source_library/projects/PRJEB22390/archive_metadata.html.metadata.json"
    )
    metadata.parent.mkdir(parents=True)
    metadata.write_bytes(b"ambient body must not be opened")
    attempted: list[Path] = []
    path_open, native_open = Path.open, os.open

    def reject_ambient(path: Path) -> None:
        if path.absolute().resolve() == metadata:
            attempted.append(path)
            raise AssertionError("Ambient source-library body open")

    def observed_path_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        reject_ambient(path)
        return path_open(path, *args, **kwargs)

    def observed_native_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if isinstance(path, (str, bytes, os.PathLike)):
            location = Path(os.fsdecode(path))
            if not location.is_absolute() and kwargs.get("dir_fd") is not None:
                descriptor = kwargs["dir_fd"]
                if sys.platform == "darwin":
                    parent = fcntl.fcntl(descriptor, 50, bytes(1024)).split(b"\0", 1)[0]
                    location = Path(os.fsdecode(parent)) / location
                else:
                    location = (
                        Path(os.readlink(f"/proc/self/fd/{descriptor}")) / location
                    )
            reject_ambient(location)
        return native_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed_path_open)
    monkeypatch.setattr(os, "open", observed_native_open)
    monkeypatch.setattr(
        os, "supports_dir_fd", os.supports_dir_fd | {observed_native_open}
    )
    for probe in (
        lambda: metadata.read_bytes(),
        lambda: os.open(metadata, os.O_RDONLY),
        lambda: build_project_registry(ambient / "data"),
    ):
        with pytest.raises(AssertionError, match="Ambient source-library body open"):
            probe()
    intentional_probes = len(attempted)
    assert intentional_probes == 3

    version = tmp_path / "v62.0"
    write_anno(
        version / "1240k/v62.0_1240k_public.anno",
        [
            "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF"
        ],
    )
    output = tmp_path / "docs/report"
    with (
        patch.object(repository, "find_repository_root", return_value=ambient),
        generated_source_library(tmp_path / "declared-source-data"),
        generated_route_authority(output),
    ):
        generate_published_reports(
            version_dir=version,
            countries=["Sweden"],
            output_root=output,
            title="Nordic Evidence Atlas",
            slug="nordic-atlas",
        )
        assert_generated_route_views(output)
    assert len(attempted) == intentional_probes
