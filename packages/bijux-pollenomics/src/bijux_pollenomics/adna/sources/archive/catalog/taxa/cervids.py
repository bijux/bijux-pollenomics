from __future__ import annotations

from ...contracts import AdnaArchiveProject
from ..factory import _paper, _project


def build_reindeer_projects() -> tuple[AdnaArchiveProject, ...]:
    return (
        _project(
            "Rangifer tarandus",
            "PRJEB60484",
            archive_status="comparator_only",
            notes="Ancient reindeer comparator retained for Arctic cervid context and kept out of domesticated-core inference.",
            paper_linkage=_paper(
                paper_title="A palaeogenomic investigation of overharvest implications in an endemic wild reindeer subspecies",
                doi="10.1111/mec.17274",
                journal_title="Molecular Ecology",
                publication_year=2024,
                pinning_evidence="The primary paper's data availability statement names PRJEB60484; its Table 1 describes the 18 ancient Svalbard specimens. A separate Scientific Reports paper reuses 16 of these specimens and has a publisher-hosted sample table.",
            ),
            ancient_status="ancient_comparator",
            sequencing_target="shotgun_genome",
            material_basis="individual_bone_or_tooth",
            dating_basis="radiocarbon",
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
