"""Dataclass and import compatibility for aDNA domain models."""

from __future__ import annotations

from dataclasses import MISSING, fields
import hashlib
import inspect
import json
from typing import Any, cast

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
        _frozen_schema(getattr(models, name))
        for name in models.__all__
        if isinstance(getattr(models, name), type)
    ]
    payload = (
        json.dumps(schemas, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    assert len(schemas) == 8
    assert hashlib.sha256(payload).hexdigest() == (
        "caedd1facb198063cf0897f58c6f813ec944398d241b2561b7b42a6ff7079bd0"
    )


def test_legacy_support_imports_remain_reachable() -> None:
    assert callable(models.dataclass)
    assert callable(models.build_temporal_semantics)


def _frozen_schema(model_type: Any) -> dict[str, object]:
    schema = _schema(model_type)
    if model_type is not models.AdnaLocalitySummary:
        return schema
    current = cast(list[dict[str, object]], schema["fields"])
    assert current[-1] == {
        "name": "sample_chronologies",
        "type": "tuple[AdnaSampleChronologySupport, ...]",
        "default": "()",
        "factory": "<MISSING>",
        "init": True,
        "repr": True,
        "compare": True,
        "hash": None,
        "kw_only": False,
    }
    signature = inspect.signature(model_type)
    assert tuple(signature.parameters)[-1] == "sample_chronologies"
    # Freeze every preexisting field and positional argument independently of
    # the explicitly admitted optional occurrence-support extension.
    schema["fields"] = current[:-1]
    annotations = dict(model_type.__annotations__)
    assert annotations.pop("sample_chronologies") == (
        "tuple[AdnaSampleChronologySupport, ...]"
    )
    schema["annotations"] = annotations
    schema["signature"] = str(
        signature.replace(
            parameters=[
                parameter
                for name, parameter in signature.parameters.items()
                if name != "sample_chronologies"
            ]
        )
    )
    return schema
