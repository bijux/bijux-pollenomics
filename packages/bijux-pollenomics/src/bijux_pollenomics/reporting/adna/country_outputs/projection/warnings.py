from __future__ import annotations


def build_warning_rows(
    country: str,
    localities: list[dict[str, object]],
    sample_rows: list[dict[str, object]],
    species_rows: list[dict[str, object]],
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    if not localities:
        warnings.append(
            {
                "severity": "caution",
                "warning_code": "no_country_resolved_animal_rows",
                "message": (
                    f"No tracked non-human animal locality lead is currently assignable "
                    f"to `{country}` under the shipped pollenomics rules."
                ),
            }
        )
        return warnings
    for species_row in species_rows:
        confidence = str(species_row["assignment_confidence"])
        species_name = str(species_row["species_latin_name"])
        if confidence == "regional_projection":
            warnings.append(
                {
                    "severity": "warning",
                    "warning_code": "regional_projection",
                    "message": (
                        f"`{species_name}` reaches `{country}` through a regional "
                        "projection, not one country-exact excavation label."
                    ),
                }
            )
        if confidence == "territory_projection":
            warnings.append(
                {
                    "severity": "warning",
                    "warning_code": "territory_projection",
                    "message": (
                        f"`{species_name}` reaches `{country}` through an explicit "
                        "territorial projection rather than a mainland-only locality."
                    ),
                }
            )
        if str(species_row["animal_scope"]) == "comparator":
            warnings.append(
                {
                    "severity": "warning",
                    "warning_code": "comparator_scope",
                    "message": (
                        f"`{species_name}` stays comparator-only in `{country}` and "
                        "must not be promoted into domesticated-core farming support."
                    ),
                }
            )
        if str(species_row["animal_scope"]) == "wild_or_progenitor_context":
            warnings.append(
                {
                    "severity": "warning",
                    "warning_code": "wild_or_progenitor_scope",
                    "message": (
                        f"`{species_name}` is wild or progenitor context in `{country}` "
                        "and must not be promoted into domesticated-core farming support."
                    ),
                }
            )
        if _as_int(species_row.get("sample_row_count", 0) or 0) <= 2:
            warnings.append(
                {
                    "severity": "warning",
                    "warning_code": "sparse_sample_support",
                    "message": (
                        f"`{species_name}` currently contributes only "
                        f"{species_row.get('sample_row_count', 0)} country-resolved sample row(s) "
                        f"to `{country}`, so the country surface remains thin."
                    ),
                }
            )
        coordinate_posture = str(species_row["coordinate_posture"])
        if "approximate" in coordinate_posture or "inferred" in coordinate_posture:
            warnings.append(
                {
                    "severity": "warning",
                    "warning_code": "approximate_coordinates",
                    "message": (
                        f"`{species_name}` still carries approximate or inferred "
                        "coordinates in the country bundle."
                    ),
                }
            )
    if sample_rows and all(
        str(row.get("coordinate_basis", ""))
        in {"named_site_geocoding", "named_site_geocoded"}
        for row in sample_rows
    ):
        warnings.append(
            {
                "severity": "warning",
                "warning_code": "named_site_geocoding_only",
                "message": (
                    f"The current `{country}` animal publication relies on named-site geocoding "
                    "rather than direct published coordinates."
                ),
            }
        )
    if len(species_rows) < 3:
        warnings.append(
            {
                "severity": "caution",
                "warning_code": "thin_species_surface",
                "message": (
                    f"`{country}` currently ships a thin animal surface with only "
                    f"`{len(species_rows)}` represented tracked species."
                ),
            }
        )
    return deduplicate_warnings(warnings)


def deduplicate_warnings(warnings: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduplicated: list[dict[str, str]] = []
    for row in warnings:
        key = (row["warning_code"], row["message"])
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(row)
    return deduplicated


def _as_int(value: object) -> int:
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return int(value)
    raise TypeError(f"expected an integer-compatible value, got {type(value).__name__}")
