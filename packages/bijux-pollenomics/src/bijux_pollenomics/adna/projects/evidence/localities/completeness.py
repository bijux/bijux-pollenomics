from __future__ import annotations

from collections import defaultdict
from functools import cache
from pathlib import Path

from ....sources.archive import build_archive_project_catalog
from .evidence_rows import build_project_sample_locality_evidence_rows
from .semantics import ADNA_LOCALITY_CLASSES


@cache
def build_species_locality_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for project in build_archive_project_catalog():
        grouped[project.species_latin_name].extend(
            build_project_sample_locality_evidence_rows(
                output_root, project.project_accession
            )
        )
    rows: list[dict[str, object]] = []
    for species_name, packets in sorted(grouped.items()):
        rows.append(
            {
                "species_latin_name": species_name,
                **_locality_completeness_counts(packets),
            }
        )
    return tuple(rows)


@cache
def build_project_locality_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        packets = build_project_sample_locality_evidence_rows(
            output_root, project.project_accession
        )
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                **_locality_completeness_counts(packets),
            }
        )
    return tuple(rows)


def _locality_completeness_counts(
    packets: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> dict[str, object]:
    exact_count = 0
    broader_count = 0
    unresolved_count = 0
    class_counts = dict.fromkeys(ADNA_LOCALITY_CLASSES, 0)
    for packet in packets:
        class_counts[str(packet["assigned_locality_class"])] += 1
        bucket = str(packet["locality_evidence_bucket"])
        if bucket == "exact_site_evidence":
            exact_count += 1
        elif bucket == "broader_locality_evidence":
            broader_count += 1
        else:
            unresolved_count += 1
    sample_count = len(packets)
    return {
        "recovered_sample_row_count": sample_count,
        "exact_site_evidence_count": exact_count,
        "broader_locality_evidence_count": broader_count,
        "unresolved_geography_count": unresolved_count,
        "excavation_site_count": class_counts["excavation_site"],
        "broader_locality_count": class_counts["broader_locality"],
        "municipality_count": class_counts["municipality"],
        "region_count": class_counts["region"],
        "country_count": class_counts["country"],
        "inferred_place_string_count": class_counts["inferred_place_string"],
        "locality_unresolved_count": class_counts["unresolved"],
        "locality_completeness_ratio": 0.0
        if sample_count == 0
        else round(exact_count / sample_count, 4),
    }
