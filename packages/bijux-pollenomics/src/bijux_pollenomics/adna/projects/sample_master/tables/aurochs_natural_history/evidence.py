"""Pinned source and identity contract for PRJEB75467 progenitor cattle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

AUROCHS_NATURAL_HISTORY_PROJECT_ACCESSION: Final = "PRJEB75467"
AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256: Final = (
    "2c4676aef05f1d9cc272eba1dabfc3d30fb7604c8fa3fc0713518414e213655f"
)
AUROCHS_NATURAL_HISTORY_ARCHIVE_TEXT_SHA256: Final = (
    "18a982463818f35cc349ca399c4ba1607f293381f6df30b2550e32406c329647"
)
AUROCHS_NATURAL_HISTORY_SHEET: Final = "Supplementary Data 1"
AUROCHS_NATURAL_HISTORY_WORKBOOK_PATH: Final = (
    "data/adna/governance/source_library/papers/10.1038-s41586-024-08112-6/"
    "supplementary/41586_2024_8112_MOESM3_ESM.xlsx"
)
AUROCHS_WILD_POPULATION_LABEL: Final = "Holocene Wild Scandinavia"
AUROCHS_PROGENITOR_POPULATION_LABELS: Final = frozenset(
    {
        AUROCHS_WILD_POPULATION_LABEL,
        "Holocene Wild Balkans",
        "Holocene Wild Britain",
        "Holocene Wild Central Asia",
        "Holocene Wild Germany",
        "Holocene Wild Iberia",
        "Holocene Wild Italy",
        "Holocene Wild Pontic-Caspian Steppe",
        "Holocene Wild Unknown",
        "Pleistocene Wild Caucauses",
        "Pleistocene Wild Germany",
        "Pleistocene Wild Italy",
        "Pleistocene Wild Siberia",
        "Pre-LGM Europe",
        "Pre-LGM North Asia",
    }
)


@dataclass(frozen=True)
class AurochsArchiveIdentity:
    """One explicit workbook label-to-ENA BioSample identity contract."""

    sample_label: str
    sample_accession: str


SCANDINAVIAN_ARCHIVE_IDENTITIES: Final = (
    AurochsArchiveIdentity("Hjo1", "SAMEA115574419"),
    AurochsArchiveIdentity("Ska1", "SAMEA115574441"),
    AurochsArchiveIdentity("Ska3", "SAMEA115574442"),
    AurochsArchiveIdentity("Zea1", "SAMEA115574456"),
    AurochsArchiveIdentity("Zea2", "SAMEA115574457"),
)
RECOVERABLE_PROGENITOR_ARCHIVE_IDENTITIES: Final = (
    AurochsArchiveIdentity("Baikal1", "SAMEA115574404"),
    AurochsArchiveIdentity("Bed4", "SAMEA115574405"),
    AurochsArchiveIdentity("Borly4b", "SAMEA115574407"),
    AurochsArchiveIdentity("Galicia1", "SAMEA115574415"),
    AurochsArchiveIdentity("Galicia2", "SAMEA115574416"),
    AurochsArchiveIdentity("Galicia3", "SAMEA115574417"),
    AurochsArchiveIdentity("Gyu1", "SAMEA115574418"),
    AurochsArchiveIdentity("Hxh2", "SAMEA115574420"),
    AurochsArchiveIdentity("Mantova1", "SAMEA115574423"),
    AurochsArchiveIdentity("NVL1", "SAMEA115574428"),
    AurochsArchiveIdentity("NVL3", "SAMEA115574429"),
    AurochsArchiveIdentity("Padova1", "SAMEA115574430"),
    AurochsArchiveIdentity("Palidoro1", "SAMEA115574432"),
    AurochsArchiveIdentity("Rhi1", "SAMEA115574433"),
    AurochsArchiveIdentity("Rhi2", "SAMEA115574434"),
    AurochsArchiveIdentity("Rhi3", "SAMEA115574435"),
    AurochsArchiveIdentity("ROS001", "SAMEA115574436"),
    AurochsArchiveIdentity("ROS002", "SAMEA115574437"),
    AurochsArchiveIdentity("Tango1", "SAMEA115574443"),
    AurochsArchiveIdentity("Tango2", "SAMEA115574444"),
    AurochsArchiveIdentity("Tri1", "SAMEA115574445"),
    AurochsArchiveIdentity("Tula1", "SAMEA115574446"),
    AurochsArchiveIdentity("Uralsk1", "SAMEA115574447"),
    AurochsArchiveIdentity("Uzzo1", "SAMEA115574448"),
    AurochsArchiveIdentity("Var1", "SAMEA115574449"),
    AurochsArchiveIdentity("Var2", "SAMEA115574450"),
    AurochsArchiveIdentity("Vratsa1", "SAMEA115574452"),
    AurochsArchiveIdentity("Vratsa2", "SAMEA115574454"),
    AurochsArchiveIdentity("YoA", "SAMEA115574455"),
)
ARCHIVE_IDENTITIES: Final = (
    *SCANDINAVIAN_ARCHIVE_IDENTITIES,
    *RECOVERABLE_PROGENITOR_ARCHIVE_IDENTITIES,
)
CHRONOLOGY_UNAVAILABLE_SAMPLE_LABELS: Final = frozenset({"Uralsk1"})
SPECIMEN_ID_UNAVAILABLE_SAMPLE_LABELS: Final = frozenset({"Bed4", "Tri1"})
PAPER_ONLY_SAMPLE_LABEL: Final = "Fre1"


__all__ = [
    "ARCHIVE_IDENTITIES",
    "AUROCHS_NATURAL_HISTORY_ARCHIVE_TEXT_SHA256",
    "AUROCHS_NATURAL_HISTORY_PROJECT_ACCESSION",
    "AUROCHS_NATURAL_HISTORY_SHEET",
    "AUROCHS_NATURAL_HISTORY_WORKBOOK_PATH",
    "AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256",
    "AUROCHS_PROGENITOR_POPULATION_LABELS",
    "AUROCHS_WILD_POPULATION_LABEL",
    "CHRONOLOGY_UNAVAILABLE_SAMPLE_LABELS",
    "PAPER_ONLY_SAMPLE_LABEL",
    "RECOVERABLE_PROGENITOR_ARCHIVE_IDENTITIES",
    "SCANDINAVIAN_ARCHIVE_IDENTITIES",
    "SPECIMEN_ID_UNAVAILABLE_SAMPLE_LABELS",
    "AurochsArchiveIdentity",
]
