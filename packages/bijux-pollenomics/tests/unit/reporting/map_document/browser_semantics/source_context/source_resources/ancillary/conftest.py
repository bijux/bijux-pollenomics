"""Real generated ancillary publishers supply browser transport fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .native_transport import publish

pytest_plugins = [
    "tests.unit.reporting.map_document.static_assets.source_resources.ancillary.native_metadata"
]


@pytest.fixture
def resource_browser(request: pytest.FixtureRequest, tmp_path: Path) -> dict[str, Any]:
    """Use original publisher inputs and the common real-browser harness."""
    kind = getattr(request, "param", "scoped")
    names = {
        "scoped": "scoped_catalogue",
        "supporting": "supporting_catalogue",
        "source_only": "legacy_catalogue",
    }
    return publish(
        request.getfixturevalue(names[kind]),
        tmp_path / "browser",
        ancillary=kind != "source_only",
        countries=()
        if kind == "source_only"
        else ("Sweden", "Norway", "Denmark", "Finland"),
    )
