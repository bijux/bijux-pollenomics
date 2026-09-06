from __future__ import annotations

import pytest
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    acquire_sead_table,
)

from .support import _BBOX, _SCOPE, _Clock


@pytest.mark.parametrize(
    "table,order_by,country_scope",
    [
        ("../tbl_sites", ("site_id",), _SCOPE),
        ("tbl_sites", (), _SCOPE),
        ("tbl_sites", ("site_id",), ("SE", "DK")),
    ],
)
def test_unsafe_or_ambiguous_acquisition_requests_are_refused(
    table: str, order_by: tuple[str, ...], country_scope: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError):
        acquire_sead_table(
            table,
            fetch_json_fn=lambda *_args, **_kwargs: [],
            select="site_id",
            order_by=order_by,
            country_scope=country_scope,
            spatial_scope=_BBOX,
            parent_run_id="run-1",
            build_id="build-1",
            clock=_Clock(),
        )
