from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import cast

from ....sources.archive import build_archive_project_catalog
from .semantics import _geocoding_safe_token
from .worksheets import build_project_locality_worksheet_rows


@cache
def build_site_name_normalization_dictionary_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for project in build_archive_project_catalog():
        for row in build_project_locality_worksheet_rows(
            output_root, project.project_accession
        ):
            token = _geocoding_safe_token(
                str(row["resolved_locality_text"] or row["original_locality_text"])
            )
            if not token:
                continue
            key = (str(row["project_accession"]), token)
            current = grouped.setdefault(
                key,
                {
                    "project_accession": row["project_accession"],
                    "species_latin_name": row["species_latin_name"],
                    "normalized_display_spelling": str(
                        row["resolved_locality_text"] or row["original_locality_text"]
                    ),
                    "geocoding_safe_token": token,
                    "original_source_spellings": set(),
                    "alternative_spellings": set(),
                    "source_surfaces": set(),
                    "locality_classes": set(),
                },
            )
            spelling = str(row["original_locality_text"]).strip()
            if spelling:
                cast(set[str], current["original_source_spellings"]).add(spelling)
                if spelling != current["normalized_display_spelling"]:
                    cast(set[str], current["alternative_spellings"]).add(spelling)
            cast(set[str], current["source_surfaces"]).add(str(row["source_surface"]))
            cast(set[str], current["locality_classes"]).add(str(row["locality_class"]))
    rows = []
    for row in grouped.values():
        rows.append(
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "normalized_display_spelling": row["normalized_display_spelling"],
                "geocoding_safe_token": row["geocoding_safe_token"],
                "original_source_spellings": sorted(
                    cast(set[str], row["original_source_spellings"])
                ),
                "alternative_spellings": sorted(
                    cast(set[str], row["alternative_spellings"])
                ),
                "source_surfaces": sorted(cast(set[str], row["source_surfaces"])),
                "locality_classes": sorted(cast(set[str], row["locality_classes"])),
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["project_accession"]),
            str(item["normalized_display_spelling"]).casefold(),
        )
    )
    return tuple(rows)
