from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path

from ..shared.text import escape_pipes
from .atlas_evidence_rows import (
    AnimalAtlasEvidenceRow,
    build_tracked_animal_atlas_evidence_rows,
)

__all__ = [
    "CountryAnimalOutputBundle",
    "build_country_animal_output_bundle",
    "render_country_animal_citations_markdown",
    "render_country_animal_samples_markdown",
    "render_country_animal_section",
    "render_country_animal_warnings_markdown",
    "write_country_animal_localities_geojson",
    "write_country_animal_samples_csv",
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
    """Public country-bundle animal outputs derived from tracked atlas evidence rows."""

    country: str
    version: str
    generated_on: str
    sample_rows: tuple[dict[str, object], ...]
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
            "total_sample_rows": len(self.sample_rows),
            "total_species": len(self.species_rows),
            "total_localities": len(self.localities),
            "total_projects": len(
                {
                    str(row.get("project_accession", "")).strip()
                    for row in self.localities
                    if str(row.get("project_accession", "")).strip()
                }
            ),
            "sample_rows": list(self.sample_rows),
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
    """Assign tracked animal atlas evidence rows into one public Nordic country bundle."""
    evidence_rows = build_tracked_animal_atlas_evidence_rows(data_root)
    sample_lookup = _load_country_sample_lookup(Path(data_root))
    locality_rows: list[dict[str, object]] = []
    for row in evidence_rows:
        assignment = _assign_evidence_row_to_country(row, country)
        if assignment is None:
            continue
        locality_rows.append(
            {
                "country": country,
                "feature_id": row.feature_id,
                "evidence_row_id": row.evidence_row_id,
                "site_record_id": row.site_record_id,
                "species_latin_name": row.species_latin_name,
                "species_common_name": row.species_common_name,
                "animal_scope": row.animal_scope,
                "project_accession": row.primary_project_accession,
                "project_accessions": list(row.project_accessions),
                "support_class": row.support_class,
                "locality": row.locality,
                "political_entity": row.political_entity,
                "country_assignment_confidence": assignment["confidence"],
                "country_assignment_reason": assignment["reason"],
                "latitude": row.latitude,
                "longitude": row.longitude,
                "latitude_text": row.latitude_text,
                "longitude_text": row.longitude_text,
                "coordinate_basis": row.coordinate_basis,
                "coordinate_confidence": row.coordinate_confidence,
                "geocoding_method": row.geocoding_method,
                "geocoder_or_gazetteer": row.geocoder_or_gazetteer,
                "confidence_rationale": row.confidence_rationale,
                "original_place_text": row.original_place_text,
                "resolved_place_text": row.resolved_place_text,
                "time_start_bp": row.chronology.time_start_bp,
                "time_end_bp": row.chronology.time_end_bp,
                "time_mean_bp": row.chronology.time_mean_bp,
                "time_label": row.chronology.original_text,
                "dating_basis": row.chronology.dating_basis,
                "nordic_inclusion": row.nordic_inclusion,
                "nordic_inclusion_reason": row.nordic_inclusion_reason,
                "interpretation_note": row.interpretation_note,
                "paper_title": row.paper_title,
                "paper_doi": row.paper_doi,
                "publication_year": row.publication_year,
                "journal_title": row.journal_title,
                "source_url": row.paper_url,
                "sample_count": row.sample_count,
                "sample_record_ids": list(row.sample_record_ids),
                "sample_group_ids": list(row.sample_group_ids),
                "sample_namespace": row.sample_namespace,
                "inclusion_statuses": list(row.inclusion_statuses),
                "inclusion_notes": list(row.inclusion_notes),
                "supplementary_sources": list(row.supplementary_sources),
                "source_artifact_path": row.source_artifact_path,
                "source_artifact_kind": row.source_artifact_kind,
                "source_locator": row.source_locator,
                "source_support_status": row.source_support_status,
                "exact_source_text": row.exact_source_text,
            }
        )

    locality_rows.sort(
        key=lambda row: (
            str(row["species_latin_name"]),
            _assignment_sort_key(str(row["country_assignment_confidence"])),
            -(int(row["time_start_bp"]) if isinstance(row["time_start_bp"], int) else 0),
            str(row["locality"]),
        )
    )
    sample_rows = _build_sample_rows(country, locality_rows, sample_lookup)
    species_rows = _build_species_rows(country, locality_rows, sample_rows)
    citations = _build_citation_rows(country, locality_rows, sample_rows)
    warnings = _build_warning_rows(country, locality_rows, sample_rows, species_rows)
    return CountryAnimalOutputBundle(
        country=country,
        version=version,
        generated_on=generated_on,
        sample_rows=tuple(sample_rows),
        species_rows=tuple(species_rows),
        localities=tuple(locality_rows),
        citations=tuple(citations),
        warnings=tuple(warnings),
    )


def write_country_animal_samples_csv(path: Path, bundle: CountryAnimalOutputBundle) -> None:
    """Write one CSV table of country-resolved animal sample rows."""
    fieldnames = (
        "country",
        "species_latin_name",
        "species_common_name",
        "sample_record_id",
        "sample_group_id",
        "sample_namespace",
        "feature_id",
        "evidence_row_id",
        "site_record_id",
        "project_accession",
        "paper_title",
        "paper_doi",
        "supplementary_source",
        "locality",
        "country_assignment_confidence",
        "country_assignment_reason",
        "coordinate_basis",
        "coordinate_confidence",
        "latitude_text",
        "longitude_text",
        "source_locator",
        "source_support_status",
        "time_label",
        "inclusion_status",
        "inclusion_note",
        "sample_basis",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in bundle.sample_rows:
            writer.writerow(row)


def write_country_animal_species_csv(path: Path, bundle: CountryAnimalOutputBundle) -> None:
    """Write one CSV table of country-resolved animal species rows."""
    fieldnames = (
        "country",
        "species_latin_name",
        "species_common_name",
        "animal_scope",
        "curated_project_count",
        "mapped_locality_count",
        "mapped_sample_count",
        "sample_row_count",
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
                    "project_accessions": ";".join(str(item) for item in row.get("project_accessions", [])),
                }
            )


def write_country_animal_localities_geojson(path: Path, bundle: CountryAnimalOutputBundle) -> None:
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
            {"label": "Coordinate basis", "value": row["coordinate_basis"]},
            {"label": "Coordinate confidence", "value": row["coordinate_confidence"]},
            {"label": "Mapped sample identifiers", "value": ", ".join(row["sample_record_ids"])},
            {"label": "Interpretation", "value": row["interpretation_note"]},
        ]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "properties": {
                    "name": row["locality"],
                    "country": row["country"],
                    "feature_id": row["feature_id"],
                    "evidence_row_id": row["evidence_row_id"],
                    "site_record_id": row["site_record_id"],
                    "species_latin_name": row["species_latin_name"],
                    "species_common_name": row["species_common_name"],
                    "animal_scope": row["animal_scope"],
                    "project_accession": row["project_accession"],
                    "project_accessions": row["project_accessions"],
                    "support_class": row["support_class"],
                    "country_assignment_confidence": row["country_assignment_confidence"],
                    "country_assignment_reason": row["country_assignment_reason"],
                    "coordinate_basis": row["coordinate_basis"],
                    "coordinate_confidence": row["coordinate_confidence"],
                    "sample_count": row["sample_count"],
                    "sample_record_ids": row["sample_record_ids"],
                    "sample_group_ids": row["sample_group_ids"],
                    "sample_namespace": row["sample_namespace"],
                    "source_artifact_path": row["source_artifact_path"],
                    "source_artifact_kind": row["source_artifact_kind"],
                    "source_locator": row["source_locator"],
                    "source_support_status": row["source_support_status"],
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


def render_country_animal_citations_markdown(bundle: CountryAnimalOutputBundle) -> str:
    """Render a public-facing citation appendix for one country's animal evidence."""
    lines = [
        f"# {bundle.country} animal aDNA citations",
        "",
        "This appendix lists the tracked animal-aDNA papers that currently back the",
        f"`{bundle.country}` country bundle.",
        "",
        "| Species | Project accession | Paper title | DOI | Year | Sample rows | Locality rows | Supplementary support | Source posture | Assignment posture |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    if not bundle.citations:
        lines.append("| No animal country citations yet | - | - | - | 0 | 0 | 0 | - | - | - |")
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
                f"{row['sample_row_count']} | "
                f"{row['locality_row_count']} | "
                f"{escape_pipes(str(row['supplementary_support']) or '-')} | "
                f"{escape_pipes(str(row['source_posture']) or '-')} | "
                f"{escape_pipes(str(row['country_assignment_confidence']))} |"
            )
    lines.append("")
    return "\n".join(lines)


def render_country_animal_samples_markdown(bundle: CountryAnimalOutputBundle) -> str:
    """Render one markdown table of country-resolved animal sample rows."""
    lines = [
        f"# {bundle.country} animal aDNA sample rows",
        "",
        "This table lists the exact curated animal sample rows that currently feed the",
        f"`{bundle.country}` country surface.",
        "",
        "| Species | Sample record | Project accession | Locality | Assignment posture | Coordinate posture | Source locator | Citation |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not bundle.sample_rows:
        lines.append("| No country-resolved animal sample rows yet | - | - | - | - | - | - | - |")
        lines.append("")
        return "\n".join(lines)
    for row in bundle.sample_rows:
        doi = str(row["paper_doi"])
        citation = f"[{escape_pipes(doi)}](https://doi.org/{doi})" if doi else "-"
        lines.append(
            f"| {escape_pipes(str(row['species_latin_name']))} | "
            f"{escape_pipes(str(row['sample_record_id']))} | "
            f"{escape_pipes(str(row['project_accession']))} | "
            f"{escape_pipes(str(row['locality']) or '-')} | "
            f"{escape_pipes(str(row['country_assignment_confidence']))} | "
            f"{escape_pipes(str(row['coordinate_basis']))} / "
            f"{escape_pipes(str(row['coordinate_confidence']))} | "
            f"{escape_pipes(str(row['source_locator']) or '-')} | "
            f"{citation} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_country_animal_warnings_markdown(bundle: CountryAnimalOutputBundle) -> str:
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
        lines.append(f"- `{row['severity']}` `{row['warning_code']}`: {row['message']}")
    lines.append("")
    return "\n".join(lines)


def render_country_animal_section(
    bundle: CountryAnimalOutputBundle,
    *,
    summary_json_name: str,
    samples_csv_name: str,
    samples_markdown_name: str,
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
- Country-resolved animal sample rows: `{len(bundle.sample_rows)}`
- Country-resolved animal locality rows: `{len(bundle.localities)}`
- Supporting tracked projects: `{len(bundle.citations)}`

### Animal Output Files

- Machine-readable animal summary: [`{summary_json_name}`](./{summary_json_name})
- Animal sample rows CSV: [`{samples_csv_name}`](./{samples_csv_name})
- Animal sample rows markdown: [`{samples_markdown_name}`](./{samples_markdown_name})
- Animal species summary CSV: [`{species_csv_name}`](./{species_csv_name})
- Animal localities GeoJSON: [`{localities_geojson_name}`](./{localities_geojson_name})
- Animal citation appendix: [`{citations_markdown_name}`](./{citations_markdown_name})
- Animal warning appendix: [`{warnings_markdown_name}`](./{warnings_markdown_name})

### Country-Resolved Animal Species

| Common name | Latin name | Animal scope | Locality rows | Assignment posture | Caution |
| --- | --- | --- | ---: | --- | --- |
{species_lines}
"""


def _assign_evidence_row_to_country(
    row: AnimalAtlasEvidenceRow,
    country: str,
) -> dict[str, str] | None:
    political_entity = row.political_entity.strip()
    if not row.nordic_inclusion:
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


def _build_sample_rows(
    country: str,
    localities: list[dict[str, object]],
    sample_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    sample_rows: list[dict[str, object]] = []
    for locality in localities:
        project_accession = str(locality.get("project_accession", "")).strip()
        locality_sample_record_ids = locality.get("sample_record_ids", [])
        if not isinstance(locality_sample_record_ids, list):
            continue
        for sample_record_id in locality_sample_record_ids:
            sample_id = str(sample_record_id).strip()
            sample = sample_lookup.get(sample_id, {})
            chronology = sample.get("chronology", {})
            coordinates = sample.get("coordinates", {})
            sample_rows.append(
                {
                    "country": country,
                    "species_latin_name": str(locality.get("species_latin_name", "")),
                    "species_common_name": str(locality.get("species_common_name", "")),
                    "sample_record_id": sample_id,
                    "sample_group_id": str(
                        sample.get("group_id")
                        or sample.get("master_id")
                        or project_accession
                    ),
                    "sample_namespace": str(
                        sample.get("identity", {}).get("namespace", "")
                    ),
                    "feature_id": str(locality.get("feature_id", "")),
                    "evidence_row_id": str(locality.get("evidence_row_id", "")),
                    "site_record_id": str(locality.get("site_record_id", "")),
                    "project_accession": project_accession,
                    "paper_title": str(
                        sample.get("publication") or locality.get("paper_title", "")
                    ),
                    "paper_doi": str(
                        sample.get("paper_doi") or locality.get("paper_doi", "")
                    ),
                    "supplementary_source": str(sample.get("supplementary_source", "")),
                    "locality": str(sample.get("locality") or locality.get("locality", "")),
                    "country_assignment_confidence": str(
                        locality.get("country_assignment_confidence", "")
                    ),
                    "country_assignment_reason": str(
                        locality.get("country_assignment_reason", "")
                    ),
                    "coordinate_basis": str(locality.get("coordinate_basis", "")),
                    "coordinate_confidence": str(locality.get("coordinate_confidence", "")),
                    "source_locator": str(locality.get("source_locator", "")),
                    "source_support_status": str(
                        locality.get("source_support_status", "")
                    ),
                    "time_label": str(
                        chronology.get("original_text") or locality.get("time_label", "")
                    ),
                    "inclusion_status": str(sample.get("inclusion_status", "")),
                    "inclusion_note": str(sample.get("inclusion_note", "")),
                    "sample_basis": str(sample.get("sample_basis", "")),
                    "latitude_text": str(
                        coordinates.get("latitude_text") or locality.get("latitude_text", "")
                    ),
                    "longitude_text": str(
                        coordinates.get("longitude_text")
                        or locality.get("longitude_text", "")
                    ),
                }
            )
    sample_rows.sort(
        key=lambda row: (
            str(row["species_latin_name"]),
            str(row["project_accession"]),
            str(row["sample_record_id"]),
        )
    )
    return sample_rows


def _build_species_rows(
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
        assignment_confidences = {str(row["country_assignment_confidence"]) for row in rows}
        coordinate_bases = {str(row["coordinate_basis"]) for row in rows}
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
                "mapped_sample_count": sum(int(row.get("sample_count", 0) or 0) for row in rows),
                "assignment_confidence": _summarize_confidence(assignment_confidences),
                "coordinate_posture": _summarize_confidence(coordinate_bases | coordinate_confidences),
                "oldest_signal_bp": max(oldest_values) if oldest_values else None,
                "youngest_signal_bp": min(youngest_values) if youngest_values else None,
                "project_accessions": project_accessions,
                "sample_row_count": len(species_sample_rows),
                "caution_note": "; ".join(caution_bits) or "current country assignment is direct and explicit",
            }
        )
    return species_rows


def _build_citation_rows(
    country: str,
    localities: list[dict[str, object]],
    sample_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in localities:
        key = (str(row["species_latin_name"]), str(row["project_accession"]))
        current = grouped.setdefault(
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
                "sample_row_ids": set(),
                "locality_row_ids": set(),
                "supplementary_support": set(),
                "source_posture": set(),
            },
        )
        current["locality_row_ids"].add(str(row["site_record_id"]))
        for source in row.get("supplementary_sources", []):
            source_text = str(source).strip()
            if source_text:
                current["supplementary_support"].add(source_text)
        source_status = str(row.get("source_support_status", "")).strip()
        if source_status:
            current["source_posture"].add(source_status)
    for row in sample_rows:
        key = (str(row["species_latin_name"]), str(row["project_accession"]))
        current = grouped.get(key)
        if current is None:
            continue
        current["sample_row_ids"].add(str(row["sample_record_id"]))
        supplementary_source = str(row.get("supplementary_source", "")).strip()
        if supplementary_source:
            current["supplementary_support"].add(supplementary_source)
    output_rows: list[dict[str, object]] = []
    for row in grouped.values():
        output_rows.append(
            {
                "country": row["country"],
                "species_latin_name": row["species_latin_name"],
                "species_common_name": row["species_common_name"],
                "animal_scope": row["animal_scope"],
                "project_accession": row["project_accession"],
                "paper_title": row["paper_title"],
                "paper_doi": row["paper_doi"],
                "publication_year": row["publication_year"],
                "journal_title": row["journal_title"],
                "country_assignment_confidence": row["country_assignment_confidence"],
                "sample_row_ids": sorted(row["sample_row_ids"]),
                "locality_row_ids": sorted(row["locality_row_ids"]),
                "sample_row_count": len(row["sample_row_ids"]),
                "locality_row_count": len(row["locality_row_ids"]),
                "supplementary_support": "; ".join(sorted(row["supplementary_support"])),
                "source_posture": "; ".join(sorted(row["source_posture"])),
            }
        )
    return sorted(
        output_rows,
        key=lambda row: (str(row["species_latin_name"]), str(row["project_accession"])),
    )


def _build_warning_rows(
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
        if int(species_row.get("sample_row_count", 0) or 0) <= 2:
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
        str(row.get("coordinate_basis", "")) in {"named_site_geocoding", "named_site_geocoded"}
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
    return _deduplicate_warnings(warnings)


def _deduplicate_warnings(warnings: list[dict[str, str]]) -> list[dict[str, str]]:
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


def _load_country_sample_lookup(data_root: Path) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    adna_root = Path(data_root) / "adna"
    for sample_path in adna_root.glob("*/normalized/sample_records.json"):
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        rows = payload.get("samples", [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            stable_token = str(row.get("identity", {}).get("stable_token", "")).strip()
            if stable_token:
                lookup[stable_token] = row
    return lookup
