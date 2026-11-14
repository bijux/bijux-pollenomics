"""Type-specific native summaries without interpreting proxy units or frozen schemas."""

from __future__ import annotations

import json
from typing import Any

from ...client import _validated_neotoma_rows, neotoma_download_dataset_id
from ...site_inventory.connected_resources import positive_native_id
from .models import NeotomaResourceSpec

_TYPES = {
    "pollen": "pollen_assemblage",
    "geochronologic": "dating_controls",
    "loss-on-ignition": "sediment_proxy",
    "charcoal": "charcoal_proxy",
    "microcharcoal": "charcoal_proxy",
    "plant macrofossil": "macrofossil_proxy",
    "pollen trap": "pollen_monitoring",
    "testate amoebae": "amoebae_proxy",
}


def classify_body(
    resource: NeotomaResourceSpec, version: str, body: bytes
) -> tuple[str, dict[str, Any]]:
    if version == "doi_frozen":
        return "unresolved_frozen_schema", {
            "parser_profile": "doi_frozen_unqualified.v1",
            "reason": "Provider DOI-mint snapshot schema requires source qualification; no current-shape assumption",
        }
    if resource.dataset_type not in _TYPES:
        return "unsupported_dataset_type", {
            "parser_profile": "unregistered_current_type.v1"
        }
    try:
        payload = json.loads(body)
        rows = _validated_neotoma_rows(payload)
        if payload.get("status") != "success":
            raise ValueError("Unsuccessful native source status")
        if not rows:
            return "unavailable_api_empty", {
                "parser_profile": "current_native_hierarchy.v1",
                "absence_certified": False,
            }
        if len(rows) != 1:
            raise ValueError("Native download must identify exactly one dataset")
        row = rows[0]
        if (
            neotoma_download_dataset_id(row, clean_optional_text_fn=str)
            != resource.dataset_id
        ):
            raise ValueError("Native dataset identities differ")
        site = row.get("site")
        unit = site.get("collectionunit") if isinstance(site, dict) else None
        if (
            not isinstance(site, dict)
            or not isinstance(unit, dict)
            or positive_native_id(site.get("siteid")) != resource.site_id
            or positive_native_id(unit.get("collectionunitid"))
            != resource.collection_unit_id
        ):
            raise ValueError("Native site or collection unit owner differs")
        for dataset in (site.get("dataset"), unit.get("dataset")):
            if (
                not isinstance(dataset, dict)
                or dataset.get("datasettype") != resource.dataset_type
                or "database" not in dataset
                or dataset["database"] != resource.database
            ):
                raise ValueError("Native dataset type/database differs")
        dataset = unit["dataset"]
        samples = dataset.get("samples")
        population = "array"
        if not isinstance(samples, list):
            if resource.dataset_type != "geochronologic":
                raise ValueError("Native samples must be an array")
            population = (
                "missing"
                if "samples" not in dataset
                else "null"
                if samples is None
                else "unsupported"
            )
            samples = []
            if population == "unsupported":
                raise ValueError("Geochronologic sample population malformed")
        identified = 0
        datum_rows = 0
        units = set()
        for sample in samples:
            if not isinstance(sample, dict):
                raise ValueError("Native sample row malformed")
            identified += int(
                type(sample.get("sampleid")) is int and sample["sampleid"] > 0
            )
            datums = sample.get("datum", [])
            if not isinstance(datums, list):
                raise ValueError("Native datum population malformed")
            for datum in datums:
                if not isinstance(datum, dict):
                    raise ValueError("Native datum row malformed")
                datum_rows += 1
                value = datum.get("units")
                if value is not None and not isinstance(value, str):
                    raise ValueError("Native source unit malformed")
                units.add(value)
        return "parsed_native", {
            "parser_profile": "current_native_hierarchy.v1",
            "dataset_type": resource.dataset_type,
            "database": resource.database,
            "resource_role": _TYPES[resource.dataset_type],
            "sample_population": population,
            "sample_rows": len(samples),
            "identified_samples": identified,
            "unidentified_sample_rows": len(samples) - identified,
            "datum_rows": datum_rows,
            "source_units": sorted(
                units, key=lambda value: (value is not None, str(value))
            ),
            "units_interpreted": False,
        }
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        return "refused_native_protocol", {
            "parser_profile": "current_native_hierarchy.v1",
            "reason": str(error),
        }
