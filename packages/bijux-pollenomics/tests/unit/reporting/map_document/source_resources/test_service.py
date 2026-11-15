"""Explicit catalogue dependencies reach public map and report-tree dispatch."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.reporting import service
from bijux_pollenomics.reporting.bundles import published_reports
from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.bundles.report_partitions.planning import (
    build_report_partition_plan,
)
from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogueInput,
)
from bijux_pollenomics.reporting.models import MultiCountryMapReport

from .conftest import atlas_catalogue as atlas_catalogue
from .conftest import catalogue_sources as catalogue_sources


class _ReachedRoutingBoundary(RuntimeError):
    pass


def test_public_map_forwards_explicit_typed_catalogue(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, digest, _ = atlas_catalogue()
    source = AtlasResourceCatalogueInput(root, digest)
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts={"Sweden": 0}, all_samples=()
        ),
    )
    observed = []

    def publish(*_: Any, **kwargs: Any) -> None:
        observed.append(kwargs["source_resource_catalogue"])
        raise _ReachedRoutingBoundary()

    monkeypatch.setattr(service, "publish_multi_country_map_bundle", publish)
    with pytest.raises(_ReachedRoutingBoundary):
        service.generate_multi_country_map(
            tmp_path / "v66",
            ("Sweden",),
            tmp_path / "atlas",
            "Map",
            "nordic",
            source_resource_catalogue=source,
        )
    assert observed == [source]


def test_report_tree_forwards_one_catalogue_to_every_map_scope(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]], tmp_path: Path
) -> None:
    root, digest, _ = atlas_catalogue()
    source = AtlasResourceCatalogueInput(root, digest)
    countries = ("Denmark", "Finland", "Norway", "Sweden")
    plan = build_report_partition_plan(
        countries, title="Map", slug="atlas", slugify_fn=lambda s: s.lower()
    ).geography
    expected = {scope.key for scope in (plan.world_scope, *plan.regional_scopes)}
    observed = {}

    def generate(**kwargs: Any) -> MultiCountryMapReport:
        scope = kwargs["geography_scope"]
        observed[scope.key] = kwargs.get("source_resource_catalogue")
        if len(observed) == len(expected):
            raise _ReachedRoutingBoundary()
        return MultiCountryMapReport(
            title=kwargs["title"],
            slug=kwargs["slug"],
            version="v66",
            generated_on="2026-11-15",
            countries=scope.countries,
            country_sample_counts=dict.fromkeys(scope.countries, 0),
            total_unique_samples=0,
            output_dir=kwargs["published_output_dir"],
            scope_key=scope.key,
            scope_label=scope.label,
            scope_kind=scope.kind,
            parent_scope_key=scope.parent_key,
        )

    with pytest.raises(_ReachedRoutingBoundary):
        published_reports.publish_published_reports_tree(
            tmp_path / "staging",
            version_dir=tmp_path / "v66",
            output_root=tmp_path / "reports",
            normalized_countries=countries,
            title="Map",
            atlas_slug="atlas",
            context_root=None,
            build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
            build_published_reports_summary_fn=lambda **_: {},
            generate_country_report_fn=lambda **_: object(),
            generate_multi_country_map_fn=generate,
            slugify_fn=lambda s: s.lower(),
            write_summary_json_fn=lambda *_: None,
            source_resource_catalogue=source,
        )
    assert set(observed) == expected
    assert all(value is source for value in observed.values())


def test_wrong_catalogue_pin_preserves_prior_map_publication(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.reporting.bundles import atlas_bundle

    root, _, _ = atlas_catalogue()
    source = AtlasResourceCatalogueInput(root, "0" * 64)
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts={"Sweden": 0}, all_samples=()
        ),
    )
    monkeypatch.setattr(service, "build_context_layers", lambda **_: ([], [], []))
    monkeypatch.setattr(atlas_bundle, "build_sweden_lake_atlas_layers", lambda **_: [])
    output = tmp_path / "prior"
    output.mkdir()
    marker = output / "user-work"
    marker.write_text("keep")
    with pytest.raises(ValueError, match="manifest identity"):
        service.generate_multi_country_map(
            tmp_path / "v66",
            ("Sweden",),
            output,
            "Map",
            "nordic",
            source_resource_catalogue=source,
        )
    assert list(output.iterdir()) == [marker]
    assert marker.read_text() == "keep"


def test_public_map_publishes_separate_metadata_contract_without_sample_promotion(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    from bijux_pollenomics.reporting.bundles import atlas_bundle

    root, digest, _ = atlas_catalogue()
    source = AtlasResourceCatalogueInput(root, digest)
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts={"Sweden": 0}, all_samples=()
        ),
    )
    monkeypatch.setattr(service, "build_context_layers", lambda **_: ([], [], []))
    monkeypatch.setattr(atlas_bundle, "build_sweden_lake_atlas_layers", lambda **_: [])
    output = tmp_path / "published"
    report = service.generate_multi_country_map(
        tmp_path / "v66",
        ("Sweden",),
        output,
        "Metadata context",
        "nordic",
        source_resource_catalogue=source,
    )
    assert report.total_unique_samples == 0
    contracts = list(output.glob("*map_publication_contract.json"))
    assert len(contracts) == 1
    contract = json.loads(contracts[0].read_bytes())
    assert contract["source_resources"]["catalogue_manifest_sha256"] == digest
    assert contract["source_resources"]["record_count"] == 4
    assert contract["source_resources"]["site_count"] == 3
    assert contract["source_resources"]["numerical_atlas_denominator_changed"] is False
    assert (output / "nordic_map.html").is_file()
