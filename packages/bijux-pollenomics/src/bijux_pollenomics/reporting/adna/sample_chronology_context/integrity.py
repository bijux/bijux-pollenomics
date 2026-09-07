"""Canonical content identities for animal chronology accountability rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .contracts import AnimalSampleChronologyCorpus

_GOVERNED_COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")


def refusal_rows_sha256(rows: Sequence[Mapping[str, object]]) -> str:
    """Bind ordered exclusive-refusal content to its publication accountability."""
    return hashlib.sha256(
        json.dumps(
            list(rows),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def build_corpus_identity(corpus: AnimalSampleChronologyCorpus) -> dict[str, object]:
    """Bind global admitted/refused accountability independently of map scope."""
    admitted_rows = [
        {
            "feature_id": node.feature_id,
            "project_accession": node.project_accession,
            "repo_stable_sample_id": node.repo_stable_sample_id,
            "project_species_latin_name": node.project_species_latin_name,
            "country_name": node.country_name,
            "younger_bp": node.younger_bp,
            "older_bp": node.older_bp,
        }
        for node in corpus.nodes
    ]
    refusal_rows = [row.as_dict() for row in corpus.refusals]
    country_names = sorted(
        {node.country_name for node in corpus.nodes if node.country_name}
    )
    country_rows = [_country_row(country, corpus) for country in country_names]
    country_rows.append(_country_row(None, corpus))
    content: dict[str, object] = {
        "schema_version": "animal-sample-chronology-corpus-identity.v1",
        "input_identity_sha256": corpus.input_identity.combined_sha256,
        "admitted_rows_sha256": _canonical_sha256(admitted_rows),
        "refusal_rows_sha256": refusal_rows_sha256(refusal_rows),
        "source_counts": dict(corpus.source_counts),
        "refusal_counts": dict(corpus.refusal_counts),
        "global_admitted_node_count": len(corpus.nodes),
        "country_rows": country_rows,
        "governed_country_rows": [
            _country_row(country, corpus) for country in _GOVERNED_COUNTRIES
        ],
        "time_min_bp": min((node.younger_bp for node in corpus.nodes), default=None),
        "time_max_bp": max((node.older_bp for node in corpus.nodes), default=None),
    }
    return {**content, "content_sha256": _canonical_sha256(content)}


def _country_row(
    country: str | None, corpus: AnimalSampleChronologyCorpus
) -> dict[str, object]:
    selected = tuple(node for node in corpus.nodes if node.country_name == country)
    return {
        "country_name": country,
        "node_count": len(selected),
        "time_min_bp": min((node.younger_bp for node in selected), default=None),
        "time_max_bp": max((node.older_bp for node in selected), default=None),
    }


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


__all__ = ["build_corpus_identity", "refusal_rows_sha256"]
