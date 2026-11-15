"""Optional resource metadata shares transport without entering scientific layers."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    validate_static_atlas_assets,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)

from ...map_document.source_resources.catalogue_inputs import (
    atlas_catalogue as atlas_catalogue,
)
from ...map_document.source_resources.catalogue_inputs import (
    catalogue_sources as catalogue_sources,
)
from ...map_document.source_resources.catalogue_inputs import legacy_site


def payloads(assets: Any) -> list[dict[str, Any]]:
    return [
        decode_chunk_script(
            path.read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row["decoded_byte_count"],
        )
        for path, row in zip(
            assets.asset_paths,
            cast(
                list[dict[str, Any]],
                normalize_asset_inventory(assets.manifest["assets"]),
            ),
            strict=True,
        )
    ]


def test_source_metadata_is_lazy_inventoried_and_never_a_scientific_node(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]], tmp_path: Path
) -> None:
    root, digest, _ = atlas_catalogue()
    old = [legacy_site()]
    source = load_atlas_resource_catalogue(
        AtlasResourceCatalogueInput(root, digest), legacy_neotoma_records=old
    )
    before = deepcopy(source)
    plain_root = tmp_path / "plain"
    plain_root.mkdir()
    rich_root = tmp_path / "rich"
    rich_root.mkdir()
    plain = write_static_atlas_assets(
        plain_root,
        slug="nordic",
        version="v66",
        point_layers=[],
        polygon_layers=[],
        detail_records=old,
    )
    rich = write_static_atlas_assets(
        rich_root,
        slug="nordic",
        version="v66",
        point_layers=[],
        polygon_layers=[],
        detail_records=old,
        source_resources=source,
    )
    rows = cast(
        list[dict[str, Any]], normalize_asset_inventory(rich.manifest["assets"])
    )
    manifest = cast(dict[str, Any], rich.manifest)
    resources = [row for row in rows if row["domain"] == "resources"]
    assert resources and all(
        row["initial_load"] is False
        and row["payload_encoding"] == "gzip_base64"
        and row["integrity"].startswith("sha256-")
        for row in resources
    )
    assert manifest["domains"]["resources"]["record_count"] == 4
    assert manifest["domains"]["resources"]["site_count"] == 3
    assert manifest["domains"]["resources"]["catalogue_manifest_sha256"] == digest
    assert source == before
    baseline = [
        {k: v for k, v in p.items() if k != "build_id"} for p in payloads(plain)
    ]
    scientific = [
        {k: v for k, v in p.items() if k != "build_id"}
        for row, p in zip(rows, payloads(rich), strict=True)
        if row["domain"] != "resources"
    ]
    assert scientific == baseline
    assert rich.manifest["build_id"] != plain.manifest["build_id"]
    validate_static_atlas_assets(rich)


def test_absent_optional_resource_input_preserves_static_data_output(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    baseline = write_static_atlas_assets(
        first, slug="nordic", version="v66", point_layers=[], polygon_layers=[]
    )
    explicit = write_static_atlas_assets(
        second,
        slug="nordic",
        version="v66",
        point_layers=[],
        polygon_layers=[],
        source_resources=None,
    )
    assert baseline.manifest == explicit.manifest
    assert [p.read_bytes() for p in baseline.asset_paths] == [
        p.read_bytes() for p in explicit.asset_paths
    ]


def test_actual_bundle_routes_legacy_site_join_to_static_owner(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    from bijux_pollenomics.reporting.bundles import atlas_bundle
    from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
    from bijux_pollenomics.reporting.models import MultiCountryMapReport

    root, digest, _ = atlas_catalogue()
    source = AtlasResourceCatalogueInput(root, digest)
    output = tmp_path / "bundle"
    output.mkdir()
    seen = []

    class ReachedStaticOwner(RuntimeError):
        pass

    def write(*args: Any, **kwargs: Any) -> Any:
        result = write_static_atlas_assets(*args, **kwargs)
        context = next(p for p in payloads(result) if p.get("kind") == "context")[
            "records"
        ][0]
        seen.extend(context["legacy_site_references"])
        raise ReachedStaticOwner()

    monkeypatch.setattr(atlas_bundle, "write_static_atlas_assets", write)
    monkeypatch.setattr(atlas_bundle, "build_sweden_lake_atlas_layers", lambda **_: [])
    with pytest.raises(ReachedStaticOwner):
        atlas_bundle.publish_multi_country_map_bundle(
            output,
            report=MultiCountryMapReport(
                title="Map",
                slug="nordic",
                version="v66",
                generated_on="Fixed",
                countries=("Sweden",),
                country_sample_counts={"Sweden": 0},
                total_unique_samples=0,
                output_dir=output,
            ),
            title="Map",
            version="v66",
            generated_on="Fixed",
            countries=("Sweden",),
            country_sample_counts={"Sweden": 0},
            all_samples=(),
            context_root=None,
            geography_scope=None,
            asset_base_path="_map_assets",
            build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
            build_context_layers_fn=lambda **_: ([], [], []),
            build_multi_country_map_summary_fn=lambda *_, **__: {},
            build_samples_geojson_fn=lambda _: {
                "type": "FeatureCollection",
                "features": [],
            },
            copy_map_assets_fn=lambda _: output,
            write_static_map_document_fn=lambda **_: (
                output / "index.html",
                output / "main.js",
            ),
            render_multi_country_map_markdown_fn=lambda **_: "",
            write_summary_json_fn=lambda *_: None,
            atlas_detail_records=[legacy_site()],
            source_resource_catalogue=source,
        )
    assert seen == [
        {
            "record_id": "neotoma:site:12",
            "site_id": "12",
            "status": "matched",
            "dataset_ids": ["201", "202"],
        }
    ]
