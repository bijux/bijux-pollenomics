"""Input and corpus identity checks for chronology publication."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json


def validate_input_identity(
    accountability: Mapping[str, object], input_identity: Mapping[str, object]
) -> None:
    """Require accountability to bind the exact valid input identity."""
    if accountability.get("input_identity") != input_identity:
        raise ValueError("animal chronology accountability input identity differs")
    combined = input_identity.get("combined_sha256")
    if (
        not isinstance(combined, str)
        or len(combined) != 64
        or any(character not in "0123456789abcdef" for character in combined)
    ):
        raise ValueError("animal chronology input identity is invalid")


def validate_corpus_identity(
    accountability: Mapping[str, object],
    input_identity: Mapping[str, object],
    corpus_identity: Mapping[str, object],
) -> None:
    """Require corpus identity and accountability denominators to agree."""
    identity_content = dict(corpus_identity)
    declared_sha256 = identity_content.pop("content_sha256", None)
    if declared_sha256 != canonical_sha256(identity_content):
        raise ValueError("animal chronology corpus content identity differs")
    if corpus_identity.get("input_identity_sha256") != input_identity.get(
        "combined_sha256"
    ):
        raise ValueError("animal chronology corpus input identity differs")
    for accountability_field, corpus_field in (
        ("source_counts", "source_counts"),
        ("refusal_counts", "refusal_counts"),
        ("refusal_rows_sha256", "refusal_rows_sha256"),
        ("global_admitted_node_count", "global_admitted_node_count"),
        ("country_rows", "country_rows"),
        ("governed_country_rows", "governed_country_rows"),
    ):
        if accountability.get(accountability_field) != corpus_identity.get(
            corpus_field
        ):
            raise ValueError(
                f"animal chronology {accountability_field} differs from corpus identity"
            )


def canonical_sha256(value: object) -> str:
    """Hash strict canonical JSON without altering historical hash semantics."""
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
