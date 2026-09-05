"""Ownership and size boundaries for SEAD evidence projection."""

from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.reporting.map_document.evidence_projection import sead


def test_projection_package_has_intent_named_bounded_modules() -> None:
    package_root = Path(sead.__file__).parent
    modules = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
    }

    assert frozenset(modules) == {
        "__init__.py",
        "accounting.py",
        "admission.py",
        "chronology.py",
        "detail_records.py",
        "models.py",
        "observations.py",
        "projection.py",
        "relations.py",
        "sites.py",
    }
    assert max(modules.values()) <= 260
    assert modules["__init__.py"] <= 45


def test_projection_workflow_has_one_coordinator_and_distinct_stage_owners() -> None:
    package_root = Path(sead.__file__).parent
    function_owners: dict[str, list[str]] = {}
    for module_path in package_root.glob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_owners.setdefault(node.name, []).append(module_path.name)

    assert function_owners["project_sead"] == ["projection.py"]
    assert function_owners["load_evidence_bundle"] == ["admission.py"]
    assert function_owners["index_claims"] == ["chronology.py"]
    assert function_owners["index_relations"] == ["relations.py"]
    assert function_owners["index_observations"] == ["observations.py"]
    assert function_owners["index_sites"] == ["sites.py"]
    assert function_owners["build_detail_records"] == ["detail_records.py"]
    assert function_owners["build_accounting"] == ["accounting.py"]
