"""Literal source additions with independently fixed predecessor identities."""

from __future__ import annotations

RESOURCE_ROUTE_SPANS: dict[str, tuple[str, tuple[tuple[bytes, bytes], ...]]] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/layers.py": (
        "965cfaf6dc1c51e10627c2062ef6edf5d64dcd11e8934e9ffcb752285808cc01",
        (
            (
                (
                    b"from typing import Any\n"
                    b"\n"
                    b"from ...modeled_context.publication_projection import project_modeled_context_layers\n"
                    b"\n"
                ),
                (
                    b"from typing import Any\n"
                    b"\n"
                    b"from ...map_document.source_resources import (\n"
                    b"    AtlasResourceCatalogueInput,\n"
                    b"    load_atlas_resource_catalogue,\n"
                    b")\n"
                    b"from ...modeled_context.publication_projection import project_modeled_context_layers\n"
                    b"\n"
                ),
            ),
            (
                (
                    b"    surface: Any,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> tuple[Any, ...]:\n"
                    b'    """Prepare atlas layers and traceable assets with optional publication metadata."""\n'
                ),
                (
                    b"    surface: Any,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b"    source_resource_catalogue: AtlasResourceCatalogueInput | None = None,\n"
                    b") -> tuple[Any, ...]:\n"
                    b'    """Prepare atlas layers and traceable assets with optional publication metadata."""\n'
                ),
            ),
            (
                (
                    b"        detail_projection_reconciliation = detail_projection.reconciliation\n"
                    b"        point_layers.extend(detail_projection.point_layers)\n"
                    b"    surface._attach_traceability_surfaces(point_layers, bundle_paths)\n"
                    b"    static_assets = surface.write_static_atlas_assets(\n"
                ),
                (
                    b"        detail_projection_reconciliation = detail_projection.reconciliation\n"
                    b"        point_layers.extend(detail_projection.point_layers)\n"
                    b"    source_resources = None\n"
                    b"    if source_resource_catalogue is not None:\n"
                    b"        neotoma_records = [\n"
                    b"            record\n"
                    b"            for record in (atlas_detail_records or ())\n"
                    b'            if isinstance(record.get("tabs"), dict)\n'
                    b'            and isinstance(record["tabs"].get("overview"), dict)\n'
                    b'            and record["tabs"]["overview"].get("source_family") == "neotoma"\n'
                    b"        ]\n"
                    b"        source_resources = load_atlas_resource_catalogue(\n"
                    b"            source_resource_catalogue, legacy_neotoma_records=neotoma_records\n"
                    b"        )\n"
                    b"    surface._attach_traceability_surfaces(point_layers, bundle_paths)\n"
                    b"    static_assets = surface.write_static_atlas_assets(\n"
                ),
            ),
            (
                (
                    b"        edge_records=atlas_edge_records,\n"
                    b"        sequence_records=atlas_sequence_records,\n"
                    b"    )\n"
                    b"    if static_assets.manifest_path != bundle_paths.map_static_assets_manifest_path:\n"
                ),
                (
                    b"        edge_records=atlas_edge_records,\n"
                    b"        sequence_records=atlas_sequence_records,\n"
                    b"        **(\n"
                    b'            {"source_resources": source_resources}\n'
                    b"            if source_resources is not None\n"
                    b"            else {}\n"
                    b"        ),\n"
                    b"    )\n"
                    b"    if static_assets.manifest_path != bundle_paths.map_static_assets_manifest_path:\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py": (
        "a743b8c4509128c3c3051826f13d140f4393dfc892e681b316aeb2431c2d3899",
        (
            (
                (
                    b"from ....evidence import AnimalCoordinateVisibilityReview\n"
                    b"from ...geography import GeographicScope\n"
                    b"from ...models import MultiCountryMapReport, SampleRecord\n"
                    b"from ..paths import AtlasBundlePaths\n"
                ),
                (
                    b"from ....evidence import AnimalCoordinateVisibilityReview\n"
                    b"from ...geography import GeographicScope\n"
                    b"from ...map_document.source_resources import AtlasResourceCatalogueInput\n"
                    b"from ...models import MultiCountryMapReport, SampleRecord\n"
                    b"from ..paths import AtlasBundlePaths\n"
                ),
            ),
            (
                (
                    b"    atlas_sequence_records: Sequence[JsonObject] | None = None,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> None:\n"
                    b'    """Write the full atlas bundle into one staging directory."""\n'
                ),
                (
                    b"    atlas_sequence_records: Sequence[JsonObject] | None = None,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b"    source_resource_catalogue: AtlasResourceCatalogueInput | None = None,\n"
                    b") -> None:\n"
                    b'    """Write the full atlas bundle into one staging directory."""\n'
                ),
            ),
            (
                (
                    b"        surface=_surface(),\n"
                    b"        publication_capture_root=publication_capture_root,\n"
                    b"    )\n"
                    b"\n"
                ),
                (
                    b"        surface=_surface(),\n"
                    b"        publication_capture_root=publication_capture_root,\n"
                    b"        **(\n"
                    b'            {"source_resource_catalogue": source_resource_catalogue}\n'
                    b"            if source_resource_catalogue is not None\n"
                    b"            else {}\n"
                    b"        ),\n"
                    b"    )\n"
                    b"\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py": (
        "4394af0afd2c55de4af10e0e6ade1c72b1e102960c4a3f844f8858f1d3245427",
        (
            (
                (
                    b"from typing import Any\n"
                    b"\n"
                    b"from .contracts import publish_contracts\n"
                    b"from .evidence import publish_evidence_and_rankings\n"
                ),
                (
                    b"from typing import Any\n"
                    b"\n"
                    b"from ...map_document.source_resources import AtlasResourceCatalogueInput\n"
                    b"from .contracts import publish_contracts\n"
                    b"from .evidence import publish_evidence_and_rankings\n"
                ),
            ),
            (
                (
                    b"    surface: Any,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> None:\n"
                    b'    """Publish atlas layers, evidence, playback, and inventoried static documents."""\n'
                ),
                (
                    b"    surface: Any,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b"    source_resource_catalogue: AtlasResourceCatalogueInput | None = None,\n"
                    b") -> None:\n"
                    b'    """Publish atlas layers, evidence, playback, and inventoried static documents."""\n'
                ),
            ),
            (
                (
                    b"        surface=surface,\n"
                    b"        publication_capture_root=publication_capture_root,\n"
                    b"    )\n"
                    b"    animal_atlas_summary = surface._build_animal_atlas_summary(\n"
                ),
                (
                    b"        surface=surface,\n"
                    b"        publication_capture_root=publication_capture_root,\n"
                    b"        **(\n"
                    b'            {"source_resource_catalogue": source_resource_catalogue}\n'
                    b"            if source_resource_catalogue is not None\n"
                    b"            else {}\n"
                    b"        ),\n"
                    b"    )\n"
                    b"    animal_atlas_summary = surface._build_animal_atlas_summary(\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py": (
        "517cec00f4e25836f91732a745d083601e8a9c8f8ddec0cd4e1792f19d5f69a4",
        (
            (
                (
                    b"from collections.abc import Callable, Iterable\n"
                    b"from datetime import date\n"
                    b"from pathlib import Path\n"
                    b"\n"
                    b"from ..adna import (\n"
                    b"    AdnaSampleQuery,\n"
                ),
                (
                    b"from collections.abc import Callable, Iterable\n"
                    b"from datetime import date\n"
                    b"from pathlib import Path\n"
                    b"from typing import TypedDict\n"
                    b"\n"
                    b"from ..adna import (\n"
                    b"    AdnaSampleQuery,\n"
                ),
            ),
            (
                (
                    b"from .context import build_context_layers\n"
                    b"from .geography import GeographicScope, infer_publication_scope\n"
                    b"from .map_document.render import write_static_map_document\n"
                    b"from .models import (\n"
                    b"    AnimalFoundationRefreshReport,\n"
                    b"    CountryReport,\n"
                ),
                (
                    b"from .context import build_context_layers\n"
                    b"from .geography import GeographicScope, infer_publication_scope\n"
                    b"from .map_document.render import write_static_map_document\n"
                    b"from .map_document.source_resources import AtlasResourceCatalogueInput\n"
                    b"from .models import (\n"
                    b"    AnimalFoundationRefreshReport,\n"
                    b"    CountryReport,\n"
                ),
            ),
            (
                (
                    b"from .review.sustainability_outputs import (\n"
                    b"    publish_repository_output_sustainability_review,\n"
                    b")\n"
                    b"\n"
                    b"\n"
                    b"def generate_country_report(\n"
                ),
                (
                    b"from .review.sustainability_outputs import (\n"
                    b"    publish_repository_output_sustainability_review,\n"
                    b")\n"
                    b"\n"
                    b"\n"
                    b"class _SourceResourceOptions(TypedDict, total=False):\n"
                    b"    source_resource_catalogue: AtlasResourceCatalogueInput\n"
                    b"\n"
                    b"\n"
                    b"def generate_country_report(\n"
                ),
            ),
            (
                (
                    b"    geography_scope: GeographicScope | None = None,\n"
                    b"    *,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> MultiCountryMapReport:\n"
                    b'    """Write a shared interactive map for multiple countries with country toggles."""\n'
                    b"    version_dir = Path(version_dir)\n"
                ),
                (
                    b"    geography_scope: GeographicScope | None = None,\n"
                    b"    *,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b"    source_resource_catalogue: AtlasResourceCatalogueInput | None = None,\n"
                    b") -> MultiCountryMapReport:\n"
                    b'    """Write a shared interactive map for multiple countries with country toggles."""\n'
                    b"    version_dir = Path(version_dir)\n"
                ),
            ),
            (
                (
                    b"        Path(published_output_dir) if published_output_dir is not None else output_dir\n"
                    b"    )\n"
                    b"\n"
                    b"    normalized_countries = normalize_requested_countries(countries)\n"
                    b"    if not normalized_countries:\n"
                    b"        raise ValueError(\n"
                ),
                (
                    b"        Path(published_output_dir) if published_output_dir is not None else output_dir\n"
                    b"    )\n"
                    b"\n"
                    b"    source_resource_options: _SourceResourceOptions = (\n"
                    b'        {"source_resource_catalogue": source_resource_catalogue}\n'
                    b"        if source_resource_catalogue is not None\n"
                    b"        else {}\n"
                    b"    )\n"
                    b"    normalized_countries = normalize_requested_countries(countries)\n"
                    b"    if not normalized_countries:\n"
                    b"        raise ValueError(\n"
                ),
            ),
            (
                (
                    b"            render_multi_country_map_markdown_fn=render_multi_country_map_markdown,\n"
                    b"            write_summary_json_fn=write_summary_json,\n"
                    b"            publication_capture_root=publication_capture_root,\n"
                    b"        )\n"
                    b"\n"
                    b"    publish_into_staging_dir(output_dir, publish_map_bundle)\n"
                ),
                (
                    b"            render_multi_country_map_markdown_fn=render_multi_country_map_markdown,\n"
                    b"            write_summary_json_fn=write_summary_json,\n"
                    b"            publication_capture_root=publication_capture_root,\n"
                    b"            **source_resource_options,\n"
                    b"        )\n"
                    b"\n"
                    b"    publish_into_staging_dir(output_dir, publish_map_bundle)\n"
                ),
            ),
            (
                (
                    b"    slug: str = DEFAULT_ATLAS_SLUG,\n"
                    b"    context_root: Path | None = None,\n"
                    b"    published_output_root: Path | None = None,\n"
                    b") -> PublishedReportsReport:\n"
                    b'    """Generate the current published report set: one shared map and one bundle per country."""\n'
                    b"    version_dir = Path(version_dir)\n"
                ),
                (
                    b"    slug: str = DEFAULT_ATLAS_SLUG,\n"
                    b"    context_root: Path | None = None,\n"
                    b"    published_output_root: Path | None = None,\n"
                    b"    *,\n"
                    b"    source_resource_catalogue: AtlasResourceCatalogueInput | None = None,\n"
                    b") -> PublishedReportsReport:\n"
                    b'    """Generate the current published report set: one shared map and one bundle per country."""\n'
                    b"    version_dir = Path(version_dir)\n"
                ),
            ),
            (
                (
                    b"        else output_root\n"
                    b"    )\n"
                    b"\n"
                    b"    normalized_countries = normalize_requested_countries(countries)\n"
                    b"    if not normalized_countries:\n"
                    b'        raise ValueError("At least one country is required to publish reports")\n'
                ),
                (
                    b"        else output_root\n"
                    b"    )\n"
                    b"\n"
                    b"    source_resource_options: _SourceResourceOptions = (\n"
                    b'        {"source_resource_catalogue": source_resource_catalogue}\n'
                    b"        if source_resource_catalogue is not None\n"
                    b"        else {}\n"
                    b"    )\n"
                    b"    normalized_countries = normalize_requested_countries(countries)\n"
                    b"    if not normalized_countries:\n"
                    b'        raise ValueError("At least one country is required to publish reports")\n'
                ),
            ),
            (
                (
                    b"            build_published_reports_summary_fn=build_published_reports_summary,\n"
                    b"            generate_country_report_fn=generate_country_report,\n"
                    b"            generate_multi_country_map_fn=generate_multi_country_map,\n"
                    b"            slugify_fn=slugify,\n"
                    b"            write_summary_json_fn=write_summary_json,\n"
                    b"        )\n"
                ),
                (
                    b"            build_published_reports_summary_fn=build_published_reports_summary,\n"
                    b"            generate_country_report_fn=generate_country_report,\n"
                    b"            generate_multi_country_map_fn=generate_multi_country_map,\n"
                    b"            **source_resource_options,\n"
                    b"            slugify_fn=slugify,\n"
                    b"            write_summary_json_fn=write_summary_json,\n"
                    b"        )\n"
                ),
            ),
        ),
    ),
}
