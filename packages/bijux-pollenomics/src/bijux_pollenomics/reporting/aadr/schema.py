from __future__ import annotations

from ...adna import (
    resolve_homo_sapiens_schema,
    sample_time_interval,
    sample_time_label,
    sample_time_mean,
    schema_value,
)
from ..models import SchemaError

__all__ = [
    "find_column",
    "find_optional_column",
    "resolve_schema",
    "sample_time_interval",
    "sample_time_label",
    "sample_time_mean",
    "schema_value",
]


def resolve_schema(fieldnames):
    """Compatibility wrapper for the Homo sapiens AADR schema contract."""
    try:
        return resolve_homo_sapiens_schema(fieldnames)
    except ValueError as error:
        raise SchemaError(str(error)) from error


def find_column(fieldnames, *prefixes):
    """Compatibility wrapper for schema column resolution."""
    try:
        return resolve_homo_sapiens_schema(fieldnames)[_lookup_key(prefixes)]
    except KeyError:
        raise SchemaError(f"Could not find any of {prefixes!r} in anno columns") from None


def find_optional_column(fieldnames, *prefixes):
    """Compatibility wrapper for optional schema columns."""
    try:
        return find_column(fieldnames, *prefixes)
    except SchemaError:
        return None


def _lookup_key(prefixes: tuple[str, ...]) -> str:
    mapping = {
        ("Genetic ID",): "genetic_id",
        ("Master ID", "Persistent Genetic ID"): "master_id",
        ("Group ID",): "group_id",
        ("Locality",): "locality",
        ("Political Entity",): "political_entity",
        ("Lat.", "Latitude"): "latitude",
        ("Long.", "Longitude"): "longitude",
        ("Publication abbreviation",): "publication",
        (
            "Year data from this individual was first published",
            "Year first published",
        ): "year_first_published",
        ("Full Date",): "full_date",
        ("Date mean in BP",): "date_mean_bp",
        ("Date standard deviation in BP",): "date_stddev_bp",
        ("Data type",): "data_type",
        ("Molecular Sex",): "molecular_sex",
    }
    for candidates, key in mapping.items():
        if prefixes == candidates:
            return key
    raise KeyError(prefixes)
