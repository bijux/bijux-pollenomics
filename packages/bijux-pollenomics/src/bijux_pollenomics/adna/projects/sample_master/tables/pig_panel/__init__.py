"""Evidence-bound pig-panel reconciliation and domesticated-core admission."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from ...models import AdnaProjectSampleMasterRow
from .site_coordinates import (
    PIG_SITE_COORDINATE_EVIDENCE_PATH as PIG_SITE_COORDINATE_EVIDENCE_PATH,
)
from .site_coordinates import (
    PigSiteCoordinateEvidence as PigSiteCoordinateEvidence,
)
from .site_coordinates import (
    load_pig_site_coordinate_evidence as load_pig_site_coordinate_evidence,
)

_EXPECTED_ARCHIVE_IDENTITIES = {
    "AA014": "SAMEA5160866",
    "AA015": "SAMEA5160867",
    "AA016": "SAMEA5160868",
    "AA017": "SAMEA5160869",
    "AA290": "SAMEA5160978",
    "AA291": "SAMEA5160979",
    "AA292": "SAMEA5160980",
    "AA293": "SAMEA5160981",
}
_UNMATCHED_WORKBOOK_LABELS = ("AA013", "AA289")
_HEADER_POSITIONS = {
    "Extract No. / Lab code": 0,
    "Age": 27,
    "Age (Mean years BP)": 28,
    "Location": 31,
    "Country": 32,
    "Status based on Zooarch": 33,
    "Status based on MC1R and Zooracheolog": 37,
    "Published?": 39,
}
_STATUS_INDEXES = (33, 37, 38)


@dataclass(frozen=True)
class PigPanelJoinAuditRow:
    """One explicitly classified workbook-to-archive identity join."""

    sample_label: str
    archive_native_sample_id: str
    locality_text: str
    political_entity: str
    source_age_text: str
    chronology_text: str
    domestication_status: str
    disposition: str
    disposition_reason: str
    workbook_source_path: str
    workbook_source_locator: str
    archive_source_path: str
    archive_source_locators: tuple[str, ...]
    latitude_text: str = ""
    longitude_text: str = ""
    map_admission: str = "refused_missing_source_coordinates"
    coordinate_basis: str = ""
    coordinate_confidence: str = ""
    coordinate_source_url: str = ""
    coordinate_source_locator: str = ""
    coordinate_spatial_scope: str = ""

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-ready audit record."""
        return asdict(self)


def build_pig_panel_join_audit(
    *,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
    archive_source_path: str,
    archive_text: str,
    coordinate_evidence: tuple[PigSiteCoordinateEvidence, ...] = (),
) -> tuple[PigPanelJoinAuditRow, ...]:
    """Reconcile the eight source-proven pig identities without broad admission."""
    _validate_workbook_header(rows)
    workbook_rows = _indexed_workbook_rows(rows)
    archive_identities = _archive_identity_evidence(archive_text)
    coordinates_by_label = {row.sample_label: row for row in coordinate_evidence}

    audit_rows = []
    for sample_label, expected_accession in _EXPECTED_ARCHIVE_IDENTITIES.items():
        row_number, row = workbook_rows[sample_label]
        accession, locators = archive_identities[sample_label]
        if accession != expected_accession:
            raise ValueError(
                f"Pig archive identity drift for {sample_label}: "
                f"{accession!r} != {expected_accession!r}"
            )
        statuses = tuple(_cell(row, index) for index in _STATUS_INDEXES)
        status, disposition, reason = _classify_domestication(sample_label, statuses)
        mean_bp = _canonical_bp_text(_cell(row, 28), sample_label=sample_label)
        site_coordinate = coordinates_by_label.get(sample_label)
        if site_coordinate is not None:
            _validate_site_coordinate_join(
                evidence=site_coordinate,
                archive_accession=accession,
                locality_text=_required_cell(row, 31, sample_label),
                political_entity=_required_cell(row, 32, sample_label),
            )
        audit_rows.append(
            PigPanelJoinAuditRow(
                sample_label=sample_label,
                archive_native_sample_id=accession,
                locality_text=_required_cell(row, 31, sample_label),
                political_entity=_required_cell(row, 32, sample_label),
                source_age_text=_required_cell(row, 27, sample_label),
                chronology_text=mean_bp,
                domestication_status=status,
                disposition=disposition,
                disposition_reason=reason,
                workbook_source_path=source_path,
                workbook_source_locator=f"Sheet1!row{row_number}",
                archive_source_path=archive_source_path,
                archive_source_locators=locators,
                latitude_text=""
                if site_coordinate is None
                else site_coordinate.latitude_text,
                longitude_text=""
                if site_coordinate is None
                else site_coordinate.longitude_text,
                map_admission=(
                    "refused_missing_source_coordinates"
                    if site_coordinate is None
                    else "admitted_approximate_site_anchor"
                ),
                coordinate_basis=""
                if site_coordinate is None
                else site_coordinate.coordinate_basis,
                coordinate_confidence=""
                if site_coordinate is None
                else site_coordinate.coordinate_confidence,
                coordinate_source_url=""
                if site_coordinate is None
                else site_coordinate.coordinate_source_url,
                coordinate_source_locator=""
                if site_coordinate is None
                else site_coordinate.coordinate_source_locator,
                coordinate_spatial_scope=""
                if site_coordinate is None
                else site_coordinate.spatial_scope,
            )
        )
    return tuple(audit_rows)


def _build_pig_panel_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
    archive_source_path: str,
    archive_text: str,
    coordinate_evidence: tuple[PigSiteCoordinateEvidence, ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if species.latin_name != "Sus scrofa domesticus":
        raise ValueError("Pig-panel admission requires Sus scrofa domesticus")
    if project.project_accession != "PRJEB30282":
        raise ValueError("Pig-panel admission requires PRJEB30282")
    audit = build_pig_panel_join_audit(
        source_path=source_path,
        rows=rows,
        archive_source_path=archive_source_path,
        archive_text=archive_text,
        coordinate_evidence=coordinate_evidence,
    )
    return tuple(
        _master_row(species=species, project=project, audit=row)
        for row in audit
        if row.disposition == "admitted_domesticated_core"
    )


def _master_row(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    audit: PigPanelJoinAuditRow,
) -> AdnaProjectSampleMasterRow:
    return AdnaProjectSampleMasterRow(
        species_latin_name=species.latin_name,
        species_common_name=species.common_name,
        project_accession=project.project_accession,
        repo_stable_sample_id=(
            f"{project.project_accession}:{audit.archive_native_sample_id}".casefold()
        ),
        archive_native_sample_id=audit.archive_native_sample_id,
        paper_native_sample_label=audit.sample_label,
        supplementary_table_sample_label=audit.sample_label,
        preferred_sample_label=audit.sample_label,
        sample_basis="supplementary_table_and_archive_identity_join",
        sample_evidence_status="direct_table_extracted",
        sample_lineage_path=audit.workbook_source_path,
        sample_lineage_locator=audit.workbook_source_locator,
        sample_lineage_excerpt=(
            f"{audit.sample_label} | {audit.locality_text} | "
            f"{audit.political_entity} | {audit.source_age_text} | "
            f"{audit.chronology_text} | {audit.domestication_status}"
        ),
        sample_identity_resolution="final",
        sample_ambiguity_note="",
        locality_text=audit.locality_text,
        political_entity=audit.political_entity,
        latitude_text=audit.latitude_text,
        longitude_text=audit.longitude_text,
        chronology_text=audit.chronology_text,
        chronology_dating_basis="archaeological_context",
        chronology_evidence_class="archaeological_context_date",
        chronology_precision_posture="sample_approximate_or_modeled",
    )


def _validate_site_coordinate_join(
    *,
    evidence: PigSiteCoordinateEvidence,
    archive_accession: str,
    locality_text: str,
    political_entity: str,
) -> None:
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


def _validate_workbook_header(rows: tuple[tuple[str, ...], ...]) -> None:
    if not rows:
        raise ValueError("Pig supplementary workbook has no rows")
    header = rows[0]
    for expected, index in _HEADER_POSITIONS.items():
        if _cell(header, index) != expected:
            raise ValueError(
                f"Pig supplementary workbook header drift at column {index + 1}: "
                f"expected {expected!r}"
            )
    if _cell(header, 38) != "Status based on Zooarch":
        raise ValueError("Pig supplementary workbook secondary status header drift")


def _indexed_workbook_rows(
    rows: tuple[tuple[str, ...], ...],
) -> dict[str, tuple[int, tuple[str, ...]]]:
    expected = (*_EXPECTED_ARCHIVE_IDENTITIES, *_UNMATCHED_WORKBOOK_LABELS)
    indexed: dict[str, list[tuple[int, tuple[str, ...]]]] = {
        label: [] for label in expected
    }
    for row_number, row in enumerate(rows[1:], start=2):
        label = _cell(row, 0)
        if label in indexed:
            indexed[label].append((row_number, row))
    malformed = {label: found for label, found in indexed.items() if len(found) != 1}
    if malformed:
        counts = {label: len(found) for label, found in malformed.items()}
        raise ValueError(
            f"Pig workbook identity rows must occur exactly once: {counts}"
        )
    return {label: found[0] for label, found in indexed.items()}


def _archive_identity_evidence(
    archive_text: str,
) -> dict[str, tuple[str, tuple[str, ...]]]:
    lines = archive_text.splitlines()
    if not lines:
        raise ValueError("Pig archive metadata has no rows")
    header = lines[0].split("\t")
    required = ("run_accession", "study_accession", "sample_accession", "submitted_ftp")
    if any(header.count(name) != 1 for name in required):
        raise ValueError("Pig archive metadata header contract is missing or ambiguous")
    indexes = {name: header.index(name) for name in required}
    observed: dict[str, tuple[str, list[str]]] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        columns = line.split("\t")
        if len(columns) != len(header):
            raise ValueError(f"Malformed pig archive row at line {line_number}")
        labels = set(
            re.findall(r"(?:^|/)(AA\d{3})_", columns[indexes["submitted_ftp"]])
        )
        for label in labels:
            if (
                label not in _EXPECTED_ARCHIVE_IDENTITIES
                and label not in _UNMATCHED_WORKBOOK_LABELS
            ):
                continue
            if columns[indexes["study_accession"]] != "PRJEB30282":
                raise ValueError(f"Pig identity {label} is bound to the wrong project")
            accession = columns[indexes["sample_accession"]].strip()
            run = columns[indexes["run_accession"]].strip()
            if not accession or not run:
                raise ValueError(
                    f"Pig identity {label} lacks archive accession evidence"
                )
            prior = observed.setdefault(label, (accession, []))
            if prior[0] != accession:
                raise ValueError(
                    f"Pig identity {label} maps to multiple archive samples"
                )
            prior[1].append(f"run_accession:{run}")
    unexpected = set(_UNMATCHED_WORKBOOK_LABELS) & observed.keys()
    if unexpected:
        raise ValueError(
            f"Previously unmatched pig identities require review: {sorted(unexpected)}"
        )
    missing = set(_EXPECTED_ARCHIVE_IDENTITIES) - observed.keys()
    if missing:
        raise ValueError(f"Pig archive identity evidence is missing: {sorted(missing)}")
    return {
        label: (accession, tuple(sorted(set(locators))))
        for label, (accession, locators) in observed.items()
    }


def _classify_domestication(
    sample_label: str, statuses: tuple[str, ...]
) -> tuple[str, str, str]:
    if statuses == ("Domestic",) * 3:
        return (
            "Domestic",
            "admitted_domesticated_core",
            "Three source classification fields concordantly report Domestic.",
        )
    if statuses == ("Wild",) * 3:
        return (
            "Wild",
            "excluded_wild",
            "Three source classification fields concordantly report Wild.",
        )
    if statuses == ("Unknown",) * 3:
        return (
            "Unknown",
            "excluded_domestication_unknown",
            "Three source classification fields report Unknown domestication status.",
        )
    raise ValueError(
        f"Pig domestication classifications disagree for {sample_label}: {statuses}"
    )


def _canonical_bp_text(value: str, *, sample_label: str) -> str:
    text = value.replace(",", "").strip()
    if not re.fullmatch(r"\d{1,5}", text):
        raise ValueError(f"Pig chronology mean is not numeric BP for {sample_label}")
    return f"{int(text)} BP"


def _required_cell(row: tuple[str, ...], index: int, sample_label: str) -> str:
    value = _cell(row, index)
    if not value:
        raise ValueError(f"Pig source field {index + 1} is empty for {sample_label}")
    return value


def _cell(row: tuple[str, ...], index: int) -> str:
    return row[index].strip() if index < len(row) else ""
