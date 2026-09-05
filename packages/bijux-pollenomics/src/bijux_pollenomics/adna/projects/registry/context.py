from __future__ import annotations

from dataclasses import dataclass

from ...sources.archive import AdnaArchiveProject

__all__ = [
    "ADNA_NORDIC_RELEVANCE",
    "AdnaProjectContext",
    "build_species_freshness_rows",
    "resolve_project_context",
]

ADNA_NORDIC_RELEVANCE = (
    "nordic_relevant_unmapped",
    "nordic_adjacent",
    "non_nordic",
    "unknown",
)
_LAST_CHECKED_ON = "2026-05-07"


@dataclass(frozen=True)
class AdnaProjectContext:
    """Curated project context that is not visible from archive selectors alone."""

    nordic_relevance: str
    nordic_relevance_reason: str
    last_checked_on: str

    def as_dict(self) -> dict[str, object]:
        return {
            "nordic_relevance": self.nordic_relevance,
            "nordic_relevance_reason": self.nordic_relevance_reason,
            "last_checked_on": self.last_checked_on,
        }


_PROJECT_CONTEXT: dict[str, AdnaProjectContext] = {
    "PRJEB59481": AdnaProjectContext(
        nordic_relevance="nordic_relevant_unmapped",
        nordic_relevance_reason=(
            "The Nordic-relevant primary supplement resolves the five Baltic sheep "
            "samples to Kastelholm and Stora Förvar, but neither site has admitted "
            "primary coordinates for atlas point publication."
        ),
        last_checked_on=_LAST_CHECKED_ON,
    ),
    "PRJEB60484": AdnaProjectContext(
        nordic_relevance="nordic_relevant_unmapped",
        nordic_relevance_reason=(
            "The ancient Svalbard reindeer comparator is a real Nordic lead, but it is "
            "still not promoted into shipped mapped animal locality outputs."
        ),
        last_checked_on=_LAST_CHECKED_ON,
    ),
    "SRS1407451": AdnaProjectContext(
        nordic_relevance="nordic_adjacent",
        nordic_relevance_reason=(
            "This ancient European dog sample informs North European context, but the "
            "current curation does not justify a Nordic-localized claim."
        ),
        last_checked_on=_LAST_CHECKED_ON,
    ),
    "SRS1407453": AdnaProjectContext(
        nordic_relevance="nordic_adjacent",
        nordic_relevance_reason=(
            "This ancient European dog sample informs North European context, but the "
            "current curation does not justify a Nordic-localized claim."
        ),
        last_checked_on=_LAST_CHECKED_ON,
    ),
    "KX379528-KX379529": AdnaProjectContext(
        nordic_relevance="nordic_adjacent",
        nordic_relevance_reason=(
            "These ancient dog mitogenomes are European comparative context rather than "
            "a Nordic-localized animal signal."
        ),
        last_checked_on=_LAST_CHECKED_ON,
    ),
    "PRJEB81815": AdnaProjectContext(
        nordic_relevance="nordic_adjacent",
        nordic_relevance_reason=(
            "The primary supplement resolves ancient and modern cat samples across "
            "Europe and adjacent regions, but it contains no Nordic sample and does "
            "not justify a Nordic-mapped claim."
        ),
        last_checked_on=_LAST_CHECKED_ON,
    ),
}


def resolve_project_context(project: AdnaArchiveProject) -> AdnaProjectContext:
    """Return the curated Nordic and freshness context for one archive project."""
    return _PROJECT_CONTEXT.get(
        project.project_accession,
        AdnaProjectContext(
            nordic_relevance="non_nordic",
            nordic_relevance_reason=(
                "The current curated project inventory does not yet identify a shipped "
                "Nordic-localized lead for this record."
            ),
            last_checked_on=_LAST_CHECKED_ON,
        ),
    )


def build_species_freshness_rows(
    projects: tuple[AdnaArchiveProject, ...],
) -> tuple[dict[str, object], ...]:
    """Aggregate one freshness row per species from the curated project context."""
    grouped: dict[str, list[AdnaArchiveProject]] = {}
    for project in projects:
        grouped.setdefault(project.species_latin_name, []).append(project)

    rows: list[dict[str, object]] = []
    for species_name, species_projects in sorted(grouped.items()):
        last_checked_on = max(
            resolve_project_context(project).last_checked_on
            for project in species_projects
        )
        rows.append(
            {
                "species_latin_name": species_name,
                "project_count": len(species_projects),
                "inventory_last_checked_on": last_checked_on,
                "paper_last_checked_on": last_checked_on,
                "has_nordic_unmapped_lead": any(
                    resolve_project_context(project).nordic_relevance
                    == "nordic_relevant_unmapped"
                    for project in species_projects
                ),
            }
        )
    return tuple(rows)
