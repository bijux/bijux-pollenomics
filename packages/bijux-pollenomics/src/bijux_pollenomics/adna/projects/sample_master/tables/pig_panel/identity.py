"""Exact source identity joins and denominator validation for the pig panel."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .admission import GOVERNED_DOMESTIC_ANCHORS
from .site_coordinates import PigSiteCoordinateEvidence

EXPECTED_ARCHIVE_SAMPLE_COUNT = 343
EXPECTED_ANCIENT_JOIN_COUNT = 320
EXPECTED_MODERN_JOIN_COUNT = 23

_ANCIENT_LABEL_RE = re.compile(
    r"(?:^|/)([A-Z]{2,3}\d{3,4})_(?:OXF\d+|SciLife)(?:[./]|$)"
)
_ANCIENT_HEADER_POSITIONS = {
    "Extract No. / Lab code": 0,
    "Previous Extraction Code": 1,
    "Accession of mtDNA data": 2,
    "Source": 3,
    "Museum/Sample code": 20,
    "Additional Sample Information": 21,
    "Radiocarbon Lab #": 22,
    "Uncalibrated_Date": 23,
    "Error +/-": 24,
    "From Cal BP (Int Cal13)": 25,
    "To Cal BP (Int Cal13)": 26,
    "Age": 27,
    "Age (Mean years BP)": 28,
    "Period": 29,
    "Group": 30,
    "Location": 31,
    "Country": 32,
    "Status based on Zooarch": 33,
    "Status based on MC1R and Zooracheolog": 37,
    "Published?": 39,
}
_MODERN_HEADERS = (
    "ID",
    "Population",
    "Breed/Country",
    "Coverage",
    "Accession",
    "doi",
)


@dataclass(frozen=True)
class ArchiveEvidence:
    """Archive sample identities and source-owned run locators."""

    sample_accessions: frozenset[str]
    ancient_accession_by_label: dict[str, str]
    locators_by_accession: dict[str, tuple[str, ...]]


def archive_evidence(archive_text: str) -> ArchiveEvidence:
    """Parse exact ancient labels and archive sample identities."""
    lines = archive_text.splitlines()
    if not lines:
        raise ValueError("Pig archive metadata has no rows")
    header = lines[0].split("\t")
    required = ("run_accession", "study_accession", "sample_accession", "submitted_ftp")
    if any(header.count(name) != 1 for name in required):
        raise ValueError("Pig archive metadata header contract is missing or ambiguous")
    indexes = {name: header.index(name) for name in required}
    locators_by_accession: dict[str, set[str]] = {}
    sample_accession_by_run: dict[str, str] = {}
    ancient_accession_by_label: dict[str, str] = {}
    ancient_labels_by_accession: dict[str, set[str]] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        columns = line.split("\t")
        if len(columns) != len(header):
            raise ValueError(f"Malformed pig archive row at line {line_number}")
        if columns[indexes["study_accession"]] != "PRJEB30282":
            raise ValueError(
                f"Pig archive row {line_number} belongs to another project"
            )
        accession = columns[indexes["sample_accession"]].strip()
        run = columns[indexes["run_accession"]].strip()
        if not accession or not run:
            raise ValueError(
                f"Pig archive row {line_number} lacks sample or run identity"
            )
        prior_accession = sample_accession_by_run.setdefault(run, accession)
        if prior_accession != accession:
            raise ValueError(
                f"Pig archive run {run} maps to multiple sample accessions: "
                f"{sorted((prior_accession, accession))}"
            )
        locators_by_accession.setdefault(accession, set()).add(f"run_accession:{run}")
        labels = set(_ANCIENT_LABEL_RE.findall(columns[indexes["submitted_ftp"]]))
        if len(labels) > 1:
            raise ValueError(
                f"Pig archive row {line_number} carries multiple sample labels"
            )
        for label in labels:
            prior = ancient_accession_by_label.setdefault(label, accession)
            if prior != accession:
                raise ValueError(
                    f"Pig identity {label} maps to multiple archive samples"
                )
            ancient_labels_by_accession.setdefault(accession, set()).add(label)
    ambiguous_accessions = {
        accession: sorted(labels)
        for accession, labels in ancient_labels_by_accession.items()
        if len(labels) > 1
    }
    if ambiguous_accessions:
        raise ValueError(
            "Pig archive samples map to multiple ancient labels: "
            f"{ambiguous_accessions}"
        )
    return ArchiveEvidence(
        sample_accessions=frozenset(locators_by_accession),
        ancient_accession_by_label=ancient_accession_by_label,
        locators_by_accession={
            accession: tuple(sorted(locators))
            for accession, locators in locators_by_accession.items()
        },
    )


def indexed_ancient_workbook_rows(
    rows: tuple[tuple[str, ...], ...], *, required_labels: frozenset[str]
) -> dict[str, tuple[int, tuple[str, ...]]]:
    """Index exactly one ancient supplement row for each archive label."""
    indexed: dict[str, list[tuple[int, tuple[str, ...]]]] = {
        label: [] for label in required_labels
    }
    for row_number, row in enumerate(rows[1:], start=2):
        label = cell(row, 0)
        if label in indexed:
            indexed[label].append((row_number, row))
    malformed = {label: found for label, found in indexed.items() if len(found) != 1}
    if malformed:
        counts = {label: len(found) for label, found in malformed.items()}
        raise ValueError(
            f"Pig workbook identity rows must occur exactly once: {counts}"
        )
    return {label: found[0] for label, found in indexed.items()}


def indexed_modern_workbook_rows(
    rows: tuple[tuple[str, ...], ...], *, required_accessions: frozenset[str]
) -> dict[str, tuple[int, tuple[str, ...]]]:
    """Index exactly one modern supplement row for each archive accession."""
    indexed: dict[str, list[tuple[int, tuple[str, ...]]]] = {
        accession: [] for accession in required_accessions
    }
    for row_number, row in enumerate(rows[1:], start=2):
        accession = cell(row, 4)
        if accession in indexed:
            indexed[accession].append((row_number, row))
    malformed = {
        accession: found for accession, found in indexed.items() if len(found) != 1
    }
    if malformed:
        counts = {accession: len(found) for accession, found in malformed.items()}
        raise ValueError(
            f"Pig modern workbook accessions must occur exactly once: {counts}"
        )
    resolved = {accession: found[0] for accession, found in indexed.items()}
    accessions_by_label: dict[str, set[str]] = {}
    for accession, (_, row) in resolved.items():
        label = cell(row, 0)
        if not label:
            raise ValueError(f"Pig modern workbook ID is empty for {accession}")
        accessions_by_label.setdefault(label, set()).add(accession)
    ambiguous_labels = {
        label: sorted(accessions)
        for label, accessions in accessions_by_label.items()
        if len(accessions) > 1
    }
    if ambiguous_labels:
        raise ValueError(
            f"Pig modern IDs map to multiple archive accessions: {ambiguous_labels}"
        )
    return resolved


def validate_denominators(
    *,
    archive: ArchiveEvidence,
    ancient_accessions: frozenset[str],
    modern_accessions: frozenset[str],
) -> None:
    """Refuse incomplete or overlapping source identity partitions."""
    if len(archive.sample_accessions) != EXPECTED_ARCHIVE_SAMPLE_COUNT:
        raise ValueError("Pig archive sample denominator drift")
    if len(ancient_accessions) != EXPECTED_ANCIENT_JOIN_COUNT:
        raise ValueError("Pig ancient supplement join denominator drift")
    if len(archive.ancient_accession_by_label) != len(ancient_accessions):
        raise ValueError("Pig ancient labels and archive samples are not one-to-one")
    if len(modern_accessions) != EXPECTED_MODERN_JOIN_COUNT:
        raise ValueError("Pig modern supplement join denominator drift")
    if ancient_accessions & modern_accessions:
        raise ValueError("Pig ancient and modern supplement identities overlap")
    if ancient_accessions | modern_accessions != archive.sample_accessions:
        raise ValueError(
            "Pig supplement joins do not reconcile to the archive denominator"
        )


def coordinate_evidence_by_label(
    coordinate_evidence: tuple[PigSiteCoordinateEvidence, ...],
) -> dict[str, PigSiteCoordinateEvidence]:
    """Restrict coordinate evidence to the two governed sample identities."""
    coordinates_by_label = {row.sample_label: row for row in coordinate_evidence}
    if len(coordinates_by_label) != len(coordinate_evidence):
        raise ValueError("Pig coordinate evidence contains duplicate sample labels")
    unexpected = set(coordinates_by_label) - GOVERNED_DOMESTIC_ANCHORS
    if unexpected:
        raise ValueError(
            f"Pig coordinate evidence widens governed anchors: {sorted(unexpected)}"
        )
    return coordinates_by_label


def validate_ancient_workbook_header(rows: tuple[tuple[str, ...], ...]) -> None:
    """Refuse ancient workbook schema drift."""
    if not rows:
        raise ValueError("Pig ancient supplementary workbook has no rows")
    header = rows[0]
    for expected, index in _ANCIENT_HEADER_POSITIONS.items():
        if cell(header, index) != expected:
            raise ValueError(
                f"Pig ancient workbook header drift at column {index + 1}: expected {expected!r}"
            )
    if cell(header, 38) != "Status based on Zooarch":
        raise ValueError("Pig ancient workbook secondary status header drift")


def validate_modern_workbook_header(rows: tuple[tuple[str, ...], ...]) -> None:
    """Refuse modern workbook schema drift."""
    if not rows:
        raise ValueError("Pig modern supplementary workbook has no rows")
    observed = tuple(cell(rows[0], index) for index in range(len(_MODERN_HEADERS)))
    if observed != _MODERN_HEADERS:
        raise ValueError(
            f"Pig modern workbook header drift: {observed!r} != {_MODERN_HEADERS!r}"
        )


def validate_site_coordinate_join(
    *,
    evidence: PigSiteCoordinateEvidence,
    archive_accession: str,
    locality_text: str,
    political_entity: str,
) -> None:
    """Require coordinates to match archive identity and source locality."""
    if evidence.archive_native_sample_id != archive_accession:
        raise ValueError(
            f"Pig site-coordinate archive identity drift for {evidence.sample_label}"
        )
    if evidence.locality_text != locality_text:
        raise ValueError(
            f"Pig site-coordinate locality drift for {evidence.sample_label}"
        )
    if evidence.political_entity != political_entity:
        raise ValueError(
            f"Pig site-coordinate political entity drift for {evidence.sample_label}"
        )


def required_cell(row: tuple[str, ...], index: int, sample_label: str) -> str:
    """Return a required source cell without normalization."""
    value = cell(row, index)
    if not value:
        raise ValueError(f"Pig source field {index + 1} is empty for {sample_label}")
    return value


def cell(row: tuple[str, ...], index: int) -> str:
    """Return one stripped source cell, or empty when absent."""
    return row[index].strip() if index < len(row) else ""
