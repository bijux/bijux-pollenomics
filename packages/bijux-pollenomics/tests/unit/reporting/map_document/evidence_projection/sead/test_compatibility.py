"""Compatibility tests for the SEAD projection facade."""

from __future__ import annotations

import inspect

from bijux_pollenomics.reporting.map_document.evidence_projection import sead
from bijux_pollenomics.reporting.map_document.evidence_projection.sead import (
    _object_rows,
    _project_sead,
    _reconcile_sead_relation_denominators,
    _site_by_entity_owner,
    _validate_sead_evidence_headers,
)


def test_facade_preserves_projection_contract_and_pinned_bindings() -> None:
    assert not hasattr(sead, "__all__")
    assert sead._project_sead is _project_sead
    assert tuple(inspect.signature(_project_sead).parameters) == (
        "context_root",
        "layers",
    )
    assert all(
        hasattr(sead, name)
        for name in (
            "SEAD_GOVERNED_ADMISSION_SHA256",
            "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
            "SEAD_GOVERNED_EVIDENCE_RUN_ID",
        )
    )


def test_facade_preserves_private_helper_imports_and_signatures() -> None:
    assert tuple(inspect.signature(_object_rows).parameters) == (
        "document",
        "field",
        "label",
    )
    assert tuple(inspect.signature(_validate_sead_evidence_headers).parameters) == (
        "claims",
        "observations",
        "relations",
        "events",
    )
    assert tuple(
        inspect.signature(_reconcile_sead_relation_denominators).parameters
    ) == (
        "relation_index",
        "entity_rows",
        "taxon_rows",
        "dimension_rows",
        "dimension_semantic_rows",
        "dataset_semantic_rows",
        "value_semantic_rows",
    )
    assert tuple(inspect.signature(_site_by_entity_owner).parameters) == (
        "entity_rows",
        "owner_field",
    )
