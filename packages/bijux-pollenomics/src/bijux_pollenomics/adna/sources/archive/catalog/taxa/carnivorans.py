from __future__ import annotations

from ...contracts import AdnaArchiveProject
from ..factory import _paper, _project


def build_cat_projects() -> tuple[AdnaArchiveProject, ...]:
    return (
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
    )


def build_dog_projects() -> tuple[AdnaArchiveProject, ...]:
    return (
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
    )
