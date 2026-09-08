"""Deterministic published-report partition planning."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace

from ....config import DEFAULT_ATLAS_SLUG, DEFAULT_ATLAS_TITLE
from ...geography import build_published_geography_plan
from ...presentation.text import slugify
from ..country_selection import normalize_requested_countries
from .models import PublishedReportPartitionPlan, ReportPartition


def build_report_partition_plan(
    countries: Iterable[str],
    *,
    title: str = DEFAULT_ATLAS_TITLE,
    slug: str = DEFAULT_ATLAS_SLUG,
    country_group_size: int = 2,
    slugify_fn: Callable[[str], str] = slugify,
) -> PublishedReportPartitionPlan:
    """Build stable world, region, country-group, and foundation partitions."""
    normalized_countries = normalize_requested_countries(countries)
    if not normalized_countries:
        raise ValueError("At least one country is required to partition reports")
    if type(country_group_size) is not int or country_group_size < 1:
        raise ValueError("country_group_size must be a positive integer")

    default_geography = build_published_geography_plan(normalized_countries)
    geography = replace(
        default_geography,
        world_scope=replace(
            default_geography.world_scope,
            slug=slugify_fn(slug),
            map_title=title,
        ),
    )
    scope_partitions: list[ReportPartition] = [
        ReportPartition(
            identity="world",
            kind="world",
            scope_keys=(geography.world_scope.key,),
        )
    ]
    if geography.regional_scopes:
        scope_partitions.append(
            ReportPartition(
                identity="regions",
                kind="regions",
                scope_keys=tuple(scope.key for scope in geography.regional_scopes),
            )
        )
    for group_index, start in enumerate(
        range(0, len(geography.country_scopes), country_group_size)
    ):
        group = geography.country_scopes[start : start + country_group_size]
        scope_partitions.append(
            ReportPartition(
                identity=f"countries-{group_index:03d}",
                kind="countries",
                scope_keys=tuple(scope.key for scope in group),
            )
        )
    foundation = ReportPartition(
        identity="foundation",
        kind="foundation",
        scope_keys=(),
        required_partition_ids=tuple(
            partition.identity for partition in scope_partitions
        ),
    )
    return PublishedReportPartitionPlan(
        geography=geography,
        partitions=(*scope_partitions, foundation),
    )
