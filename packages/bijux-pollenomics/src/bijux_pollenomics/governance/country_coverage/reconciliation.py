"""Country-coverage cell and denominator reconciliation."""

from __future__ import annotations

from collections.abc import Mapping

from .constants import (
    COUNT_FIELDS,
    COUNTRIES,
    COUNTRY_DIMENSIONS,
    EMPD2_ASSIGNMENT_NOT_APPLIED,
    NFI_ASSIGNMENT_NOT_APPLIED,
    SOURCE_FAMILIES,
    CountryCoverageError,
)
from .decoding import _object


def _validate_cells(
    cells: list[dict[str, object]], schema: Mapping[str, object]
) -> None:
    try:
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
    except ImportError as error:
        raise CountryCoverageError("jsonschema is required") from error
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for index, cell in enumerate(cells):
        errors = sorted(validator.iter_errors(cell), key=lambda item: list(item.path))
        if errors:
            raise CountryCoverageError(
                f"cell {index} violates schema: {errors[0].message}"
            )


def _validate_reconciliation(cells: list[dict[str, object]]) -> None:
    expected_keys = {
        (source, dimension, country)
        for source in SOURCE_FAMILIES
        for dimension in COUNTRY_DIMENSIONS
        for country in COUNTRIES
    }
    observed_keys = {
        (
            str(cell["source_family"]),
            str(cell["country_dimension"]),
            str(cell["country_code"]),
        )
        for cell in cells
    }
    if observed_keys != expected_keys or len(cells) != len(expected_keys):
        raise CountryCoverageError("country coverage cell inventory does not reconcile")
    if any(cell["availability_status"] == "unknown" for cell in cells):
        raise CountryCoverageError("country coverage cannot retain unknown cells")
    for cell in cells:
        counts = _object(cell.get("counts"), "country coverage counts")
        if tuple(counts) != COUNT_FIELDS:
            raise CountryCoverageError("country coverage count inventory changed")

    index = {
        (
            str(cell["source_family"]),
            str(cell["country_dimension"]),
            str(cell["country_code"]),
        ): cell
        for cell in cells
    }

    def total(source: str, dimension: str, measure: str) -> int:
        result = 0
        for country in COUNTRIES:
            counts = _object(index[(source, dimension, country)]["counts"], "counts")
            value = counts.get(measure)
            if not isinstance(value, int) or isinstance(value, bool):
                raise CountryCoverageError(
                    f"{source} {dimension} {measure} has an incomplete denominator"
                )
            result += value
        return result

    landclim_reported = total("landclim", "source_reported", "sites")
    if landclim_reported != total("landclim", "publication", "sites"):
        raise CountryCoverageError("LandClim site partitions do not reconcile")
    neotoma_reported = total("neotoma", "source_reported", "sites")
    if neotoma_reported != total("neotoma", "governed_assignment", "sites"):
        raise CountryCoverageError("Neotoma governed sites do not reconcile")
    for country in COUNTRIES:
        governed_counts = _object(
            index[("neotoma", "governed_assignment", country)]["counts"], "counts"
        )
        publication_counts = _object(
            index[("neotoma", "publication", country)]["counts"], "counts"
        )
        if governed_counts["accepted_records"] != publication_counts["sites"]:
            raise CountryCoverageError(
                "Neotoma accepted publication sites do not reconcile"
            )
    neotoma_accounted = sum(
        total("neotoma", "governed_assignment", measure)
        for measure in ("accepted_records", "unresolved_records", "excluded_records")
    )
    if neotoma_reported != neotoma_accounted:
        raise CountryCoverageError("Neotoma admission outcomes do not reconcile")
    sead_received = total("sead", "source_reported", "received_records")
    sead_governed_sites = total("sead", "governed_assignment", "sites")
    if sead_received != sead_governed_sites:
        raise CountryCoverageError("SEAD country decisions do not reconcile")
    sead_accounted = sum(
        total("sead", "governed_assignment", measure)
        for measure in ("accepted_records", "unresolved_records", "excluded_records")
    )
    if sead_received != sead_accounted:
        raise CountryCoverageError("SEAD admission outcomes do not reconcile")
    boundary_received = total("boundaries", "source_reported", "received_records")
    if boundary_received != total(
        "boundaries", "governed_assignment", "accepted_records"
    ):
        raise CountryCoverageError("boundary admission does not reconcile")
    if boundary_received != total("boundaries", "publication", "published_records"):
        raise CountryCoverageError("boundary publication does not reconcile")
    _validate_reference_sources(index)


def _validate_reference_sources(
    index: Mapping[tuple[str, str, str], Mapping[str, object]],
) -> None:
    empd2 = {
        "SE": (132, 3_379, 131, 21),
        "DK": (20, 968, 20, 0),
        "NO": (622, 19_774, 622, 66),
        "FI": (141, 3_040, 141, 25),
    }
    for country, expected in empd2.items():
        counts = _object(
            index[("empd2", "source_reported", country)]["counts"], "counts"
        )
        observed = tuple(
            counts[field]
            for field in (
                "received_records",
                "observations",
                "possible_candidates",
                "unresolved_records",
            )
        )
        if observed != expected or counts["samples"] != expected[0]:
            raise CountryCoverageError(f"EMPD2 {country} denominators changed")
    if sum(values[0] for values in empd2.values()) != 915:
        raise CountryCoverageError("EMPD2 reviewed denominator does not reconcile")
    if sum(values[2] for values in empd2.values()) != 914:
        raise CountryCoverageError("EMPD2 candidate denominator does not reconcile")
    if sum(values[3] for values in empd2.values()) != 112:
        raise CountryCoverageError("EMPD2 unresolved denominator does not reconcile")

    nfi = _object(index[("nfi", "source_reported", "SE")]["counts"], "counts")
    if (
        nfi["received_records"],
        nfi["sites"],
        nfi["possible_candidates"],
        nfi["unresolved_records"],
    ) != (43_892, 6_018, 16, 16):
        raise CountryCoverageError("Swedish NFI denominators changed")

    assignment_methods = {
        "empd2": EMPD2_ASSIGNMENT_NOT_APPLIED,
        "nfi": NFI_ASSIGNMENT_NOT_APPLIED,
    }
    for source, method in assignment_methods.items():
        for dimension in COUNTRY_DIMENSIONS:
            for country in COUNTRIES:
                cell = index[(source, dimension, country)]
                counts = _object(cell["counts"], "counts")
                if cell["lifecycle_status"] == "admitted":
                    raise CountryCoverageError(
                        f"{source} candidate evidence cannot imply admission"
                    )
                if dimension != "source_reported" and (
                    any(value is not None for value in counts.values())
                    or cell["country_assignment_method"] != method
                    or cell["boundary_artifact_digest"] is not None
                ):
                    raise CountryCoverageError(
                        f"{source} non-source partition must remain not applied"
                    )
        for country in ("UNASSIGNED", "OUTSIDE"):
            counts = _object(
                index[(source, "source_reported", country)]["counts"], "counts"
            )
            if any(value is not None for value in counts.values()):
                raise CountryCoverageError(
                    f"{source} noncountry source partition must remain unknown"
                )
