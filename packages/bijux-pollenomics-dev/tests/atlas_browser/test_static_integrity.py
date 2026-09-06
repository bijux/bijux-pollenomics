from __future__ import annotations

import json
from pathlib import Path

import pytest
from bijux_pollenomics_dev.ci.atlas_browser.contracts import AtlasBrowserContractError
from bijux_pollenomics_dev.ci.atlas_browser.static_integrity import audit_static_atlas

from .fixtures import candidate, write_static_atlas


def test_static_atlas_binds_document_manifest_assets_and_provider(
    tmp_path: Path,
) -> None:
    scope = write_static_atlas(tmp_path)

    report = audit_static_atlas(tmp_path, scope, candidate())

    assert report["status"] == "PASS"
    assert report["asset_count"] == 1
    assert report["provider_policy"] == {
        "keyless_osm": True,
        "carto_absent": True,
        "api_key_markers_absent": True,
    }


def test_static_atlas_rejects_asset_tampering(tmp_path: Path) -> None:
    scope = write_static_atlas(tmp_path)
    asset = next((tmp_path / Path(scope.document).parent).glob("*.js"))
    asset.write_text("changed\n", encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="digest mismatch"):
        audit_static_atlas(tmp_path, scope, candidate())


def test_static_atlas_rejects_hidden_provider_credentials(tmp_path: Path) -> None:
    scope = write_static_atlas(tmp_path)
    document = tmp_path / scope.document
    document.write_text(
        document.read_text(encoding="utf-8") + "<!-- API KEY REQUIRED -->",
        encoding="utf-8",
    )

    with pytest.raises(AtlasBrowserContractError, match="provider markers"):
        audit_static_atlas(tmp_path, scope, candidate())


def test_static_atlas_rejects_manifest_count_ambiguity(tmp_path: Path) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"]["record_count"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="record_count"):
        audit_static_atlas(tmp_path, scope, candidate())
