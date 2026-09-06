"""Canonical acquisition fixtures shared by full-acquisition tests."""

from __future__ import annotations

from datetime import UTC, datetime

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    SeadTableAcquisition,
    acquire_sead_table,
)

from tests.support.repository import REPOSITORY_ROOT

_SCOPE = ("SE", "DK", "NO", "FI")
_BBOX = {"bbox": [4.0, 54.0, 35.0, 72.0], "crs": "EPSG:4326"}
_REPOSITORY_ROOT = REPOSITORY_ROOT


class _Clock:
    def __init__(self) -> None:
        self._values = iter(
            (
                datetime(2026, 9, 4, 10, 0, tzinfo=UTC),
                datetime(2026, 9, 4, 10, 1, tzinfo=UTC),
            )
        )

    def __call__(self) -> datetime:
        return next(self._values)


def _acquire(fetch_json_fn: object) -> SeadTableAcquisition:
    return acquire_sead_table(
        "tbl_sites",
        fetch_json_fn=fetch_json_fn,  # type: ignore[arg-type]
        select="site_id,site_name",
        filters=(("latitude_dd", "gte.54.0"),),
        order_by=("site_id",),
        country_scope=_SCOPE,
        spatial_scope=_BBOX,
        parent_run_id="run-1",
        build_id="build-1",
        page_size=2,
        max_pages=3,
        request_retries=2,
        request_timeout_seconds=5,
        clock=_Clock(),
        sleep_fn=lambda _: None,
    )
