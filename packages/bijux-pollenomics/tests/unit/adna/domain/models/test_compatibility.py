"""Dataclass and import compatibility for aDNA domain models."""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import MISSING, fields
from typing import Any

from bijux_pollenomics.adna.domain import models


def _stable_default(value: object) -> str:
    return "<MISSING>" if value is MISSING else repr(value)


def _schema(model_type: Any) -> dict[str, object]:
    return {
        "name": model_type.__name__,
        "signature": str(inspect.signature(model_type)),
        "annotations": model_type.__annotations__,
        "fields": [
            {
                "name": field.name,
                "type": str(field.type),
                "default": _stable_default(field.default),
                "factory": _stable_default(field.default_factory),
                "init": field.init,
                "repr": field.repr,
                "compare": field.compare,
                "hash": field.hash,
                "kw_only": field.kw_only,
            }
            for field in fields(model_type)
        ],
    }


def test_exports_retain_exact_order() -> None:
    assert models.__all__ == [
        "ADNA_COORDINATE_CONFIDENCE",
        "ADNA_CHRONOLOGY_EVIDENCE_CLASSES",
        "ADNA_CHRONOLOGY_PRECISION_POSTURES",
        "ADNA_COORDINATE_PROVENANCE_CLASSES",
        "ADNA_DATING_BASES",
        "ADNA_MAPPING_POSTURES",
        "AdnaChronology",
        "AdnaCoordinate",
        "AdnaCoordinateProvenanceRecord",
        "AdnaLocalityIdentity",
        "AdnaLocalitySummary",
        "AdnaSampleIdentity",
        "AdnaSampleRecord",
        "AdnaSiteEvidenceRecord",
    ]


def test_dataclass_fields_annotations_defaults_and_signatures_are_frozen() -> None:
    schemas = [
        _schema(getattr(models, name))
        for name in models.__all__
        if isinstance(getattr(models, name), type)
    ]
    payload = (
        json.dumps(schemas, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    assert len(schemas) == 8
    assert hashlib.sha256(payload).hexdigest() == (
        "100a19f57ba1aa01cf394f3d9f7bc22c36485cbd63535766f2630feecb4a574d"
    )


def test_legacy_support_imports_remain_reachable() -> None:
    assert callable(models.dataclass)
    assert callable(models.build_temporal_semantics)
