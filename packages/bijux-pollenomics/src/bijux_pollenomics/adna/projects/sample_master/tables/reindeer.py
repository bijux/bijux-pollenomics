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
_PREPRINT = f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1111-mec.17274/author_preprint.pdf"
_PREPRINT_SHA256 = "59862eade5dee058b4e0050001c189ec1c7edc18dea06cf15dadba353600f2af"
_PREPRINT_URL = "https://www.biorxiv.org/content/10.1101/2023.09.21.558762v1.full.pdf"
_PREPRINT_S3 = (
    f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1111-mec.17274/"
    "supplementary/author-preprint-table-s3.xlsx"
)
_PREPRINT_S3_SHA256 = "fe4066aecc10fb4573613ac1641756c80503cb4bf41c7bf9a49ab25aa2ecfe97"
_PREPRINT_S3_URL = (
    "https://www.biorxiv.org/content/biorxiv/early/2023/09/22/"
    "2023.09.21.558762/DC2/embed/media-2.xlsx?download=true"
)
_ARTICLE = f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1111-mec.17274/article.pdf"
_ARTICLE_SHA256 = "1446b3d42f066605e162cd043ae4eb2da1ef14748534af7b1205cada19d0fb3f"
_ARTICLE_URL = "https://api.nva.unit.no/publication/0198cc66e16f-a743d6e1-054b-400e-a2c4-dd186a645095/filelink/dfe8ba06-53e4-4e80-856e-7a12dd0dbd3f"
# Author preprint Table 1, printed pp. 41–43. The source gives UTM E/N but no zone;
# these values are custody evidence only and do not become WGS84 map coordinates.
_PREPRINT_ROWS = {
    "B20": ("E-Svalbard", 651368, 8661900, 2351, "2329-2460"),
    "BBH7": ("Nordaustlandet", 641458, 8915138, 511, "500-521"),
    "M44": ("C-Spitsbergen", 536291, 8707272, 597, "525-644"),
    "M46": ("C-Spitsbergen", 536023, 8706959, 703, "668-768"),
    "M68": ("C-Spitsbergen", 545390, 8700500, None, "0-447"),
    "M72": ("C-Spitsbergen", 546200, 8701580, 958, "916-1057"),
    "MB60": ("E-Svalbard", 637956, 8689040, None, "27-260"),
    "MDV11": ("E-Svalbard", 636986, 8688774, 605, "549-647"),
    "MLM12": ("E-Svalbard", 651249, 8661821, 1326, "1298-1349"),
    "MLM16": ("E-Svalbard", 651084, 8661716, 1762, "1716-1821"),
    "MLM51": ("E-Svalbard", 658011, 8650398, 1968, "1894-2046"),
    "MLM61": ("E-Svalbard", 637640, 8688976, 1875, "1825-1935"),
    "MLM80": ("E-Svalbard", 658480, 8700183, 3912, "3846-3973"),
    "MLM82": ("E-Svalbard", 658632, 8700166, 3127, "3063-3212"),
    "R20": ("Wijdfjorden", 525246, 8785449, None, "0-450"),
    "R25a": ("Wijdfjorden", 525722, 8783391, None, "8-277"),
    "R29a": ("Wijdfjorden", 525722, 8783391, None, "12-267"),
    "R36": ("Wijdfjorden", 525768, 8783368, None, "1-282"),
}
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
    if row.preferred_sample_label == "R20":
        return (
            _ARTICLE,
            "Table 1 published p. 4, ID R20",
            row.sample_lineage_excerpt,
        )
    source = _WORKBOOK if row.supplementary_table_sample_label else _PREPRINT
    return (
        source,
        (
            "Table 1 pp. 41-43, ID B20"
            if row.preferred_sample_label == "B20"
            else row.sample_lineage_locator.split(" || ")[-1]
        ),
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
    preprint_path = Path(output_root) / _PREPRINT.removeprefix("data/")
    if (
        sha256(read_source_artifact_bytes(preprint_path)).hexdigest()
        != _PREPRINT_SHA256
    ):
        raise ValueError("Reindeer author preprint changed")
    preprint_receipt = json.loads(
        preprint_path.with_suffix(".pdf.metadata.json").read_text(encoding="utf-8")
    )
    if (
        preprint_receipt.get("source_url") != _PREPRINT_URL
        or preprint_receipt.get("content_sha256") != _PREPRINT_SHA256
    ):
        raise ValueError("Reindeer author preprint receipt changed")
    preprint_s3_path = Path(output_root) / _PREPRINT_S3.removeprefix("data/")
    if (
        sha256(read_source_artifact_bytes(preprint_s3_path)).hexdigest()
        != _PREPRINT_S3_SHA256
    ):
        raise ValueError("Reindeer author Table S3 changed")
    preprint_s3_receipt = json.loads(
        preprint_s3_path.with_suffix(".xlsx.metadata.json").read_text(encoding="utf-8")
    )
    if (
        preprint_s3_receipt.get("source_url") != _PREPRINT_S3_URL
        or preprint_s3_receipt.get("content_sha256") != _PREPRINT_S3_SHA256
        or preprint_s3_receipt.get("preprint_version") != "1"
    ):
        raise ValueError("Reindeer author Table S3 receipt changed")
    article_path = Path(output_root) / _ARTICLE.removeprefix("data/")
    if sha256(read_source_artifact_bytes(article_path)).hexdigest() != _ARTICLE_SHA256:
        raise ValueError("Reindeer published article changed")
    article_receipt = json.loads(
        article_path.with_suffix(".pdf.metadata.json").read_text(encoding="utf-8")
    )
    if (
        article_receipt.get("source_url") != _ARTICLE_URL
        or article_receipt.get("content_sha256") != _ARTICLE_SHA256
        or article_receipt.get("published_article_doi") != "10.1111/mec.17274"
    ):
        raise ValueError("Reindeer published article receipt changed")
    preprint_s3_sheet = _read_xlsx_rows(preprint_s3_path, sheet_name="Tabellenblatt1")
    preprint_s3_ancient = preprint_s3_sheet[2:20]
    if (
        len(preprint_s3_ancient) != 18
        or {cells[0] for cells in preprint_s3_ancient} != set(_PREPRINT_ROWS)
        or any(
            cells[6] != _PREPRINT_ROWS[cells[0]][4] or cells[7] != "ancient"
            for cells in preprint_s3_ancient
        )
    ):
        raise ValueError("Reindeer author Table S3 specimen or age rows changed")
    preprint_s3_areas = {cells[0]: cells[1] for cells in preprint_s3_ancient}
    if preprint_s3_areas["B20"] != "Edgeøya":
        raise ValueError("Reindeer B20 author locality changed")
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
    preprint_joined: set[str] = set()
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
        preprint = _PREPRINT_ROWS.get(alias)
        if preprint is not None:
            preprint_joined.add(alias)

        match = table.get(alias)
        if match is None:
            if preprint is not None:
                area, easting, northing, median, age = preprint
                locator = f"Table 1 pp. 41-43, ID {alias}"
                s3_locator = "Table S3 row 5, ID B20"
                b20 = alias == "B20"
                name_note = (
                    " Source spelling Wijdfjorden is normalized to Wijdefjorden "
                    "using the later table and the same or adjacent R25a grid."
                    if area == "Wijdfjorden"
                    else ""
                )
                result.append(
                    replace(
                        row,
                        paper_native_sample_label=alias,
                        preferred_sample_label=alias,
                        sample_evidence_status="direct_table_extracted",
                        sample_lineage_path=(
                            f"{relative} || {_PREPRINT} || {_PREPRINT_S3}"
                            if b20
                            else f"{relative} || {_PREPRINT}"
                        ),
                        sample_lineage_locator=(
                            f"SAMPLE[@accession='{accession}']/@alias || "
                            + locator
                            + (f" || {s3_locator}" if b20 else "")
                        ),
                        sample_lineage_excerpt=(
                            f"ENA BioSample {accession} aliases {alias}; author bioRxiv "
                            f"preprint {locator} reports {area}, {age} BP (2 sigma), "
                            f"UTM E {easting} m and N {northing} m. The UTM zone is "
                            f"not given; no WGS84 point is derived.{name_note}"
                            + (
                                " Author preprint Table S3 row 5 names Edgeøya."
                                if b20
                                else ""
                            )
                        ),
                        locality_text=(
                            "Wijdefjorden"
                            if area == "Wijdfjorden"
                            else preprint_s3_areas[alias]
                            if b20
                            else ""
                        ),
                        political_entity="Norway",
                        chronology_text=f"{age} BP",
                        chronology_dating_basis="radiocarbon",
                        chronology_evidence_class="direct_radiocarbon_date",
                        chronology_precision_posture="sample_precise_interval",
                        chronology_time_mean_bp=median,
                    )
                )
                continue
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
        if preprint is not None and alias != "R20" and preprint[4] != age:
            raise ValueError(
                f"Reindeer preprint and later table ages disagree: {alias}"
            )
        if alias == "R20" and (
            preprint is None or preprint[4] != "0-450" or age != "41-252"
        ):
            raise ValueError("Reindeer R20 cross-publication date conflict changed")
        match_age = _AGE_RE.fullmatch(age)
        if match_age is None or int(match_age[1]) > int(match_age[2]):
            raise ValueError(f"Reindeer age interval changed: {alias}")
        median = int(cells[8])
        if not int(match_age[1]) <= median <= int(match_age[2]):
            raise ValueError(f"Reindeer age median outside interval: {alias}")
        locator = f"SI Table S1 row {number}, Sample ID {cells[0]}"
        # The project-specific primary article is the authority for R20. Its
        # broad interval contains the later reanalysis interval; retain both.
        selected_age = preprint[4] if alias == "R20" and preprint else age
        selected_median = None if alias == "R20" else median
        excerpt = (
            f"ENA BioSample {accession} aliases {alias}; supplementary table row "
            f"{number} reports {cells[3]}, {locality}, {age} BP (2 sigma), "
            f"median {median} BP; ENA BioProject field: {cells[13]}."
            + (
                " Published Molecular Ecology Table 1 p. 4 and author preprint "
                "Table S3 row 20 give R20 0–450 calibrated BP (2 sigma); the "
                "primary project interval is selected without a median."
                if alias == "R20"
                else ""
            )
        )
        result.append(
            replace(
                row,
                preferred_sample_label=alias,
                paper_native_sample_label=alias if cells[13] == _PROJECT else "",
                supplementary_table_sample_label=cells[0],
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=(
                    f"{relative} || {_ARTICLE} || {_PREPRINT_S3} || {_WORKBOOK}"
                    if alias == "R20"
                    else f"{relative} || {_WORKBOOK}"
                ),
                sample_lineage_locator=(
                    f"SAMPLE[@accession='{accession}']/@alias || "
                    "Table 1 published p. 4, ID R20 || Table S3 row 20, ID R20 || "
                    f"{locator}"
                    if alias == "R20"
                    else f"SAMPLE[@accession='{accession}']/@alias || {locator}"
                ),
                sample_lineage_excerpt=excerpt,
                sample_ambiguity_note=(
                    "Published primary-project interval 0–450 BP selected; later secondary reanalysis reports nested 41–252 BP. The narrower date is retained as an alternative, not silently merged or substituted."
                    if alias == "R20"
                    else ""
                ),
                locality_text=locality,
                political_entity="Russia" if alias in _FJL_ALIASES else "Norway",
                chronology_text=f"{selected_age} BP",
                chronology_dating_basis="radiocarbon",
                chronology_evidence_class="direct_radiocarbon_date",
                chronology_precision_posture="sample_precise_interval",
                chronology_time_mean_bp=selected_median,
            )
        )
    if joined != set(table) - {"B20a"}:
        raise ValueError("Reindeer specimen table join changed")
    if preprint_joined != set(_PREPRINT_ROWS):
        raise ValueError("Reindeer preprint specimen population changed")
    return tuple(result)
