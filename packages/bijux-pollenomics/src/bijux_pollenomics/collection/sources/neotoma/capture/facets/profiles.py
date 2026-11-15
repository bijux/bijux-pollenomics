"""Derived native facet shapes without chronology selection or scientific admission."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from ...client import decode_neotoma_json_object, positive_native_id
from ..resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceSpec,
)
from ..resources.protocol import identity
from .models import NeotomaFacetPlan
from .protocol import validate_plan

PROFILE_SCHEMA = "neotoma-dataset-facet-source-profile.v1"
_TAXON_FIELDS = {
    "taxonid",
    "taxonname",
    "author",
    "ecolgroup",
    "status",
    "highertaxonid",
    "publicationid",
    "publication",
}


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a native object")
    return value


def _rows(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} must be an array of native objects")
    return value


def _id(value: Any, label: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    try:
        positive_native_id(value)
    except ValueError as error:
        raise ValueError(f"{label} must be a native positive integer") from error


def _text(value: Any, label: str, *, nullable: bool = False) -> None:
    if not (isinstance(value, str) or (nullable and value is None)):
        raise ValueError(f"{label} must be native text")


def _fields(
    row: dict[str, Any], required: set[str], optional: set[str], label: str
) -> None:
    if not required <= set(row) or set(row) - required - optional:
        raise ValueError(f"unobserved or missing {label} fields")


def _number(value: Any, label: str) -> None:
    if value is not None and type(value) not in (int, float):
        raise ValueError(f"{label} must be a native number or explicit null")


def _dataset(value: Any, resource: NeotomaResourceSpec) -> None:
    _id(value, "datasetid")
    if value != resource.dataset_id:
        raise ValueError("native dataset owner differs from authenticated request")


def _relationships(
    value: Any, resource: NeotomaResourceSpec, *, publication: bool
) -> None:
    rows = _rows(value, "datasets")
    selected = []
    for row in rows:
        _fields(
            row,
            {"datasetid", "siteid", "primary"}
            if publication
            else {"datasetid", "datasettype"},
            set(),
            "datasets",
        )
        _id(row.get("datasetid"), "datasets.datasetid")
        if publication:
            _id(row.get("siteid"), "datasets.siteid")
            if type(row.get("primary")) is not bool:
                raise ValueError("datasets.primary must be a native boolean")
        else:
            _text(row.get("datasettype"), "datasets.datasettype")
        if row["datasetid"] == resource.dataset_id:
            selected.append(row)
    if not selected:
        raise ValueError("native datasets does not bind the requested dataset")
    for row in selected:
        if publication and row["siteid"] != resource.site_id:
            raise ValueError("native publication dataset site owner differs")
        if not publication and row["datasettype"] != resource.dataset_type:
            raise ValueError("native chronology dataset type owner differs")


def _chronologies(data: Any, resource: NeotomaResourceSpec) -> int:
    rows = _rows(data, "chronologies data")
    for row in rows:
        if set(row) != {"chronology"}:
            raise ValueError("unobserved chronology wrapper")
        chronology = _object(row["chronology"], "chronology")
        _fields(
            chronology,
            {
                "agetype",
                "default",
                "controls",
                "datasets",
                "modelType",
                "preparedby",
                "chronologyid",
                "datePrepared",
                "chronologyName",
                "chronologynotes",
                "reliableagespan",
            },
            set(),
            "chronology",
        )
        _id(chronology.get("chronologyid"), "chronologyid")
        _relationships(chronology.get("datasets"), resource, publication=False)
        if type(chronology.get("default")) is not bool:
            raise ValueError("chronology.default must be a native boolean")
        for key in ("agetype", "modelType", "datePrepared", "chronologyName"):
            _text(chronology.get(key), f"chronology.{key}", nullable=True)
        prepared = _object(chronology.get("preparedby"), "preparedby")
        _fields(
            prepared,
            {"contactid"},
            {"contactname", "familyname", "firstname", "initials"},
            "preparedby",
        )
        _id(prepared.get("contactid"), "preparedby.contactid", nullable=True)
        span = _object(chronology["reliableagespan"], "reliableagespan")
        _fields(span, {"older", "younger"}, set(), "reliableagespan")
        for key, value in span.items():
            _number(value, f"reliableagespan.{key}")
        for control in _rows(chronology.get("controls"), "controls"):
            _fields(
                control,
                {
                    "chroncontrolid",
                    "age",
                    "depth",
                    "thickness",
                    "agetype",
                    "controltype",
                    "geochron",
                    "controllimits",
                },
                {"analysisunitid", "analysisunitname", "notes", "relativeage"},
                "chronology control",
            )
            _id(control.get("chroncontrolid"), "chroncontrolid")
            for key in ("age", "depth", "thickness"):
                _number(control[key], f"control.{key}")
            for key in ("agetype", "controltype"):
                _text(control[key], f"control.{key}", nullable=True)
            geochron = _object(control.get("geochron"), "geochron")
            _fields(
                geochron,
                {"geochronid"},
                {
                    "notes",
                    "delta13c",
                    "infinite",
                    "geochronage",
                    "geochrontype",
                    "materialdated",
                    "geochronagetype",
                    "geochronlabnumber",
                },
                "geochron",
            )
            _id(geochron.get("geochronid"), "geochronid", nullable=True)
            bounds = _object(control["controllimits"], "controllimits")
            _fields(bounds, {"ageolder", "ageyounger"}, set(), "controllimits")
            for key, value in bounds.items():
                _number(value, f"controllimits.{key}")
    return len(rows)


def _lithology(data: Any, resource: NeotomaResourceSpec) -> int:
    rows = _rows(data, "lithology data")
    if not rows:
        raise ValueError("lithology dataset wrapper is absent")
    count = 0
    for row in rows:
        if set(row) != {"datasetid", "lithology"}:
            raise ValueError("unobserved lithology dataset wrapper")
        _dataset(row["datasetid"], resource)
        for layer in _rows(row["lithology"], "lithology"):
            if set(layer) != {"lithologyid", "depth", "lowerboundary", "description"}:
                raise ValueError("unobserved lithology record")
            _id(layer["lithologyid"], "lithologyid")
            depth = _object(layer["depth"], "lithology.depth")
            if set(depth) != {"top", "bottom"}:
                raise ValueError("unobserved lithology depth fields")
            for key, value in depth.items():
                _number(value, f"lithology.depth.{key}")
            _text(layer["lowerboundary"], "lowerboundary", nullable=True)
            _text(layer["description"], "description", nullable=True)
            count += 1
    return count


def _publications(data: Any, resource: NeotomaResourceSpec) -> int:
    rows = _rows(data, "publications data")
    for row in rows:
        if set(row) != {"publication"}:
            raise ValueError("unobserved publication wrapper")
        publication = _object(row["publication"], "publication")
        _fields(
            publication,
            {"publicationid", "datasets", "doi", "author"},
            {
                "articletitle",
                "booktitle",
                "citation",
                "citationnumber",
                "city",
                "country",
                "edition",
                "issue",
                "journal",
                "notes",
                "numvolumes",
                "originallanguage",
                "pages",
                "publisher",
                "pubtype",
                "pubtypeid",
                "seriestitle",
                "seriesvolume",
                "state",
                "url",
                "volume",
                "volumetitle",
                "year",
            },
            "publication",
        )
        _id(publication.get("publicationid"), "publicationid")
        _relationships(publication.get("datasets"), resource, publication=True)
        for author in _rows(publication.get("author"), "publication.author"):
            if set(author) != {"order", "familyname", "givennames"}:
                raise ValueError("unobserved publication author fields")
            _id(author["order"], "author.order")
            _text(author["familyname"], "author.familyname", nullable=True)
            _text(author["givennames"], "author.givennames", nullable=True)
    return len(rows)


def _taxa(data: Any) -> int:
    rows = _rows(data, "taxa data")
    for row in rows:
        if set(row) != _TAXON_FIELDS:
            raise ValueError("unobserved taxon fields; endpoint owner only")
        _id(row["taxonid"], "taxonid")
        _id(row["highertaxonid"], "highertaxonid", nullable=True)
        _id(row["publicationid"], "publicationid", nullable=True)
        for key in ("taxonname", "ecolgroup", "status", "author", "publication"):
            _text(row[key], f"taxa.{key}", nullable=key in {"author", "publication"})
    return len(rows)


def qualify_neotoma_facet_body(
    resource: NeotomaResourceSpec,
    facet: str,
    body: bytes,
    *,
    expected_body_sha256: str,
) -> dict[str, Any]:
    """Qualify a source shape, preserving every native row and partial owner proof.

    The caller must authenticate the endpoint receipt separately. A byte digest alone
    cannot establish an HTTP endpoint or authorize exposure of a protected resource.
    """
    validate_plan(
        NeotomaFacetPlan((resource,), "0" * 64, (facet,)), DEFAULT_RESOURCE_LIMITS
    )
    if resource.exposure_role not in DEVELOPMENT_ROLES:
        raise ValueError("Neotoma facet exposure role forbids body access")
    if sha256(body).hexdigest() != expected_body_sha256:
        raise ValueError("Neotoma facet body identity differs")
    source = decode_neotoma_json_object(body)
    owner = dict.fromkeys(
        ("dataset", "site", "collection_unit", "dataset_type", "database"),
        "not_supplied",
    )
    result: dict[str, Any] = {
        "schema_version": PROFILE_SCHEMA,
        "facet": facet,
        "root_identity": identity(resource),
        "source_body_sha256": expected_body_sha256,
        "source_payload": source,
        "qualification_status": "unqualified_source_schema",
        "owner_verification": owner,
        "scientific_admission": "not_asserted",
        "units_interpreted": False,
        "chronology_selected": False,
        "qualification_scope": "observed wrappers, native owner/link fields and control/layer numbers; source annotations retained",
    }
    try:
        if (
            set(source) != {"status", "data", "message"}
            or source["status"] != "success"
        ):
            raise ValueError("unobserved source success envelope")
        _text(source["message"], "message")
        data = source["data"]
        if facet == "chronologies":
            count = _chronologies(data, resource)
            if count:
                owner.update(
                    dataset="native_payload_matches_request",
                    dataset_type="native_payload_matches_request",
                )
        elif facet == "lithology":
            count = _lithology(data, resource)
            owner["dataset"] = "native_payload_matches_request"
        elif facet == "publications":
            count = _publications(data, resource)
            if count:
                owner.update(
                    dataset="native_payload_matches_request",
                    site="native_payload_matches_request",
                )
        elif facet == "taxa":
            count = _taxa(data)
            owner["dataset"] = "authenticated_request_endpoint_only"
        else:
            projects = _object(data, "projects data")
            if set(projects) != {"datasetid", "projects"}:
                raise ValueError("unobserved projects dataset wrapper")
            _dataset(projects["datasetid"], resource)
            if projects["projects"] != []:
                raise ValueError("populated projects source schema is not qualified")
            count = 0
            owner["dataset"] = "native_payload_matches_request"
        result.update(
            qualification_status="qualified_source_schema",
            received_record_count=count,
            population_status="source_records_received"
            if count
            else "source_explicit_empty_array",
            reason="literal source shape; no scientific interpretation",
        )
    except ValueError as error:
        result["reason"] = str(error)
        for field in owner:
            owner[field] = "not_verified_unqualified_source_schema"
    return result
