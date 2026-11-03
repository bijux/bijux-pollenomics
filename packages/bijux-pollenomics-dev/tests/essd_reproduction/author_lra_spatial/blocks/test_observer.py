"""Independent source joins and exact support bounds meet at the real consumer."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.blocks.audit import (
    audit_block_screen,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.blocks.inputs import (
    load_block_inputs,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.blocks.observer import (
    bind_metadata,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.blocks.screen import (
    screen_blocks,
)

from .test_inputs import _fixture


def test_original_sources_screen_and_independent_certificate_integrate(
    tmp_path: Path,
) -> None:
    args = _fixture(tmp_path)
    packet = load_block_inputs(*args)
    original = deepcopy(packet)
    source_facts = bind_metadata(*args, packet)
    result = screen_blocks(packet, minimum_buffer_m=20000.0)
    verified = audit_block_screen(packet, result)
    assert packet == original
    assert source_facts["sites"] == 15
    assert source_facts["raw_outcomes_opened"] == 0
    assert verified["status"] == "passed"
    assert verified["comparisons_verified"] == 112
    assert verified["all_comparisons_fail_for_every_nonnegative_uncertainty"] is True
    assert result["summary"]["admitted_target_roles"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("block_id", "other"),
        ("latitude", 45.0),
        ("source_radius_m", 20.0),
        ("target_radius_m", 20.0),
        ("basin_shoreline_radius_m", 1.0),
    ],
)
def test_source_geometry_and_grid_cannot_be_replaced_with_convenient_values(
    tmp_path: Path, field: str, value: str | float
) -> None:
    args = _fixture(tmp_path)
    packet = load_block_inputs(*args)
    packet["sites"][0][field] = value
    with pytest.raises(ValueError, match="Literal source geometry"):
        bind_metadata(*args, packet)


def test_source_priority_cannot_change_to_avoid_a_missing_anchor(
    tmp_path: Path,
) -> None:
    args = _fixture(tmp_path)
    packet = load_block_inputs(*args)
    packet["regional_priority"].reverse()
    with pytest.raises(ValueError, match="Original priority"):
        bind_metadata(*args, packet)


def test_changed_primary_bytes_refuse_after_the_packet_has_been_prepared(
    tmp_path: Path,
) -> None:
    args = _fixture(tmp_path)
    packet = load_block_inputs(*args)
    csv = args[2] / args[3]["sources"]["site_metadata"]["path"]
    raw = csv.read_bytes()
    changed = raw.replace(b"512", b"562", 1)
    assert changed != raw and len(changed) == len(raw)
    csv.write_bytes(changed)
    with pytest.raises(ValueError, match="Original metadata identity"):
        bind_metadata(*args, packet)
