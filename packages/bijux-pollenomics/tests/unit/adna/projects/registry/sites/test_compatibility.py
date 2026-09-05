"""Compatibility and ownership boundaries for sample-site registry code."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from bijux_pollenomics.adna.projects.registry import sites

_PUBLIC_CONTRACT = (
    "ADNA_LOCALITY_RESOLUTION_STATUSES",
    "AdnaProjectSampleSiteRow",
    "build_project_sample_site_rows",
    "build_project_sample_site_review_rows",
    "build_sample_site_ambiguity_ledger",
    "build_sample_site_manual_curation_queue",
    "materialize_project_sample_site_library",
)

_LEGACY_PRIVATE_FUNCTIONS = (
    "_project_by_accession",
    "_artifact_kind_from_path",
    "_project_level_locality_status",
    "_review_note_for",
    "_counts_by_status",
    "_recommended_next_surface",
    "_empty_sample_site_row",
    "_render_sample_site_ambiguity_markdown",
    "_render_sample_site_manual_queue_markdown",
    "_project_hierarchy_profiles",
    "_resolve_hierarchy",
    "_ghostscript_text",
)


def test_facade_preserves_public_and_private_import_contracts() -> None:
    assert tuple(sites.__all__) == _PUBLIC_CONTRACT
    assert all(hasattr(sites, name) for name in _PUBLIC_CONTRACT)
    assert all(callable(getattr(sites, name)) for name in _LEGACY_PRIVATE_FUNCTIONS)
    assert sites.shutil is not None
    assert sites.subprocess is not None


def test_facade_preserves_legacy_callable_signatures() -> None:
    expected = {
        "build_project_sample_site_rows": ("output_root", "project_accession"),
        "build_project_sample_site_review_rows": ("output_root",),
        "build_sample_site_ambiguity_ledger": ("output_root",),
        "build_sample_site_manual_curation_queue": ("output_root",),
        "materialize_project_sample_site_library": ("output_root",),
        "_resolve_hierarchy": (
            "hierarchy_profiles",
            "locality_text",
            "political_entity",
        ),
    }
    assert {
        name: tuple(inspect.signature(getattr(sites, name)).parameters)
        for name in expected
    } == expected


def test_functions_have_one_intent_named_owner() -> None:
    package_root = Path(sites.__file__).parent
    names = (*_PUBLIC_CONTRACT[2:], *_LEGACY_PRIVATE_FUNCTIONS)
    owners: dict[str, list[str]] = {name: [] for name in names}
    for module_path in package_root.glob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in owners:
                owners[node.name].append(module_path.name)

    assert all(len(module_owners) == 1 for module_owners in owners.values())


def test_sample_site_package_is_bounded_by_durable_responsibility() -> None:
    package_root = Path(sites.__file__).parent
    modules = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
    }

    assert frozenset(modules) == {
        "__init__.py",
        "assembly.py",
        "curation.py",
        "evidence.py",
        "hierarchy.py",
        "materialization.py",
        "records.py",
        "rendering.py",
        "review.py",
    }
    assert len(modules) <= 10
    assert max(modules.values()) <= 220
