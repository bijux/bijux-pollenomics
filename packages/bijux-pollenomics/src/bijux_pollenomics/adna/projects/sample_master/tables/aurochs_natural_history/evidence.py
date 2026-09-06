"""Pinned source contract for the PRJEB75467 Scandinavian aurochs subset."""

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


@dataclass(frozen=True)
class AurochsArchiveIdentity:
    """One explicit workbook label-to-ENA BioSample identity contract."""

    sample_label: str
    sample_accession: str


ARCHIVE_IDENTITIES: Final = (
    AurochsArchiveIdentity("Hjo1", "SAMEA115574419"),
    AurochsArchiveIdentity("Ska1", "SAMEA115574441"),
    AurochsArchiveIdentity("Ska3", "SAMEA115574442"),
    AurochsArchiveIdentity("Zea1", "SAMEA115574456"),
    AurochsArchiveIdentity("Zea2", "SAMEA115574457"),
)
PAPER_ONLY_SAMPLE_LABEL: Final = "Fre1"


__all__ = [
    "ARCHIVE_IDENTITIES",
    "AUROCHS_NATURAL_HISTORY_ARCHIVE_TEXT_SHA256",
    "AUROCHS_NATURAL_HISTORY_PROJECT_ACCESSION",
    "AUROCHS_NATURAL_HISTORY_SHEET",
    "AUROCHS_NATURAL_HISTORY_WORKBOOK_PATH",
    "AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256",
    "AUROCHS_WILD_POPULATION_LABEL",
    "PAPER_ONLY_SAMPLE_LABEL",
    "AurochsArchiveIdentity",
]
