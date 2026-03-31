from __future__ import annotations

from ...core.bp_time import build_bp_interval_label, derive_bp_interval_from_mean_and_stddev, midpoint_bp_year
from ..models import SchemaError
from ..utils import clean_text

__all__ = [
    "find_column",
    "find_optional_column",
    "resolve_schema",
    "sample_time_interval",
    "sample_time_label",
    "sample_time_mean",
]


def resolve_schema(fieldnames: list[str]) -> dict[str, str | None]:
    """Map expected logical fields to raw AADR column names."""
    return {
        "genetic_id": find_column(fieldnames, "Genetic ID"),
        "master_id": find_column(fieldnames, "Master ID"),
        "group_id": find_column(fieldnames, "Group ID"),
        "locality": find_column(fieldnames, "Locality"),
        "political_entity": find_column(fieldnames, "Political Entity"),
        "latitude": find_column(fieldnames, "Lat.", "Latitude"),
        "longitude": find_column(fieldnames, "Long.", "Longitude"),
        "publication": find_column(fieldnames, "Publication abbreviation"),
        "year_first_published": find_column(
            fieldnames,
            "Year data from this individual was first published",
            "Year first published",
        ),
        "full_date": find_column(fieldnames, "Full Date"),
        "date_mean_bp": find_column(fieldnames, "Date mean in BP"),
        "date_stddev_bp": find_optional_column(fieldnames, "Date standard deviation in BP"),
        "data_type": find_column(fieldnames, "Data type"),
        "molecular_sex": find_column(fieldnames, "Molecular Sex"),
    }


def find_column(fieldnames: list[str], *prefixes: str) -> str:
    """Find a column by exact name or a stable prefix."""
    lowered = {field.casefold(): field for field in fieldnames}
    for prefix in prefixes:
        exact = lowered.get(prefix.casefold())
        if exact:
            return exact
    for prefix in prefixes:
        prefix_key = prefix.casefold()
        for field in fieldnames:
            if field.casefold().startswith(prefix_key):
                return field
    raise SchemaError(f"Could not find any of {prefixes!r} in anno columns")


def find_optional_column(fieldnames: list[str], *prefixes: str) -> str | None:
    """Find a column by exact name or prefix when present."""
    try:
        return find_column(fieldnames, *prefixes)
    except SchemaError:
        return None


def sample_time_interval(row: dict[str, str], schema: dict[str, str | None]) -> tuple[int, int] | None:
    """Derive one AADR BP interval from the row's mean and standard deviation."""
    return derive_bp_interval_from_mean_and_stddev(
        row.get(schema["date_mean_bp"], ""),
        row.get(schema["date_stddev_bp"], ""),
    )


def sample_time_mean(row: dict[str, str], schema: dict[str, str | None]) -> int | None:
    """Return the sample mean BP year used for time filtering summaries."""
    interval = sample_time_interval(row, schema)
    return midpoint_bp_year(interval[0], interval[1]) if interval is not None else None


def sample_time_label(row: dict[str, str], schema: dict[str, str | None]) -> str:
    """Return the best available human-readable AADR time label."""
    full_date = clean_text(row.get(schema["full_date"], ""))
    if full_date:
        return full_date
    interval = sample_time_interval(row, schema)
    if interval is None:
        return ""
    return build_bp_interval_label(interval[0], interval[1])
