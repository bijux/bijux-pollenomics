"""Real generated ancillary publishers supply browser transport fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .....static_assets.source_resources.ancillary.native_metadata import (
    ancillary_sources as ancillary_sources,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    capsule_inputs as capsule_inputs,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    legacy_catalogue as legacy_catalogue,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    reference_archive as reference_archive,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    reference_source as reference_source,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    scoped_ancillary_sources as scoped_ancillary_sources,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    scoped_catalogue as scoped_catalogue,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    scoped_inputs as scoped_inputs,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    scoped_selection_products as scoped_selection_products,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    site_context_products as site_context_products,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    supporting_catalogue as supporting_catalogue,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    supporting_sources as supporting_sources,
)
from .....static_assets.source_resources.ancillary.native_metadata import (
    unit_products as unit_products,
)
from .native_transport import publish


@pytest.fixture
def resource_browser(request: pytest.FixtureRequest, tmp_path: Path) -> dict[str, Any]:
    """Use original publisher inputs and the common real-browser harness."""
    kind = getattr(request, "param", "scoped")
    names = {
        "scoped": "scoped_catalogue",
        "supporting": "supporting_catalogue",
        "source_only": "legacy_catalogue",
        "source_only_scoped": "scoped_catalogue",
    }
    return publish(
        request.getfixturevalue(names[kind]),
        tmp_path / "browser",
        ancillary=kind != "source_only",
        countries=()
        if kind in {"source_only", "source_only_scoped"}
        else ("Sweden", "Norway", "Denmark", "Finland"),
    )
