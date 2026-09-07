"""Hash-bound archive and supplement parsing for the ancient-cattle panel."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import re

from .evidence import APPROXIMATE_BP_BY_SAMPLE, SITE_EVIDENCE, CattleSiteEvidence

_EXPECTED_TAXA = {
    ("9913", "Bos taurus"): 68,
    ("9909", "Bos primigenius"): 5,
    ("9915", "Bos indicus"): 3,
    ("9904", "Bos gaurus"): 1,
}
_TABLE_S2_ROW_RE = re.compile(
    r"^\s+(?P<sample>[A-Z][A-Za-z0-9]+)\s+"
    r"-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s+"
    r"\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s+.+?\s+"
    r"(?P<approximate_bp>\d+)\s+\d+(?:\.\d+)?\s+\d+(?:\.\d+)?\s*$"
)


@dataclass(frozen=True)
class ArchiveSample:
    """One archive-owned sample identity and its submitted files."""

    accession: str
    experiment_ids: tuple[str, ...]
    submitted_basenames: tuple[str, ...]
    tax_id: str
    scientific_name: str


def parse_archive(archive_text: str) -> dict[str, ArchiveSample]:
    """Parse and denominator-check the pinned PRJEB31621 archive table."""
    reader = csv.DictReader(StringIO(archive_text), delimiter="\t")
    required = {
        "run_accession",
        "sample_accession",
        "experiment_accession",
        "tax_id",
        "scientific_name",
        "submitted_ftp",
    }
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise ValueError("PRJEB31621 archive columns are missing")
    source_rows = [row for row in reader if row["sample_accession"].strip()]
    if len(source_rows) != 364:
        raise ValueError("PRJEB31621 archive run denominator drift")
    if len({row["run_accession"] for row in source_rows}) != 364:
        raise ValueError("duplicate PRJEB31621 run accession")
    if len({row["experiment_accession"] for row in source_rows}) != 364:
        raise ValueError("duplicate PRJEB31621 experiment accession")
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in source_rows:
        grouped.setdefault(row["sample_accession"].strip(), []).append(row)
    if len(grouped) != 77:
        raise ValueError("PRJEB31621 archive sample denominator drift")
    built: dict[str, ArchiveSample] = {}
    for accession, rows in grouped.items():
        taxon = {
            (row["tax_id"].strip(), row["scientific_name"].strip()) for row in rows
        }
        if len(taxon) != 1:
            raise ValueError(f"archive taxonomy conflict for {accession}")
        tax_id, scientific_name = next(iter(taxon))
        built[accession] = ArchiveSample(
            accession=accession,
            experiment_ids=tuple(
                sorted(row["experiment_accession"].strip() for row in rows)
            ),
            submitted_basenames=tuple(
                sorted(
                    {
                        Path(item.strip()).name
                        for row in rows
                        for item in row["submitted_ftp"].split(";")
                        if item.strip()
                    }
                )
            ),
            tax_id=tax_id,
            scientific_name=scientific_name,
        )
    taxa: dict[tuple[str, str], int] = {}
    for sample in built.values():
        key = (sample.tax_id, sample.scientific_name)
        taxa[key] = taxa.get(key, 0) + 1
    if taxa != _EXPECTED_TAXA:
        raise ValueError("PRJEB31621 archive taxonomy denominator drift")
    return built


def validate_supplement(supplement_text: str | None) -> tuple[str, ...]:
    """Validate ancient identities and BP claims in the pinned supplement."""
    expected_ids = tuple(
        sample_id for site in SITE_EVIDENCE for sample_id in site.sample_ids
    )
    if supplement_text is None:
        return expected_ids
    if "Table S1." not in supplement_text or "Table S2." not in supplement_text:
        raise ValueError("PRJEB31621 supplement table markers are missing")
    table_s1 = supplement_text.split("Table S1.", 1)[1].split("Table S2.", 1)[0]
    table_s1_ids = tuple(
        match.group(1)
        for line in table_s1.splitlines()
        if (match := re.match(r"^\s+([A-Z][A-Za-z0-9]+)\s+\d", line))
    )
    if len(table_s1_ids) != 66 or set(table_s1_ids) != set(expected_ids):
        raise ValueError("PRJEB31621 Table S1 ancient identity denominator drift")
    if len(set(table_s1_ids)) != len(table_s1_ids):
        raise ValueError("duplicate PRJEB31621 Table S1 ancient identity")
    table_s2 = supplement_text.split("Table S2.", 1)[1].split("Table S3.", 1)[0]
    parsed_bp: dict[str, int] = {}
    external_ids: set[str] = set()
    seen_table_s2_ids: set[str] = set()
    for line in table_s2.splitlines():
        match = _TABLE_S2_ROW_RE.match(line)
        if match is None:
            continue
        sample_id = match.group("sample")
        if sample_id in seen_table_s2_ids:
            raise ValueError(f"duplicate PRJEB31621 Table S2 identity: {sample_id}")
        seen_table_s2_ids.add(sample_id)
        if sample_id not in set(expected_ids):
            external_ids.add(sample_id)
            continue
        parsed_bp[sample_id] = int(match.group("approximate_bp"))
    if external_ids != {"CPC98"}:
        raise ValueError("PRJEB31621 Table S2 external identity set drift")
    if parsed_bp != APPROXIMATE_BP_BY_SAMPLE:
        raise ValueError("PRJEB31621 Table S2 approximate-BP mapping drift")
    for site in SITE_EVIDENCE:
        if site.source_heading not in supplement_text:
            raise ValueError(
                f"PRJEB31621 archaeological section missing: {site.section_number}"
            )
    return table_s1_ids


def site_by_sample() -> dict[str, CattleSiteEvidence]:
    """Build the unique sample-to-site assignment index."""
    result: dict[str, CattleSiteEvidence] = {}
    for site in SITE_EVIDENCE:
        for sample_id in site.sample_ids:
            if sample_id in result:
                raise ValueError(f"duplicate cattle site assignment for {sample_id}")
            result[sample_id] = site
    if len(SITE_EVIDENCE) != 40 or len(result) != 66:
        raise ValueError("PRJEB31621 site-evidence denominator drift")
    return result
