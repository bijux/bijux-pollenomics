from __future__ import annotations

import pytest

from bijux_pollenomics.reporting.bundles.report_partitions import (
    build_report_partition_plan,
)


def test_plan_groups_countries_deterministically() -> None:
    plan = build_report_partition_plan(
        ("Sweden", "Norway", "Finland", "Denmark"),
        title="Comparative Evidence",
        slug="Comparative Atlas",
        country_group_size=2,
    )

    assert plan.partition_ids == (
        "world",
        "regions",
        "countries-000",
        "countries-001",
        "foundation",
    )
    assert plan.geography.world_scope.slug == "comparative-atlas"
    assert plan.geography.world_scope.map_title == "Comparative Evidence"
    assert plan.partitions[-1].required_partition_ids == plan.partition_ids[:-1]
    assert plan.partitions[2].scope_keys == (
        "country:sweden",
        "country:norway",
    )
    assert plan.partitions[3].scope_keys == (
        "country:finland",
        "country:denmark",
    )


@pytest.mark.parametrize("group_size", (0, -1, True, 1.5))
def test_plan_rejects_invalid_country_group_size(group_size: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        build_report_partition_plan(
            ("Sweden",),
            country_group_size=group_size,  # type: ignore[arg-type]
        )
