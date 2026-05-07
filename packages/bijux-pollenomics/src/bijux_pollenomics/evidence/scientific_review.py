from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from ..adna import AdnaLocalitySummary, build_bovine_support_program
from ..data_downloader.models import ContextPointRecord
from .models import AtlasEvidenceSpeciesRow
from .surfaces import build_atlas_evidence_surface

__all__ = [
    "ChronologyOverlapRow",
    "EvidenceUncertaintyRow",
    "NordicScenarioAssessment",
    "ScientificReviewSurface",
    "SpeciesCountryCoverageRow",
    "SpeciesPeriodCoverageRow",
    "build_scientific_review_surface",
]

_PERIOD_BINS = (
    ("0-1000 BP", 0, 1000),
    ("1001-3000 BP", 1001, 3000),
    ("3001-6000 BP", 3001, 6000),
    ("6001+ BP", 6001, None),
)


@dataclass(frozen=True)
class SpeciesCountryCoverageRow:
    """Species-by-country coverage row that keeps unmapped animal context explicit."""

    country: str
    species_latin_name: str
    evidence_scope: str
    mapped_locality_count: int
    contextual_project_count: int
    assignment_confidence: str
    caution_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "country": self.country,
            "species_latin_name": self.species_latin_name,
            "evidence_scope": self.evidence_scope,
            "mapped_locality_count": self.mapped_locality_count,
            "contextual_project_count": self.contextual_project_count,
            "assignment_confidence": self.assignment_confidence,
            "caution_note": self.caution_note,
        }


@dataclass(frozen=True)
class SpeciesPeriodCoverageRow:
    """Species-by-period coverage row with explicit chronology honesty."""

    species_latin_name: str
    period_label: str
    evidence_scope: str
    mapped_locality_count: int
    contextual_project_count: int
    chronology_confidence: str
    caution_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "period_label": self.period_label,
            "evidence_scope": self.evidence_scope,
            "mapped_locality_count": self.mapped_locality_count,
            "contextual_project_count": self.contextual_project_count,
            "chronology_confidence": self.chronology_confidence,
            "caution_note": self.caution_note,
        }


@dataclass(frozen=True)
class ChronologyOverlapRow:
    """Comparison row between species evidence and contextual time windows."""

    species_latin_name: str
    context_layer_key: str
    overlap_status: str
    overlapping_direct_localities: int
    non_overlapping_direct_localities: int
    noncomparable_records: int
    rationale: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "context_layer_key": self.context_layer_key,
            "overlap_status": self.overlap_status,
            "overlapping_direct_localities": self.overlapping_direct_localities,
            "non_overlapping_direct_localities": self.non_overlapping_direct_localities,
            "noncomparable_records": self.noncomparable_records,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class EvidenceUncertaintyRow:
    """Explicit uncertainty row for species identity, locality, or chronology weakness."""

    subject: str
    uncertainty_kind: str
    severity: str
    reason: str
    impact: str

    def as_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "uncertainty_kind": self.uncertainty_kind,
            "severity": self.severity,
            "reason": self.reason,
            "impact": self.impact,
        }


@dataclass(frozen=True)
class NordicScenarioAssessment:
    """Assessment of one real Nordic farming-history scenario."""

    scenario_key: str
    question: str
    claim_scope: str
    usable_evidence: tuple[str, ...]
    blockers: tuple[str, ...]
    current_posture: str

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario_key": self.scenario_key,
            "question": self.question,
            "claim_scope": self.claim_scope,
            "usable_evidence": list(self.usable_evidence),
            "blockers": list(self.blockers),
            "current_posture": self.current_posture,
        }


@dataclass(frozen=True)
class ScientificReviewSurface:
    """Scientist-facing summary of what the platform can claim today."""

    schema_version: str
    descriptive_scope: tuple[str, ...]
    comparative_scope: tuple[str, ...]
    exploratory_scope: tuple[str, ...]
    country_coverage: tuple[SpeciesCountryCoverageRow, ...]
    period_coverage: tuple[SpeciesPeriodCoverageRow, ...]
    chronology_overlaps: tuple[ChronologyOverlapRow, ...]
    uncertainties: tuple[EvidenceUncertaintyRow, ...]
    scenarios: tuple[NordicScenarioAssessment, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "descriptive_scope": list(self.descriptive_scope),
            "comparative_scope": list(self.comparative_scope),
            "exploratory_scope": list(self.exploratory_scope),
            "country_coverage": [row.as_dict() for row in self.country_coverage],
            "period_coverage": [row.as_dict() for row in self.period_coverage],
            "chronology_overlaps": [row.as_dict() for row in self.chronology_overlaps],
            "uncertainties": [row.as_dict() for row in self.uncertainties],
            "scenarios": [row.as_dict() for row in self.scenarios],
        }


def build_scientific_review_surface(
    *,
    countries: tuple[str, ...],
    human_localities: Iterable[AdnaLocalitySummary],
    animal_localities: Iterable[AdnaLocalitySummary] = (),
    context_points: Iterable[ContextPointRecord],
) -> ScientificReviewSurface:
    """Build the scientific-review surface for one atlas run."""
    direct_localities = tuple(human_localities)
    mapped_animal_localities = tuple(animal_localities)
    context_records = tuple(context_points)
    evidence_surface = build_atlas_evidence_surface(
        countries=countries,
        human_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        context_points=context_records,
    )
    species_rows = evidence_surface.species_rows
    country_coverage = _build_country_coverage(
        countries=countries,
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        species_rows=species_rows,
    )
    period_coverage = _build_period_coverage(
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        species_rows=species_rows,
    )
    chronology_overlaps = _build_chronology_overlaps(
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        context_points=context_records,
        species_rows=species_rows,
    )
    uncertainties = _build_uncertainties(
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        species_rows=species_rows,
    )
    scenarios = _build_scenarios(
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        species_rows=species_rows,
        chronology_overlaps=chronology_overlaps,
    )
    return ScientificReviewSurface(
        schema_version="scientific-review-surface.v2",
        descriptive_scope=(
            "mapped Homo sapiens locality inventory",
            "mapped species-owned animal locality leads with explicit caveats",
            "country and period coverage with explicit animal precision caution",
        ),
        comparative_scope=(
            "cross-species heuristic ranking",
            "context-layer chronology comparison",
        ),
        exploratory_scope=(
            "non-human atlas interpretation",
            "scenario-level Nordic farming-history inference",
            "future lake-selection logic",
        ),
        country_coverage=country_coverage,
        period_coverage=period_coverage,
        chronology_overlaps=chronology_overlaps,
        uncertainties=uncertainties,
        scenarios=scenarios,
    )


def _build_country_coverage(
    *,
    countries: tuple[str, ...],
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[SpeciesCountryCoverageRow, ...]:
    rows: list[SpeciesCountryCoverageRow] = []
    for country in countries:
        country_direct = tuple(
            locality
            for locality in direct_localities
            if (locality.identity.political_entity or "").strip() == country
        )
        country_animal_localities = tuple(
            locality
            for locality in animal_localities
            if (locality.identity.political_entity or "").strip() == country
        )
        rows.append(
            SpeciesCountryCoverageRow(
                country=country,
                species_latin_name="Homo sapiens",
                evidence_scope="mapped_direct",
                mapped_locality_count=len(country_direct),
                contextual_project_count=0,
                assignment_confidence="country_filter_from_aadr_metadata",
                caution_note="Human country assignment is metadata-derived and remains separate from non-human context.",
            )
        )
        for row in species_rows:
            if row.species_latin_name == "Homo sapiens":
                continue
            species_country_localities = tuple(
                locality
                for locality in country_animal_localities
                if locality.species_latin_name == row.species_latin_name
            )
            rows.append(
                SpeciesCountryCoverageRow(
                    country=country,
                    species_latin_name=row.species_latin_name,
                    evidence_scope=(
                        "mapped_direct"
                        if species_country_localities
                        else row.contribution_role
                    ),
                    mapped_locality_count=len(species_country_localities),
                    contextual_project_count=row.curated_project_count,
                    assignment_confidence=(
                        "country_resolved_from_mapped_locality_rows"
                        if species_country_localities
                        else "not_country_assignable_from_current_runtime"
                    ),
                    caution_note=(
                        "Mapped animal locality rows remain cautionary leads and can still be approximate, regional, or comparator-only."
                        if species_country_localities
                        else "Current non-human support is species-level review context, not country-resolved locality evidence."
                    ),
                )
            )
    return tuple(rows)


def _build_period_coverage(
    *,
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[SpeciesPeriodCoverageRow, ...]:
    rows: list[SpeciesPeriodCoverageRow] = []
    grouped: dict[str, list[AdnaLocalitySummary]] = defaultdict(list)
    for locality in direct_localities:
        grouped[_period_label_for(locality)].append(locality)
    for label, _, _ in _PERIOD_BINS:
        rows.append(
            SpeciesPeriodCoverageRow(
                species_latin_name="Homo sapiens",
                period_label=label,
                evidence_scope="mapped_direct",
                mapped_locality_count=len(grouped.get(label, [])),
                contextual_project_count=0,
                chronology_confidence="locality_level_bp_window",
                caution_note="Human period coverage remains locality-based metadata, not genotype-aware chronology.",
            )
        )
    for row in species_rows:
        if row.species_latin_name == "Homo sapiens":
            continue
        species_animal_localities = tuple(
            locality
            for locality in animal_localities
            if locality.species_latin_name == row.species_latin_name
        )
        if species_animal_localities:
            grouped_animal: dict[str, list[AdnaLocalitySummary]] = defaultdict(list)
            for locality in species_animal_localities:
                grouped_animal[_period_label_for(locality)].append(locality)
            for period_label in sorted(grouped_animal):
                rows.append(
                    SpeciesPeriodCoverageRow(
                        species_latin_name=row.species_latin_name,
                        period_label=period_label,
                        evidence_scope="mapped_direct",
                        mapped_locality_count=len(grouped_animal[period_label]),
                        contextual_project_count=row.curated_project_count,
                        chronology_confidence=row.chronology_posture,
                        caution_note="Mapped animal chronology remains bounded by locality-lead precision and support-class caveats.",
                    )
                )
            continue
        rows.append(
            SpeciesPeriodCoverageRow(
                species_latin_name=row.species_latin_name,
                period_label="project_level_or_unresolved",
                evidence_scope=row.contribution_role,
                mapped_locality_count=0,
                contextual_project_count=row.curated_project_count,
                chronology_confidence=row.chronology_posture,
                caution_note="Non-human chronology is not yet resolved to mapped locality periods.",
            )
        )
    return tuple(rows)


def _build_chronology_overlaps(
    *,
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    context_points: tuple[ContextPointRecord, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[ChronologyOverlapRow, ...]:
    rows: list[ChronologyOverlapRow] = []
    grouped_context: dict[str, list[ContextPointRecord]] = defaultdict(list)
    for point in context_points:
        grouped_context[point.layer_key].append(point)
    for layer_key, points in sorted(grouped_context.items()):
        overlapping = 0
        non_overlapping = 0
        noncomparable = 0
        for locality in direct_localities:
            if locality.time_start_bp is None or locality.time_end_bp is None:
                noncomparable += 1
                continue
            if any(_locality_overlaps_point(locality, point) for point in points):
                overlapping += 1
            else:
                non_overlapping += 1
        rows.append(
            ChronologyOverlapRow(
                species_latin_name="Homo sapiens",
                context_layer_key=layer_key,
                overlap_status="locality_level_overlap_available",
                overlapping_direct_localities=overlapping,
                non_overlapping_direct_localities=non_overlapping,
                noncomparable_records=noncomparable,
                rationale="Human locality chronology can be compared directly with time-aware context points.",
            )
        )
    for row in species_rows:
        if row.species_latin_name == "Homo sapiens":
            continue
        species_animal_localities = tuple(
            locality
            for locality in animal_localities
            if locality.species_latin_name == row.species_latin_name
        )
        for layer_key in sorted(grouped_context) or ("no_context_layers",):
            if species_animal_localities and layer_key != "no_context_layers":
                overlapping = 0
                non_overlapping = 0
                noncomparable = 0
                layer_points = grouped_context.get(layer_key, [])
                for locality in species_animal_localities:
                    if locality.time_start_bp is None or locality.time_end_bp is None:
                        noncomparable += 1
                        continue
                    if any(_locality_overlaps_point(locality, point) for point in layer_points):
                        overlapping += 1
                    else:
                        non_overlapping += 1
                rows.append(
                    ChronologyOverlapRow(
                        species_latin_name=row.species_latin_name,
                        context_layer_key=layer_key,
                        overlap_status="mapped_locality_overlap_with_caution",
                        overlapping_direct_localities=overlapping,
                        non_overlapping_direct_localities=non_overlapping,
                        noncomparable_records=noncomparable,
                        rationale="Mapped animal locality leads can be compared with context layers, but only with their stated chronology and precision caveats.",
                    )
                )
                continue
            rows.append(
                ChronologyOverlapRow(
                    species_latin_name=row.species_latin_name,
                    context_layer_key=layer_key,
                    overlap_status="not_comparable_project_level_only",
                    overlapping_direct_localities=0,
                    non_overlapping_direct_localities=0,
                    noncomparable_records=max(1, row.curated_project_count),
                    rationale="Non-human chronology is still project-level and cannot be aligned to atlas localities honestly.",
                )
            )
    return tuple(rows)


def _build_uncertainties(
    *,
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[EvidenceUncertaintyRow, ...]:
    rows: list[EvidenceUncertaintyRow] = []
    for row in species_rows:
        if row.species_latin_name != "Homo sapiens":
            species_animal_localities = tuple(
                locality
                for locality in animal_localities
                if locality.species_latin_name == row.species_latin_name
            )
            rows.append(
                EvidenceUncertaintyRow(
                    subject=row.species_latin_name,
                    uncertainty_kind="species_assignment",
                    severity="high" if "mixed_species_rule_unresolved" in row.blocking_reasons else "medium",
                    reason="nonhuman support remains species-review context or mixed-species blocked",
                    impact="cross-species comparisons cannot be promoted to locality-level inference safely",
                )
            )
            rows.append(
                EvidenceUncertaintyRow(
                    subject=row.species_latin_name,
                    uncertainty_kind="locality_precision",
                    severity=(
                        "medium"
                        if species_animal_localities
                        else "high"
                    ),
                    reason=row.geography_posture,
                    impact=(
                        "mapped animal atlas points remain useful but must keep their coordinate and regional caveats visible"
                        if species_animal_localities
                        else "country or atlas placement for animal evidence would overstate runtime geography support"
                    ),
                )
            )
            rows.append(
                EvidenceUncertaintyRow(
                    subject=row.species_latin_name,
                    uncertainty_kind="date_precision",
                    severity="medium",
                    reason=row.chronology_posture,
                    impact=(
                        "mapped animal localities support chronology comparison only within the explicit BP and caveat bounds"
                        if species_animal_localities
                        else "animal evidence cannot yet support locality-aligned chronology claims"
                    ),
                )
            )
    if any(locality.coordinate_confidence != "exact" for locality in direct_localities):
        rows.append(
            EvidenceUncertaintyRow(
                subject="Homo sapiens",
                uncertainty_kind="locality_precision",
                severity="low",
                reason="some mapped human localities rely on approximate or inferred coordinates",
                impact="descriptive maps remain valid but should not be treated as exact site centroids automatically",
            )
        )
    return tuple(rows)


def _build_scenarios(
    *,
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
    chronology_overlaps: tuple[ChronologyOverlapRow, ...],
) -> tuple[NordicScenarioAssessment, ...]:
    animal_context_species = tuple(
        row.species_latin_name
        for row in species_rows
        if row.species_latin_name != "Homo sapiens" and row.contribution_role == "contextual"
    )
    mapped_animal_species = tuple(
        sorted({locality.species_latin_name for locality in animal_localities})
    )
    has_human_direct = bool(direct_localities)
    has_human_overlap = any(
        row.species_latin_name == "Homo sapiens"
        and row.overlapping_direct_localities > 0
        for row in chronology_overlaps
    )
    bovine_program = build_bovine_support_program()
    return (
        NordicScenarioAssessment(
            scenario_key="nordic_farming_arrival",
            question="Can the platform compare early human presence with domesticated-animal context and landscape change in one honest review surface?",
            claim_scope="exploratory",
            usable_evidence=(
                "mapped_homo_sapiens_localities" if has_human_direct else "no_human_direct_localities",
                *(mapped_animal_species or animal_context_species or ("no_contextual_animal_species",)),
            ),
            blockers=(
                "animal_evidence_mapped_with_precision_caveats",
                "nonhuman_chronology_not_uniformly_country_resolved",
            ),
            current_posture="exploratory_only",
        ),
        NordicScenarioAssessment(
            scenario_key="pastoral_species_turnover",
            question="Can the platform compare animal-management turnover signals across species without flattening their support classes?",
            claim_scope="comparative",
            usable_evidence=mapped_animal_species or animal_context_species or ("no_contextual_animal_species",),
            blockers=("species_support_asymmetry", "mapped_animal_precision_caveats"),
            current_posture="comparative_with_locality_caveats",
        ),
        NordicScenarioAssessment(
            scenario_key="cattle_management_split",
            question="Can the platform distinguish taurine and indicine cattle support without collapsing them into one cattle story?",
            claim_scope="descriptive",
            usable_evidence=("bovine_support_program",),
            blockers=bovine_program.combined_claim_rule.currently_blocked_by,
            current_posture="descriptive_only",
        ),
        NordicScenarioAssessment(
            scenario_key="lake_selection_for_domestication_signal",
            question="Can the platform recommend lake targets for domestication-focused fieldwork today?",
            claim_scope="exploratory",
            usable_evidence=(
                "human_context_overlap" if has_human_overlap else "limited_human_context_overlap",
            ),
            blockers=(
                "field_sampling_gate_not_cleared",
                "animal_evidence_not_yet_dense_enough_for_fieldwork_recommendation",
            ),
            current_posture="exploratory_only",
        ),
    )


def _period_label_for(locality: AdnaLocalitySummary) -> str:
    mean_bp = locality.time_mean_bp
    if mean_bp is None:
        return "project_level_or_unresolved"
    for label, start, end in _PERIOD_BINS:
        if end is None and mean_bp >= start:
            return label
        if end is not None and start <= mean_bp <= end:
            return label
    return "project_level_or_unresolved"


def _locality_overlaps_point(
    locality: AdnaLocalitySummary,
    point: ContextPointRecord,
) -> bool:
    if locality.time_start_bp is None or locality.time_end_bp is None:
        return False
    if point.time_start_bp is None or point.time_end_bp is None:
        return False
    return not (
        point.time_end_bp < locality.time_start_bp
        or point.time_start_bp > locality.time_end_bp
    )
