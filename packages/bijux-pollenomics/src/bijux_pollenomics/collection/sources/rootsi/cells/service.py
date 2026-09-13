"""Public private-review operations with separate custody and replay claims."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .decoding import parser
from .inputs import bind_capture
from .models import ReviewBundle
from .publication import publish
from .reading import read_bundle, replay_bundle


def prepare_rootsi_cell_review(
    *,
    inventory_path: Path,
    expected_inventory_sha256: str,
    workbook_files: Mapping[str, Path],
    destination: Path,
    scope: str = "selected_workbooks",
) -> ReviewBundle:
    """Decode retained XLS bytes for quarantined review, without scientific admission."""
    capture = bind_capture(
        inventory_path=inventory_path,
        expected_inventory_sha256=expected_inventory_sha256,
        workbook_files=workbook_files,
        scope=scope,
    )
    decoder = parser()
    return publish(capture, destination, decoder)


def read_rootsi_cell_review(
    directory: Path, *, expected_manifest_sha256: str
) -> ReviewBundle:
    """Read pinned internally consistent evidence without importing xlrd."""
    return read_bundle(directory, expected_manifest_sha256)


def replay_rootsi_cell_review(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    inventory_path: Path,
    expected_inventory_sha256: str,
    workbook_files: Mapping[str, Path],
    scope: str = "selected_workbooks",
) -> ReviewBundle:
    """Verify retained rows against workbook bytes; no fresh 7z membership assertion."""
    bundle = read_bundle(directory, expected_manifest_sha256)
    capture = bind_capture(
        inventory_path=inventory_path,
        expected_inventory_sha256=expected_inventory_sha256,
        workbook_files=workbook_files,
        scope=scope,
    )
    replay_bundle(bundle, capture, parser())
    return bundle
