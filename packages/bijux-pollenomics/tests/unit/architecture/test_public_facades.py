"""Keep source-only imports independent while preserving actual public owners."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from tests.support.repository import REPOSITORY_ROOT


def _run(script: str) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        str(REPOSITORY_ROOT / "packages" / package / "src")
        for package in ("bijux-pollenomics", "bijux-pollenomics-dev", "pollenomics")
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", textwrap.dedent(script)],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_capture_import_succeeds_with_reporting_disabled() -> None:
    _run(
        """
        import importlib
        import importlib.abc
        import sys

        class ReportingUnavailable(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == 'bijux_pollenomics.reporting' or fullname.startswith('bijux_pollenomics.reporting.'):
                    raise ModuleNotFoundError('Reporting deliberately unavailable')

        sys.meta_path.insert(0, ReportingUnavailable())
        capture = importlib.import_module('bijux_pollenomics.collection.sources.neotoma.capture')
        assert callable(capture.capture_neotoma_metadata)
        forbidden = ('reporting', 'analysis', 'evidence', 'adna', 'collection.workflow', 'collection.sources.neotoma.materialization', 'collection.sources.neotoma.resource_catalogue')
        for owner in forbidden:
            prefix = 'bijux_pollenomics.' + owner
            assert not any(name == prefix or name.startswith(prefix + '.') for name in sys.modules), prefix
        """
    )


@pytest.mark.parametrize(
    "module_name,child",
    (
        ("bijux_pollenomics", "reporting"),
        ("bijux_pollenomics.collection", "workflow"),
        ("bijux_pollenomics.collection.sources.neotoma", "materialization"),
    ),
)
def test_discovery_is_lazy_and_named_child_keeps_module_identity(
    module_name: str, child: str
) -> None:
    _run(
        f"""
        import importlib
        import sys
        module = importlib.import_module({module_name!r})
        child_name = module.__name__ + '.' + {child!r}
        assert child_name not in sys.modules
        before = set(sys.modules)
        assert set(module.__all__) <= set(dir(module))
        assert {child!r} in dir(module)
        assert set(sys.modules) == before
        try:
            getattr(module, 'unknown_public_facade_attribute')
        except AttributeError:
            pass
        else:
            raise AssertionError('Unknown attribute must refuse')
        assert set(sys.modules) == before
        assert getattr(module, {child!r}) is importlib.import_module(child_name)
        """
    )


def test_public_objects_star_imports_and_cached_replacements() -> None:
    _run(
        """
        import importlib
        import inspect
        import pickle

        for name, contract in CONTRACTS.items():
            module = importlib.import_module(name)
            expected_all, owners = contract
            assert module.__all__ == expected_all
            namespace = {}
            exec('from ' + name + ' import *', namespace)
            assert set(namespace) - {'__builtins__'} == set(expected_all)
            for public_name, (owner_name, owner_attribute) in owners.items():
                owner = importlib.import_module(owner_name, name)
                actual = getattr(module, public_name)
                expected = getattr(owner, owner_attribute)
                assert actual is expected, (name, public_name)
                assert namespace[public_name] is expected
                assert inspect.signature(actual) == inspect.signature(expected) if callable(actual) else True
                if inspect.isclass(actual):
                    assert pickle.loads(pickle.dumps(actual)) is actual
            selected = next(iter(owners))
            replacement = object()
            setattr(module, selected, replacement)
            assert getattr(module, selected) is replacement
            assert module.__getattr__(selected) is replacement

        from bijux_pollenomics import collect_data
        from pollenomics import collect_data as alias_collect_data
        assert collect_data is alias_collect_data
        """.replace("CONTRACTS", repr(_CONTRACTS))
    )


def test_collection_wrapper_retains_module_global_collection_seam() -> None:
    _run(
        """
        from datetime import date
        import importlib
        from pathlib import Path
        from types import SimpleNamespace
        from bijux_pollenomics import collect_context_data
        from bijux_pollenomics.collection import collect_context_data as public_wrapper
        api = importlib.import_module('bijux_pollenomics.collection.api')
        calls = []
        def collect(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(generated_on=date(2000, 1, 1), output_root=Path('source-root'), landclim_site_count=1, landclim_grid_cell_count=2, landclim_temporal_grid_feature_count=3, neotoma_point_count=4, sead_point_count=5, raa_total_site_count=6, raa_heritage_site_count=7, svar_lake_count=8)
        api.collect_data = collect
        assert collect_context_data is public_wrapper is api.collect_context_data
        report = public_wrapper(Path('requested-root'))
        assert calls == [{'output_root': Path('requested-root'), 'sources': ('boundaries', 'landclim', 'neotoma', 'sead', 'raa', 'svar')}]
        assert report.neotoma_point_count == 4
        assert report.output_root == Path('source-root')
        """
    )


def test_static_public_types_reject_undeclared_names(tmp_path: Path) -> None:
    """A dynamic runtime fallback must not turn misspelled static APIs into Any."""
    consumer = tmp_path / "public_facade_consumer.py"
    consumer.write_text(
        "from typing import assert_type\n"
        "import bijux_pollenomics as public\n"
        "import bijux_pollenomics.collection as collection\n"
        "import bijux_pollenomics.collection.sources.neotoma as neotoma\n"
        "from bijux_pollenomics.architecture import RuntimeSurfaceContract\n"
        "assert_type(public.runtime_surface_contract(), RuntimeSurfaceContract)\n"
        "public.unknown_public_facade_attribute()\n"
        "collection.unknown_public_facade_attribute()\n"
        "neotoma.unknown_public_facade_attribute()\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "mypy",
            "--config-file",
            "configs/mypy.ini",
            "--follow-imports=silent",
            "--cache-dir",
            str(tmp_path / "mypy-cache"),
            str(consumer),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    errors = [line for line in result.stdout.splitlines() if "[attr-defined]" in line]
    assert len(errors) == 3, result.stdout + result.stderr
    assert "[assert-type]" not in result.stdout


_CONTRACTS: dict[str, tuple[list[str], dict[str, tuple[str, str]]]] = {
    "bijux_pollenomics": (
        [
            "CompatibilityAliasContract",
            "ContextDataReport",
            "CountryReport",
            "DataCollectionReport",
            "MultiCountryMapReport",
            "OwnershipMapEntry",
            "ProductScope",
            "PublishedReportsReport",
            "RuntimeSurfaceContract",
            "SurfaceMap",
            "__version__",
            "build_ownership_map",
            "build_product_scope",
            "build_surface_map",
            "collect_context_data",
            "collect_data",
            "compatibility_alias_contract",
            "generate_country_report",
            "generate_multi_country_map",
            "generate_published_reports",
            "runtime_surface_contract",
        ],
        {
            "CompatibilityAliasContract": (
                ".architecture",
                "CompatibilityAliasContract",
            ),
            "OwnershipMapEntry": (".architecture", "OwnershipMapEntry"),
            "ProductScope": (".architecture", "ProductScope"),
            "RuntimeSurfaceContract": (".architecture", "RuntimeSurfaceContract"),
            "SurfaceMap": (".architecture", "SurfaceMap"),
            "build_ownership_map": (".architecture", "build_ownership_map"),
            "build_product_scope": (".architecture", "build_product_scope"),
            "build_surface_map": (".architecture", "build_surface_map"),
            "compatibility_alias_contract": (
                ".architecture",
                "compatibility_alias_contract",
            ),
            "runtime_surface_contract": (".architecture", "runtime_surface_contract"),
            "ContextDataReport": (".collection.api", "ContextDataReport"),
            "DataCollectionReport": (".collection.api", "DataCollectionReport"),
            "collect_context_data": (".collection.api", "collect_context_data"),
            "collect_data": (".collection.api", "collect_data"),
            "CountryReport": (".reporting.api", "CountryReport"),
            "MultiCountryMapReport": (".reporting.api", "MultiCountryMapReport"),
            "PublishedReportsReport": (".reporting.api", "PublishedReportsReport"),
            "generate_country_report": (".reporting.api", "generate_country_report"),
            "generate_multi_country_map": (
                ".reporting.api",
                "generate_multi_country_map",
            ),
            "generate_published_reports": (
                ".reporting.api",
                "generate_published_reports",
            ),
        },
    ),
    "bijux_pollenomics.collection": (
        [
            "AVAILABLE_SOURCES",
            "SOURCE_IDENTITIES",
            "AadrAnnoDownloadReport",
            "ContextDataReport",
            "DataCollectionReport",
            "DataCollectionSummary",
            "SourceAcquisitionMetadata",
            "SourceHashes",
            "SourceIdentity",
            "SourceProvenanceRecord",
            "SourceReplacementRule",
            "SourceSupportStatus",
            "SourceTraceabilityRecord",
            "build_source_hashes",
            "build_source_provenance",
            "build_source_replacement_rules",
            "build_source_support_matrix",
            "build_source_traceability_records",
            "collect_context_data",
            "collect_data",
            "download_aadr_anno_files",
            "validate_collection_summary_file",
            "validate_collection_summary_payload",
        ],
        {
            "AVAILABLE_SOURCES": (".api", "AVAILABLE_SOURCES"),
            "SOURCE_IDENTITIES": (".api", "SOURCE_IDENTITIES"),
            "AadrAnnoDownloadReport": (".api", "AadrAnnoDownloadReport"),
            "ContextDataReport": (".api", "ContextDataReport"),
            "DataCollectionReport": (".api", "DataCollectionReport"),
            "DataCollectionSummary": (".api", "DataCollectionSummary"),
            "SourceAcquisitionMetadata": (".api", "SourceAcquisitionMetadata"),
            "SourceHashes": (".api", "SourceHashes"),
            "SourceIdentity": (".api", "SourceIdentity"),
            "SourceProvenanceRecord": (".api", "SourceProvenanceRecord"),
            "SourceReplacementRule": (".api", "SourceReplacementRule"),
            "SourceSupportStatus": (".api", "SourceSupportStatus"),
            "SourceTraceabilityRecord": (".api", "SourceTraceabilityRecord"),
            "build_source_hashes": (".api", "build_source_hashes"),
            "build_source_provenance": (".api", "build_source_provenance"),
            "build_source_replacement_rules": (
                ".api",
                "build_source_replacement_rules",
            ),
            "build_source_support_matrix": (".api", "build_source_support_matrix"),
            "build_source_traceability_records": (
                ".api",
                "build_source_traceability_records",
            ),
            "collect_context_data": (".api", "collect_context_data"),
            "collect_data": (".api", "collect_data"),
            "download_aadr_anno_files": (".api", "download_aadr_anno_files"),
            "validate_collection_summary_file": (
                ".api",
                "validate_collection_summary_file",
            ),
            "validate_collection_summary_payload": (
                ".api",
                "validate_collection_summary_payload",
            ),
        },
    ),
    "bijux_pollenomics.collection.sources.neotoma": (
        [
            "build_neotoma_bbox_geojson",
            "build_neotoma_download_archive_parts",
            "build_neotoma_relational_snapshot",
            "build_neotoma_site_country_decisions",
            "build_neotoma_site_rows_from_downloads",
            "build_neotoma_site_snapshot_rows",
            "build_neotoma_temporal_review",
            "classify_neotoma_site_country",
            "extract_neotoma_download_dataset_ids",
            "fetch_neotoma_api_payload",
            "fetch_neotoma_api_rows",
            "fetch_neotoma_dataset_download_row",
            "fetch_neotoma_dataset_download_rows",
            "fetch_neotoma_dataset_inventory_rows",
            "materialize_neotoma_relational_snapshot",
            "neotoma_download_dataset_id",
            "neotoma_site_raw_country",
            "normalize_neotoma_rows",
            "render_neotoma_temporal_review_markdown",
            "validate_neotoma_download_coverage",
            "write_neotoma_download_archive",
            "write_neotoma_review_outputs",
        ],
        {
            "build_neotoma_download_archive_parts": (
                ".archive",
                "build_neotoma_download_archive_parts",
            ),
            "write_neotoma_download_archive": (
                ".archive",
                "write_neotoma_download_archive",
            ),
            "build_neotoma_bbox_geojson": (".client", "build_neotoma_bbox_geojson"),
            "extract_neotoma_download_dataset_ids": (
                ".client",
                "extract_neotoma_download_dataset_ids",
            ),
            "fetch_neotoma_api_payload": (".client", "fetch_neotoma_api_payload"),
            "fetch_neotoma_api_rows": (".client", "fetch_neotoma_api_rows"),
            "fetch_neotoma_dataset_download_row": (
                ".client",
                "fetch_neotoma_dataset_download_row",
            ),
            "fetch_neotoma_dataset_download_rows": (
                ".client",
                "fetch_neotoma_dataset_download_rows",
            ),
            "fetch_neotoma_dataset_inventory_rows": (
                ".client",
                "fetch_neotoma_dataset_inventory_rows",
            ),
            "neotoma_download_dataset_id": (".client", "neotoma_download_dataset_id"),
            "validate_neotoma_download_coverage": (
                ".client",
                "validate_neotoma_download_coverage",
            ),
            "normalize_neotoma_rows": (".context_points", "normalize_neotoma_rows"),
            "build_neotoma_site_country_decisions": (
                ".country",
                "build_neotoma_site_country_decisions",
            ),
            "classify_neotoma_site_country": (
                ".country",
                "classify_neotoma_site_country",
            ),
            "neotoma_site_raw_country": (".country", "neotoma_site_raw_country"),
            "materialize_neotoma_relational_snapshot": (
                ".materialization",
                "materialize_neotoma_relational_snapshot",
            ),
            "build_neotoma_relational_snapshot": (
                ".relational",
                "build_neotoma_relational_snapshot",
            ),
            "build_neotoma_temporal_review": (
                ".review",
                "build_neotoma_temporal_review",
            ),
            "render_neotoma_temporal_review_markdown": (
                ".review",
                "render_neotoma_temporal_review_markdown",
            ),
            "write_neotoma_review_outputs": (".review", "write_neotoma_review_outputs"),
            "build_neotoma_site_rows_from_downloads": (
                ".site_inventory",
                "build_neotoma_site_rows_from_downloads",
            ),
            "build_neotoma_site_snapshot_rows": (
                ".site_inventory",
                "build_neotoma_site_snapshot_rows",
            ),
        },
    ),
}
