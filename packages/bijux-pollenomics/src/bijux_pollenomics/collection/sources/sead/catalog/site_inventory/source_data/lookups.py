"""Build SEAD chronology vocabulary and bibliography lookup indexes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeVar

from bijux_pollenomics.collection.sources.sead.acquisition.identifiers import (
    optional_sead_identifier,
    required_sead_identifier,
)
from bijux_pollenomics.core.text import clean_optional_text

from ..values import parse_optional_int
from .source_tables import SeadInventorySourceRows

_ReferenceValue = TypeVar("_ReferenceValue")


def lookup_optional_reference(
    index: Mapping[int, _ReferenceValue], source_key: object, default: _ReferenceValue
) -> _ReferenceValue:
    """Resolve a nullable source reference without inventing a missing key."""
    identifier = optional_sead_identifier(source_key)
    return default if identifier is None else index.get(identifier, default)


@dataclass(frozen=True, slots=True)
class SeadLookupIndex:
    """Index source vocabulary and citation rows by exact native keys."""

    age_type_by_id: dict[int, str]
    age_type_description_by_id: dict[int, str]
    dataset_name_by_id: dict[int, str]
    uncertainty_by_id: dict[int, dict[str, str]]
    relative_age_by_id: dict[int, dict[str, object]]
    method_by_id: dict[int, dict[str, str]]
    bibliography_by_id: dict[int, dict[str, str]]
    dataset_reference_by_id: dict[int, dict[str, str]]
    dataset_bibliography_id_by_id: dict[int, int | None]


def build_lookup_index(source: SeadInventorySourceRows) -> SeadLookupIndex:
    """Resolve native lookup identities while preserving absent references."""
    age_type_by_id = {
        required_sead_identifier(row["age_type_id"]): clean_optional_text(
            row.get("age_type")
        )
        for row in source.age_types
        if row.get("age_type_id") is not None
    }
    age_type_description_by_id = {
        required_sead_identifier(row["age_type_id"]): clean_optional_text(
            row.get("description")
        )
        for row in source.age_types
        if row.get("age_type_id") is not None
    }
    dataset_name_by_id = {
        required_sead_identifier(row["dataset_id"]): clean_optional_text(
            row.get("dataset_name")
        )
        for row in source.datasets
        if row.get("dataset_id") is not None
    }
    uncertainty_by_id = {
        required_sead_identifier(row["dating_uncertainty_id"]): {
            "label": clean_optional_text(row.get("uncertainty")),
            "description": clean_optional_text(row.get("description")),
        }
        for row in source.dating_uncertainties
        if row.get("dating_uncertainty_id") is not None
    }
    relative_age_by_id: dict[int, dict[str, object]] = {
        required_sead_identifier(row["relative_age_id"]): {
            "label": clean_optional_text(row.get("relative_age_name")),
            "description": clean_optional_text(row.get("description")),
            "abbreviation": clean_optional_text(row.get("abbreviation")),
            "cal_age_older": parse_optional_int(row.get("cal_age_older")),
            "cal_age_younger": parse_optional_int(row.get("cal_age_younger")),
            "c14_age_older": parse_optional_int(row.get("c14_age_older")),
            "c14_age_younger": parse_optional_int(row.get("c14_age_younger")),
        }
        for row in source.relative_ages
        if row.get("relative_age_id") is not None
    }
    method_by_id = {
        required_sead_identifier(row["method_id"]): {
            "name": clean_optional_text(row.get("method_name")),
            "alternate_name": clean_optional_text(row.get("method_abbrev_or_alt_name")),
            "description": clean_optional_text(row.get("description")),
        }
        for row in source.methods
        if row.get("method_id") is not None
    }
    bibliography_by_id = {
        required_sead_identifier(row["biblio_id"]): {
            "title": clean_optional_text(row.get("title")),
            "full_reference": clean_optional_text(row.get("full_reference")),
            "year": clean_optional_text(row.get("year")),
            "doi": clean_optional_text(row.get("doi")),
            "url": clean_optional_text(row.get("url")),
        }
        for row in source.bibliography_rows
        if row.get("biblio_id") is not None
    }
    dataset_reference_by_id = {
        required_sead_identifier(row["dataset_id"]): lookup_optional_reference(
            bibliography_by_id, row.get("biblio_id"), {}
        )
        for row in source.datasets
        if row.get("dataset_id") is not None
    }
    dataset_bibliography_id_by_id = {
        required_sead_identifier(row["dataset_id"]): optional_sead_identifier(
            row.get("biblio_id")
        )
        for row in source.datasets
        if row.get("dataset_id") is not None
    }
    return SeadLookupIndex(
        age_type_by_id=age_type_by_id,
        age_type_description_by_id=age_type_description_by_id,
        dataset_name_by_id=dataset_name_by_id,
        uncertainty_by_id=uncertainty_by_id,
        relative_age_by_id=relative_age_by_id,
        method_by_id=method_by_id,
        bibliography_by_id=bibliography_by_id,
        dataset_reference_by_id=dataset_reference_by_id,
        dataset_bibliography_id_by_id=dataset_bibliography_id_by_id,
    )


__all__ = ["SeadLookupIndex", "build_lookup_index"]
