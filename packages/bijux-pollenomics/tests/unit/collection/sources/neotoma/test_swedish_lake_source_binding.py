"""The Swedish transfer cannot silently reuse a changed Neotoma snapshot."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[7]
VERIFY = ROOT / "docs/report/regions/nordic/swedish-lake-transfer/verify.py"


@pytest.mark.parametrize("changed", ["manifest", "surface"])
def test_swedish_transfer_refuses_changed_published_source(
    tmp_path: Path, changed: str
) -> None:
    verify_current_source = runpy.run_path(str(VERIFY))["verify_current_source"]
    relational = tmp_path / "data/neotoma/relational"
    surface = relational / "surfaces/observations/part-00001.json"
    surface.parent.mkdir(parents=True)
    manifest = relational / "manifest.json"
    manifest.write_bytes(b"published manifest")
    surface.write_bytes(b"published observations")
    relative = surface.relative_to(tmp_path).as_posix()
    source = {
        "source_manifest_sha256": sha256(manifest.read_bytes()).hexdigest(),
        "source_surface_sha256": {relative: sha256(surface.read_bytes()).hexdigest()},
    }
    verify_current_source(source, tmp_path)

    target = manifest if changed == "manifest" else surface
    target.write_bytes(b"changed published source")
    with pytest.raises(ValueError, match=f"source {changed} changed"):
        verify_current_source(source, tmp_path)
