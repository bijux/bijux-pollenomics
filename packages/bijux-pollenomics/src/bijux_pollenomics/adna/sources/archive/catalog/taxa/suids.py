from __future__ import annotations

from ...contracts import AdnaArchiveProject
from ..factory import _paper, _project


def build_pig_projects() -> tuple[AdnaArchiveProject, ...]:
    return (
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
    )
