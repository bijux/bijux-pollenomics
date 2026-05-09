from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ..species.definitions import resolve_species_definition

__all__ = [
    "ADNA_ACCESSION_SCOPES",
    "ADNA_ACCESS_POLICIES",
    "ADNA_DOMESTICATION_SCOPES",
    "ADNA_ENA_RESULT_KINDS",
    "ADNA_PROJECT_EVIDENCE_STRENGTHS",
    "AdnaArchiveProject",
    "AdnaEnaQuery",
    "AdnaEnaRecord",
    "AdnaPaperLinkage",
    "build_archive_project_catalog",
    "build_ena_filereport_url",
    "build_species_archive_projects",
    "classify_archive_project_evidence",
    "parse_ena_filereport_tsv",
]

ADNA_ACCESSION_SCOPES: Final[tuple[str, ...]] = (
    "project",
    "sample",
    "accession_range",
)
ADNA_ACCESS_POLICIES: Final[tuple[str, ...]] = (
    "public_downloadable",
    "embargoed_until_release_date",
    "restricted_access",
    "delayed_release_unverified",
)
ADNA_DOMESTICATION_SCOPES: Final[tuple[str, ...]] = (
    "domesticated_core",
    "wild_or_progenitor_context",
    "ancient_comparator",
    "modern_or_irrelevant",
)
ADNA_ENA_RESULT_KINDS: Final[tuple[str, ...]] = ("read_run", "analysis")
ADNA_PROJECT_EVIDENCE_STRENGTHS: Final[tuple[str, ...]] = (
    "primary_paper_pinned",
    "archive_only",
    "paper_only",
    "secondary_reference_only",
    "manual_note_only",
)
_ENA_API_BASE = "https://www.ebi.ac.uk/ena/portal/api/filereport"


@dataclass(frozen=True)
class AdnaEnaQuery:
    """Typed ENA selector contract for species-aware ancient-DNA metadata fetches."""

    projects: tuple[str, ...]
    samples: tuple[str, ...]
    extra_accessions: tuple[str, ...]
    result_kind: str = "read_run"

    def normalized_accessions(self) -> tuple[str, ...]:
        normalized = {
            *_normalize_values(self.projects),
            *_normalize_values(self.samples),
            *_normalize_values(self.extra_accessions),
        }
        return tuple(sorted(normalized))

    def validate(self) -> None:
        if self.result_kind not in ADNA_ENA_RESULT_KINDS:
            raise ValueError(f"Unsupported ENA result kind: {self.result_kind}")
        accessions = self.normalized_accessions()
        if not accessions:
            raise ValueError(
                "Provide at least one ENA project, sample, or accession selector"
            )
        for accession in accessions:
            if not _valid_selector(accession):
                raise ValueError(f"Invalid ENA selector: {accession}")

    def sample_allowed(self, sample_accession: str) -> bool:
        sample_filter = set(_normalize_values(self.samples))
        if not sample_filter:
            return True
        return sample_accession in sample_filter


@dataclass(frozen=True)
class AdnaEnaRecord:
    """Decoded ENA filereport row for ancient-DNA archive intake review."""

    study_accession: str | None
    sample_accession: str | None
    experiment_accession: str | None
    run_accession: str | None
    analysis_accession: str | None
    analysis_type: str | None
    tax_id: str | None
    scientific_name: str | None
    library_layout: str | None
    library_source: str | None
    library_strategy: str | None
    instrument_model: str | None
    base_count: int | None
    read_count: int | None
    fastq_bytes: tuple[int, ...]
    fastq_ftp: tuple[str, ...]
    submitted_ftp: tuple[str, ...]
    sra_ftp: tuple[str, ...]
    bam_ftp: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "study_accession": self.study_accession,
            "sample_accession": self.sample_accession,
            "experiment_accession": self.experiment_accession,
            "run_accession": self.run_accession,
            "analysis_accession": self.analysis_accession,
            "analysis_type": self.analysis_type,
            "tax_id": self.tax_id,
            "scientific_name": self.scientific_name,
            "library_layout": self.library_layout,
            "library_source": self.library_source,
            "library_strategy": self.library_strategy,
            "instrument_model": self.instrument_model,
            "base_count": self.base_count,
            "read_count": self.read_count,
            "fastq_bytes": list(self.fastq_bytes),
            "fastq_ftp": list(self.fastq_ftp),
            "submitted_ftp": list(self.submitted_ftp),
            "sra_ftp": list(self.sra_ftp),
            "bam_ftp": list(self.bam_ftp),
        }


@dataclass(frozen=True)
class AdnaPaperLinkage:
    """Primary or secondary literature anchor for one curated ancient-DNA archive row."""

    paper_title: str
    doi: str | None = None
    pubmed_id: str | None = None
    pmc_id: str | None = None
    journal_title: str | None = None
    publication_year: int | None = None
    reference_kind: str = "primary_paper"
    pinning_evidence: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "paper_title": self.paper_title,
            "doi": self.doi,
            "pubmed_id": self.pubmed_id,
            "pmc_id": self.pmc_id,
            "journal_title": self.journal_title,
            "publication_year": self.publication_year,
            "reference_kind": self.reference_kind,
            "pinning_evidence": self.pinning_evidence,
        }


@dataclass(frozen=True)
class AdnaArchiveProject:
    """Species-aware archive project catalog entry for domesticated-animal aDNA."""

    species_latin_name: str
    project_accession: str
    result_kind: str
    metadata_url: str
    source_family: str
    accession_scope: str
    archive_status: str
    notes: str
    paper_linkage: AdnaPaperLinkage | None = None
    ancient_status: str = "archive_unreviewed"
    sequencing_target: str | None = None
    material_basis: str | None = None
    dating_basis: str | None = None
    geographic_basis: str | None = None
    access_policy: str = "public_downloadable"
    public_release_date: str | None = None
    domestication_scope: str = "domesticated_core"

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "project_accession": self.project_accession,
            "result_kind": self.result_kind,
            "metadata_url": self.metadata_url,
            "source_family": self.source_family,
            "accession_scope": self.accession_scope,
            "archive_status": self.archive_status,
            "notes": self.notes,
            "paper_linkage": None
            if self.paper_linkage is None
            else self.paper_linkage.as_dict(),
            "ancient_status": self.ancient_status,
            "sequencing_target": self.sequencing_target,
            "material_basis": self.material_basis,
            "dating_basis": self.dating_basis,
            "geographic_basis": self.geographic_basis,
            "access_policy": self.access_policy,
            "public_release_date": self.public_release_date,
            "domestication_scope": self.domestication_scope,
            "evidence_strength": classify_archive_project_evidence(self),
        }


def classify_archive_project_evidence(project: AdnaArchiveProject) -> str:
    """Classify how strongly one archive row is pinned to real scientific evidence."""
    has_archive = bool(project.metadata_url)
    linkage = project.paper_linkage
    if linkage is None:
        if has_archive:
            return "archive_only"
        return "manual_note_only"
    if linkage.reference_kind == "secondary_reference":
        return "secondary_reference_only"
    if has_archive:
        return "primary_paper_pinned"
    return "paper_only"


def build_ena_filereport_url(accession: str, result_kind: str = "read_run") -> str:
    """Build the canonical ENA filereport URL for one accession."""
    if result_kind not in ADNA_ENA_RESULT_KINDS:
        raise ValueError(f"Unsupported ENA result kind: {result_kind}")
    fields = ",".join(_filereport_fields(result_kind))
    return (
        f"{_ENA_API_BASE}?accession={accession}&result={result_kind}&fields={fields}"
        "&format=tsv&download=true&limit=0"
    )


def parse_ena_filereport_tsv(
    tsv: str,
    query: AdnaEnaQuery,
) -> tuple[AdnaEnaRecord, ...]:
    """Decode an ENA filereport TSV payload into typed records."""
    query.validate()
    lines = tsv.splitlines()
    if not lines:
        raise ValueError("ENA filereport response is empty")
    headers = lines[0].split("\t")
    _validate_headers(headers, query.result_kind)

    rows: list[AdnaEnaRecord] = []
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        values = line.split("\t")
        if len(values) != len(headers):
            raise ValueError(
                f"ENA filereport row {line_number} has {len(values)} columns, expected {len(headers)}"
            )
        row = dict(zip(headers, values, strict=True))
        sample_accession = _opt_field(row.get("sample_accession", ""))
        if sample_accession is not None and not query.sample_allowed(sample_accession):
            continue
        rows.append(
            AdnaEnaRecord(
                study_accession=_opt_field(row.get("study_accession", "")),
                sample_accession=sample_accession,
                experiment_accession=_opt_field(row.get("experiment_accession", "")),
                run_accession=_opt_field(row.get("run_accession", "")),
                analysis_accession=_opt_field(row.get("analysis_accession", "")),
                analysis_type=_opt_field(row.get("analysis_type", "")),
                tax_id=_opt_field(row.get("tax_id", "")),
                scientific_name=_opt_field(row.get("scientific_name", "")),
                library_layout=_opt_field(row.get("library_layout", "")),
                library_source=_opt_field(row.get("library_source", "")),
                library_strategy=_opt_field(row.get("library_strategy", "")),
                instrument_model=_opt_field(row.get("instrument_model", "")),
                base_count=_parse_optional_int(
                    row.get("base_count", ""), "base_count", line_number
                ),
                read_count=_parse_optional_int(
                    row.get("read_count", ""), "read_count", line_number
                ),
                fastq_bytes=_parse_int_list(
                    row.get("fastq_bytes", ""), "fastq_bytes", line_number
                ),
                fastq_ftp=_split_field(row.get("fastq_ftp", "")),
                submitted_ftp=_split_field(row.get("submitted_ftp", "")),
                sra_ftp=_split_field(row.get("sra_ftp", "")),
                bam_ftp=_split_field(row.get("bam_ftp", "")),
            )
        )
    return tuple(rows)


def build_archive_project_catalog() -> tuple[AdnaArchiveProject, ...]:
    """Return the curated archive project inventory for domesticated-animal aDNA intake."""
    return (
        _project(
            "Equus caballus",
            "PRJEB22390",
            archive_status="paper_pinned_core",
            notes="Botai and Przewalski/domestic ancestry anchor.",
            paper_linkage=_paper(
                paper_title="Ancient genomes revisit the ancestry of domestic and Przewalski's horses",
                doi="10.1126/science.aao3297",
                pubmed_id="29472442",
                journal_title="Science",
                publication_year=2018,
                pinning_evidence="Primary paper and PubMed record explicitly anchor PRJEB22390 to the horse ancestry study.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus caballus",
            "PRJEB44430",
            archive_status="paper_pinned_core",
            notes="Major horse domestication-and-dispersal anchor.",
            paper_linkage=_paper(
                paper_title="The origins and spread of domestic horses from the Western Eurasian steppes",
                doi="10.1038/s41586-021-04018-9",
                journal_title="Nature",
                publication_year=2021,
                pinning_evidence="Primary paper data-availability material anchors the ENA project to the domestication study.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus caballus",
            "PRJEB31613",
            archive_status="paper_pinned_core",
            notes="Extensive horse management time series.",
            paper_linkage=_paper(
                paper_title="Tracking Five Millennia of Horse Management with Extensive Ancient Genome Time Series",
                doi="10.1016/j.cell.2019.03.049",
                pmc_id="PMC6547883",
                journal_title="Cell",
                publication_year=2019,
                pinning_evidence="Primary paper and PMC record explicitly connect the project to ancient horse management genomes.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus caballus",
            "PRJEB19970",
            archive_status="paper_pinned_core",
            notes="Early domestic horses and domestication-associated genomic change.",
            paper_linkage=_paper(
                paper_title="Ancient genomic changes associated with domestication of the horse",
                doi="10.1126/science.aam5298",
                pubmed_id="28450643",
                journal_title="Science",
                publication_year=2017,
                pinning_evidence="Primary paper and PubMed record explicitly anchor PRJEB19970 to early domestic horse genomes.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus caballus",
            "PRJEB56293",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Ancient horse project, but currently phenotype-method oriented and not yet core-pinned.",
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus caballus",
            "PRJEB7537",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Archive-backed horse dataset kept provisional until explicit primary-paper linkage is recorded.",
            ancient_status="ancient_unverified",
            sequencing_target="unknown_or_mixed",
            material_basis="not_yet_curated",
            dating_basis="not_yet_curated",
            geographic_basis="not_yet_curated",
        ),
        _project(
            "Equus caballus",
            "PRJEB10854",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Archive-backed horse dataset kept provisional until explicit primary-paper linkage is recorded.",
            ancient_status="ancient_unverified",
            sequencing_target="unknown_or_mixed",
            material_basis="not_yet_curated",
            dating_basis="not_yet_curated",
            geographic_basis="not_yet_curated",
        ),
        _project(
            "Equus caballus",
            "PRJEB9799",
            archive_status="reject_or_out_of_scope",
            notes="Modern horse breed genomics from the source note set; not ancient domestication support.",
            ancient_status="modern_or_irrelevant",
            sequencing_target="shotgun_genome",
            material_basis="modern_tissue",
            dating_basis="modern_sampling",
            geographic_basis="country_or_breed_panel",
        ),
        _project(
            "Ovis aries",
            "PRJEB36540",
            archive_status="paper_pinned_core",
            notes="Early Anatolian sheep domestication-demography anchor.",
            paper_linkage=_paper(
                paper_title="Archaeogenetic analysis of Neolithic sheep from Anatolia suggests a complex demographic history since domestication",
                doi="10.1038/s42003-021-02794-8",
                journal_title="Communications Biology",
                publication_year=2021,
                pinning_evidence="Primary paper anchors PRJEB36540 to the Neolithic sheep dataset.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Ovis aries",
            "PRJEB41594",
            archive_status="paper_pinned_core",
            notes="Central Asian sheep dispersal anchor.",
            paper_linkage=_paper(
                paper_title="Evidence for early dispersal of domestic sheep into Central Asia",
                doi="10.1038/s41562-021-01083-y",
                journal_title="Nature Human Behaviour",
                publication_year=2021,
                pinning_evidence="Primary paper anchors PRJEB41594 to the early domestic sheep dispersal study.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Ovis aries",
            "PRJEB59481",
            archive_status="paper_pinned_core",
            notes="Baltic ancient sheep genomes across four millennia.",
            paper_linkage=_paper(
                paper_title="Ancient Sheep Genomes Reveal Four Millennia of North European Short-Tailed Sheep in the Baltic Sea Region",
                doi="10.1093/gbe/evae114",
                pmc_id="PMC11162877",
                journal_title="Genome Biology and Evolution",
                publication_year=2024,
                pinning_evidence="Primary paper explicitly names PRJEB59481 in the data availability statement.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Ovis aries",
            "PRJEB61808",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Archive-backed sheep dataset awaiting explicit primary-paper pinning.",
            ancient_status="ancient_unverified",
            sequencing_target="unknown_or_mixed",
            material_basis="not_yet_curated",
            dating_basis="not_yet_curated",
            geographic_basis="not_yet_curated",
        ),
        _project(
            "Ovis aries",
            "PRJEB69690",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Archive-backed sheep dataset awaiting explicit primary-paper pinning.",
            ancient_status="ancient_unverified",
            sequencing_target="unknown_or_mixed",
            material_basis="not_yet_curated",
            dating_basis="not_yet_curated",
            geographic_basis="not_yet_curated",
        ),
        _project(
            "Ovis aries",
            "PRJEB81145",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Archive-backed sheep dataset awaiting explicit primary-paper pinning.",
            ancient_status="ancient_unverified",
            sequencing_target="unknown_or_mixed",
            material_basis="not_yet_curated",
            dating_basis="not_yet_curated",
            geographic_basis="not_yet_curated",
        ),
        _project(
            "Sus scrofa domesticus",
            "PRJEB30282",
            archive_status="paper_pinned_core",
            notes="Ancient pig genomic turnover anchor after introduction to Europe.",
            paper_linkage=_paper(
                paper_title="Ancient pigs reveal a near-complete genomic turnover following their introduction to Europe",
                doi="10.1073/pnas.1901169116",
                pmc_id="PMC6717267",
                journal_title="Proceedings of the National Academy of Sciences",
                publication_year=2019,
                pinning_evidence="Primary paper and PMC record explicitly anchor PRJEB30282 to the ancient pig turnover dataset.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Sus scrofa domesticus",
            "PRJNA788987",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Ancient Chinese pig genomes remain archive-verified until paper linkage is recorded in code.",
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="archaeological_period_assignment",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Sus scrofa domesticus",
            "PRJNA878488",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Ancient Polynesian pig genomes remain archive-verified until paper linkage is recorded in code.",
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="archaeological_period_assignment",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Sus scrofa domesticus",
            "PRJNA421430",
            archive_status="reject_or_out_of_scope",
            notes="Method and modern tissue context from the source note set; not curated ancient pig support.",
            ancient_status="modern_or_irrelevant",
            sequencing_target="capture_or_method_panel",
            material_basis="modern_tissue",
            dating_basis="modern_sampling",
            geographic_basis="country_or_breed_panel",
        ),
        _project(
            "Bos taurus",
            "PRJEB31621",
            archive_status="paper_pinned_core",
            notes="Near East cattle origins and turnover anchor.",
            paper_linkage=_paper(
                paper_title="Ancient cattle genomics, origins, and rapid turnover in the Fertile Crescent",
                doi="10.1126/science.aav1002",
                pubmed_id="31296769",
                journal_title="Science",
                publication_year=2019,
                pinning_evidence="Primary paper and PubMed record explicitly anchor PRJEB31621 to ancient cattle genomes.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Bos taurus",
            "PRJEB75467",
            archive_status="paper_pinned_core",
            notes="Aurochs genomic natural-history context for cattle domestication.",
            paper_linkage=_paper(
                paper_title="The genomic natural history of the aurochs",
                doi="10.1038/s41586-024-08112-6",
                journal_title="Nature",
                publication_year=2024,
                pinning_evidence="Primary paper anchors PRJEB75467 to the aurochs reference framework.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
            domestication_scope="wild_or_progenitor_context",
        ),
        _project(
            "Bos taurus",
            "PRJNA705960",
            archive_status="archive_verified_needs_paper_pinning",
            notes="Ancient Galician cattle mtDNA dataset kept archive-verified until explicit primary-paper linkage is encoded.",
            ancient_status="ancient_confirmed",
            sequencing_target="mitogenome",
            material_basis="individual_bone_or_tooth",
            dating_basis="archaeological_period_assignment",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Capra hircus",
            "PRJEB90141",
            archive_status="paper_pinned_core",
            notes="Ancient goat demographic-history anchor from genome imputation study.",
            paper_linkage=_paper(
                paper_title="Inferring Domestic Goat Demographic History Through Ancient Genome Imputation",
                doi="10.1093/gbe/evaf181",
                pmc_id="PMC12598287",
                journal_title="Genome Biology and Evolution",
                publication_year=2025,
                pinning_evidence="Primary paper and PMC record explicitly anchor PRJEB90141 to the ancient goat study.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
            public_release_date="2025-12-31",
        ),
        _project(
            "Capra hircus",
            "PRJEB90261",
            archive_status="paper_pinned_core",
            notes="Canary Islands goat temporal continuity anchor.",
            paper_linkage=_paper(
                paper_title="Paleogenomic evidence on the temporal continuity of indigenous goat exploitation in the Canary Islands",
                doi="10.1016/j.isci.2025.113771",
                pmc_id="PMC12629918",
                journal_title="iScience",
                publication_year=2025,
                pinning_evidence="Primary paper and PMC record explicitly anchor PRJEB90261 to the Canary Islands goat dataset.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="historical_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Capra hircus",
            "PRJNA1328209",
            archive_status="paper_pinned_core",
            notes="Qinghai-Xizang Plateau goat population-history anchor.",
            paper_linkage=_paper(
                paper_title="Ancient genomes reveal the genetic history of domestic goats on the Qinghai-Xizang Plateau approximately 3,600 years ago",
                doi="10.24272/j.issn.2095-8137.2025.080",
                pubmed_id="41983443",
                journal_title="Zoological Research",
                publication_year=2025,
                pinning_evidence="Primary paper and PubMed record explicitly anchor PRJNA1328209 to the goat dataset.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="archaeological_period_assignment",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Felis catus",
            "PRJEB81815",
            archive_status="paper_pinned_core",
            notes="Domestic cat dispersal from North Africa to Europe.",
            paper_linkage=_paper(
                paper_title="The dispersal of domestic cats from North Africa to Europe around 2000 years ago",
                doi="10.1126/science.adt2642",
                pmc_id="PMC7618505",
                journal_title="Science",
                publication_year=2024,
                pinning_evidence="Primary paper explicitly names PRJEB81815 in data availability.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="historical_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Felis catus",
            "PRJNA1178732",
            source_family="BioProject",
            archive_status="paper_pinned_core",
            notes="Late-arrival domestic cat dataset for China via Silk Road context.",
            paper_linkage=_paper(
                paper_title="The late arrival of domestic cats in China via the Silk Road after 3,500 years of human-leopard cat commensalism",
                doi="10.1016/j.xgen.2025.101099",
                pmc_id="PMC12926185",
                journal_title="Cell Genomics",
                publication_year=2025,
                pinning_evidence="Primary paper explicitly names PRJNA1178732 for newly generated FASTQ data.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="historical_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Canis lupus familiaris",
            "SRS1407451",
            source_family="SRA",
            accession_scope="sample",
            archive_status="paper_pinned_core",
            notes="Ancient dog CTC sample explicitly named on the primary paper page.",
            paper_linkage=_paper(
                paper_title="Ancient European dog genomes reveal continuity since the Early Neolithic",
                doi="10.1038/ncomms16082",
                pmc_id="PMC5520058",
                journal_title="Nature Communications",
                publication_year=2017,
                pinning_evidence="Primary paper data-availability section explicitly names sample-level SRA accession SRS1407451 for ancient dog CTC.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Canis lupus familiaris",
            "SRS1407453",
            source_family="SRA",
            accession_scope="sample",
            archive_status="paper_pinned_core",
            notes="Ancient dog HXH sample explicitly named on the primary paper page.",
            paper_linkage=_paper(
                paper_title="Ancient European dog genomes reveal continuity since the Early Neolithic",
                doi="10.1038/ncomms16082",
                pmc_id="PMC5520058",
                journal_title="Nature Communications",
                publication_year=2017,
                pinning_evidence="Primary paper data-availability section explicitly names sample-level SRA accession SRS1407453 for ancient dog HXH.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Canis lupus familiaris",
            "KX379528-KX379529",
            source_family="GenBank",
            accession_scope="accession_range",
            archive_status="paper_pinned_core",
            notes="Ancient dog mitochondrial genomes named on the primary paper page.",
            paper_linkage=_paper(
                paper_title="Ancient European dog genomes reveal continuity since the Early Neolithic",
                doi="10.1038/ncomms16082",
                pmc_id="PMC5520058",
                journal_title="Nature Communications",
                publication_year=2017,
                pinning_evidence="Primary paper data-availability section explicitly names mitochondrial genome accessions KX379528-KX379529.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="mitogenome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Camelus dromedarius",
            "SRP073444",
            source_family="SRA",
            archive_status="paper_pinned_core",
            notes="Domestic-dromedary anchor. Comparator camelid evidence does not extend support to other camelid species automatically.",
            paper_linkage=_paper(
                paper_title="Combined hybridization capture and shotgun sequencing for ancient DNA analysis of extinct wild and domestic dromedary camel",
                doi="10.1111/1755-0998.12551",
                pmc_id="PMC5324683",
                journal_title="Molecular Ecology Resources",
                publication_year=2017,
                pinning_evidence="Primary paper explicitly names SRA project SRP073444 for the dromedary study and distinguishes domestic-dromedary material from wider camelid context.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="capture_and_shotgun",
            material_basis="individual_bone_or_tooth",
            dating_basis="historical_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Camelus dromedarius",
            "KU605068-KU605080",
            source_family="GenBank",
            accession_scope="accession_range",
            archive_status="paper_pinned_core",
            notes="Dromedary mitogenome range named on the primary paper page. It supports Camelus dromedarius only, not other camelids.",
            paper_linkage=_paper(
                paper_title="Combined hybridization capture and shotgun sequencing for ancient DNA analysis of extinct wild and domestic dromedary camel",
                doi="10.1111/1755-0998.12551",
                pmc_id="PMC5324683",
                journal_title="Molecular Ecology Resources",
                publication_year=2017,
                pinning_evidence="Primary paper explicitly names mitochondrial genome accession range KU605068-KU605080 for the dromedary study.",
            ),
            ancient_status="ancient_confirmed",
            sequencing_target="mitogenome",
            material_basis="individual_bone_or_tooth",
            dating_basis="historical_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus asinus",
            "PRJEB50952",
            archive_status="comparator_only",
            notes="Ancient donkey comparator project kept separate from horse support.",
            ancient_status="ancient_comparator",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus asinus",
            "PRJEB52849",
            archive_status="comparator_only",
            notes="Ancient donkey comparator project kept separate from horse support.",
            ancient_status="ancient_comparator",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="archaeological_period_assignment",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus asinus",
            "PRJEB52590",
            archive_status="comparator_only",
            notes="Ancient donkey comparator project kept separate from horse support.",
            ancient_status="ancient_comparator",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="archaeological_period_assignment",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus asinus",
            "PRJEB43564",
            archive_status="comparator_only",
            notes="Ancient donkey comparator project kept separate from horse support.",
            ancient_status="ancient_comparator",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="archaeological_period_assignment",
            geographic_basis="site_level_localities",
        ),
        _project(
            "Equus asinus",
            "PRJEB55549",
            archive_status="reject_or_out_of_scope",
            result_kind="analysis",
            notes="Analysis-level donkey entry; not promoted into direct curated support.",
            ancient_status="archive_unreviewed",
            sequencing_target="analysis_only",
            material_basis="not_yet_curated",
            dating_basis="not_yet_curated",
            geographic_basis="not_yet_curated",
        ),
        _project(
            "Rangifer tarandus",
            "PRJEB60484",
            archive_status="comparator_only",
            notes="Ancient reindeer comparator retained for Arctic cervid context and kept out of domesticated-core inference.",
            paper_linkage=_paper(
                paper_title="Ancient reindeer mitogenomes reveal island-hopping colonisation of the Arctic archipelagos",
                doi="10.1038/s41598-024-54296-2",
                pmc_id="PMC10876933",
                journal_title="Scientific Reports",
                publication_year=2024,
                pinning_evidence="Primary paper and PMC page connect PRJEB60484 to ancient Svalbard reindeer comparator data.",
            ),
            ancient_status="ancient_comparator",
            sequencing_target="mitogenome",
            material_basis="individual_bone_or_tooth",
            dating_basis="historical_and_archaeological_context",
            geographic_basis="site_level_localities",
            domestication_scope="ancient_comparator",
        ),
        _project(
            "Rangifer tarandus",
            "PRJEB57293",
            archive_status="reject_or_out_of_scope",
            notes="Modern Svalbard reindeer comparator retained only as an explicit reject so modern context does not inflate ancient support.",
            ancient_status="modern_or_irrelevant",
            sequencing_target="mitogenome",
            material_basis="modern_tissue",
            dating_basis="modern_sampling",
            geographic_basis="site_level_localities",
            domestication_scope="modern_or_irrelevant",
        ),
        _project(
            "Rangifer tarandus",
            "PRJEB61721",
            archive_status="reject_or_out_of_scope",
            notes="Modern Svalbard reindeer comparator retained only as an explicit reject so modern context does not inflate ancient support.",
            ancient_status="modern_or_irrelevant",
            sequencing_target="mitogenome",
            material_basis="modern_tissue",
            dating_basis="modern_sampling",
            geographic_basis="site_level_localities",
            domestication_scope="modern_or_irrelevant",
        ),
        _project(
            "Rangifer tarandus",
            "PRJNA634908",
            source_family="BioProject",
            archive_status="reject_or_out_of_scope",
            notes="Modern caribou comparator retained only as an explicit reject so cross-cervid context does not masquerade as domesticated support.",
            ancient_status="modern_or_irrelevant",
            sequencing_target="mitogenome",
            material_basis="modern_tissue",
            dating_basis="modern_sampling",
            geographic_basis="country_or_breed_panel",
            domestication_scope="modern_or_irrelevant",
        ),
    )


def build_species_archive_projects(species_name: str) -> tuple[AdnaArchiveProject, ...]:
    """Return the curated archive projects for one registered species."""
    species = resolve_species_definition(species_name)
    return tuple(
        row
        for row in build_archive_project_catalog()
        if row.species_latin_name == species.latin_name
    )


def _paper(
    *,
    paper_title: str,
    pinning_evidence: str,
    doi: str | None = None,
    pubmed_id: str | None = None,
    pmc_id: str | None = None,
    journal_title: str | None = None,
    publication_year: int | None = None,
    reference_kind: str = "primary_paper",
) -> AdnaPaperLinkage:
    return AdnaPaperLinkage(
        paper_title=paper_title,
        doi=doi,
        pubmed_id=pubmed_id,
        pmc_id=pmc_id,
        journal_title=journal_title,
        publication_year=publication_year,
        reference_kind=reference_kind,
        pinning_evidence=pinning_evidence,
    )


def _project(
    species_latin_name: str,
    accession: str,
    *,
    source_family: str = "ENA",
    accession_scope: str = "project",
    archive_status: str,
    notes: str,
    paper_linkage: AdnaPaperLinkage | None = None,
    ancient_status: str,
    sequencing_target: str,
    material_basis: str,
    dating_basis: str,
    geographic_basis: str,
    result_kind: str = "read_run",
    access_policy: str = "public_downloadable",
    public_release_date: str | None = None,
    domestication_scope: str = "domesticated_core",
) -> AdnaArchiveProject:
    return AdnaArchiveProject(
        species_latin_name=species_latin_name,
        project_accession=accession,
        result_kind=result_kind,
        metadata_url=_metadata_url_for(
            accession=accession,
            source_family=source_family,
            accession_scope=accession_scope,
            result_kind=result_kind,
        ),
        source_family=source_family,
        accession_scope=accession_scope,
        archive_status=archive_status,
        notes=notes,
        paper_linkage=paper_linkage,
        ancient_status=ancient_status,
        sequencing_target=sequencing_target,
        material_basis=material_basis,
        dating_basis=dating_basis,
        geographic_basis=geographic_basis,
        access_policy=access_policy,
        public_release_date=public_release_date,
        domestication_scope=domestication_scope,
    )


def _normalize_values(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value.strip())


def _metadata_url_for(
    *,
    accession: str,
    source_family: str,
    accession_scope: str,
    result_kind: str,
) -> str:
    if source_family == "ENA":
        return build_ena_filereport_url(accession, result_kind)
    if source_family == "SRA":
        return f"https://www.ncbi.nlm.nih.gov/sra?term={accession}"
    if source_family == "BioProject":
        return f"https://www.ncbi.nlm.nih.gov/bioproject/{accession}"
    if source_family == "GenBank":
        anchor = (
            accession.split("-", 1)[0]
            if accession_scope == "accession_range"
            else accession
        )
        return f"https://www.ncbi.nlm.nih.gov/nuccore/{anchor}"
    raise ValueError(f"Unsupported archive source family: {source_family}")


def _valid_selector(value: str) -> bool:
    return all(ch.isascii() and (ch.isalnum() or ch in {"_", "-", "."}) for ch in value)


def _filereport_fields(result_kind: str) -> tuple[str, ...]:
    if result_kind == "read_run":
        return (
            "study_accession",
            "sample_accession",
            "experiment_accession",
            "run_accession",
            "tax_id",
            "scientific_name",
            "library_layout",
            "library_source",
            "library_strategy",
            "instrument_model",
            "base_count",
            "read_count",
            "fastq_bytes",
            "fastq_ftp",
            "submitted_ftp",
            "sra_ftp",
        )
    return (
        "study_accession",
        "sample_accession",
        "experiment_accession",
        "analysis_accession",
        "analysis_type",
        "tax_id",
        "scientific_name",
        "submitted_ftp",
        "bam_ftp",
    )


def _required_headers(result_kind: str) -> tuple[str, ...]:
    if result_kind == "read_run":
        return (
            "study_accession",
            "sample_accession",
            "experiment_accession",
            "run_accession",
        )
    return (
        "study_accession",
        "sample_accession",
        "experiment_accession",
        "analysis_accession",
    )


def _validate_headers(headers: list[str], result_kind: str) -> None:
    missing = [name for name in _required_headers(result_kind) if name not in headers]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"ENA filereport payload is missing required columns: {names}")


def _opt_field(value: str) -> str | None:
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _parse_optional_int(value: str, field_name: str, line_number: int) -> int | None:
    normalized = _opt_field(value)
    if normalized is None:
        return None
    try:
        return int(normalized)
    except ValueError as error:
        raise ValueError(
            f"ENA filereport row {line_number} has invalid {field_name} value {normalized!r}: {error}"
        ) from error


def _parse_int_list(value: str, field_name: str, line_number: int) -> tuple[int, ...]:
    out: list[int] = []
    for token in value.split(";"):
        normalized = token.strip()
        if not normalized:
            continue
        try:
            out.append(int(normalized))
        except ValueError as error:
            raise ValueError(
                f"ENA filereport row {line_number} has invalid {field_name} value {normalized!r}: {error}"
            ) from error
    return tuple(out)


def _split_field(value: str) -> tuple[str, ...]:
    return tuple(token.strip() for token in value.split(";") if token.strip())
