"""Compatibility and patch-seam tests for the Neotoma facade."""

from __future__ import annotations

import inspect

import pytest
from bijux_pollenomics.evidence.classification import neotoma

from .support import representative_snapshot


def test_facade_preserves_public_and_private_surface() -> None:
    assert neotoma.__all__ == ["build_neotoma_classification_accounting"]
    assert str(inspect.signature(neotoma.build_neotoma_classification_accounting)) == (
        "(relational_snapshot: 'Mapping[str, object]') -> 'dict[str, object]'"
    )
    for name in (
        "_canonical_json",
        "_concept_id",
        "_country_partition_rows",
        "_deduplicate_observations",
        "_mapping_posture",
        "_qualifier_markers",
        "_source_concept_identity",
    ):
        assert callable(getattr(neotoma, name))


def test_accounting_uses_facade_patch_seams(monkeypatch: pytest.MonkeyPatch) -> None:
    original = neotoma._canonical_json
    calls = 0

    def canonical_json(value: object) -> str:
        nonlocal calls
        calls += 1
        return original(value)

    monkeypatch.setattr(neotoma, "_canonical_json", canonical_json)

    payload = neotoma.build_neotoma_classification_accounting(representative_snapshot())

    assert calls >= 5
    assert payload["schema_version"] == "neotoma-classification-accounting.v1"
