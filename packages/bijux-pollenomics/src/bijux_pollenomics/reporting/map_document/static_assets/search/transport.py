"""Lossless document transport for the fully derived substring postings map."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from .postings import SEARCH_ABI, grams, validate_search_index

SEARCH_DOCUMENTS_SCHEMA = "atlas-search-documents.v1"
SEARCH_TRANSPORT_COUNT_FIELDS = (
    "document_count",
    "utf16_unit_count",
    "posting_key_count",
    "posting_reference_count",
)
_DOCUMENT_FIELDS = {"layer_index", "feature_index", "layer_key", "record_id", "text"}


def validate_search_transport_counts(value: object) -> dict[str, int]:
    """Require the complete declared work inventory without numeric coercion."""
    if not isinstance(value, Mapping) or set(value) != set(
        SEARCH_TRANSPORT_COUNT_FIELDS
    ):
        raise ValueError(
            "search transport counts must contain exactly four resource fields"
        )
    counts: dict[str, int] = {}
    for field in SEARCH_TRANSPORT_COUNT_FIELDS:
        count = value[field]
        if type(count) is not int or not 0 <= count < 2**53:
            raise ValueError(
                f"search transport {field} must be a nonnegative safe integer"
            )
        counts[field] = count
    return counts


def read_search_transport(payload: Mapping[str, object]) -> dict[str, int] | None:
    """Absence retains legacy postings; partial or unknown declarations refuse."""
    declared = "search_transport_schema" in payload
    counted = "search_transport_counts" in payload
    if not declared and not counted:
        return None
    if (
        not declared
        or not counted
        or payload.get("search_transport_schema") != SEARCH_DOCUMENTS_SCHEMA
        or payload.get("search_index_abi") != SEARCH_ABI
    ):
        raise ValueError("search transport declaration is missing or unsupported")
    return validate_search_transport_counts(payload["search_transport_counts"])


def _document(key: object, row: object) -> tuple[str, Mapping[str, object], str]:
    if (
        not isinstance(key, str)
        or not key.startswith("d:")
        or not isinstance(row, Mapping)
        or set(row) != _DOCUMENT_FIELDS
        or type(row.get("layer_index")) is not int
        or cast(int, row["layer_index"]) < 0
        or type(row.get("feature_index")) is not int
        or cast(int, row["feature_index"]) < 0
        or not isinstance(row.get("layer_key"), str)
        or not row["layer_key"]
        or not isinstance(row.get("text"), str)
        or key != f"d:{row['layer_index']}:{row['feature_index']}"
    ):
        raise ValueError("search transport document identity is invalid")
    return key, cast(Mapping[str, object], row), cast(str, row["text"])


def encode_search_documents(rows: object) -> tuple[dict[str, object], dict[str, int]]:
    """Validate every original posting before omitting its derivable wire copy."""
    validate_search_index(rows)
    source = cast(Mapping[str, object], rows)
    documents: dict[str, object] = {}
    units = 0
    posting_keys = 0
    references = 0
    for key, row in source.items():
        if key.startswith("p:"):
            posting_keys += 1
            references += len(cast(list[object], row))
        else:
            document_key, document, text = _document(key, row)
            documents[document_key] = document
            units += len(text.encode("utf-16-le", errors="surrogatepass")) // 2
    counts = validate_search_transport_counts(
        {
            "document_count": len(documents),
            "utf16_unit_count": units,
            "posting_key_count": posting_keys,
            "posting_reference_count": references,
        }
    )
    return dict(sorted(documents.items())), counts


def search_document_utf16_units(key: object, row: object) -> int:
    """Validate an encoded document before accepting it into a decoded inventory."""
    _, _, text = _document(key, row)
    return len(text.encode("utf-16-le", errors="surrogatepass")) // 2


def restore_search_documents(
    rows: object, declared_counts: object
) -> dict[str, object]:
    """Restore all postings while enforcing declared work exactly and incrementally.

    These counts describe derived work, not a fixed heap ceiling. The surrounding
    consumer remains responsible for its measured resource envelope.
    """
    counts = validate_search_transport_counts(declared_counts)
    if not isinstance(rows, Mapping):
        raise ValueError("search transport documents must be an object")
    documents: dict[str, object] = {}
    postings: dict[str, list[str]] = {}
    observed = dict.fromkeys(SEARCH_TRANSPORT_COUNT_FIELDS, 0)

    def increment(field: str, amount: int = 1) -> None:
        observed[field] += amount
        if observed[field] > counts[field]:
            raise ValueError(f"search transport exceeds declared {field}")

    for key, row in rows.items():
        document_key, document, text = _document(key, row)
        increment("document_count")
        increment(
            "utf16_unit_count",
            len(text.encode("utf-16-le", errors="surrogatepass")) // 2,
        )
        documents[document_key] = document
        for gram in grams(text):
            posting_key = "p:" + gram
            if posting_key not in postings:
                increment("posting_key_count")
                postings[posting_key] = []
            increment("posting_reference_count")
            postings[posting_key].append(document_key)
    if observed != counts:
        raise ValueError("search transport resource counts do not reconcile")
    return dict(
        sorted(
            {
                **documents,
                **{key: sorted(values) for key, values in postings.items()},
            }.items()
        )
    )
