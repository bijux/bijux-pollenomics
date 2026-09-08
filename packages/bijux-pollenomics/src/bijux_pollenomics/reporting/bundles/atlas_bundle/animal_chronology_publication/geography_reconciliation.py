"""Geographic accountability reconciliation for chronology publication."""

from __future__ import annotations

from collections.abc import Mapping

from .contract_values import mapping, mapping_rows, nonblank_text, nonnegative_integer

GOVERNED_COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")


def validate_country_accountability(
    accountability: Mapping[str, object], layers: list[dict[str, object]]
) -> None:
    """Reconcile global, governed-country, and publication-scope rows."""
    country_rows = mapping_rows(accountability.get("country_rows"), "country rows")
    names = [row.get("country_name") for row in country_rows]
    expected_order = sorted(name for name in names if isinstance(name, str))
    if names != [*expected_order, None] or len(set(names)) != len(names):
        raise ValueError("animal chronology country row identity or order differs")
    global_count = nonnegative_integer(
        accountability.get("global_admitted_node_count"), "global admitted count"
    )
    if sum(_country_row_count(row) for row in country_rows) != global_count:
        raise ValueError("animal chronology country rows do not reconcile")
    by_country = {row.get("country_name"): row for row in country_rows}
    governed = mapping_rows(
        accountability.get("governed_country_rows"), "governed country rows"
    )
    if [row.get("country_name") for row in governed] != list(GOVERNED_COUNTRIES):
        raise ValueError("animal chronology governed country identity differs")
    if any(
        row
        != by_country.get(
            row.get("country_name"),
            {
                "country_name": row.get("country_name"),
                "node_count": 0,
                "time_min_bp": None,
                "time_max_bp": None,
            },
        )
        for row in governed
    ):
        raise ValueError("animal chronology governed country rows differ")
    for row in country_rows:
        _validate_country_row_bounds(row)

    scope = mapping(accountability.get("scope"), "scope")
    scope_kind = nonblank_text(scope.get("kind"), "scope kind")
    scope_countries_value = scope.get("countries")
    if not isinstance(scope_countries_value, list) or any(
        not isinstance(country, str) or not country for country in scope_countries_value
    ):
        raise ValueError("animal chronology scope countries are invalid")
    scope_countries = set(scope_countries_value)
    features = [
        feature
        for layer in layers
        for feature in mapping_rows(layer.get("features"), "layer features")
    ]
    if scope_kind == "world":
        if scope_countries_value and (
            len(scope_countries_value) != len(GOVERNED_COUNTRIES)
            or set(scope_countries_value) != set(GOVERNED_COUNTRIES)
        ):
            raise ValueError("animal chronology world scope countries differ")
        if _country_rows_from_features(features) != country_rows:
            raise ValueError(
                "animal chronology global country rows differ from features"
            )
    elif any(
        str(feature.get("country") or "") not in scope_countries for feature in features
    ):
        raise ValueError("animal chronology projected feature is outside scope")


def _country_rows_from_features(
    features: list[dict[str, object]],
) -> list[dict[str, object]]:
    countries = sorted(
        {str(feature.get("country")) for feature in features if feature.get("country")}
    )
    rows = [_feature_country_row(country, features) for country in countries]
    rows.append(_feature_country_row(None, features))
    return rows


def _feature_country_row(
    country: str | None, features: list[dict[str, object]]
) -> dict[str, object]:
    selected = [
        feature
        for feature in features
        if (str(feature.get("country")) if feature.get("country") else None) == country
    ]
    return {
        "country_name": country,
        "node_count": len(selected),
        "time_min_bp": min(
            (
                nonnegative_integer(feature.get("time_start_bp"), "feature time start")
                for feature in selected
            ),
            default=None,
        ),
        "time_max_bp": max(
            (
                nonnegative_integer(feature.get("time_end_bp"), "feature time end")
                for feature in selected
            ),
            default=None,
        ),
    }


def _country_row_count(row: Mapping[str, object]) -> int:
    return nonnegative_integer(row.get("node_count"), "country node count")


def _validate_country_row_bounds(row: Mapping[str, object]) -> None:
    count = _country_row_count(row)
    minimum = row.get("time_min_bp")
    maximum = row.get("time_max_bp")
    if count == 0:
        if minimum is not None or maximum is not None:
            raise ValueError("animal chronology empty country has non-null bounds")
        return
    if nonnegative_integer(minimum, "country minimum time") > nonnegative_integer(
        maximum, "country maximum time"
    ):
        raise ValueError("animal chronology country time bounds are inverted")
