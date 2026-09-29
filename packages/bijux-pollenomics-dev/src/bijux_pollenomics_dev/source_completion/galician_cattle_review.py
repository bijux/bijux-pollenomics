"""Review the pinned Galician cattle paper before project species promotion."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
from io import StringIO
import json
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
DOI = "10.1371/journal.pone.0249537"
PROJECT = "PRJNA705960"
ARCHIVE = Path(
    "data/adna/governance/source_library/projects/PRJNA705960/archive_metadata.html.gz"
)


def _sha(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def sheet_rows(path: Path) -> dict[int, dict[str, str]]:
    """Read only the first worksheet's literal cells with Python's stdlib."""
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if "xl/worksheets/sheet1.xml" not in names:
            raise ValueError("Expected first worksheet is absent")
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            strings = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.findall(".//x:t", NS))
                for item in strings.findall("x:si", NS)
            ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    result: dict[int, dict[str, str]] = {}
    for row in sheet.findall(".//x:sheetData/x:row", NS):
        number = int(row.attrib["r"])
        fields: dict[str, str] = {}
        for cell in row.findall("x:c", NS):
            coordinate = cell.attrib["r"]
            column = re.match(r"[A-Z]+", coordinate)
            if column is None:
                raise ValueError("Worksheet cell coordinate is invalid")
            value = cell.find("x:v", NS)
            text = (
                (value.text or "")
                if value is not None
                else "".join(item.text or "" for item in cell.findall(".//x:t", NS))
            )
            if cell.attrib.get("t") == "s":
                text = shared[int(text)]
            fields[column.group()] = text or ""
        result[number] = fields
    return result


def derive(
    article: str,
    correction: str,
    dating: dict[int, dict[str, str]],
    mapping: dict[int, dict[str, str]],
    archive_text: str,
    biosample_aliases: dict[str, str],
) -> dict[str, Any]:
    """Reconcile source-owned sample aliases without promoting mixed taxa."""
    if DOI not in article or PROJECT not in article:
        raise ValueError("Article DOI or BioProject identity is missing")
    if (
        "The third author" not in correction
        or "Johanna L. A. Paijmans" not in correction
    ):
        raise ValueError("Correction scope was not verified")
    if dating.get(15, {}).get("C") != "species":
        raise ValueError("Dating table species column changed")
    source_rows = [dating[number] for number in range(16, 34) if number in dating]
    if len(source_rows) != 18:
        raise ValueError("Paper specimen denominator changed")
    species = Counter(row.get("C", "") for row in source_rows)
    if set(species) != {"Bos taurus", "Bos primigenius"}:
        raise ValueError("Paper specimen taxonomy changed")
    if mapping.get(1, {}).get("A") != "Sample":
        raise ValueError("Sequenced sample header changed")
    sequenced = [
        mapping[number].get("A", "") for number in range(2, 13) if number in mapping
    ]
    if len(sequenced) != 11 or len(set(sequenced)) != 11:
        raise ValueError("Sequenced paper sample denominator changed")
    seq_taxa = Counter(
        "Bos primigenius" if label.startswith("Bp_") else "Bos taurus"
        for label in sequenced
    )
    if any(not label.startswith(("Bp_", "Bt_")) for label in sequenced):
        raise ValueError("Paper sample taxon prefix changed")
    archive_rows = list(csv.DictReader(StringIO(archive_text), delimiter="\t"))
    accessions = [row["sample_accession"] for row in archive_rows]
    if len(archive_rows) != 11 or len(set(accessions)) != 11:
        raise ValueError("Archive BioSample population changed")
    if {row["study_accession"] for row in archive_rows} != {PROJECT}:
        raise ValueError("Archive BioProject identity changed")
    archive_taxa = Counter(row["scientific_name"] for row in archive_rows)
    if seq_taxa != archive_taxa:
        raise ValueError("Paper and archive taxon totals differ")
    paper_by_alias: dict[str, tuple[int, dict[str, str]]] = {}
    for number in range(16, 34):
        row = dating[number]
        label = row.get("J", "")
        if label.startswith(("Bp_", "Bt_")):
            key = re.sub("[^a-z0-9]", "", label.lower())
            if key in paper_by_alias:
                raise ValueError("Paper sample labels collide after normalization")
            paper_by_alias[key] = number, row
    if len(paper_by_alias) != len(archive_rows) or set(biosample_aliases) != set(
        accessions
    ):
        raise ValueError("Paper/BioSample alias population differs")
    crosswalk = []
    seen_paper_rows: set[int] = set()
    for archive_row in sorted(archive_rows, key=lambda row: row["sample_accession"]):
        accession = archive_row["sample_accession"]
        alias = biosample_aliases[accession]
        key = re.sub("[^a-z0-9]", "", alias.lower())
        pair = paper_by_alias.get(key)
        if pair is None:
            raise ValueError(f"BioSample alias does not match paper label: {accession}")
        number, paper_row = pair
        if (
            number in seen_paper_rows
            or paper_row["C"] != archive_row["scientific_name"]
        ):
            raise ValueError("BioSample alias repeats or taxonomy differs from paper")
        seen_paper_rows.add(number)
        crosswalk.append(
            {
                "biosample_accession": accession,
                "biosample_alias": alias,
                "paper_row": number,
                "paper_sample_label": paper_row["J"],
                "paper_specimen_code": paper_row["A"],
                "source_species": paper_row["C"],
            }
        )
    if seen_paper_rows != {number for number, _ in paper_by_alias.values()}:
        raise ValueError("Paper sample label lacks a BioSample accession")
    return {
        "schema_version": "galician-cattle-paper-review.v1",
        "source_project": PROJECT,
        "paper_doi": DOI,
        "paper_correction_doi": "10.1371/journal.pone.0269578",
        "paper_correction_scope": "third_author_name_only",
        "paper_specimen_rows": len(source_rows),
        "paper_specimen_species_counts": dict(sorted(species.items())),
        "paper_sequenced_sample_labels": len(sequenced),
        "paper_sequenced_species_counts": dict(sorted(seq_taxa.items())),
        "archive_biosample_accessions": len(accessions),
        "archive_species_counts": dict(sorted(archive_taxa.items())),
        "sample_label_to_biosample_crosswalk_status": "resolved_by_source_owned_ena_biosample_alias",
        "sample_label_to_biosample_crosswalk": crosswalk,
        "source_catalog_project_species": "Bos taurus",
        "source_catalog_species_conflict": True,
        "source_paper_linkage_status": "primary_paper_identified_not_promoted",
        "animal_sample_admission": "unchanged_refused_pending_sample_owned_taxonomy_and_lineage_review",
        "nordic_relevance": "none_galician_source_context",
    }


def build(
    repository: Path,
    capture: Path,
    output: Path,
) -> dict[str, Any]:
    paths = {
        "article": capture / "article.html",
        "correction": capture / "correction.html",
        "dating_table": capture / "dating-table.xlsx",
        "mapping_table": capture / "mapping-table.xlsx",
        "archive": repository / ARCHIVE,
    }
    with gzip.open(paths["archive"], "rt") as archive_stream:
        archive_text = archive_stream.read()
    source_accessions: set[str] = set()
    for row in csv.DictReader(StringIO(archive_text), delimiter="\t"):
        accession = row.get("sample_accession")
        if not accession:
            raise ValueError("Archive BioSample accession is absent")
        source_accessions.add(accession)
    accessions = sorted(source_accessions)
    biosample_aliases: dict[str, str] = {}
    for accession in accessions:
        path = capture / "biosamples" / f"{accession}.xml"
        sample_set = ET.fromstring(path.read_bytes())
        sample = sample_set if sample_set.tag == "SAMPLE" else sample_set.find("SAMPLE")
        if sample is None or sample.attrib.get("accession") != accession:
            raise ValueError(f"ENA BioSample XML identity differs: {accession}")
        biosample_aliases[accession] = sample.attrib["alias"]
        paths[f"biosample:{accession}"] = path
    report = derive(
        paths["article"].read_text(),
        paths["correction"].read_text(),
        sheet_rows(paths["dating_table"]),
        sheet_rows(paths["mapping_table"]),
        archive_text,
        biosample_aliases,
    )
    report["sources"] = {
        key: {
            "path": path.relative_to(repository).as_posix(),
            **_sha(path),
        }
        for key, path in paths.items()
    }
    report["official_urls"] = {
        "article": f"https://journals.plos.org/plosone/article?id={DOI}",
        "correction": "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0269578",
        "dating_table": f"https://journals.plos.org/plosone/article/file?id={DOI}.s001&type=supplementary",
        "mapping_table": f"https://journals.plos.org/plosone/article/file?id={DOI}.s002&type=supplementary",
        "biosample_xml_template": "https://www.ebi.ac.uk/ena/browser/api/xml/{biosample_accession}",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(
        args.repository.resolve(), args.capture.resolve(), args.output.resolve()
    )
    print(
        json.dumps(
            {
                "paper_specimens": result["paper_specimen_rows"],
                "sequenced_labels": result["paper_sequenced_sample_labels"],
                "archive_accessions": result["archive_biosample_accessions"],
                "status": result["source_paper_linkage_status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
