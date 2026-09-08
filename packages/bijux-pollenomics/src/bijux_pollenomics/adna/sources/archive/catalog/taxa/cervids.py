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
