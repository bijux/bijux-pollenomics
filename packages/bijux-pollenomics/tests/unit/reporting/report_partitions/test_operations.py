from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.reporting.bundles.report_partitions import (
    generate_report_partition,
)

from .support import generate_map


def test_high_level_partition_api_resolves_runtime_publishers(
    tmp_path: Path, monkeypatch
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
