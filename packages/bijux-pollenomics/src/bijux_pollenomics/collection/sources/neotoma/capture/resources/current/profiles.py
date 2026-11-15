"""Native proxy fields retain literal scalar kinds without assemblage assumptions."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from ....client import (
    _validated_neotoma_rows,
    decode_neotoma_json_object,
    positive_native_id,
    validate_neotoma_selected_download,
)
from ..models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
)
from ..protocol import validate_plan

CURRENT_SOURCE_TYPES = frozenset(
    {
        "pollen surface sample",
        "ostracode surface sample",
        "testate amoebae surface sample",
        "speleothem",
        "dinoflagellates",
    }
)
_CONTEXT_FIELDS = (
    "taxonid",
    "variablename",
    "element",
    "elementtype",
    "units",
    "taxongroup",
    "ecologicalgroup",
    "context",
    "symmetry",
)


class _UnavailableCurrentSource(ValueError):
    """The authenticated current endpoint explicitly returned successful empty data."""


@dataclass(frozen=True)
class NeotomaCurrentSource:
    """Source-owned values; no chronology, vegetation or count-denominator admission."""

    parser_profile: str
    body_sha256: str
    payload: dict[str, Any]
    site: dict[str, Any]
    collection_unit: dict[str, Any]
    dataset: dict[str, Any]
    samples: list[dict[str, Any]]


def _optional_id(record: dict[str, Any], field: str) -> None:
    if field in record and record[field] is not None:
        positive_native_id(record[field])


def _samples(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("Native current sample population must be an explicit array")
    for sample in value:
        if not isinstance(sample, dict):
            raise ValueError("Native current sample must be an object")
        _optional_id(sample, "sampleid")
        _optional_id(sample, "analysisunitid")
        datums = sample.get("datum")
        if not isinstance(datums, list):
            raise ValueError(
                "Native current datum population must be an explicit array"
            )
        for datum in datums:
            required = set(_CONTEXT_FIELDS) - {"taxonid"} | {"value"}
            if not isinstance(datum, dict) or not required <= set(datum):
                raise ValueError("Native current datum fields are missing or malformed")
            _optional_id(datum, "taxonid")
            if datum["value"] is not None and type(datum["value"]) not in (int, float):
                raise ValueError(
                    "Native current value must be a number or explicit null"
                )
            for field in _CONTEXT_FIELDS[1:]:
                if datum[field] is not None and not isinstance(datum[field], str):
                    raise ValueError(
                        f"Native current {field} must be text or explicit null"
                    )
    return value


def parse_neotoma_current_source(
    resource: NeotomaResourceSpec, body: bytes, *, expected_body_sha256: str
) -> NeotomaCurrentSource:
    """Qualify five observed current layouts while preserving their native measures.

    The caller authenticates HTTP custody separately. Native variable IDs may
    identify parameters; neither their presence nor a unit label establishes a
    biological count, a denominator, a physical sample depth or method eligibility.
    """
    validate_plan(NeotomaResourcePlan((resource,), "0" * 64), DEFAULT_RESOURCE_LIMITS)
    if resource.exposure_role not in DEVELOPMENT_ROLES:
        raise ValueError("Current source qualification refuses this exposure role")
    if resource.dataset_type not in CURRENT_SOURCE_TYPES:
        raise ValueError("Current source type has no observed native profile")
    if not isinstance(resource.database, str):
        raise ValueError(
            "Current source profile requires observed native database text"
        )
    if sha256(body).hexdigest() != expected_body_sha256:
        raise ValueError("Current source body identity differs")
    payload = decode_neotoma_json_object(body)
    if payload.get("status") != "success":
        raise ValueError("Current native source status is unsuccessful")
    rows = _validated_neotoma_rows(payload)
    if not rows:
        raise _UnavailableCurrentSource(
            "Current API returned successful empty data; absence is not certified"
        )
    if len(rows) != 1:
        raise ValueError("Current source must identify exactly one native dataset")
    site = rows[0].get("site")
    unit = site.get("collectionunit") if isinstance(site, dict) else None
    if not isinstance(site, dict) or not isinstance(unit, dict):
        raise ValueError("Current native site or collection unit is malformed")
    for dataset in (site.get("dataset"), unit.get("dataset")):
        if not isinstance(dataset, dict):
            raise ValueError("Current native dataset declaration is missing")
        positive_native_id(dataset.get("datasetid"))
    validate_neotoma_selected_download(
        rows[0],
        expected_dataset_id=resource.dataset_id,
        expected_site_id=resource.site_id,
        expected_collection_unit_id=resource.collection_unit_id,
        expected_dataset_type=resource.dataset_type,
        expected_database=resource.database,
    )
    dataset = unit["dataset"]
    samples = _samples(dataset.get("samples"))
    return NeotomaCurrentSource(
        "current_native_proxy_hierarchy.v1",
        expected_body_sha256,
        payload,
        site,
        unit,
        dataset,
        samples,
    )


def summarize_current_source(parsed: NeotomaCurrentSource) -> dict[str, Any]:
    """Keep source contexts paired; no summation, rounding, depth or time inference."""
    datums = [datum for sample in parsed.samples for datum in sample["datum"]]
    contexts = {}
    for datum in datums:
        context = {key: datum[key] for key in _CONTEXT_FIELDS if key in datum}
        contexts[json.dumps(context, sort_keys=True)] = context
    identified = sum(
        type(s.get("sampleid")) is int and s["sampleid"] > 0 for s in parsed.samples
    )
    return {
        "parser_profile": parsed.parser_profile,
        "dataset_type": parsed.dataset["datasettype"],
        "sample_population": "array",
        "sample_rows": len(parsed.samples),
        "identified_sample_rows": identified,
        "unidentified_sample_rows": len(parsed.samples) - identified,
        "datum_rows": len(datums),
        "source_units": sorted(
            {d["units"] for d in datums}, key=lambda v: (v is not None, str(v))
        ),
        "native_contexts": [contexts[key] for key in sorted(contexts)],
        "native_samples_pointer": "/data/0/site/collectionunit/dataset/samples",
        "units_interpreted": False,
        "biological_denominator": "not_established",
        "physical_depth_or_chronology_inferred": False,
        "scientific_admission": "not_asserted",
    }
