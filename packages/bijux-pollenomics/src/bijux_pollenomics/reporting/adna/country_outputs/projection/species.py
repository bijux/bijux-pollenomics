from __future__ import annotations


def build_species_rows(
    country: str,
    localities: list[dict[str, object]],
    sample_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in localities:
        grouped.setdefault(str(row["species_latin_name"]), []).append(row)
    sample_grouped: dict[str, list[dict[str, object]]] = {}
    for row in sample_rows:
        sample_grouped.setdefault(str(row["species_latin_name"]), []).append(row)
    species_rows: list[dict[str, object]] = []
    for species_name, rows in sorted(grouped.items()):
        species_sample_rows = sample_grouped.get(species_name, [])
        project_accessions = sorted(
            {
                str(row["project_accession"])
                for row in rows
                if str(row["project_accession"]).strip()
            }
        )
        assignment_confidences = {
            str(row["country_assignment_confidence"]) for row in rows
        }
        coordinate_bases = {str(row["coordinate_basis"]) for row in rows}
        coordinate_confidences = {str(row["coordinate_confidence"]) for row in rows}
        exact_coordinate_sample_count = sum(
            1
            for row in species_sample_rows
            if str(row.get("coordinate_confidence", "")).strip() == "exact"
        )
        approximate_coordinate_sample_count = sum(
            1
            for row in species_sample_rows
            if str(row.get("coordinate_confidence", "")).strip()
            in {"approximate", "inferred"}
        )
        sample_lineage_backed_count = sum(
            1
            for row in species_sample_rows
            if str(row.get("sample_lineage_path", "")).strip()
        )
        chronology_provenance_backed_count = sum(
            1
            for row in species_sample_rows
            if str(row.get("chronology_provenance_path", "")).strip()
        )
        site_evidence_backed_count = sum(
            1
            for row in species_sample_rows
            if str(row.get("site_evidence_path", "")).strip()
        )
        coordinate_provenance_backed_count = sum(
            1
            for row in species_sample_rows
            if str(row.get("coordinate_provenance_path", "")).strip()
        )
        oldest_values = [
            _as_int(row["time_start_bp"])
            for row in rows
            if isinstance(row.get("time_start_bp"), int)
        ]
        youngest_values = [
            _as_int(row["time_end_bp"])
            for row in rows
            if isinstance(row.get("time_end_bp"), int)
        ]
        caution_bits = []
        if "regional_projection" in assignment_confidences:
            caution_bits.append("regional Baltic projection, not country-exact")
        if "territory_projection" in assignment_confidences:
            caution_bits.append(
                "territorial projection rather than mainland-only assignment"
            )
        if any(str(row.get("animal_scope")) == "comparator" for row in rows):
            caution_bits.append("comparator evidence only")
        if len(species_sample_rows) <= 2:
            caution_bits.append("sample support remains sparse")
        if coordinate_bases & {"named_site_geocoding", "named_site_geocoded"}:
            caution_bits.append(
                "point surface relies on named-site geocoding rather than direct coordinates"
            )
        if coordinate_confidences & {"approximate", "inferred"}:
            caution_bits.append("coordinates remain approximate or inferred")
        species_rows.append(
            {
                "country": country,
                "species_latin_name": species_name,
                "species_common_name": str(rows[0]["species_common_name"]),
                "animal_scope": str(rows[0]["animal_scope"]),
                "curated_project_count": len(project_accessions),
                "mapped_locality_count": len(rows),
                "mapped_sample_count": sum(
                    _as_int(row.get("sample_count", 0) or 0) for row in rows
                ),
                "assignment_confidence": summarize_confidence(assignment_confidences),
                "coordinate_posture": summarize_confidence(
                    coordinate_bases | coordinate_confidences
                ),
                "oldest_signal_bp": max(oldest_values) if oldest_values else None,
                "youngest_signal_bp": min(youngest_values) if youngest_values else None,
                "project_accessions": project_accessions,
                "sample_row_count": len(species_sample_rows),
                "exact_coordinate_sample_count": exact_coordinate_sample_count,
                "approximate_coordinate_sample_count": approximate_coordinate_sample_count,
                "sample_lineage_backed_sample_count": sample_lineage_backed_count,
                "site_evidence_backed_sample_count": site_evidence_backed_count,
                "chronology_provenance_backed_sample_count": (
                    chronology_provenance_backed_count
                ),
                "coordinate_provenance_backed_sample_count": (
                    coordinate_provenance_backed_count
                ),
                "caution_note": "; ".join(caution_bits)
                or "current country assignment is direct and explicit",
            }
        )
    return species_rows

def summarize_confidence(values: set[str]) -> str:
    if len(values) == 1:
        return next(iter(values))
    return ";".join(sorted(values))


def _as_int(value: object) -> int:
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return int(value)
    raise TypeError(f"expected an integer-compatible value, got {type(value).__name__}")
