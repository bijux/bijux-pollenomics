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


@pytest.mark.parametrize("invalid_count", [2, True, 1.0])
def test_static_atlas_rejects_manifest_count_ambiguity(
    tmp_path: Path, invalid_count: object
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"]["record_count"] = invalid_count
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="record_count"):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize(
    "invalid_count", [None, -1, 1.5, "1", True, 9_007_199_254_740_992]
)
def test_static_atlas_rejects_invalid_asset_counts(
    tmp_path: Path, invalid_count: object
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"]["records"][0][5] = invalid_count
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="safe integer"):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize("invalid_count", [0, 9_007_199_254_740_992])
def test_static_atlas_rejects_invalid_decoded_byte_count(
    tmp_path: Path, invalid_count: object
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"]["records"][0][3] = invalid_count
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="safe integer"):
        audit_static_atlas(tmp_path, scope, candidate())


def test_static_atlas_rejects_unknown_asset_domain(tmp_path: Path) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"]["records"][0][0] = "unknown"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="identity is malformed"):
        audit_static_atlas(tmp_path, scope, candidate())


def test_static_atlas_rejects_untimed_count_above_total(tmp_path: Path) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["assets"]["records"][0]
    row[0] = "nodes"
    row[8] = "point"
    row[13] = row[5] + 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="exceeds record_count"):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize(
    ("untimed", "minimum", "maximum"),
    [
        (None, 0.0, 100.0),
        (1, 0.0, 100.0),
        (0, None, None),
    ],
)
def test_static_atlas_rejects_node_time_accounting_contradictions(
    tmp_path: Path, untimed: object, minimum: object, maximum: object
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["assets"]["records"][0]
    row[0] = "nodes"
    row[8] = "point"
    row[11] = minimum
    row[12] = maximum
    row[13] = untimed
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize("field", ["untimed_record_count", "time_bounds"])
def test_static_atlas_rejects_non_node_time_selection_metadata(
    tmp_path: Path, field: str
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["assets"]["records"][0]
    if field == "untimed_record_count":
        row[13] = 0
    else:
        row[11] = 0.0
        row[12] = 100.0
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="non-node"):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize(
    ("field_index", "invalid_value", "message"),
    [
        (6, True, "layer_index"),
        (6, -1, "layer_index"),
        (7, "", "layer_key"),
        (8, "heat", "layer_kind"),
        (9, None, "country_keys"),
        (9, ["Sweden", ""], "country_keys"),
        (10, [56, 11, 55, 10], "bounds"),
        (10, [-91, 10, 56, 11], "bounds"),
        (14, None, "scientific_signal_ids"),
        (14, ["signal", ""], "scientific_signal_ids"),
    ],
)
def test_static_atlas_rejects_invalid_node_selection_metadata(
    tmp_path: Path,
    field_index: int,
    invalid_value: object,
    message: str,
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["assets"]["records"][0]
    row[0] = "nodes"
    row[6:15] = [0, "layer", "point", [], None, None, None, row[5], []]
    row[field_index] = invalid_value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match=message):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize("field_index", (6, 7, 8, 9, 10, 14))
def test_static_atlas_rejects_non_node_selection_metadata(
    tmp_path: Path, field_index: int
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"]["records"][0][field_index] = 0
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="non-node selection"):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize(
    ("budget", "invalid_value"),
    [
        ("static_assets_max_files", True),
        ("static_assets_max_files", 1.0),
        ("static_assets_max_files", 9_007_199_254_740_992),
        ("static_assets_max_bytes", True),
        ("static_assets_max_bytes", 4096.0),
        ("static_assets_max_bytes", 9_007_199_254_740_992),
    ],
)
def test_static_atlas_rejects_ambiguous_budgets(
    tmp_path: Path, budget: str, invalid_value: object
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["budgets"][budget] = invalid_value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="safe integer"):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize(
    ("minimum", "maximum", "message"),
    [
        (0.0, None, "asymmetric BP bounds"),
        (None, 100.0, "asymmetric BP bounds"),
        (float("nan"), 100.0, "finite safe number"),
        (0.0, 1e300, "finite safe number"),
        (-1.0, 100.0, "BP bounds are negative or reversed"),
        (200.0, 100.0, "BP bounds are negative or reversed"),
    ],
)
def test_static_atlas_rejects_invalid_time_bounds(
    tmp_path: Path, minimum: object, maximum: object, message: str
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["assets"]["records"][0]
    row[11] = minimum
    row[12] = maximum
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match=message):
        audit_static_atlas(tmp_path, scope, candidate())
