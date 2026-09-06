"""Reader-visible animal audit rendering tests."""

from __future__ import annotations

import pytest
from bijux_pollenomics.adna.governance.audit_catalogs.rendering import (
    render_coordinate_caveat_surface_markdown,
    render_coordinate_confidence_scale_markdown,
)

pytestmark = pytest.mark.generated_artifacts


def test_coordinate_rendering_exposes_each_evidence_posture() -> None:
    common = {
        "species_latin_name": "Ovis aries",
        "project_accession": "PRJEB1",
        "site_label": "Direct site",
        "coordinate_basis": "archive_coordinates",
        "coordinate_confidence": "exact",
        "original_place_text": "Original place",
        "resolved_place_text": "Resolved place",
        "mapping_posture": "mappable_point",
    }
    payload = {
        "direct_coordinates": [common],
        "place_name_resolution": [
            {
                **common,
                "site_label": "Resolved site",
                "coordinate_basis": "named_site_geocoding",
                "coordinate_confidence": "approximate",
            }
        ],
        "still_weak_geography": [
            {
                **common,
                "site_label": "Region only",
                "mapping_posture": "refused_region_only",
            }
        ],
    }

    markdown = render_coordinate_caveat_surface_markdown(payload)
    confidence_scale = render_coordinate_confidence_scale_markdown()

    assert "Direct site" in markdown
    assert "Resolved site" in markdown
    assert "Original place" in markdown
    assert "Animal point publication is currently allowed only" in confidence_scale
