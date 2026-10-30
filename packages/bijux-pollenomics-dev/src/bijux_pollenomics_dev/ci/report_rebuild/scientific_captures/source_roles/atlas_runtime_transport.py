"""Bind exact Atlas runtime transport extensions to original source contexts."""

from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule
from ..presentation_source_roles import atlas_extension_matches
from .documentation import DOCUMENTED_SOURCE_STRINGS, _documented_source_matches

_RUNTIME_TRANSPORT_CONTRACTS: dict[
    str, tuple[int, str, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py": (
        12521,
        "f16570b6986b48a6a4ed857042ada1a6c95830bda5d24b646d2afadaabd5f8f6",
        "ordinary_original_bytes",
        (
            (
                (
                    b"\n"
                    b"from bijux_pollenomics.reporting.geography import build_published_geography_plan\n"
                    b"from bijux_pollenomics.reporting.lra_products.api import render_lra_report\n"
                    b"from bijux_pollenomics.reporting.map_document import render_multi_country_map_html\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
                (
                    b"\n"
                    b"from bijux_pollenomics.reporting.geography import build_published_geography_plan\n"
                    b"from bijux_pollenomics.reporting.lra_products.api import render_lra_report\n"
                    b"from bijux_pollenomics.reporting.map_document.render import write_static_map_document\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
            ),
            (
                (
                    b'            if scope.key == "nordic"\n'
                    b"        )\n"
                    b"    )\n"
                    b"    document = render_multi_country_map_html(\n"
                    b'        "Retained PANGAEA modeled context",\n'
                    b'        "retained-pangaea-context",\n'
                    b'        "2026-09-28",\n'
                ),
                (
                    b'            if scope.key == "nordic"\n'
                    b"        )\n"
                    b"    )\n"
                    b"    write_static_map_document(\n"
                    b'        modeled_root / "index.html",\n'
                    b'        "Retained PANGAEA modeled context",\n'
                    b'        "retained-pangaea-context",\n'
                    b'        "2026-09-28",\n'
                ),
            ),
            (
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    (modeled_root / "index.html").write_text(document)\n'
                    b'    map_assets = package / "reporting/assets/map"\n'
                    b'    for path in sorted(map_assets.rglob("*")):\n'
                    b"        if path.is_file():\n"
                ),
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    map_assets = package / "reporting/assets/map"\n'
                    b'    for path in sorted(map_assets.rglob("*")):\n'
                    b"        if path.is_file():\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross_border_neighbor_candidate.py": (
        10011,
        "de576c9da07d9d9cfb171869019761d93280624e73efb718faa8d03a75955731",
        "ordinary_original_bytes",
        (
            (
                (
                    b"\n"
                    b"from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic\n"
                    b"from bijux_pollenomics.core.geospatial.geojson import JsonObject\n"
                    b"from bijux_pollenomics.reporting.map_document import render_multi_country_map_html\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
                (
                    b"\n"
                    b"from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic\n"
                    b"from bijux_pollenomics.core.geospatial.geojson import JsonObject\n"
                    b"from bijux_pollenomics.reporting.map_document.render import write_static_map_document\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
            ),
            (
                (
                    b"        scientific_signals=signals,\n"
                    b"        edge_records=edges,\n"
                    b"    )\n"
                    b"    document = render_multi_country_map_html(\n"
                    b'        "Controlled cross-border neighbor fixture",\n'
                    b'        "controlled-cross-border",\n'
                    b'        "2026-09-28",\n'
                ),
                (
                    b"        scientific_signals=signals,\n"
                    b"        edge_records=edges,\n"
                    b"    )\n"
                    b"    write_static_map_document(\n"
                    b'        destination / "index.html",\n'
                    b'        "Controlled cross-border neighbor fixture",\n'
                    b'        "controlled-cross-border",\n'
                    b'        "2026-09-28",\n'
                ),
            ),
            (
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    (destination / "index.html").write_text(document, encoding="utf-8")\n'
                    b"    shutil.copytree(\n"
                    b"        repository\n"
                    b'        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map",\n'
                ),
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b"    shutil.copytree(\n"
                    b"        repository\n"
                    b'        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map",\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled_panel_candidate.py": (
        9722,
        "56e4e59ce0c23f1f242f4d995bbda826ca7485da1b9995f5f0ff456cf28e09b6",
        "ordinary_original_bytes",
        (
            (
                (
                    b"from typing import Any, cast\n"
                    b"\n"
                    b"from bijux_pollenomics.reporting.geography import build_published_geography_plan\n"
                    b"from bijux_pollenomics.reporting.map_document import render_multi_country_map_html\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
                (
                    b"from typing import Any, cast\n"
                    b"\n"
                    b"from bijux_pollenomics.reporting.geography import build_published_geography_plan\n"
                    b"from bijux_pollenomics.reporting.map_document.render import write_static_map_document\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
            ),
            (
                (
                    b'            if scope.key == "nordic"\n'
                    b"        )\n"
                    b"    )\n"
                    b"    document = render_multi_country_map_html(\n"
                    b'        "Retained PANGAEA modeled panels",\n'
                    b'        "retained-pangaea-panel-context",\n'
                    b'        "2026-09-28",\n'
                ),
                (
                    b'            if scope.key == "nordic"\n'
                    b"        )\n"
                    b"    )\n"
                    b"    write_static_map_document(\n"
                    b'        destination / "index.html",\n'
                    b'        "Retained PANGAEA modeled panels",\n'
                    b'        "retained-pangaea-panel-context",\n'
                    b'        "2026-09-28",\n'
                ),
            ),
            (
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    (destination / "index.html").write_text(document)\n'
                    b'    package = repository / "packages/bijux-pollenomics/src/bijux_pollenomics"\n'
                    b'    for domain in ("reporting", "core"):\n'
                    b'        for path in sorted((package / domain).rglob("*")):\n'
                ),
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    package = repository / "packages/bijux-pollenomics/src/bijux_pollenomics"\n'
                    b'    for domain in ("reporting", "core"):\n'
                    b'        for path in sorted((package / domain).rglob("*")):\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py": (
        12590,
        "1e2b74ed221ba0a2952bb83f3ef7177f6b6e4e031da37586c2ea406557f30c55",
        "ordinary_original_bytes",
        (
            (
                (
                    b"from typing import Any\n"
                    b"\n"
                    b"from bijux_pollenomics.reporting.geography import build_published_geography_plan\n"
                    b"from bijux_pollenomics.reporting.map_document import render_multi_country_map_html\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
                (
                    b"from typing import Any\n"
                    b"\n"
                    b"from bijux_pollenomics.reporting.geography import build_published_geography_plan\n"
                    b"from bijux_pollenomics.reporting.map_document.render import write_static_map_document\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
            ),
            (
                (
                    b'            if scope.key == "nordic"\n'
                    b"        )\n"
                    b"    )\n"
                    b"    document = render_multi_country_map_html(\n"
                    b'        "Nordic retained source contexts",\n'
                    b'        "retained-source-context",\n'
                    b'        "2026-09-27",\n'
                ),
                (
                    b'            if scope.key == "nordic"\n'
                    b"        )\n"
                    b"    )\n"
                    b"    write_static_map_document(\n"
                    b'        destination / "index.html",\n'
                    b'        "Nordic retained source contexts",\n'
                    b'        "retained-source-context",\n'
                    b'        "2026-09-27",\n'
                ),
            ),
            (
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    (destination / "index.html").write_text(document)\n'
                    b'    map_assets = reporting / "assets/map"\n'
                    b'    for path in sorted(map_assets.rglob("*")):\n'
                    b"        if path.is_file():\n"
                ),
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    map_assets = reporting / "assets/map"\n'
                    b'    for path in sorted(map_assets.rglob("*")):\n'
                    b"        if path.is_file():\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py": (
        7274,
        "aea053ee48e2e41920967abf66bf7e4a3e5e0fb79a08b5249276c73fe7ca0d6b",
        "existing_named_documentation",
        (
            (
                (
                    b"import shutil\n"
                    b"from typing import Any, cast\n"
                    b"\n"
                    b"from bijux_pollenomics.reporting.map_document import render_multi_country_map_html\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
                (
                    b"import shutil\n"
                    b"from typing import Any, cast\n"
                    b"\n"
                    b"from bijux_pollenomics.reporting.map_document.render import write_static_map_document\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
            ),
            (
                (
                    b"        point_layers=[layer],\n"
                    b"        polygon_layers=[],\n"
                    b"    )\n"
                    b"    document = render_multi_country_map_html(\n"
                    b'        "Sample-owned chronology",\n'
                    b'        "published-v66",\n'
                    b'        "2026-10-14",\n'
                ),
                (
                    b"        point_layers=[layer],\n"
                    b"        polygon_layers=[],\n"
                    b"    )\n"
                    b"    html_path, _ = write_static_map_document(\n"
                    b'        destination / "index.html",\n'
                    b'        "Sample-owned chronology",\n'
                    b'        "published-v66",\n'
                    b'        "2026-10-14",\n'
                ),
            ),
            (
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    (destination / "index.html").write_text(document, encoding="utf-8")\n'
                    b"    map_assets = (\n"
                    b"        repository\n"
                    b'        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map"\n'
                ),
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b"    map_assets = (\n"
                    b"        repository\n"
                    b'        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map"\n'
                ),
            ),
            (
                (
                    b'        "dated_feature_count": 1,\n'
                    b'        "undated_feature_count": 1,\n'
                    b'        "candidate_build_id": assets.manifest["build_id"],\n'
                    b'        "candidate_document_sha256": hashlib.sha256(document.encode()).hexdigest(),\n'
                    b'        "component_index_schema": cast(\n'
                    b'            dict[str, Any], assets.manifest["compatibility"]\n'
                    b'        )["index_schema"],\n'
                ),
                (
                    b'        "dated_feature_count": 1,\n'
                    b'        "undated_feature_count": 1,\n'
                    b'        "candidate_build_id": assets.manifest["build_id"],\n'
                    b'        "candidate_document_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),\n'
                    b'        "component_index_schema": cast(\n'
                    b'            dict[str, Any], assets.manifest["compatibility"]\n'
                    b'        )["index_schema"],\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py": (
        11467,
        "423a78430628ffce3e17d54901cc4e5317d48616f09ee5e3cf030a3b1a883d79",
        "ordinary_original_bytes",
        (
            (
                (
                    b"from typing import Any\n"
                    b"\n"
                    b"from bijux_pollenomics.reporting.geography import build_published_geography_plan\n"
                    b"from bijux_pollenomics.reporting.map_document import render_multi_country_map_html\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
                (
                    b"from typing import Any\n"
                    b"\n"
                    b"from bijux_pollenomics.reporting.geography import build_published_geography_plan\n"
                    b"from bijux_pollenomics.reporting.map_document.render import write_static_map_document\n"
                    b"from bijux_pollenomics.reporting.map_document.static_assets import (\n"
                    b"    write_static_atlas_assets,\n"
                    b")\n"
                ),
            ),
            (
                (
                    b'            if scope.key == "nordic"\n'
                    b"        )\n"
                    b"    )\n"
                    b"    document = render_multi_country_map_html(\n"
                    b'        "Retained Neotoma source details",\n'
                    b'        "retained-neotoma",\n'
                    b'        "2026-09-27",\n'
                ),
                (
                    b'            if scope.key == "nordic"\n'
                    b"        )\n"
                    b"    )\n"
                    b"    html_path, _ = write_static_map_document(\n"
                    b'        destination / "index.html",\n'
                    b'        "Retained Neotoma source details",\n'
                    b'        "retained-neotoma",\n'
                    b'        "2026-09-27",\n'
                ),
            ),
            (
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b'    (destination / "index.html").write_text(document, encoding="utf-8")\n'
                    b"    map_assets = (\n"
                    b"        repository\n"
                    b'        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map"\n'
                ),
                (
                    b'        "./_map_assets",\n'
                    b"        static_assets=assets,\n"
                    b"    )\n"
                    b"    map_assets = (\n"
                    b"        repository\n"
                    b'        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map"\n'
                ),
            ),
            (
                (
                    b'        "inputs_sha256": inputs,\n'
                    b'        "source_records": source_summaries,\n'
                    b'        "candidate_build_id": assets.manifest["build_id"],\n'
                    b'        "candidate_document_sha256": hashlib.sha256(document.encode()).hexdigest(),\n'
                    b'        "scientific_posture": "source_owned_site_context; preserve chronology refusals; no reviewed classification or propagation claim",\n'
                    b"    }\n"
                    b"    for relative_path, digest in inputs.items():\n"
                ),
                (
                    b'        "inputs_sha256": inputs,\n'
                    b'        "source_records": source_summaries,\n'
                    b'        "candidate_build_id": assets.manifest["build_id"],\n'
                    b'        "candidate_document_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),\n'
                    b'        "scientific_posture": "source_owned_site_context; preserve chronology refusals; no reviewed classification or propagation claim",\n'
                    b"    }\n"
                    b"    for relative_path, digest in inputs.items():\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py": (
        3225,
        "fcf8be43d6c73e7acc3be4db275bdcb8e2a8d9a81069e00dbe35432185375cd6",
        "ordinary_original_bytes",
        (
            (
                (
                    b"    static_assets: Any,\n"
                    b"    build_multi_country_map_summary_fn: Any,\n"
                    b"    copy_map_assets_fn: Any,\n"
                    b"    render_multi_country_map_html_fn: Any,\n"
                    b"    render_multi_country_map_markdown_fn: Any,\n"
                    b"    write_summary_json_fn: Any,\n"
                    b"    surface: Any,\n"
                    b") -> None:\n"
                    b"    write_summary_json_fn(\n"
                    b"        bundle_paths.bundle_manifest_path,\n"
                    b"        surface.build_multi_country_bundle_manifest(\n"
                ),
                (
                    b"    static_assets: Any,\n"
                    b"    build_multi_country_map_summary_fn: Any,\n"
                    b"    copy_map_assets_fn: Any,\n"
                    b"    write_static_map_document_fn: Any,\n"
                    b"    render_multi_country_map_markdown_fn: Any,\n"
                    b"    write_summary_json_fn: Any,\n"
                    b"    surface: Any,\n"
                    b") -> None:\n"
                    b'    """Write the atlas document, inventory its runtime, and finalize bundle reports."""\n'
                    b"    copy_map_assets_fn(staging_output_dir)\n"
                    b"    _, runtime_path = write_static_map_document_fn(\n"
                    b"        output_path=bundle_paths.map_html_path,\n"
                    b"        title=title,\n"
                    b"        version=version,\n"
                    b"        generated_on=generated_on,\n"
                    b"        countries=countries,\n"
                    b"        policy=map_policy,\n"
                    b"        point_layers=point_layers,\n"
                    b"        polygon_layers=polygon_layers,\n"
                    b"        asset_base_path=asset_base_path,\n"
                    b"        static_assets=static_assets,\n"
                    b"    )\n"
                    b'    extra_artifacts.append(("Static atlas runtime", runtime_path.name))\n'
                    b"    write_summary_json_fn(\n"
                    b"        bundle_paths.bundle_manifest_path,\n"
                    b"        surface.build_multi_country_bundle_manifest(\n"
                ),
            ),
            (
                (
                    b"            animal_atlas_summary=animal_atlas_summary,\n"
                    b"        ),\n"
                    b"    )\n"
                    b"    copy_map_assets_fn(staging_output_dir)\n"
                    b"    write_summary_json_fn(\n"
                    b"        bundle_paths.summary_json_path,\n"
                    b"        build_multi_country_map_summary_fn(\n"
                ),
                (
                    b"            animal_atlas_summary=animal_atlas_summary,\n"
                    b"        ),\n"
                    b"    )\n"
                    b"    write_summary_json_fn(\n"
                    b"        bundle_paths.summary_json_path,\n"
                    b"        build_multi_country_map_summary_fn(\n"
                ),
            ),
            (
                (
                    b"            map_publication_contract=map_publication_contract,\n"
                    b"            animal_atlas_summary=animal_atlas_summary,\n"
                    b"        ),\n"
                    b"    )\n"
                    b"    bundle_paths.map_html_path.write_text(\n"
                    b"        render_multi_country_map_html_fn(\n"
                    b"            title=title,\n"
                    b"            version=version,\n"
                    b"            generated_on=generated_on,\n"
                    b"            countries=countries,\n"
                    b"            policy=map_policy,\n"
                    b"            point_layers=point_layers,\n"
                    b"            polygon_layers=polygon_layers,\n"
                    b"            asset_base_path=asset_base_path,\n"
                    b"            static_assets=static_assets,\n"
                    b"        ),\n"
                    b'        encoding="utf-8",\n'
                    b"    )\n"
                    b"    bundle_paths.readme_path.write_text(\n"
                    b"        render_multi_country_map_markdown_fn(\n"
                ),
                (
                    b"            map_publication_contract=map_publication_contract,\n"
                    b"            animal_atlas_summary=animal_atlas_summary,\n"
                    b"        ),\n"
                    b"    )\n"
                    b"    bundle_paths.readme_path.write_text(\n"
                    b"        render_multi_country_map_markdown_fn(\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py": (
        4363,
        "1237c261bd34487bbe66efd0fba1f8ea5afa5b0ee81ed91dabe8f033b4b6bce3",
        "ordinary_original_bytes",
        (
            (
                (
                    b"    build_multi_country_map_summary_fn: Callable[..., dict[str, object]],\n"
                    b"    build_samples_geojson_fn: Callable[[Iterable[SampleRecord]], JsonObject],\n"
                    b"    copy_map_assets_fn: Callable[[Path], Path],\n"
                    b"    render_multi_country_map_html_fn: Callable[..., str],\n"
                    b"    render_multi_country_map_markdown_fn: Callable[..., str],\n"
                    b"    write_summary_json_fn: Callable[[Path, dict[str, object]], None],\n"
                    b"    atlas_detail_records: Sequence[JsonObject] | None = None,\n"
                ),
                (
                    b"    build_multi_country_map_summary_fn: Callable[..., dict[str, object]],\n"
                    b"    build_samples_geojson_fn: Callable[[Iterable[SampleRecord]], JsonObject],\n"
                    b"    copy_map_assets_fn: Callable[[Path], Path],\n"
                    b"    write_static_map_document_fn: Callable[..., tuple[Path, Path]],\n"
                    b"    render_multi_country_map_markdown_fn: Callable[..., str],\n"
                    b"    write_summary_json_fn: Callable[[Path, dict[str, object]], None],\n"
                    b"    atlas_detail_records: Sequence[JsonObject] | None = None,\n"
                ),
            ),
            (
                (
                    b"        build_multi_country_map_summary_fn=build_multi_country_map_summary_fn,\n"
                    b"        build_samples_geojson_fn=build_samples_geojson_fn,\n"
                    b"        copy_map_assets_fn=copy_map_assets_fn,\n"
                    b"        render_multi_country_map_html_fn=render_multi_country_map_html_fn,\n"
                    b"        render_multi_country_map_markdown_fn=render_multi_country_map_markdown_fn,\n"
                    b"        write_summary_json_fn=write_summary_json_fn,\n"
                    b"        atlas_detail_records=atlas_detail_records,\n"
                ),
                (
                    b"        build_multi_country_map_summary_fn=build_multi_country_map_summary_fn,\n"
                    b"        build_samples_geojson_fn=build_samples_geojson_fn,\n"
                    b"        copy_map_assets_fn=copy_map_assets_fn,\n"
                    b"        write_static_map_document_fn=write_static_map_document_fn,\n"
                    b"        render_multi_country_map_markdown_fn=render_multi_country_map_markdown_fn,\n"
                    b"        write_summary_json_fn=write_summary_json_fn,\n"
                    b"        atlas_detail_records=atlas_detail_records,\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py": (
        4480,
        "ec95b59e5cd910866cc0196d32b983d0e78cc17f22304bf41e84904f58edae2c",
        "ordinary_original_bytes",
        (
            (
                (
                    b"    build_multi_country_map_summary_fn: Any,\n"
                    b"    build_samples_geojson_fn: Any,\n"
                    b"    copy_map_assets_fn: Any,\n"
                    b"    render_multi_country_map_html_fn: Any,\n"
                    b"    render_multi_country_map_markdown_fn: Any,\n"
                    b"    write_summary_json_fn: Any,\n"
                    b"    atlas_detail_records: Any,\n"
                ),
                (
                    b"    build_multi_country_map_summary_fn: Any,\n"
                    b"    build_samples_geojson_fn: Any,\n"
                    b"    copy_map_assets_fn: Any,\n"
                    b"    write_static_map_document_fn: Any,\n"
                    b"    render_multi_country_map_markdown_fn: Any,\n"
                    b"    write_summary_json_fn: Any,\n"
                    b"    atlas_detail_records: Any,\n"
                ),
            ),
            (
                (
                    b"    atlas_sequence_records: Any,\n"
                    b"    surface: Any,\n"
                    b") -> None:\n"
                    b"    (\n"
                    b"        bundle_paths,\n"
                    b"        point_layers,\n"
                ),
                (
                    b"    atlas_sequence_records: Any,\n"
                    b"    surface: Any,\n"
                    b") -> None:\n"
                    b'    """Publish atlas layers, evidence, playback, and inventoried static documents."""\n'
                    b"    (\n"
                    b"        bundle_paths,\n"
                    b"        point_layers,\n"
                ),
            ),
            (
                (
                    b"        static_assets=static_assets,\n"
                    b"        build_multi_country_map_summary_fn=build_multi_country_map_summary_fn,\n"
                    b"        copy_map_assets_fn=copy_map_assets_fn,\n"
                    b"        render_multi_country_map_html_fn=render_multi_country_map_html_fn,\n"
                    b"        render_multi_country_map_markdown_fn=render_multi_country_map_markdown_fn,\n"
                    b"        write_summary_json_fn=write_summary_json_fn,\n"
                    b"        surface=surface,\n"
                ),
                (
                    b"        static_assets=static_assets,\n"
                    b"        build_multi_country_map_summary_fn=build_multi_country_map_summary_fn,\n"
                    b"        copy_map_assets_fn=copy_map_assets_fn,\n"
                    b"        write_static_map_document_fn=write_static_map_document_fn,\n"
                    b"        render_multi_country_map_markdown_fn=render_multi_country_map_markdown_fn,\n"
                    b"        write_summary_json_fn=write_summary_json_fn,\n"
                    b"        surface=surface,\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py": (
        17181,
        "b9e8af47a6369d89604bb78e61daf388bd02964862fd19055fbb93662bd92a9e",
        "existing_atlas_workflow_export",
        (
            (
                (
                    b"from ...analysis.lra.inputs.schema import REQUEST_SCHEMA\n"
                    b"from ...core.geospatial.geojson import JsonObject\n"
                    b"from ...core.owned_tree import publish_new_output_tree\n"
                    b"from ..map_document import render_multi_country_map_html\n"
                    b"from ..map_document.native_lra import bind_native_view\n"
                    b"from ..map_document.static_assets import write_static_atlas_assets\n"
                    b"from ..rendering.artifacts import copy_map_assets\n"
                    b"from ..scope_policy import MAP_SCOPE_POLICIES\n"
                ),
                (
                    b"from ...analysis.lra.inputs.schema import REQUEST_SCHEMA\n"
                    b"from ...core.geospatial.geojson import JsonObject\n"
                    b"from ...core.owned_tree import publish_new_output_tree\n"
                    b"from ..map_document.native_lra import bind_native_view\n"
                    b"from ..map_document.render import write_static_map_document\n"
                    b"from ..map_document.static_assets import write_static_atlas_assets\n"
                    b"from ..rendering.artifacts import copy_map_assets\n"
                    b"from ..scope_policy import MAP_SCOPE_POLICIES\n"
                ),
            ),
            (
                (
                    b"        .read_bytes()\n"
                    b"    )\n"
                    b"    render_layers: list[JsonObject] = [dict(layer) for layer in layers]\n"
                    b"    document = render_multi_country_map_html(\n"
                    b'        title="Exploratory synthetic LRA anchors",\n'
                    b'        version="presentation-v1" if temporal_profile is None else "presentation-v2",\n'
                    b'        generated_on="Source identities in the accompanying report",\n'
                ),
                (
                    b"        .read_bytes()\n"
                    b"    )\n"
                    b"    render_layers: list[JsonObject] = [dict(layer) for layer in layers]\n"
                    b"    write_static_map_document(\n"
                    b'        output_path=stage / "map.html",\n'
                    b'        title="Exploratory synthetic LRA anchors",\n'
                    b'        version="presentation-v1" if temporal_profile is None else "presentation-v2",\n'
                    b'        generated_on="Source identities in the accompanying report",\n'
                ),
            ),
            (
                (
                    b"        static_assets=assets,\n"
                    b"        native_lra=native_view,\n"
                    b"    )\n"
                    b'    (stage / "map.html").write_text(document)\n'
                    b'    return str(assets.manifest["build_id"])\n'
                    b"\n"
                    b"\n"
                ),
                (
                    b"        static_assets=assets,\n"
                    b"        native_lra=native_view,\n"
                    b"    )\n"
                    b'    return str(assets.manifest["build_id"])\n'
                    b"\n"
                    b"\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py": (
        2007,
        "5d4e6e72c8794e40d6a741d40a74d7c0e3dbe6de9791e0c555f3043da5bf0def",
        "ordinary_original_bytes",
        (
            (
                (
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from typing import Any\n"
                    b"\n"
                    b"from ...core.geospatial.geojson import JsonObject\n"
                    b"from ..map_publication import MapScopePolicy\n"
                    b"from ..presentation.text import escape_html\n"
                    b"from .payload import build_map_document_payload\n"
                    b"from .static_assets import StaticAtlasAssets, validate_static_atlas_document\n"
                    b"from .static_assets.stylesheet import compact_stylesheet\n"
                    b"from .template import MAP_DOCUMENT_TEMPLATE\n"
                    b"\n"
                ),
                (
                    b'"""Compose Atlas documents and write bounded static runtime resources."""\n'
                    b"\n"
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"import base64\n"
                    b"import hashlib\n"
                    b"import json\n"
                    b"from pathlib import Path\n"
                    b"import re\n"
                    b"from typing import Any\n"
                    b"\n"
                    b"from ...core.geospatial.geojson import JsonObject\n"
                    b"from ..map_publication import MapScopePolicy\n"
                    b"from ..presentation.text import escape_html\n"
                    b"from .payload import build_map_document_payload, serialize_json_for_script\n"
                    b"from .static_assets import StaticAtlasAssets, validate_static_atlas_document\n"
                    b"from .static_assets.asset_inventory import normalize_asset_inventory\n"
                    b"from .static_assets.budgets import (\n"
                    b"    ATLAS_BOOTSTRAP_MAX_BYTES,\n"
                    b"    ATLAS_DOCUMENT_MAX_BYTES,\n"
                    b"    ATLAS_INITIAL_MAX_BYTES,\n"
                    b"    ATLAS_INITIAL_MAX_REQUESTS,\n"
                    b"    ATLAS_STATIC_ASSETS_MAX_BYTES,\n"
                    b"    ATLAS_STATIC_ASSETS_MAX_FILES,\n"
                    b")\n"
                    b"from .static_assets.serialization import write_immutable\n"
                    b"from .static_assets.stylesheet import compact_stylesheet\n"
                    b"from .template import MAP_DOCUMENT_TEMPLATE\n"
                    b"\n"
                ),
            ),
            (
                (
                    b"    return document[:start] + compact + document[end:]\n"
                    b"\n"
                    b"\n"
                    b"def render_multi_country_map_html(\n"
                    b"    title: str,\n"
                    b"    version: str,\n"
                    b"    generated_on: str,\n"
                ),
                (
                    b"    return document[:start] + compact + document[end:]\n"
                    b"\n"
                    b"\n"
                    b"def _compose_map_document(\n"
                    b"    title: str,\n"
                    b"    version: str,\n"
                    b"    generated_on: str,\n"
                ),
            ),
            (
                (
                    b"    *,\n"
                    b"    native_lra: dict[str, Any] | None = None,\n"
                    b") -> str:\n"
                    b'    """Render the standalone interactive map document."""\n'
                    b"    rendered_document = (\n"
                    b"        _compact_inline_stylesheet(MAP_DOCUMENT_TEMPLATE)\n"
                    b"        if static_assets is not None\n"
                ),
                (
                    b"    *,\n"
                    b"    native_lra: dict[str, Any] | None = None,\n"
                    b") -> str:\n"
                    b'    """Compose source and payload without publishing an intermediate document."""\n'
                    b"    rendered_document = (\n"
                    b"        _compact_inline_stylesheet(MAP_DOCUMENT_TEMPLATE)\n"
                    b"        if static_assets is not None\n"
                ),
            ),
            (
                (
                    b"        native_lra=native_lra,\n"
                    b"    ).items():\n"
                    b"        rendered_document = rendered_document.replace(placeholder, value)\n"
                    b"    if static_assets is not None:\n"
                    b"        validate_static_atlas_document(rendered_document)\n"
                    b"    return rendered_document\n"
                ),
                (
                    b"        native_lra=native_lra,\n"
                    b"    ).items():\n"
                    b"        rendered_document = rendered_document.replace(placeholder, value)\n"
                    b"    return rendered_document\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py": (
        12435,
        "7f44338f73d6efd918f9d82d3e8ba9d686db4cfa92251e3d2446794945a6b6e4",
        "ordinary_original_bytes",
        (
            (
                (
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from collections.abc import Callable, Iterable\n"
                ),
                (
                    b'"""Coordinate country reports, Atlas bundles, and published report outputs."""\n'
                    b"\n"
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from collections.abc import Callable, Iterable\n"
                ),
            ),
            (
                (
                    b")\n"
                    b"from .context import build_context_layers\n"
                    b"from .geography import GeographicScope, infer_publication_scope\n"
                    b"from .models import (\n"
                    b"    AnimalFoundationRefreshReport,\n"
                    b"    CountryReport,\n"
                ),
                (
                    b")\n"
                    b"from .context import build_context_layers\n"
                    b"from .geography import GeographicScope, infer_publication_scope\n"
                    b"from .map_document.render import write_static_map_document\n"
                    b"from .models import (\n"
                    b"    AnimalFoundationRefreshReport,\n"
                    b"    CountryReport,\n"
                ),
            ),
            (
                (
                    b"from .rendering import (\n"
                    b"    build_samples_geojson,\n"
                    b"    copy_map_assets,\n"
                    b"    render_multi_country_map_html,\n"
                    b"    render_multi_country_map_markdown,\n"
                    b"    render_sample_markdown,\n"
                    b"    render_summary_markdown,\n"
                ),
                (
                    b"from .rendering import (\n"
                    b"    build_samples_geojson,\n"
                    b"    copy_map_assets,\n"
                    b"    render_multi_country_map_markdown,\n"
                    b"    render_sample_markdown,\n"
                    b"    render_summary_markdown,\n"
                ),
            ),
            (
                (
                    b"            build_multi_country_map_summary_fn=build_multi_country_map_summary,\n"
                    b"            build_samples_geojson_fn=build_samples_geojson,\n"
                    b"            copy_map_assets_fn=copy_map_assets,\n"
                    b"            render_multi_country_map_html_fn=render_multi_country_map_html,\n"
                    b"            render_multi_country_map_markdown_fn=render_multi_country_map_markdown,\n"
                    b"            write_summary_json_fn=write_summary_json,\n"
                    b"        )\n"
                ),
                (
                    b"            build_multi_country_map_summary_fn=build_multi_country_map_summary,\n"
                    b"            build_samples_geojson_fn=build_samples_geojson,\n"
                    b"            copy_map_assets_fn=copy_map_assets,\n"
                    b"            write_static_map_document_fn=write_static_map_document,\n"
                    b"            render_multi_country_map_markdown_fn=render_multi_country_map_markdown,\n"
                    b"            write_summary_json_fn=write_summary_json,\n"
                    b"        )\n"
                ),
            ),
        ),
    ),
}
ATLAS_RUNTIME_TRANSPORT_SOURCES = frozenset(_RUNTIME_TRANSPORT_CONTRACTS)
_WORKFLOW_EXPORT_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py"
_DOCUMENTED_CANDIDATE_SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py"
_CONTEXT_ALLOWED_SOURCES = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": frozenset(
        (
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross_border_neighbor_candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled_panel_candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py",
        )
    ),
    "data/atlas/sample-chronology-source-view-capture": frozenset(
        (
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled_panel_candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py",
        )
    ),
}
_CAPTURE_CONTEXTS = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        "source/",
    ),
}


_RUNTIME_SOURCE = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py"
)
_RUNTIME_DECLARATION_NAMES = (
    "render_multi_country_map_html",
    "_RUNTIME_BEGIN",
    "_RUNTIME_END",
    "_BOOTSTRAP",
    "_RUNTIME_LOADER",
    "_runtime_resources",
    "write_static_map_document",
)
_RUNTIME_NEW_SIGNATURES = {
    "render_multi_country_map_html": """def render_multi_country_map_html(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    policy: MapScopePolicy,
    point_layers: list[JsonObject],
    polygon_layers: list[JsonObject],
    asset_base_path: str,
    static_assets: StaticAtlasAssets | None = None,
    *,
    native_lra: dict[str, Any] | None = None,
) -> str:
    pass
""",
    "_runtime_resources": """def _runtime_resources(assets: StaticAtlasAssets, runtime_bytes: int) -> None:
    pass
""",
    "write_static_map_document": """def write_static_map_document(
    output_path: Path,
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    policy: MapScopePolicy,
    point_layers: list[JsonObject],
    polygon_layers: list[JsonObject],
    asset_base_path: str,
    static_assets: StaticAtlasAssets,
    *,
    native_lra: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    pass
""",
}
_RUNTIME_LITERAL_GLOBALS = {
    "_RUNTIME_BEGIN": ("<!-- atlas-runtime:begin -->"),
    "_RUNTIME_END": ("<!-- atlas-runtime:end -->"),
    "_RUNTIME_LOADER": (
        "<script>\n"
        "(() => {\n"
        "  const fail = () => {\n"
        "    const alert = document.createElement('main');\n"
        "    alert.setAttribute('role', 'alert');\n"
        "    alert.setAttribute('aria-live', 'assertive');\n"
        "    alert.textContent = 'Atlas runtime could not be loaded. Keep the complete atlas files together and reload.';\n"
        "    document.body.prepend(alert);\n"
        "  };\n"
        "  try {\n"
        "    const runtime = JSON.parse(document.getElementById('atlas-static-bootstrap').textContent).runtime;\n"
        "    const script = document.createElement('script');\n"
        "    script.src = runtime.path;\n"
        "    script.async = false;\n"
        "    if (location.protocol === 'http:' || location.protocol === 'https:') {\n"
        "      script.integrity = runtime.integrity;\n"
        "      script.crossOrigin = 'anonymous';\n"
        "    } else if (location.protocol !== 'file:') { throw new Error('Unsupported atlas protocol'); }\n"
        "    script.onerror = fail;\n"
        "    document.body.append(script);\n"
        "  } catch (error) { fail(); }\n"
        "})();\n"
        "</script>"
    ),
}
_RUNTIME_BOOTSTRAP_EXPRESSION = 're.compile(\'(<script id="atlas-static-bootstrap" type="application/json">)(.*?)(</script>)\', re.DOTALL)'


def _without_runtime_additions(current: bytes) -> bytes | None:
    """Remove only seven closed deferred declarations at the physical module tail."""
    try:
        body = current.decode("utf-8")
        tree = ast.parse(body)
        if not any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and len(node.names) == 1
            and node.names[0].name == "annotations"
            and node.names[0].asname is None
            for node in tree.body
        ):
            return None
        declarations = tree.body[-7:]
        names = []
        for node in declarations:
            if isinstance(node, ast.FunctionDef):
                names.append(node.name)
                expected = ast.parse(
                    _RUNTIME_NEW_SIGNATURES.get(node.name, "pass")
                ).body[0]
                observed = copy.deepcopy(node)
                observed.body = [ast.Pass()]
                if ast.dump(observed, include_attributes=False) != ast.dump(
                    expected, include_attributes=False
                ):
                    return None
            elif (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                name = node.targets[0].id
                names.append(name)
                if name == "_BOOTSTRAP":
                    if ast.dump(node.value, include_attributes=False) != ast.dump(
                        ast.parse(_RUNTIME_BOOTSTRAP_EXPRESSION, mode="eval").body,
                        include_attributes=False,
                    ):
                        return None
                elif name in _RUNTIME_LITERAL_GLOBALS:
                    value = ast.literal_eval(node.value)
                    if (
                        type(value) is not str
                        or value != _RUNTIME_LITERAL_GLOBALS[name]
                    ):
                        return None
                else:
                    return None
            else:
                return None
        if tuple(names) != _RUNTIME_DECLARATION_NAMES:
            return None
        lines = body.splitlines(keepends=True)
        if "".join(lines[declarations[-1].end_lineno :]):
            return None
        start = sum(len(line) for line in lines[: declarations[0].lineno - 1])
        prefix = body[:start]
        if not prefix.endswith("\n\n\n"):
            return None
        return prefix[:-2].encode("utf-8")
    except (SyntaxError, UnicodeDecodeError, ValueError, TypeError, RecursionError):
        return None


def atlas_runtime_transport_extension_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Undo only runtime transport spans, then the named prior correspondence."""
    contract = _RUNTIME_TRANSPORT_CONTRACTS.get(name)
    if contract is None:
        return False
    size, digest, composition, spans = contract
    if len(captured) != size or hashlib.sha256(captured).hexdigest() != digest:
        return False
    restored = (
        _without_runtime_additions(current) if name == _RUNTIME_SOURCE else current
    )
    if restored is None:
        return False
    for prior, extension in spans:
        if restored.count(extension) != 1:
            return False
        restored = restored.replace(extension, prior, 1)
    if composition == "ordinary_original_bytes":
        return restored == captured
    if composition == "existing_atlas_workflow_export":
        return name == _WORKFLOW_EXPORT_SOURCE and atlas_extension_matches(
            name, captured, restored
        )
    if composition == "existing_named_documentation":
        return (
            name == _DOCUMENTED_CANDIDATE_SOURCE
            and name in DOCUMENTED_SOURCE_STRINGS
            and _documented_source_matches(name, captured, restored)
        )
    return False


def validated_atlas_runtime_transport_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate changed runtime transport without retagging browser outputs."""
    context = _CAPTURE_CONTEXTS.get(source_buffer.prefix)
    name = historical.get("path")
    contract = _RUNTIME_TRANSPORT_CONTRACTS.get(name) if isinstance(name, str) else None
    if contract is None:
        raise ReportRebuildError("Unknown Atlas runtime transport source")
    size, digest, composition, spans = contract
    expected = {"sha256": digest, "bytes": size}
    if (
        context is None
        or name not in _CONTEXT_ALLOWED_SOURCES.get(source_buffer.prefix, frozenset())
        or repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != context[0]
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != context[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for original, path in group["resolved_paths"]
            if original == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Atlas runtime transport source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    current_path = _regular_confined_file(
        repository,
        name,
        "current Atlas runtime transport",
    )
    before = current_path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 64 * 1024:
        raise ReportRebuildError(
            "Atlas runtime transport source is linked or unbounded"
        )
    current = current_path.read_bytes()
    if not atlas_runtime_transport_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Atlas runtime transport differs beyond its named source extension"
        )
    source_buffer.fresh()
    again = _regular_confined_file(
        repository,
        name,
        "current Atlas runtime transport",
    )
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError(
            "Atlas runtime transport source changed during verification"
        )
    return {
        "path": name,
        "classification": "runtime_transport_extension",
        "original_member": logical,
        "original_bytes": size,
        "original_sha256": digest,
        "whole_old_module_reconstructed": True,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "named_runtime_transport_spans_reversed": len(spans),
        "seven_closed_runtime_declarations_checked": name == _RUNTIME_SOURCE,
        "new_deferred_runtime_bodies_part_of_historical_equality_claim": False,
        "preexisting_correspondence": composition,
        "runtime_sidecar_and_writer_callback_API_intentionally_changed": True,
        "current_runtime_SRI_and_protocol_behavior_requires_software_controls": True,
        "scientific_chunk_identity_preservation_requires_separate_controls": True,
        "historical_native_equal_current_output_claimed": False,
        "historical_browser_equal_current_browser_claimed": False,
        "current_runtime_transport_byte_equal_claimed": False,
        "historical_outputs_revalidated_under_current_contract_claimed": False,
        "old_native_equal_current_admission_claimed": False,
        "new_native_or_scientific_execution_claimed": False,
    }
