"""Native speleothem rows keep unit references, nulls and join variants intact."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from ...client import decode_neotoma_json_object, positive_native_id
from ..resources.models import DEVELOPMENT_ROLES

_FIELDS = {
    "siteid",
    "collectionunitid",
    "entityid",
    "entityname",
    "geology",
    "rockage",
    "monitoring",
    "speleothemtype",
    "speleothemdriptype",
    "dripheight",
    "dripheightunits",
    "entitycovertype",
    "entitycoverthickness",
    "entrancedistance",
    "entrancedistanceunits",
    "landusecovertype",
    "landusecoverpercent",
    "vegetationcovertype",
    "vegetationcoverpercent",
}
_NUMBERS = {
    "dripheight",
    "entitycoverthickness",
    "entrancedistance",
    "landusecoverpercent",
    "vegetationcoverpercent",
}
_TEXT = {
    "entityname",
    "geology",
    "rockage",
    "speleothemtype",
    "speleothemdriptype",
    "dripheightunits",
    "entitycovertype",
    "landusecovertype",
    "vegetationcovertype",
}
_SOURCE_CONTRACT = {
    "repository_commit": "49c76b4c77c73025a8c0017f7b7842437161f6c1",
    "sql_blob_sha1": "6fee8407f7767c3201ed97e4e3b0c9e30cb2ce9d",
    "url": "https://github.com/NeotomaDB/api_nodetest/blob/49c76b4c77c73025a8c0017f7b7842437161f6c1/v2.0/helpers/speleothems/speleothemsbycuid.sql",
    "entrance_unit_join_target": "ndb.variableunits.variableunitsid",
    "drip_unit_projection": "resolved variableunits text",
    "deployed_version_equivalence": "not_established",
}


class _UnavailableUnitSource(ValueError):
    """The current endpoint explicitly supplied successful empty data."""


@dataclass(frozen=True)
class NeotomaUnitSource:
    body_sha256: str
    payload: dict[str, Any]
    records: list[dict[str, Any]]
    scope: dict[str, Any]


def parse_neotoma_unit_source(
    scope: dict[str, Any],
    body: bytes,
    *,
    expected_body_sha256: str,
) -> NeotomaUnitSource:
    """Preserve source entities without interpreting physical dimensions or reference data.

    HTTP custody and the full endpoint scope are authenticated by the caller.
    The API's entrance-distance unit is an integer reference; drip-height units
    are a text projection in the pinned source contract. They never substitute
    for each other or for undocumented cover-thickness/sample-depth units.
    """
    if scope.get("exposure_role") not in DEVELOPMENT_ROLES:
        raise ValueError("Unit source qualification refuses this exposure role")
    unit_id = positive_native_id(scope.get("collection_unit_id"))
    site_id = positive_native_id(scope.get("site_id"))
    if (
        scope.get("unit_key") != f"speleothem-unit-{unit_id}"
        or scope.get("resource_kind") != "speleothem"
    ):
        raise ValueError("Native unit expected scope identity is invalid")
    if sha256(body).hexdigest() != expected_body_sha256:
        raise ValueError("Unit source body identity differs")
    payload = decode_neotoma_json_object(body)
    if (
        set(payload) != {"status", "data", "message"}
        or payload["status"] != "success"
        or not isinstance(payload["message"], str)
    ):
        raise ValueError("Native unit source status or success envelope is malformed")
    rows = payload["data"]
    if not isinstance(rows, list):
        raise ValueError("Native unit data must be an explicit array")
    if not rows:
        raise _UnavailableUnitSource(
            "Unit API returned successful empty data; absence is not certified"
        )
    records = []
    for wrapper in rows:
        if not isinstance(wrapper, dict) or set(wrapper) != {"speleothem"}:
            raise ValueError("Native unit speleothem wrapper is unsupported")
        record = wrapper["speleothem"]
        if not isinstance(record, dict) or set(record) != _FIELDS:
            raise ValueError("Native unit fields are missing or unsupported")
        if (
            positive_native_id(record["siteid"]) != site_id
            or positive_native_id(record["collectionunitid"]) != unit_id
        ):
            raise ValueError(
                "Native unit or site owner differs from authenticated scope"
            )
        positive_native_id(record["entityid"])
        reference = record["entrancedistanceunits"]
        if reference is not None:
            positive_native_id(reference)
        for field in _NUMBERS:
            if record[field] is not None and type(record[field]) not in (int, float):
                raise ValueError(
                    f"Native unit {field} must be a number or explicit null"
                )
        for field in _TEXT:
            if record[field] is not None and not isinstance(record[field], str):
                raise ValueError(f"Native unit {field} must be text or explicit null")
        if record["monitoring"] is not None and type(record["monitoring"]) is not bool:
            raise ValueError("Native unit monitoring must be boolean or explicit null")
        records.append(record)
    return NeotomaUnitSource(expected_body_sha256, payload, records, scope)


def summarize_unit_source(parsed: NeotomaUnitSource) -> dict[str, Any]:
    """Count received variants separately from distinct native entities; infer no units."""
    availability = {
        field: {
            "explicit_null_rows": sum(row[field] is None for row in parsed.records),
            "non_null_rows": sum(row[field] is not None for row in parsed.records),
        }
        for field in ("vegetationcoverpercent", "landusecoverpercent")
    }
    return {
        "parser_profile": "current_native_speleothem_unit.v1",
        "received_record_rows": len(parsed.records),
        "distinct_native_entity_ids": sorted(
            {row["entityid"] for row in parsed.records}
        ),
        "native_records": parsed.records,
        "native_record_pointers": [
            f"/data/{index}/speleothem" for index in range(len(parsed.records))
        ],
        "native_owner_verification": {
            "site": "native_payload_matches_expected_scope",
            "collection_unit": "native_payload_matches_expected_scope",
            "dataset": "not_supplied",
            "database": "not_supplied",
        },
        "entrance_distance_unit_references": sorted(
            {
                row["entrancedistanceunits"]
                for row in parsed.records
                if row["entrancedistanceunits"] is not None
            }
        ),
        "unit_reference_label_resolution": "not_established",
        "unit_field_contract": {**_SOURCE_CONTRACT},
        "cover_thickness_unit": "not_established",
        "reference_field_availability": availability,
        "independent_vegetation_reference": "not_established",
        "units_interpreted": False,
        "physical_depth_or_chronology_inferred": False,
        "scientific_admission": "not_asserted",
    }
