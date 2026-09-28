"""Exact ENA specimen joins to the published reindeer supplementary table."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re

from bijux_pollenomics.adna.sources.library import ADNA_SOURCE_LIBRARY_DIR
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_bytes
from bijux_pollenomics.core.xml_security import parse_hardened_xml

from ..models import AdnaProjectSampleMasterRow
from .workbook import _read_xlsx_rows

_WORKBOOK = (
    f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41598-024-54296-2/"
    "supplementary/41598_2024_54296_MOESM2_ESM.xlsx"
)
_WORKBOOK_SHA256 = "1a11850c94d8a08f91a11feecc298dc9be9003911bd6dc39df6f6796c2348988"
_HEADER = (
    "Sample ID",
    "Subspecies ",
    "Country",
    "Region",
    "Detailed location",
    "Material",
    "Museum collection",
    "Museum collection accession number",
    "Median age (BP)",
    "Age range (BP, 2 sigma)",
    "DNA extraction method",
    "Library preparation method",
    "Reference",
    "ENA BioProject",
)
_PROJECT = "PRJEB60484"
_FJL_ALIASES = {"FJL1a", "FJL3"}
_AGE_RE = re.compile(r"(\d+)-(\d+)")


def reindeer_chronology_evidence(
    row: AdnaProjectSampleMasterRow,
) -> tuple[str, str, str] | None:
    """Return the table row alone as provenance for an admitted date."""
    if row.project_accession != _PROJECT or not row.chronology_text:
        return None
    return (
        _WORKBOOK,
        row.sample_lineage_locator.split(" || ")[-1],
        row.sample_lineage_excerpt,
    )


def build_reindeer_sample_rows(
    output_root: Path,
    archive_rows: tuple[AdnaProjectSampleMasterRow, ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Join only exact BioSample aliases and retain unjoined archive specimens."""
    workbook_path = Path(output_root) / _WORKBOOK.removeprefix("data/")
    if (
        sha256(read_source_artifact_bytes(workbook_path)).hexdigest()
        != _WORKBOOK_SHA256
    ):
        raise ValueError("Reindeer supplementary table changed")
    sheet = _read_xlsx_rows(workbook_path, sheet_name="SI Table S1")
    if len(sheet) < 34 or sheet[3][: len(_HEADER)] != _HEADER:
        raise ValueError("Reindeer supplementary table layout changed")
    table: dict[str, tuple[int, tuple[str, ...]]] = {}
    for number, cells in enumerate(sheet[4:], start=5):
        if len(cells) < 14:
            continue
        alias = cells[0].removesuffix("*")
        if cells[13] == _PROJECT or alias in _FJL_ALIASES:
            if alias in table:
                raise ValueError(f"Duplicate reindeer specimen label: {alias}")
            table[alias] = (number, cells)
    if sum(cells[13] == _PROJECT for _, cells in table.values()) != 16:
        raise ValueError("Reindeer project table population changed")
    if {alias for alias in _FJL_ALIASES if alias in table} != _FJL_ALIASES:
        raise ValueError("Franz Josef Land specimen rows changed")

    if (
        len(archive_rows) != 20
        or len({r.archive_native_sample_id for r in archive_rows}) != 20
    ):
        raise ValueError("Reindeer archive BioSample population changed")
    result = []
    joined: set[str] = set()
    for row in archive_rows:
        accession = row.archive_native_sample_id
        relative = (
            f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{_PROJECT}/ena_samples/{accession}.xml"
        )
        source_path = Path(output_root) / relative.removeprefix("data/")
        payload = read_source_artifact_bytes(source_path)
        receipt = json.loads(
            source_path.with_suffix(".xml.metadata.json").read_text(encoding="utf-8")
        )
        if (
            receipt.get("content_sha256") != sha256(payload).hexdigest()
            or receipt.get("sample_accession") != accession
            or receipt.get("source_url")
            != f"https://www.ebi.ac.uk/ena/browser/api/xml/{accession}"
        ):
            raise ValueError(f"Reindeer ENA receipt changed: {accession}")
        root = parse_hardened_xml(payload)
        samples = root.findall("./SAMPLE")
        if root.tag != "SAMPLE_SET" or len(samples) != 1:
            raise ValueError(f"Reindeer ENA sample count changed: {accession}")
        sample = samples[0]
        alias = sample.get("alias", "")
        if (
            sample.get("accession") != accession
            or not alias
            or sample.findtext("TITLE") != alias
        ):
            raise ValueError(f"Reindeer ENA specimen identity changed: {accession}")

        match = table.get(alias)
        if match is None:
            result.append(
                replace(
                    row,
                    preferred_sample_label=alias,
                    sample_lineage_path=relative,
                    sample_lineage_locator=f"SAMPLE[@accession='{accession}']/@alias",
                    sample_lineage_excerpt=f"ENA BioSample {accession} has alias {alias}; no exact supplementary-table specimen row is available.",
                )
            )
            continue
        joined.add(alias)
        number, cells = match
        if alias in _FJL_ALIASES:
            if cells[2] != "Russia" or cells[13] != "This study":
                raise ValueError(f"Franz Josef Land source role changed: {alias}")
        elif cells[2] != "Svalbard, Norway" or cells[13] != _PROJECT:
            raise ValueError(f"Svalbard source role changed: {alias}")
        locality = cells[4] if cells[4] != "NA" else cells[3]
        age = cells[9]
        match_age = _AGE_RE.fullmatch(age)
        if match_age is None or int(match_age[1]) > int(match_age[2]):
            raise ValueError(f"Reindeer age interval changed: {alias}")
        median = int(cells[8])
        if not int(match_age[1]) <= median <= int(match_age[2]):
            raise ValueError(f"Reindeer age median outside interval: {alias}")
        locator = f"SI Table S1 row {number}, Sample ID {cells[0]}"
        # The primary paper's R20 interval differs from this later reanalysis.
        # Keep its locality and identity; hold the age for source reconciliation.
        dated = alias != "R20"
        excerpt = (
            f"ENA BioSample {accession} aliases {alias}; supplementary table row "
            f"{number} reports {cells[3]}, {locality}, {age} BP (2 sigma), "
            f"median {median} BP; ENA BioProject field: {cells[13]}."
        )
        result.append(
            replace(
                row,
                preferred_sample_label=alias,
                paper_native_sample_label=alias if cells[13] == _PROJECT else "",
                supplementary_table_sample_label=cells[0],
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=f"{relative} || {_WORKBOOK}",
                sample_lineage_locator=f"SAMPLE[@accession='{accession}']/@alias || {locator}",
                sample_lineage_excerpt=excerpt,
                sample_ambiguity_note=(
                    "Secondary table age differs from the primary article's Table 1 interval; chronology awaits primary-source capture."
                    if not dated
                    else ""
                ),
                locality_text=locality,
                political_entity="Russia" if alias in _FJL_ALIASES else "Norway",
                chronology_text=f"{age} BP" if dated else "",
                chronology_dating_basis="radiocarbon" if dated else "",
                chronology_evidence_class="direct_radiocarbon_date" if dated else "",
                chronology_precision_posture="sample_precise_interval" if dated else "",
                chronology_time_mean_bp=median if dated else None,
            )
        )
    if joined != set(table) - {"B20a"}:
        raise ValueError("Reindeer specimen table join changed")
    return tuple(result)
