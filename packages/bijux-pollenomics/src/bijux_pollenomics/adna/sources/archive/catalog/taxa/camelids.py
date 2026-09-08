from __future__ import annotations

from ...contracts import AdnaArchiveProject
from ..factory import _paper, _project


def build_dromedary_projects() -> tuple[AdnaArchiveProject, ...]:
    return (
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
    )
