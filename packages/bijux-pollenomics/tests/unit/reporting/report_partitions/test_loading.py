from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.bundles.report_partitions.loading import (
    load_scope_reports,
)
from bijux_pollenomics.reporting.bundles.report_partitions.planning import (
    build_report_partition_plan,
)

from .support import generate_country, generate_map


def test_loading_rejects_mixed_map_versions(tmp_path: Path) -> None:
    plan = build_report_partition_plan(("Sweden", "Norway"))
    for scope in (
        plan.geography.world_scope,
        *plan.geography.regional_scopes,
    ):
        generate_map(
            countries=scope.countries,
            output_dir=tmp_path.joinpath(*scope.output_dir_parts),
            published_output_dir=tmp_path.joinpath(*scope.output_dir_parts),
            title=scope.map_title,
            slug=scope.slug,
            geography_scope=scope,
        )
    for scope in plan.geography.country_scopes:
        generate_country(
            country=scope.countries[0],
            output_dir=tmp_path.joinpath(*scope.output_dir_parts),
            published_output_dir=tmp_path.joinpath(*scope.output_dir_parts),
            map_reference=("fixture", "map.html"),
        )

    regional_scope = plan.geography.regional_scopes[0]
    regional_summary = tmp_path.joinpath(
        *regional_scope.output_dir_parts,
        f"{regional_scope.slug}_summary.json",
    )
    payload = json.loads(regional_summary.read_text(encoding="utf-8"))
    payload["version"] = "v67"
    regional_summary.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Map summary version differs from plan"):
        load_scope_reports(tmp_path, plan=plan, version="v66")
