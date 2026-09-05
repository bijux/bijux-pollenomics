"""Durable package boundary tests for source chronology nodes."""

from __future__ import annotations

from pathlib import Path

import bijux_pollenomics.analysis.propagation.source_chronology as facade


def test_facade_exports_only_the_governed_source_node_surface() -> None:
    assert facade.__all__ == [
        "CountrySourceNodeReconciliation",
        "SOURCE_NODE_CONFIG_DIGEST",
        "SourceChronologyNode",
        "SourceNodeAdmissionRefusal",
        "SourceNodeContext",
        "SourceNodeDerivationResult",
        "SourceNodeFacetRefusal",
        "SourceNodeMaterializationResult",
        "SourceNodeReconciliation",
        "derive_neotoma_source_chronology_nodes",
        "materialize_source_chronology_nodes",
        "source_node_config_payload",
    ]


def test_source_package_is_bounded_and_grouped_by_intent() -> None:
    package = Path(facade.__file__).parent
    direct_modules = [
        path for path in package.glob("*.py") if path.name != "__init__.py"
    ]
    modules = list(package.rglob("*.py"))

    assert len(direct_modules) <= 10
    assert (
        max(len(path.read_text(encoding="utf-8").splitlines()) for path in modules)
        <= 220
    )
