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


def test_static_atlas_accepts_previous_manifest_without_chronology_split(
    tmp_path: Path,
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    table = manifest["assets"]
    table["schema_version"] = "atlas-static-asset-table.v2"
    del table["fields"][14:17]
    del table["records"][0][14:17]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = audit_static_atlas(tmp_path, scope, candidate())

    assert report["status"] == "PASS"


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
    row[14:17] = [row[13], 0, 0]
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
    if isinstance(untimed, int) and not isinstance(untimed, bool):
        row[14:17] = [untimed, 0, 0]
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
        (17, None, "scientific_signal_ids"),
        (17, ["signal", ""], "scientific_signal_ids"),
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
    row[6:18] = [
        0,
        "layer",
        "point",
        [],
        None,
        None,
        None,
        row[5],
        row[5],
        0,
        0,
        [],
    ]
    row[field_index] = invalid_value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match=message):
        audit_static_atlas(tmp_path, scope, candidate())


@pytest.mark.parametrize("field_index", (6, 7, 8, 9, 10, 14, 15, 16, 17))
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
    "split",
    ([None, 0, 0], [1, 1, 0], [-1, 1, 1], [True, 0, 0]),
)
def test_static_atlas_rejects_invalid_node_chronology_split(
    tmp_path: Path, split: list[object]
) -> None:
    scope = write_static_atlas(tmp_path)
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["assets"]["records"][0]
    row[0] = "nodes"
    row[6:18] = [
        0,
        "layer",
        "point",
        [],
        None,
        None,
        None,
        1,
        *split,
        [],
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AtlasBrowserContractError, match="chronology"):
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


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "default_profile",
        "wrong_profile",
        "git_candidate",
        "bootstrap_axis",
        "view_profile",
        "invalid_json",
        "view_hash",
        "table_schema",
        "table_axis",
        "table_extra",
        "node_schema",
        "count_bool",
        "unsafe_extent",
        "overflow_integer",
    ],
)
def test_signed_static_requires_explicit_content_bound_profile(
    tmp_path: Path, mutation: str | None
) -> None:
    from dataclasses import replace
    import hashlib

    from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
        SIGNED_NATIVE_LRA_PROFILE,
        AtlasArtifactCandidate,
    )

    original_scope = write_static_atlas(tmp_path / "artifacts")
    scope = replace(
        original_scope,
        document="artifacts/" + original_scope.document,
        manifest="artifacts/" + original_scope.manifest,
    )
    folder = (tmp_path / scope.document).parent
    manifest_path = tmp_path / scope.manifest
    manifest = json.loads(manifest_path.read_bytes())
    temporal = {
        "temporal_profile": "calendar-bp1950-signed.v1",
        "temporal_axis": "BP1950",
    }
    view = {"schema_version": "lra-atlas-view.v2", **temporal}
    if mutation == "view_profile":
        view["temporal_profile"] = "radiocarbon"
    view_bytes = b"{" if mutation == "invalid_json" else json.dumps(view).encode()
    (folder / "native-view.json").write_bytes(view_bytes)
    view_sha = hashlib.sha256(view_bytes).hexdigest()
    presentation = {
        "schema_version": "lra-presentation.v2",
        **temporal,
        "native_view_sha256": view_sha,
        "files": {"native-view.json": view_sha},
    }
    presentation_bytes = json.dumps(presentation).encode()
    (folder / "manifest.json").write_bytes(presentation_bytes)
    manifest.update(
        schema_version="atlas-static-bootstrap.v3",
        native_view_sha256=view_sha,
        **temporal,
    )
    manifest["compatibility"] = {
        "node_schema": "atlas-node-chunk.v2",
        "index_schema": "atlas-static-indexes.v4",
    }
    table = manifest["assets"]
    table.update(schema_version="atlas-static-asset-table.v4", **temporal)
    if mutation == "bootstrap_axis":
        manifest["temporal_axis"] = "CE"
    if mutation == "view_hash":
        manifest["native_view_sha256"] = "0" * 64
    if mutation == "table_schema":
        table["schema_version"] = "atlas-static-asset-table.v3"
    if mutation == "table_axis":
        table["temporal_axis"] = "CE"
    if mutation == "table_extra":
        table["unbound"] = True
    if mutation == "node_schema":
        manifest["compatibility"]["node_schema"] = "atlas-node-chunk.v1"
    if mutation == "count_bool":
        table["records"][0][table["fields"].index("record_count")] = True
    if mutation in {"unsafe_extent", "overflow_integer"}:
        value = -(10**1000) if mutation == "overflow_integer" else -(2**53)
        table["records"][0][table["fields"].index("time_min_bp")] = value
        table["records"][0][table["fields"].index("time_max_bp")] = value
    manifest_path.write_text(json.dumps(manifest))
    artifact = AtlasArtifactCandidate(
        build_id=candidate().build_id,
        generator_repository_head="a" * 40,
        generator_repository_tree="b" * 40,
        generator_receipt="artifacts/receipt.json",
        generator_receipt_sha256="c" * 64,
        presentation_root=folder.relative_to(tmp_path).as_posix(),
        presentation_manifest_sha256=hashlib.sha256(presentation_bytes).hexdigest(),
        presentation_inventory_sha256="d" * 64,
        product_manifest_sha256="e" * 64,
        display_geometry_sha256="f" * 64,
    )
    profile = (
        None
        if mutation == "default_profile"
        else "unknown"
        if mutation == "wrong_profile"
        else SIGNED_NATIVE_LRA_PROFILE
    )
    if mutation:
        with pytest.raises(AtlasBrowserContractError):
            audit_static_atlas(
                tmp_path,
                scope,
                candidate() if mutation == "git_candidate" else artifact,
                verification_profile=profile,
            )
    else:
        report = audit_static_atlas(
            tmp_path, scope, artifact, verification_profile=profile
        )
        assert report["status"] == "PASS"
        assert report["asset_count"] == 1
