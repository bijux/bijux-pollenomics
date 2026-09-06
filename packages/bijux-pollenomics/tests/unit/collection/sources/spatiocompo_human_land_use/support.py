from __future__ import annotations

import hashlib
from dataclasses import replace

from bijux_pollenomics.collection.sources.spatiocompo_human_land_use.authority import (
    EXPECTED_ROWS_PER_SLICE,
    expected_header,
)
from bijux_pollenomics.collection.sources.spatiocompo_human_land_use.models import (
    ExportFileAuthority,
)

DEFAULT_VALUES = ("0.18", "0.27", "0.55", "0.2", "0.3", "0.5", "0.1")


def fixture_payload(
    authority: ExportFileAuthority,
    *,
    first_values: tuple[str, ...] = DEFAULT_VALUES,
    malformed_first_row: bool = False,
    duplicate_second_coordinate: bool = False,
) -> bytes:
    lines = [",".join(expected_header(authority))]
    for index in range(EXPECTED_ROWS_PER_SLICE):
        if malformed_first_row and index == 0:
            lines.append("57")
            continue
        coordinate_index = 0 if duplicate_second_coordinate and index == 1 else index
        longitude = -10 + coordinate_index % 40
        latitude = 45 + coordinate_index // 40
        values = first_values if index == 0 else DEFAULT_VALUES
        lines.append(",".join((str(longitude), str(latitude), *values)))
    return ("\n".join(lines) + "\n").encode()


def fixture_authority(
    authority: ExportFileAuthority,
    payload: bytes,
    *,
    upstream_status: str = "available",
) -> ExportFileAuthority:
    return replace(
        authority,
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        upstream_status=upstream_status,
    )
