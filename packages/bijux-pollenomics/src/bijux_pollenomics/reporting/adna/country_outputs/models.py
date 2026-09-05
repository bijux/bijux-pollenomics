from __future__ import annotations

from dataclasses import dataclass


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
    evidence_quality_summary: dict[str, object]
    traceability_summary: dict[str, object]

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
            "evidence_quality_summary": self.evidence_quality_summary,
            "traceability_summary": self.traceability_summary,
            "sample_rows": list(self.sample_rows),
            "species_rows": list(self.species_rows),
            "localities": list(self.localities),
            "citations": list(self.citations),
            "warnings": list(self.warnings),
        }
