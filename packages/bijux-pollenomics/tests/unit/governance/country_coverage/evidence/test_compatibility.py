"""Compatibility and topology checks for country-coverage evidence."""

from __future__ import annotations

import ast
import inspect

import bijux_pollenomics.governance.country_coverage.evidence as evidence
from tests.support.repository import REPOSITORY_ROOT


_EXPORTED_FUNCTIONS = (
    "_cell",
    "_coverage_evidence",
    "_empty_counts",
    "_record_partition",
    "_site_partition",
    "_source_snapshot_ids",
    "_validate_sead_country_summaries",
    "_validate_stage_rows",
)

_PACKAGE_ROOT = (
    REPOSITORY_ROOT / "packages/bijux-pollenomics/src/bijux_pollenomics/governance/"
    "country_coverage/evidence"
)


def test_facade_preserves_the_legacy_callable_inventory() -> None:
    assert tuple(evidence.__all__) == _EXPORTED_FUNCTIONS
    assert all(callable(getattr(evidence, name)) for name in _EXPORTED_FUNCTIONS)


def test_facade_preserves_legacy_function_signatures() -> None:
    parameters = {
        name: tuple(inspect.signature(getattr(evidence, name)).parameters)
        for name in _EXPORTED_FUNCTIONS
    }
    assert parameters == {
        "_cell": (
            "source_family",
            "dimension",
            "country_code",
            "evidence",
            "stage",
            "snapshot_id",
            "boundary_digest",
            "config_digest",
            "build_id",
        ),
        "_coverage_evidence": (
            "documents",
            "input_bytes",
            "boundary_digest",
            "boundary_version",
            "boundary_collections",
            "boundary_counts",
            "sead_claim_document",
        ),
        "_empty_counts": (),
        "_record_partition": (
            "evidence",
            "source",
            "dimension",
            "values",
            "published",
        ),
        "_site_partition": (
            "evidence",
            "source",
            "dimension",
            "values",
            "published",
        ),
        "_source_snapshot_ids": ("collection", "documents", "input_bytes"),
        "_validate_sead_country_summaries": (
            "admission",
            "decisions",
            "decision_count",
            "decision_statuses",
            "decision_methods",
            "decision_country_codes",
            "governed",
            "boundary_digest",
            "boundary_version",
            "country_assignment_sha256",
            "boundary_counts",
            "boundary_manifest",
            "boundary_manifest_sha256",
        ),
        "_validate_stage_rows": ("rows",),
    }


def test_legacy_functions_have_one_implementation_owner() -> None:
    owners: dict[str, list[str]] = {name: [] for name in _EXPORTED_FUNCTIONS}
    for module_path in _PACKAGE_ROOT.glob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in owners:
                owners[node.name].append(module_path.name)
    assert owners == {
        "_cell": ["model.py"],
        "_coverage_evidence": ["ledger.py"],
        "_empty_counts": ["partitions.py"],
        "_record_partition": ["partitions.py"],
        "_site_partition": ["partitions.py"],
        "_source_snapshot_ids": ["snapshots.py"],
        "_validate_sead_country_summaries": ["sead_validation.py"],
        "_validate_stage_rows": ["model.py"],
    }


def test_package_has_bounded_intent_modules() -> None:
    modules = sorted(
        path for path in _PACKAGE_ROOT.glob("*.py") if path.name != "__init__.py"
    )
    packages = sorted(path for path in _PACKAGE_ROOT.iterdir() if path.is_dir())
    assert len(modules) <= 10
    assert {path.stem for path in modules} == {
        "landclim",
        "ledger",
        "model",
        "neotoma",
        "partitions",
        "sead",
        "sead_validation",
        "snapshots",
        "supplementary",
    }
    assert {path.name for path in packages if path.name != "__pycache__"} == {
        "sead_decisions"
    }
    line_counts = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in modules
    }
    assert max(line_counts.values()) <= 220
