from __future__ import annotations

from bijux_pollenomics.adna.domain.models.vocabularies import (
    ADNA_APPROXIMATE_COORDINATE_CONFIDENCE,
)


def build_species_rows(
    country: str,
    localities: list[dict[str, object]],
    sample_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in localities:
        key = (str(row["species_latin_name"]), str(row["animal_scope"]))
        grouped.setdefault(key, []).append(row)
    sample_grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in sample_rows:
        key = (str(row["species_latin_name"]), str(row["animal_scope"]))
        sample_grouped.setdefault(key, []).append(row)
    species_rows: list[dict[str, object]] = []
    for (species_name, animal_scope), rows in sorted(grouped.items()):
        species_sample_rows = sample_grouped.get((species_name, animal_scope), [])
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
            in ADNA_APPROXIMATE_COORDINATE_CONFIDENCE
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
        canonical_bp_pairs = [
            pair for row in rows if (pair := _canonical_bp_pair(row)) is not None
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
        if animal_scope == "wild_or_progenitor_context":
            caution_bits.append(
                "wild or progenitor context; not domesticated-core support"
            )
        if len(species_sample_rows) <= 2:
            caution_bits.append("sample support remains sparse")
        if coordinate_bases & {"named_site_geocoding", "named_site_geocoded"}:
            caution_bits.append(
                "point surface relies on named-site geocoding rather than direct coordinates"
            )
        if coordinate_confidences & set(ADNA_APPROXIMATE_COORDINATE_CONFIDENCE):
            caution_bits.append("coordinates remain approximate or inferred")
        species_rows.append(
            {
                "country": country,
                "species_latin_name": species_name,
                "species_common_name": str(rows[0]["species_common_name"]),
                "animal_scope": animal_scope,
                "curated_project_count": len(project_accessions),
                "mapped_locality_count": len(rows),
                "mapped_sample_count": sum(
                    _as_int(row.get("sample_count", 0) or 0) for row in rows
                ),
                "assignment_confidence": summarize_confidence(assignment_confidences),
                "coordinate_posture": summarize_confidence(
                    coordinate_bases | coordinate_confidences
                ),
                "oldest_signal_bp": (
                    max(older_bp for _, older_bp in canonical_bp_pairs)
                    if canonical_bp_pairs
                    else None
                ),
                "youngest_signal_bp": (
                    min(younger_bp for younger_bp, _ in canonical_bp_pairs)
                    if canonical_bp_pairs
                    else None
                ),
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


def _canonical_bp_pair(row: dict[str, object]) -> tuple[int, int] | None:
    younger_bp = row.get("time_start_bp")
    older_bp = row.get("time_end_bp")
    if (
        isinstance(younger_bp, bool)
        or not isinstance(younger_bp, int)
        or isinstance(older_bp, bool)
        or not isinstance(older_bp, int)
        or younger_bp < 0
        or younger_bp > older_bp
    ):
        return None
    return younger_bp, older_bp


def _as_int(value: object) -> int:
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return int(value)
    raise TypeError(f"expected an integer-compatible value, got {type(value).__name__}")
