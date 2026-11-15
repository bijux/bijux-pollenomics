"""Observed contributor, DOI and site shapes with exact native parent links."""

from __future__ import annotations

from typing import Any

from ...client import positive_native_id
from ..resources.models import NeotomaResourceSpec


def _fields(value: Any, names: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != names:
        raise ValueError(f"unobserved {label} fields")
    return value


def _rows(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} must be an array of native objects")
    return value


def _text(value: Any, label: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{label} must be native text or explicit null")


def _dataset(value: Any, resource: NeotomaResourceSpec) -> None:
    if positive_native_id(value) != resource.dataset_id:
        raise ValueError("native association dataset differs from requested owner")


def _contacts(rows: list[dict[str, Any]], resource: NeotomaResourceSpec) -> int:
    count = 0
    for row in rows:
        _fields(row, {"contacts"}, "contact wrapper")
        association = _fields(
            row["contacts"], {"contacts", "datasetid"}, "dataset contacts"
        )
        _dataset(association["datasetid"], resource)
        for contact in _rows(association["contacts"], "contacts"):
            _fields(
                contact,
                {
                    "url",
                    "email",
                    "address",
                    "fullname",
                    "lastname",
                    "firstname",
                    "contactid",
                },
                "contact",
            )
            positive_native_id(contact["contactid"])
            for field in (
                "url",
                "email",
                "address",
                "fullname",
                "lastname",
                "firstname",
            ):
                _text(contact[field], "contact." + field)
            count += 1
    return count


def _dois(rows: list[dict[str, Any]], resource: NeotomaResourceSpec) -> int:
    for row in rows:
        _fields(row, {"datasetid", "dois"}, "dataset DOI")
        _dataset(row["datasetid"], resource)
        _text(row["dois"], "dois")
    return len(rows)


def _sites(rows: list[dict[str, Any]], resource: NeotomaResourceSpec) -> int:
    selected = []
    for site in rows:
        _fields(
            site,
            {
                "siteid",
                "sitename",
                "sitedescription",
                "geography",
                "altitude",
                "recdatecreated",
                "collectionunits",
            },
            "site",
        )
        if positive_native_id(site["siteid"]) != resource.site_id:
            raise ValueError("native site differs from requested dataset site")
        for field in ("sitename", "sitedescription", "geography", "recdatecreated"):
            _text(site[field], "site." + field)
        if site["altitude"] is not None and type(site["altitude"]) not in (int, float):
            raise ValueError("site.altitude must be a native number or explicit null")
        for unit in _rows(site["collectionunits"], "collectionunits"):
            _fields(
                unit,
                {
                    "handle",
                    "datasets",
                    "collectionunit",
                    "collectionunitid",
                    "collectionunittype",
                },
                "collection unit",
            )
            unit_id = positive_native_id(unit["collectionunitid"])
            for field in ("handle", "collectionunit", "collectionunittype"):
                _text(unit[field], "collectionunit." + field)
            for dataset in _rows(unit["datasets"], "datasets"):
                _fields(dataset, {"datasetid", "datasettype"}, "site dataset")
                dataset_id = positive_native_id(dataset["datasetid"])
                if not isinstance(dataset["datasettype"], str):
                    raise ValueError("native dataset type must be text")
                if dataset_id == resource.dataset_id:
                    selected.append((unit_id, dataset["datasettype"]))
    if rows and selected != [(resource.collection_unit_id, resource.dataset_type)]:
        raise ValueError(
            "native site dataset/core/type association differs or is ambiguous"
        )
    return len(rows)


def qualify_association(
    data: Any, resource: NeotomaResourceSpec, facet: str
) -> tuple[int, dict[str, str]]:
    """Describe source association rows without normalizing DOI or geographic values."""
    rows = _rows(data, facet + " data")
    if facet == "contacts":
        count = _contacts(rows, resource)
    elif facet == "doi":
        count = _dois(rows, resource)
    elif facet == "sites":
        count = _sites(rows, resource)
    else:
        raise ValueError("association source profile is not registered")
    owners = {"dataset": "native_payload_matches_request"} if rows else {}
    if facet == "sites" and rows:
        owners.update(
            site="native_payload_matches_request",
            collection_unit="native_payload_matches_request",
            dataset_type="native_payload_matches_request",
        )
    return count, owners
