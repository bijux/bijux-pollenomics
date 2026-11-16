"""Current native detail owners, without inferred authorship or dataset ownership."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from ...client import decode_neotoma_json_object, positive_native_id
from ..resources.models import DEVELOPMENT_ROLES
from .models import LINKED_KINDS

_CONTACT_FIELDS = {
    "contactid",
    "stewardid",
    "contactname",
    "familyname",
    "leadinginitials",
    "givennames",
    "suffix",
    "title",
    "phone",
    "fax",
    "email",
    "url",
    "address",
    "notes",
    "contactstatus",
}
_TAXON_FIELDS = {
    "taxonid",
    "taxoncode",
    "taxonname",
    "author",
    "ecolgroup",
    "highertaxonid",
    "status",
    "taxagroupid",
    "publicationid",
    "publication",
}
_PUBLICATION_FIELDS = {
    "publicationid",
    "pubtypeid",
    "pubtype",
    "year",
    "citation",
    "articletitle",
    "journal",
    "volume",
    "issue",
    "pages",
    "citationnumber",
    "doi",
    "booktitle",
    "numvolumes",
    "edition",
    "volumetitle",
    "seriestitle",
    "seriesvolume",
    "publisher",
    "url",
    "city",
    "state",
    "country",
    "originallanguage",
    "notes",
    "author",
    "datasets",
}


class _UnavailableLinkedSource(ValueError):
    """The source explicitly returned successful empty data for this request."""


@dataclass(frozen=True)
class NeotomaLinkedSource:
    target_kind: str
    native_id: int
    body_sha256: str
    payload: dict[str, Any]
    records: list[dict[str, Any]]


def _fields(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"Native linked {label} fields are unsupported or missing")
    return value


def _rows(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"Native linked {label} must be an explicit array of objects")
    return value


def _text(value: Any, label: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"Native linked {label} must be text or explicit null")


def _optional_id(value: Any) -> None:
    if value is not None:
        positive_native_id(value)


def _publication_datasets(value: Any) -> None:
    rows = _rows(value, "publication datasets")
    for row in rows:
        _fields(row, {"datasetid", "siteid", "primary"}, "publication dataset")
    if rows == [{"datasetid": None, "siteid": None, "primary": None}]:
        return
    for row in rows:
        positive_native_id(row["datasetid"])
        positive_native_id(row["siteid"])
        if row["primary"] is not None and type(row["primary"]) is not bool:
            raise ValueError("Native publication primary must be a boolean or null")


def parse_neotoma_linked_source(
    identity: dict[str, Any],
    body: bytes,
    *,
    expected_body_sha256: str,
) -> NeotomaLinkedSource:
    """Preserve every native row; the caller authenticates HTTP/proof custody.

    A global detail record owns its own native ID. Its source-root link proofs
    remain separate from any dataset associations in this later response.
    """
    if identity.get("exposure_role") not in DEVELOPMENT_ROLES:
        raise ValueError("Linked source qualification refuses this exposure role")
    kind = identity.get("kind")
    native_id = positive_native_id(identity.get("native_id"))
    if kind not in LINKED_KINDS or identity.get("target_key") != f"{kind}-{native_id}":
        raise ValueError("Linked source target identity is invalid")
    if sha256(body).hexdigest() != expected_body_sha256:
        raise ValueError("Linked source body identity differs")
    payload = decode_neotoma_json_object(body)
    _fields(payload, {"status", "data", "message"}, "success envelope")
    if payload["status"] != "success" or not isinstance(payload["message"], str):
        raise ValueError("Linked native source status is unsuccessful or malformed")
    rows = _rows(payload["data"], "data")
    if not rows:
        raise _UnavailableLinkedSource(
            "Linked API returned successful empty data; absence is not certified"
        )
    records = []
    for row in rows:
        if kind == "publication":
            _fields(row, {"publication"}, "publication wrapper")
            record = _fields(row["publication"], _PUBLICATION_FIELDS, "publication")
            _optional_id(record["pubtypeid"])
            for author in _rows(record["author"], "publication authors"):
                _fields(author, {"order", "familyname", "givennames"}, "author")
                positive_native_id(author["order"])
                _text(author["familyname"], "author familyname")
                _text(author["givennames"], "author givennames")
            _publication_datasets(record["datasets"])
            id_field = "publicationid"
            text_fields = _PUBLICATION_FIELDS - {
                "publicationid",
                "pubtypeid",
                "author",
                "datasets",
            }
        elif kind == "contact":
            record = _fields(row, _CONTACT_FIELDS, "contact")
            _optional_id(record["stewardid"])
            id_field = "contactid"
            text_fields = _CONTACT_FIELDS - {"contactid", "stewardid"}
        else:
            record = _fields(row, _TAXON_FIELDS, "taxon")
            _optional_id(record["publicationid"])
            _optional_id(record["highertaxonid"])
            id_field = "taxonid"
            text_fields = _TAXON_FIELDS - {"taxonid", "publicationid", "highertaxonid"}
        if positive_native_id(record[id_field]) != native_id:
            raise ValueError("Linked native detail owner differs from selected target")
        for field in text_fields:
            _text(record[field], field)
        records.append(record)
    return NeotomaLinkedSource(kind, native_id, expected_body_sha256, payload, records)


def summarize_linked_source(
    parsed: NeotomaLinkedSource, *, source_proofs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Keep prior facet relationships distinct from current global native details."""
    checks = []
    association_population = {}
    if parsed.target_kind == "publication":
        datasets = [row for record in parsed.records for row in record["datasets"]]
        unavailable = any(row["datasetid"] is None for row in datasets)
        if unavailable:
            association_population["dataset_association_population"] = (
                "source_null_aggregate_placeholder"
                if all(row["datasetid"] is None for row in datasets)
                else "identified_associations_and_source_null_aggregate_placeholder"
            )
        for proof in source_proofs:
            check = {
                "relation": proof["relation"],
                "root_dataset_id": proof["root_dataset_id"],
                "source_facet_key": proof["source_facet_key"],
                "json_pointer": proof["json_pointer"],
            }
            if proof["relation"] != "dataset_publication":
                check["status"] = "not_a_dataset_publication_edge"
            else:
                dataset_id = positive_native_id(proof["root_dataset_id"])
                site_id = positive_native_id(proof["root_identity"]["site_id"])
                matches = [row for row in datasets if row["datasetid"] == dataset_id]
                check["status"] = (
                    "conflicting_native_site"
                    if any(row["siteid"] != site_id for row in matches)
                    else "confirmed_by_current_detail_body"
                    if matches
                    else "source_dataset_associations_unavailable"
                    if unavailable
                    else "not_reported_in_current_body"
                )
                if any(row["primary"] is None for row in matches):
                    check["primary_assertion_status"] = (
                        "unknown"
                        if all(row["primary"] is None for row in matches)
                        else "partially_unknown"
                    )
            checks.append(check)
    suffix = "/publication" if parsed.target_kind == "publication" else ""
    return {
        "parser_profile": "current_native_linked_metadata.v1",
        "target_kind": parsed.target_kind,
        "native_id": parsed.native_id,
        "native_owner_verification": "native_payload_matches_expected_target",
        "received_record_rows": len(parsed.records),
        "native_records": parsed.records,
        "native_record_pointers": [
            f"/data/{index}{suffix}" for index in range(len(parsed.records))
        ],
        "source_proof_count": len(source_proofs),
        "dataset_relation_checks": checks,
        **association_population,
        "source_relationship_authority": "original authenticated facet proofs; current detail association checks reported separately",
        "units_interpreted": False,
        "scientific_admission": "not_asserted",
    }
