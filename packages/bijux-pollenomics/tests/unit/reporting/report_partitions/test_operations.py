"""Partition APIs validate complete candidates before replacing publication."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.reporting.bundles.report_partitions import (
    generate_report_partition,
)
from bijux_pollenomics.reporting.bundles.report_partitions.models import (
    ReportPartitionResult,
)
from bijux_pollenomics.reporting.geography import GeographicScope
from bijux_pollenomics.reporting.models import MultiCountryMapReport

from .support import generate_map


def test_high_level_partition_api_resolves_runtime_publishers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    version_dir = tmp_path / "source" / "v66"
    version_dir.mkdir(parents=True)
    output_root = tmp_path / "fragment"
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.service.generate_multi_country_map",
        generate_map,
    )

    result = generate_report_partition(
        "world",
        version_dir=version_dir,
        countries=("Sweden", "Norway"),
        output_root=output_root,
        published_output_root=Path("docs/report"),
        context_root=tmp_path / "data",
    )

    assert result.partition.identity == "world"
    assert result.output_root == output_root
    assert result.relative_paths == (
        "world/world_animal_atlas_evidence.json",
        "world/world_map.html",
        "world/world_samples.geojson",
        "world/world_summary.json",
    )


def test_invalid_partition_preserves_previous_complete_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    version = tmp_path / "source" / "v66"
    version.mkdir(parents=True)
    output = tmp_path / "fragment"
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.service.generate_multi_country_map", generate_map
    )

    def generate() -> ReportPartitionResult:
        return generate_report_partition(
            "world",
            version_dir=version,
            countries=("Sweden", "Norway"),
            output_root=output,
            published_output_root=Path("docs/report"),
            context_root=tmp_path / "generated-context",
        )

    generate()
    previous = {
        p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()
    }

    def invalid_map(
        *,
        countries: tuple[str, ...],
        output_dir: Path,
        title: str,
        slug: str,
        published_output_dir: Path,
        geography_scope: GeographicScope,
        **values: object,
    ) -> MultiCountryMapReport:
        result = generate_map(
            countries=countries,
            output_dir=output_dir,
            title=title,
            slug=slug,
            published_output_dir=published_output_dir,
            geography_scope=geography_scope,
            **values,
        )
        (output_dir.parent / "not-owned-by-world.txt").write_text(
            "invalid partition member"
        )
        return result

    monkeypatch.setattr(
        "bijux_pollenomics.reporting.service.generate_multi_country_map", invalid_map
    )
    with pytest.raises(ValueError, match="partition paths differ"):
        generate()
    current = {
        p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()
    }
    assert current == previous
