"""Static guards for the narrowly scoped retained RAÄ runtime journey."""

from __future__ import annotations

from pathlib import Path
import re

from bijux_pollenomics_dev.ci import atlas_browser
from bijux_pollenomics_dev.ci.atlas_browser.verdict import (
    RAA_RETAINED_CONTEXT_REQUIRED_ASSERTIONS,
)


def test_raa_runtime_profile_matches_exact_python_verdict() -> None:
    source = (
        Path(atlas_browser.__file__)
        .with_name("raa-retained-context.mjs")
        .read_text(encoding="utf-8")
    )
    declaration = re.search(
        r"RAA_RETAINED_CONTEXT_REQUIRED_ASSERTIONS = \[(.*?)\];",
        source,
        re.DOTALL,
    )

    assert declaration is not None
    names = frozenset(re.findall(r"'([a-z0-9_]+)'", declaration.group(1)))
    assert names == RAA_RETAINED_CONTEXT_REQUIRED_ASSERTIONS


def test_raa_runtime_journey_exercises_required_behavior() -> None:
    source = (
        Path(atlas_browser.__file__)
        .with_name("raa-retained-context.mjs")
        .read_text(encoding="utf-8")
    )

    for required in (
        '.layer-checkbox[value="raa-archaeology"]',
        'data-legend-layer="raa-archaeology"',
        "density-ramp-description",
        "time-start-slider",
        "time-interval-slider",
        "raa_atlas_input_status.json",
        "nordic_map_publication_contract.json",
        "nordic_map_assets.json",
        "visible_governed_candidate_count",
        ".textContent?.trim()",
        "Toggle RAÄ archaeology density",
        "tile.openstreetmap.org",
        "tile.opentopomap.org",
    ):
        assert required in source
    assert source.count("toggleRaa(normal.cdp, evaluate, false)") == 2
    assert source.count("toggleRaa(normal.cdp, evaluate, true)") == 2
