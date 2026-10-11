"""Row payload contracts for public animal atlas readiness."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from bijux_pollenomics.reporting.adna.public_outputs.atlas_readiness import (
    _required_rows,
)


def test_required_rows_accept_read_only_payload_mapping() -> None:
    rows: list[dict[str, object]] = [{"species_latin_name": "Ovis aries"}]
    assert _required_rows(MappingProxyType({"rows": rows}), "rows") is rows


@pytest.mark.parametrize("value", (None, {}, [object()], [{}, object()]))
def test_required_rows_refuse_missing_or_malformed_rows(value: object) -> None:
    with pytest.raises(ValueError, match="must be a list of rows"):
        _required_rows({"rows": value}, "rows")
