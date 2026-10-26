"""Retain the two existing AADR source records without choosing their dates."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

IDS = {"CGG_2_105915.SG", "CGG_2_105916.SG"}
PREFIXES = {
    "persistent_id": "Persistent Genetic ID",
    "individual_id": "Individual ID",
    "skeletal_code": "Skeletal code",
    "skeletal_element": "Skeletal element",
    "publication": "Publication abbreviation",
    "doi": "doi for publication",
    "dating_method": "Method for Determining Date",
    "date_mean_bp": "Date mean in BP",
    "date_sd_bp": "Date standard deviation in BP",
    "full_date": "Full Date",
    "morphology": "Age at death,",
    "locality": "Locality",
    "country": "Political Entity",
    "latitude": "Latitude",
    "longitude": "Longitude",
}


def source_rows(path: Path, panel: str) -> list[dict[str, Any]]:
    """Read descriptive ANNO fields only; preserve every source literal."""
    selected = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream, delimiter="\t")
        header = next(reader)
        if not header[0].startswith("Genetic ID"):
            raise ValueError("AADR genetic identifier header differs")
        columns = {}
        for name, prefix in PREFIXES.items():
            matches = [i for i, value in enumerate(header) if value.startswith(prefix)]
            if len(matches) != 1:
                raise ValueError("AADR required descriptive header is ambiguous")
            columns[name] = matches[0]
        for number, row in enumerate(reader, start=2):
            if row[0] not in IDS:
                continue
            if len(row) != len(header):
                raise ValueError("AADR descriptive source row has changed width")
            selected.append(
                {
                    "panel": panel,
                    "physical_row": number,
                    "genetic_id": row[0],
                    "fields": {
                        name: {"source_header": header[index], "literal": row[index]}
                        for name, index in columns.items()
                    },
                }
            )
    if len(selected) != 2 or {row["genetic_id"] for row in selected} != IDS:
        raise ValueError("AADR two-conflict source population differs")
    return selected
