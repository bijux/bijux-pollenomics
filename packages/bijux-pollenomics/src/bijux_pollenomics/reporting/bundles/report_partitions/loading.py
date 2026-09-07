"""Load reducer metadata from independently generated report scopes."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
from typing import cast

from ...geography import GeographicScope
from ...models import CountryReport, LocalitySummary, MultiCountryMapReport
from ..paths import build_country_bundle_paths
from .models import PublishedReportPartitionPlan


@dataclass(frozen=True)
class _LocalityInterval:
    time_start_bp: int | None
    time_end_bp: int | None
    time_mean_bp: int | None


def load_scope_reports(
    report_root: Path,
    *,
    plan: PublishedReportPartitionPlan,
    version: str,
) -> tuple[
    dict[str, MultiCountryMapReport],
    tuple[CountryReport, ...],
    dict[str, CountryReport],
]:
    """Recover report metadata needed by cross-scope reducers."""
    root = Path(report_root)
    scope_reports = {
        scope.key: _load_map_report(root, scope, version=version)
        for scope in (
            plan.geography.world_scope,
            *plan.geography.regional_scopes,
        )
    }
    country_reports_by_scope = {
        scope.key: _load_country_report(root, scope, version=version)
        for scope in plan.geography.country_scopes
    }
    country_reports = tuple(
        country_reports_by_scope[scope.key] for scope in plan.geography.country_scopes
    )
    return scope_reports, country_reports, country_reports_by_scope


def _load_map_report(
    report_root: Path, scope: GeographicScope, *, version: str
) -> MultiCountryMapReport:
    scope_key = scope.key
    scope_slug = scope.slug
    scope_dir = report_root.joinpath(*scope.output_dir_parts)
    payload = _json_object(scope_dir / f"{scope_slug}_summary.json")
    if payload.get("schema_version") != "geographic-evidence-surface-summary.v1":
        raise ValueError(f"Map summary schema is unsupported: {scope_key}")
    if payload.get("scope_key") != scope_key or payload.get("slug") != scope_slug:
        raise ValueError(f"Map summary identity differs from plan: {scope_key}")
    if payload.get("version") != version:
        raise ValueError(f"Map summary version differs from plan: {scope_key}")
    countries = _string_tuple(payload.get("countries"), "map countries")
    if countries != scope.countries:
        raise ValueError(f"Map summary countries differ from plan: {scope_key}")
    count_payload = payload.get("country_sample_counts")
    if not isinstance(count_payload, dict) or any(
        not isinstance(key, str) or type(value) is not int
        for key, value in count_payload.items()
    ):
        raise ValueError(f"Map summary counts are invalid: {scope_key}")
    return MultiCountryMapReport(
        title=_required_string(payload, "title"),
        slug=scope_slug,
        version=_required_string(payload, "version"),
        generated_on=_required_string(payload, "generated_on"),
        countries=countries,
        country_sample_counts=cast(dict[str, int], count_payload),
        total_unique_samples=_required_int(payload, "total_unique_samples"),
        output_dir=scope_dir,
        scope_key=scope_key,
        scope_label=_required_string(payload, "scope_label"),
        scope_kind=_required_string(payload, "scope_kind"),
        parent_scope_key=_optional_string(payload.get("parent_scope_key")),
    )


def _load_country_report(
    report_root: Path, scope: GeographicScope, *, version: str
) -> CountryReport:
    country = scope.countries[0]
    country_dir = report_root.joinpath(*scope.output_dir_parts)
    paths = build_country_bundle_paths(country_dir, country, version)
    payload = _json_object(paths.summary_json_path)
    if payload.get("schema_version") != "country-report-summary.v1":
        raise ValueError(f"Country summary schema is unsupported: {country}")
    if payload.get("country") != country or payload.get("version") != version:
        raise ValueError(f"Country summary identity differs from plan: {country}")
    dataset_counts = payload.get("dataset_row_counts")
    if not isinstance(dataset_counts, dict) or any(
        not isinstance(key, str) or type(value) is not int
        for key, value in dataset_counts.items()
    ):
        raise ValueError(f"Country summary counts are invalid: {country}")
    localities = cast(
        tuple[LocalitySummary, ...],
        tuple(_load_locality_intervals(paths.localities_csv_path)),
    )
    return CountryReport(
        country=country,
        version=version,
        generated_on=_required_string(payload, "generated_on"),
        total_unique_samples=_required_int(payload, "total_unique_samples"),
        total_unique_localities=_required_int(payload, "total_unique_localities"),
        dataset_row_counts=cast(dict[str, int], dataset_counts),
        samples=(),
        localities=localities,
        output_dir=country_dir,
    )


def _load_locality_intervals(path: Path) -> list[_LocalityInterval]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required_fields = {"time_start_bp", "time_end_bp", "time_mean_bp"}
            if not required_fields.issubset(set(reader.fieldnames or ())):
                raise ValueError(
                    f"Country locality interval fields are missing: {path}"
                )
            rows = list(reader)
    except (OSError, UnicodeError) as error:
        raise ValueError(
            f"Country locality intervals cannot be read: {path}"
        ) from error
    return [
        _LocalityInterval(
            time_start_bp=_optional_int(row["time_start_bp"]),
            time_end_bp=_optional_int(row["time_end_bp"]),
            time_mean_bp=_optional_int(row["time_mean_bp"]),
        )
        for row in rows
    ]


def _json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Report partition metadata cannot be read: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"Report partition metadata must be an object: {path}")
    return cast(dict[str, object], payload)


def _required_string(payload: dict[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Report partition field is invalid: {field}")
    return value


def _required_int(payload: dict[str, object], field: str) -> int:
    value = payload.get(field)
    if type(value) is not int or value < 0:
        raise ValueError(f"Report partition field is invalid: {field}")
    return value


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(f"Report partition field is invalid: {field}")
    return tuple(value)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError("Report partition parent scope is invalid")
    return value


def _optional_int(value: object) -> int | None:
    if value in {None, ""}:
        return None
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as error:
            raise ValueError("Country locality interval is not an integer") from error
    raise ValueError("Country locality interval is not an integer")
