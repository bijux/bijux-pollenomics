"""Inspect the received PANGAEA taxonomy and published output schema verbatim."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from typing import Any
from zipfile import ZipFile

from .evidence import EvidenceReader


def parse_taxonomy(content: str) -> list[dict[str, Any]]:
    """Expand explicit CSV group headings, retaining each heading's source row."""
    rows = []
    lct = pft = definition = None
    lct_row = pft_row = None
    for line, row in enumerate(csv.DictReader(io.StringIO(content)), start=2):
        taxon = row.get("Plant taxa/Pollen-morphological types")
        if not taxon:
            continue
        if row["Land-cover types (LCTs)"]:
            lct, lct_row = row["Land-cover types (LCTs)"], line
        if row["PFT"]:
            pft, pft_row, definition = row["PFT"], line, row["PFT definition"]
        if lct is None or pft is None:
            raise ValueError(f"Taxon at CSV row {line} has no explicit preceding group")
        rows.append(
            {
                "source_row": line,
                "source_taxon": taxon,
                "source_pft": pft,
                "source_pft_definition": definition,
                "pft_heading_row": pft_row,
                "source_lct": lct,
                "lct_heading_row": lct_row,
                "source_fall_speed": row["FSP (m/s)"],
                "source_ppe_sd": row["PPE (SD)"],
                "review_status": "pending_qualified_review",
            }
        )
    return rows


def audit_landclim(reader: EvidenceReader) -> dict[str, Any]:
    """Report observed groups and units without silently correcting the publication."""
    path = "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
    raw = reader.read_bytes(path)
    if raw is None:
        reader.issue("landclim_taxonomy_missing", path)
        return {"accounting_status": "missing_taxonomy", "path": path}
    taxonomy = parse_taxonomy(raw.decode("utf-8-sig"))
    pfts = sorted({row["source_pft"] for row in taxonomy})
    lct_codes = set()
    for row in taxonomy:
        match = re.search(r"\(([^)]+)\)$", row["source_lct"])
        if match is None:
            raise ValueError(f"LCT heading lacks an explicit code: {row['source_lct']}")
        lct_codes.add(match[1])
    lcts = sorted(lct_codes)
    archive_path = "data/landclim/raw/landclim_ii_reveals_results.zip"
    archive_content = reader.read_bytes(archive_path)
    if archive_content is None:
        reader.issue("landclim_publication_archive_missing", archive_path)
    members = []
    if archive_content is not None:
        with ZipFile(io.BytesIO(archive_content)) as archive:
            for name in sorted(archive.namelist()):
                if not name.endswith(".csv"):
                    continue
                content = archive.read(name)
                table = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
                fields = table.fieldnames or []
                first_group = min(
                    (fields.index(code) for code in pfts if code in fields),
                    default=len(fields),
                )
                output_pfts = [
                    code for code in fields[first_group:] if code not in lcts
                ]
                sums: list[float] = []
                nonnumeric_rows = 0
                row_count = 0
                for row in table:
                    row_count += 1
                    try:
                        values = [float(row[code]) for code in lcts]
                    except (ValueError, TypeError, KeyError):
                        nonnumeric_rows += 1
                        continue
                    if all(math.isfinite(value) for value in values):
                        sums.append(math.fsum(values))
                    else:
                        nonnumeric_rows += 1
                members.append(
                    {
                        "archive_member": name,
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "row_count": row_count,
                        "columns": fields,
                        "output_pft_columns": output_pfts,
                        "pft_columns_without_taxonomy_definition": sorted(
                            set(output_pfts) - set(pfts)
                        ),
                        "taxonomy_pfts_without_output_column": sorted(
                            set(pfts) - set(output_pfts)
                        ),
                        "lct_sum_min": min(sums) if sums else None,
                        "lct_sum_max": max(sums) if sums else None,
                        "numeric_lct_sum_row_count": len(sums),
                        "nonnumeric_lct_row_count": nonnumeric_rows,
                        "rows_with_lct_sum_near_one": sum(
                            math.isclose(s, 1, abs_tol=1e-6) for s in sums
                        ),
                        "rows_with_lct_sum_near_100": sum(
                            math.isclose(s, 100, abs_tol=1e-6) for s in sums
                        ),
                    }
                )
    return {
        "source_doi": "10.1594/PANGAEA.937075",
        "taxonomy_path": path,
        "taxon_row_count": len(taxonomy),
        "taxonomy_pft_count": len(pfts),
        "taxonomy_pfts": pfts,
        "taxonomy_lct_codes": lcts,
        "taxa_review_inventory": taxonomy,
        "archive_path": archive_path,
        "archive_members": members,
        "semantic_confirmation": "requires_publication_mapping_and_units_review",
        "interpretation": "Output columns and observed sums are evidence, not a corrected method profile. Standard errors must not be required to sum to one or 100.",
    }
