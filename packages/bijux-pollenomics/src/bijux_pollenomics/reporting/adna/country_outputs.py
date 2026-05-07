from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path

from ...adna import AdnaLocalitySummary, build_species_support_matrix
from ..shared.text import escape_pipes
from .animal_localities import load_tracked_animal_localities

__all__ = [
    "CountryAnimalOutputBundle",
    "build_country_animal_output_bundle",
    "render_country_animal_citations_markdown",
    "render_country_animal_section",
    "render_country_animal_warnings_markdown",
    "write_country_animal_localities_geojson",
    "write_country_animal_species_csv",
]

_REGIONAL_COUNTRY_ASSIGNMENTS: dict[str, tuple[str, ...]] = {
    "Baltic Sea Region": ("Sweden", "Denmark", "Finland"),
}
_TERRITORY_COUNTRY_ASSIGNMENTS: dict[str, str] = {
    "Svalbard": "Norway",
}


@dataclass(frozen=True)
class CountryAnimalOutputBundle:
    """Public country-bundle animal outputs derived from tracked species data."""

    country: str
    version: str
    generated_on: str
    species_rows: tuple[dict[str, object], ...]
    localities: tuple[dict[str, object], ...]
    citations: tuple[dict[str, object], ...]
    warnings: tuple[dict[str, str], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "country-animal-adna-summary.v1",
            "country": self.country,
            "version": self.version,
            "generated_on": self.generated_on,
            "total_species": len(self.species_rows),
            "total_localities": len(self.localities),
            "total_projects": len(
                {
                    str(row.get("project_accession", "")).strip()
                    for row in self.localities
                    if str(row.get("project_accession", "")).strip()
                }
            ),
            "species_rows": list(self.species_rows),
            "localities": list(self.localities),
            "citations": list(self.citations),
            "warnings": list(self.warnings),
        }


def build_country_animal_output_bundle(
    *,
    data_root: Path,
    country: str,
    version: str,
    generated_on: str,
) -> CountryAnimalOutputBundle:
    """Assign tracked animal locality leads into one public Nordic country bundle."""
    localities = load_tracked_animal_localities(data_root)
    metadata_by_species = _load_species_metadata(Path(data_root))

    locality_rows: list[dict[str, object]] = []
    for locality in localities:
        assignment = _assign_locality_to_country(locality, country)
        if assignment is None:
            continue
        species_metadata = metadata_by_species.get(locality.species_latin_name, {})
        animal_scope = str(species_metadata.get("animal_scope", "domesticated_core"))
        project_accession = locality.project_accessions[0] if locality.project_accessions else ""
        citation_lookup = species_metadata.get("citation_lookup", {})
        review_lookup = species_metadata.get("review_lookup", {})
        if not isinstance(citation_lookup, dict) or not isinstance(review_lookup, dict):
            citation_lookup = {}
            review_lookup = {}
        citation = citation_lookup.get(project_accession, {})
        review = review_lookup.get(project_accession, {})
        locality_rows.append(
            {
                "country": country,
                "species_latin_name": locality.species_latin_name,
                "species_common_name": locality.species_common_name,
                "animal_scope": animal_scope,
                "project_accession": project_accession,
                "support_class": str(review.get("support_class", "mapped_locality")),
                "locality": locality.locality or locality.identity.locality_text,
                "political_entity": locality.identity.political_entity or "",
                "country_assignment_confidence": assignment["confidence"],
                "country_assignment_reason": assignment["reason"],
                "latitude": locality.latitude,
                "longitude": locality.longitude,
                "coordinate_confidence": locality.coordinate_confidence,
                "time_start_bp": locality.time_start_bp,
                "time_end_bp": locality.time_end_bp,
                "time_mean_bp": locality.time_mean_bp,
                "time_label": locality.time_label,
                "dating_basis": locality.dating_basis,
                "nordic_inclusion": locality.nordic_inclusion,
                "nordic_inclusion_reason": locality.nordic_inclusion_reason,
                "interpretation_note": locality.interpretation_note,
                "paper_title": str(citation.get("paper_title", "") or review.get("paper_title", "")),
                "paper_doi": str(citation.get("paper_doi", "") or review.get("paper_doi", "")),
                "publication_year": str(citation.get("publication_year", "")),
                "journal_title": str(citation.get("journal_title", "")),
                "source_url": _doi_url_for(
                    str(citation.get("paper_doi", "") or review.get("paper_doi", ""))
                ),
            }
        )

    locality_rows.sort(
        key=lambda row: (
            row["species_latin_name"],
            _assignment_sort_key(str(row["country_assignment_confidence"])),
            -(int(row["time_start_bp"]) if isinstance(row["time_start_bp"], int) else 0),
            str(row["locality"]),
        )
    )
    species_rows = _build_species_rows(country, locality_rows)
    citations = _build_citation_rows(country, locality_rows)
    warnings = _build_warning_rows(country, locality_rows, species_rows)
    return CountryAnimalOutputBundle(
        country=country,
        version=version,
        generated_on=generated_on,
        species_rows=tuple(species_rows),
        localities=tuple(locality_rows),
        citations=tuple(citations),
        warnings=tuple(warnings),
    )


def write_country_animal_species_csv(
    path: Path, bundle: CountryAnimalOutputBundle
) -> None:
    """Write one CSV table of country-resolved animal species rows."""
    fieldnames = (
        "country",
        "species_latin_name",
        "species_common_name",
        "animal_scope",
        "curated_project_count",
        "mapped_locality_count",
        "assignment_confidence",
        "coordinate_posture",
        "oldest_signal_bp",
        "youngest_signal_bp",
        "project_accessions",
        "caution_note",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in bundle.species_rows:
            writer.writerow(
                {
                    **row,
                    "project_accessions": ";".join(
                        str(item) for item in row.get("project_accessions", [])
                    ),
                }
            )


def write_country_animal_localities_geojson(
    path: Path, bundle: CountryAnimalOutputBundle
) -> None:
    """Write one map-ready feature collection for country-resolved animal localities."""
    features: list[dict[str, object]] = []
    for row in bundle.localities:
        latitude = row.get("latitude")
        longitude = row.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            continue
        popup_rows = [
            {"label": "Species", "value": row["species_latin_name"]},
            {"label": "Animal scope", "value": str(row["animal_scope"]).replace("_", " ")},
            {"label": "Project accession", "value": row["project_accession"]},
            {"label": "Country assignment", "value": row["country_assignment_confidence"]},
            {"label": "Assignment note", "value": row["country_assignment_reason"]},
            {"label": "Chronology", "value": row["time_label"]},
            {"label": "Coordinate confidence", "value": row["coordinate_confidence"]},
            {"label": "Interpretation", "value": row["interpretation_note"]},
        ]
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
                "properties": {
                    "name": row["locality"],
                    "country": row["country"],
                    "species_latin_name": row["species_latin_name"],
                    "species_common_name": row["species_common_name"],
                    "animal_scope": row["animal_scope"],
                    "project_accession": row["project_accession"],
                    "support_class": row["support_class"],
                    "country_assignment_confidence": row["country_assignment_confidence"],
                    "country_assignment_reason": row["country_assignment_reason"],
                    "coordinate_confidence": row["coordinate_confidence"],
                    "time_start_bp": row["time_start_bp"],
                    "time_end_bp": row["time_end_bp"],
                    "time_mean_bp": row["time_mean_bp"],
                    "time_label": row["time_label"],
                    "paper_title": row["paper_title"],
                    "paper_doi": row["paper_doi"],
                    "source_url": row["source_url"],
                    "popup_rows": [item for item in popup_rows if item["value"]],
                },
            }
        )
    path.write_text(
        json.dumps(
            {
                "schema_version": "country-animal-adna-localities.v1",
                "type": "FeatureCollection",
                "country": bundle.country,
                "features": features,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def render_country_animal_citations_markdown(
    bundle: CountryAnimalOutputBundle,
) -> str:
    """Render a public-facing citation appendix for one country's animal evidence."""
    lines = [
        f"# {bundle.country} animal aDNA citations",
        "",
        "This appendix lists the tracked animal-aDNA papers that currently back the",
        f"`{bundle.country}` country bundle.",
        "",
        "| Species | Project accession | Paper title | DOI | Year | Assignment posture |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    if not bundle.citations:
        lines.append("| No animal country citations yet | - | - | - | 0 | - |")
    else:
        for row in bundle.citations:
            doi = str(row["paper_doi"])
            doi_cell = f"[{escape_pipes(doi)}](https://doi.org/{doi})" if doi else "-"
            lines.append(
                f"| {escape_pipes(str(row['species_latin_name']))} | "
                f"{escape_pipes(str(row['project_accession']))} | "
                f"{escape_pipes(str(row['paper_title']) or '-')} | "
                f"{doi_cell} | "
                f"{escape_pipes(str(row['publication_year']) or '0')} | "
                f"{escape_pipes(str(row['country_assignment_confidence']))} |"
            )
    lines.append("")
    return "\n".join(lines)


def render_country_animal_warnings_markdown(
    bundle: CountryAnimalOutputBundle,
) -> str:
    """Render one warning appendix for country-level animal evidence limits."""
    lines = [
        f"# {bundle.country} animal aDNA warnings",
        "",
        "These warnings make the country-level animal surface honest instead of",
        "letting regional, comparator, or approximate evidence look cleaner than it is.",
        "",
    ]
    if not bundle.warnings:
        lines.append("- No additional warnings. The current country bundle has no tracked animal rows.")
        lines.append("")
        return "\n".join(lines)
    for row in bundle.warnings:
        lines.append(
            f"- `{row['severity']}` `{row['warning_code']}`: {row['message']}"
        )
    lines.append("")
    return "\n".join(lines)


def render_country_animal_section(
    bundle: CountryAnimalOutputBundle,
    *,
    summary_json_name: str,
    species_csv_name: str,
    localities_geojson_name: str,
    citations_markdown_name: str,
    warnings_markdown_name: str,
) -> str:
    """Render the README addendum for country-level animal outputs."""
    if not bundle.species_rows:
        return f"""

## Animal aDNA Country Outputs

No tracked non-human animal locality lead is currently assignable to `{bundle.country}`
with the current repository rules, so this country bundle ships only the human AADR
surface for now.
"""
    species_lines = "\n".join(
        f"| {escape_pipes(str(row['species_common_name']))} | "
        f"{escape_pipes(str(row['species_latin_name']))} | "
        f"{escape_pipes(str(row['animal_scope']))} | "
        f"{row['mapped_locality_count']} | "
        f"{escape_pipes(str(row['assignment_confidence']))} | "
        f"{escape_pipes(str(row['caution_note']))} |"
        for row in bundle.species_rows
    )
    return f"""

## Animal aDNA Country Outputs

- Tracked animal species represented: `{len(bundle.species_rows)}`
- Country-resolved animal locality rows: `{len(bundle.localities)}`
- Supporting tracked projects: `{len(bundle.citations)}`

### Animal Output Files

- Machine-readable animal summary: [`{summary_json_name}`](./{summary_json_name})
- Animal species summary CSV: [`{species_csv_name}`](./{species_csv_name})
- Animal localities GeoJSON: [`{localities_geojson_name}`](./{localities_geojson_name})
- Animal citation appendix: [`{citations_markdown_name}`](./{citations_markdown_name})
- Animal warning appendix: [`{warnings_markdown_name}`](./{warnings_markdown_name})

### Country-Resolved Animal Species

| Common name | Latin name | Animal scope | Locality rows | Assignment posture | Caution |
| --- | --- | --- | ---: | --- | --- |
{species_lines}
"""


def _load_species_metadata(data_root: Path) -> dict[str, dict[str, object]]:
    adna_root = data_root / "adna"
    metadata: dict[str, dict[str, object]] = {}
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        species_root = adna_root / species.slug
        if not species_root.is_dir():
            continue
        metadata[species.latin_name] = {
            "animal_scope": _animal_scope_for(species_root),
            "review_lookup": _load_review_lookup(species_root),
            "citation_lookup": _load_citation_lookup(species_root),
        }
    return metadata


def _animal_scope_for(species_root: Path) -> str:
    payload = json.loads(
        (species_root / "reports" / "support_summary.json").read_text(encoding="utf-8")
    )
    dataset_review = payload.get("dataset_review", {})
    return (
        "comparator"
        if isinstance(dataset_review, dict)
        and str(dataset_review.get("product_role", "")).strip() == "comparator"
        else "domesticated_core"
    )


def _load_review_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(
        (species_root / "review" / "species_review.json").read_text(encoding="utf-8")
    )
    lookup: dict[str, dict[str, str]] = {}
    for key in (
        "accepted_projects",
        "rejected_projects",
        "too_weak_projects",
        "comparator_projects",
        "nordic_unmapped_leads",
    ):
        rows = payload.get(key, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            accession = str(row.get("project_accession", "")).strip()
            if accession:
                lookup[accession] = {
                    "support_class": str(row.get("support_class", "")),
                    "reason": str(row.get("reason", "")),
                    "paper_title": str(row.get("paper_title", "")),
                    "paper_doi": str(row.get("paper_doi", "")),
                }
    return lookup


def _load_citation_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    path = species_root / "manifests" / "citation_manifest.csv"
    if not path.is_file():
        return {}
    lookup: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            accession = str(row.get("project_accession", "")).strip()
            if not accession:
                continue
            lookup[accession] = {
                "paper_title": str(row.get("paper_title", "")).strip(),
                "paper_doi": str(row.get("paper_doi", "")).strip(),
                "publication_year": str(row.get("publication_year", "")).strip(),
                "journal_title": str(row.get("journal_title", "")).strip(),
            }
    return lookup


def _assign_locality_to_country(
    locality: AdnaLocalitySummary,
    country: str,
) -> dict[str, str] | None:
    political_entity = (locality.identity.political_entity or "").strip()
    if not locality.nordic_inclusion:
        return None
    if political_entity == country:
        return {
            "confidence": "exact_country",
            "reason": f"The tracked locality lead is already labeled `{country}`.",
        }
    territory_owner = _TERRITORY_COUNTRY_ASSIGNMENTS.get(political_entity)
    if territory_owner == country:
        return {
            "confidence": "territory_projection",
            "reason": (
                f"The tracked locality lead is labeled `{political_entity}` and is "
                f"published under `{country}` as an explicit territorial projection."
            ),
        }
    regional_countries = _REGIONAL_COUNTRY_ASSIGNMENTS.get(political_entity, ())
    if country in regional_countries:
        return {
            "confidence": "regional_projection",
            "reason": (
                f"The tracked locality lead is labeled `{political_entity}` and is "
                f"published under `{country}` as a regional Baltic projection, not "
                "a country-exact excavation."
            ),
        }
    return None


def _build_species_rows(
    country: str,
    localities: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in localities:
        grouped.setdefault(str(row["species_latin_name"]), []).append(row)
    species_rows: list[dict[str, object]] = []
    for species_name, rows in sorted(grouped.items()):
        project_accessions = sorted(
            {
                str(row["project_accession"])
                for row in rows
                if str(row["project_accession"]).strip()
            }
        )
        assignment_confidences = {str(row["country_assignment_confidence"]) for row in rows}
        coordinate_confidences = {str(row["coordinate_confidence"]) for row in rows}
        oldest_values = [
            int(row["time_start_bp"])
            for row in rows
            if isinstance(row.get("time_start_bp"), int)
        ]
        youngest_values = [
            int(row["time_end_bp"])
            for row in rows
            if isinstance(row.get("time_end_bp"), int)
        ]
        caution_bits = []
        if "regional_projection" in assignment_confidences:
            caution_bits.append("regional Baltic projection, not country-exact")
        if "territory_projection" in assignment_confidences:
            caution_bits.append("territorial projection rather than mainland-only assignment")
        if any(str(row.get("animal_scope")) == "comparator" for row in rows):
            caution_bits.append("comparator evidence only")
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
                "assignment_confidence": _summarize_confidence(assignment_confidences),
                "coordinate_posture": _summarize_confidence(coordinate_confidences),
                "oldest_signal_bp": max(oldest_values) if oldest_values else None,
                "youngest_signal_bp": min(youngest_values) if youngest_values else None,
                "project_accessions": project_accessions,
                "caution_note": "; ".join(caution_bits)
                or "current country assignment is direct and explicit",
            }
        )
    return species_rows


def _build_citation_rows(
    country: str,
    localities: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in localities:
        key = (str(row["species_latin_name"]), str(row["project_accession"]))
        grouped.setdefault(
            key,
            {
                "country": country,
                "species_latin_name": row["species_latin_name"],
                "species_common_name": row["species_common_name"],
                "animal_scope": row["animal_scope"],
                "project_accession": row["project_accession"],
                "paper_title": row["paper_title"],
                "paper_doi": row["paper_doi"],
                "publication_year": row["publication_year"],
                "journal_title": row["journal_title"],
                "country_assignment_confidence": row["country_assignment_confidence"],
            },
        )
    return sorted(
        grouped.values(),
        key=lambda row: (
            str(row["species_latin_name"]),
            str(row["project_accession"]),
        ),
    )


def _build_warning_rows(
    country: str,
    localities: list[dict[str, object]],
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
        if "approximate" in str(species_row["coordinate_posture"]) or "inferred" in str(
            species_row["coordinate_posture"]
        ):
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
    return _deduplicate_warnings(warnings)


def _deduplicate_warnings(
    warnings: list[dict[str, str]],
) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduplicated: list[dict[str, str]] = []
    for row in warnings:
        key = (row["warning_code"], row["message"])
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(row)
    return deduplicated


def _summarize_confidence(values: set[str]) -> str:
    if len(values) == 1:
        return next(iter(values))
    return ";".join(sorted(values))


def _assignment_sort_key(confidence: str) -> int:
    order = {
        "exact_country": 0,
        "territory_projection": 1,
        "regional_projection": 2,
    }
    return order.get(confidence, 9)


def _doi_url_for(doi: str) -> str:
    doi = doi.strip()
    return f"https://doi.org/{doi}" if doi else ""
