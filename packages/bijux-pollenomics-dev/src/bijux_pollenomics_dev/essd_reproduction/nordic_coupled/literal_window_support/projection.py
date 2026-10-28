"""Preserve the original literal-panel schema and source contract."""

from __future__ import annotations

from typing import Any

from ...physical_forward.inputs import require
from ..native_window_support.projection import project as project_native
from ..native_window_support.projection import sample_account as account_native
from ..native_window_support.projection import selected_age as selected_age
from ..regional_source_support import TAXA, WINDOWS, literal_panel, objects


def sample_account(
    sample: dict[str, Any], index: int, chronology: dict[str, Any]
) -> dict[str, Any]:
    """Retain the original literal sample function and serialized fields."""
    return account_native(sample, index, chronology, literal_panel)


def project(
    source: dict[str, Any], core: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, Any]:
    """Keep the qualified literal contract distinct from author harmonization."""
    require(
        protocol["schema_version"] == "nordic-literal-window-support-protocol.v1"
        and core in objects(protocol["cores"])
        and protocol["taxa"] == list(TAXA)
        and protocol["windows"] == [list(edge) for edge in WINDOWS],
        "Declared core/panel/window contract differs",
    )
    return project_native(
        source,
        core,
        protocol,
        panel_projector=literal_panel,
        schema_version="nordic-literal-core-support.v1",
        status="literal_source_support_accounted",
        require_alternative_reference=True,
    )
