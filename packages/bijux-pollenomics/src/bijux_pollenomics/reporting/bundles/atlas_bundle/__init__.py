"""Multi-country atlas bundle publication."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from ....adna import AdnaLocalitySummary
from ....analysis import (
    build_ranking_engine_manifest,
    build_ranking_sensitivity_report,
    rank_localities,
    render_candidate_site_markdown,
    render_candidate_site_sensitivity_markdown,
    write_candidate_site_sensitivity_json,
    write_candidate_sites_csv,
    write_candidate_sites_json,
)
from ....collection.contracts.models import ContextPointRecord
from ....core.geospatial.geojson import JsonObject
from ....evidence import (
    AnimalCoordinateVisibilityReview,
    build_atlas_evidence_surface,
    build_scientific_review_surface,
    render_atlas_evidence_surface_markdown,
    render_scientific_review_surface_markdown,
    write_atlas_evidence_surface_json,
    write_scientific_review_surface_json,
)
from ...aadr import summarize_localities
from ...adna import build_tracked_animal_atlas_bundle
from ...geography import GeographicScope
from ...map_document.evidence_projection import build_map_evidence_projection
from ...map_document.static_assets import write_static_atlas_assets
from ...map_publication import (
    build_map_point_traceability,
    build_map_publication_contract,
    render_map_point_traceability_markdown,
    render_map_publication_contract_markdown,
    resolve_map_scope_policy,
)
from ...models import MultiCountryMapReport, SampleRecord
from ..paths import AtlasBundlePaths
from ..summary_builders.atlas import build_multi_country_bundle_manifest
from ..sweden_lake_layers import build_sweden_lake_atlas_layers
from .operations_api import _as_optional_int as _as_optional_int
from .operations_api import (
    _attach_traceability_surfaces as _attach_traceability_surfaces,
)
from .operations_api import (
    _build_animal_atlas_summary as _build_animal_atlas_summary,
)
from .operations_api import _extract_context_points as _extract_context_points
from .operations_api import _layer_features as _layer_features
from .operations_api import (
    publish_multi_country_map_bundle as publish_multi_country_map_bundle,
)

__all__ = ["publish_multi_country_map_bundle"]

for _definition in (
    publish_multi_country_map_bundle,
    _extract_context_points,
    _as_optional_int,
    _build_animal_atlas_summary,
    _layer_features,
    _attach_traceability_surfaces,
):
    _definition.__module__ = __name__

del _definition
for _internal_module_name in (
    "context",
    "contracts",
    "evidence",
    "finalization",
    "layers",
    "operations_api",
    "workflow",
):
    globals().pop(_internal_module_name, None)
del _internal_module_name
