from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from .atlas_accountability import build_animal_atlas_candidate_accountability
from .contracts import (
    AnimalOutputHonesty,
    AtlasAccountability,
    HonestyRow,
    HonestyTotals,
    PublicAnimalOutputAudit,
)
from .coverage import build_cross_species_coverage_dashboard
from .repository import (
    _load_coordinate_provenance_rows,
    _load_country_sample_ids_by_species,
    _load_mapped_sample_ids_by_species,
    _load_sample_rows,
    _nested_string,
    _species_roots,
)


def build_public_animal_output_audit(
    data_root: Path,
    report_root: Path,
) -> PublicAnimalOutputAudit:
    """Summarize what the shipped public report tree currently exposes for animal aDNA."""
    report_root = Path(report_root)
    country_root = report_root / "countries"
    dashboard = build_cross_species_coverage_dashboard(data_root, report_root)
    countries = (
        tuple(path.name for path in sorted(country_root.iterdir()) if path.is_dir())
        if country_root.exists()
        else ()
    )
    atlas_readme = report_root / "world" / "README.md"
    atlas_notes = (
        atlas_readme.read_text(encoding="utf-8") if atlas_readme.exists() else ""
    )
    honesty = build_public_animal_output_honesty(data_root, report_root)
    accountability_path = (
        Path(data_root)
        / "adna"
        / "final"
        / "atlas"
        / "animal_atlas_candidate_accountability.json"
    )
    if accountability_path.is_file():
        accountability = cast(
            AtlasAccountability,
            json.loads(accountability_path.read_text(encoding="utf-8")),
        )
    else:
        accountability = build_animal_atlas_candidate_accountability(data_root)
    return {
        "schema_version": "animal-output-audit.v1",
        "report_root": str(report_root),
        "countries": list(countries),
        "atlas_bundle_present": (report_root / "world").is_dir(),
        "country_bundle_count": len(countries),
        "point_candidate_count": accountability["candidate_row_count"],
        "candidate_rows_with_full_traceability": accountability["passed_row_count"],
        "tracked_sample_count": honesty["totals"]["tracked_sample_count"],
        "mapped_sample_count": honesty["totals"]["mapped_sample_count"],
        "blocked_sample_count": honesty["totals"]["blocked_sample_count"],
        "unresolved_sample_count": honesty["totals"]["unresolved_sample_count"],
        "country_published_sample_count": honesty["totals"][
            "country_published_sample_count"
        ],
        "atlas_notes": atlas_notes,
        "species_rows": dashboard["rows"],
    }


def build_public_animal_output_honesty(
    data_root: Path,
    report_root: Path,
) -> AnimalOutputHonesty:
    """Compare tracked, mapped, blocked, and unresolved sample counts in one place."""
    report_root = Path(report_root)
    country_sample_ids_by_species = _load_country_sample_ids_by_species(report_root)
    mapped_sample_ids_by_species = _load_mapped_sample_ids_by_species(Path(data_root))
    rows: list[HonestyRow] = []
    totals: HonestyTotals = {
        "tracked_sample_count": 0,
        "mapped_sample_count": 0,
        "blocked_sample_count": 0,
        "unresolved_sample_count": 0,
        "country_published_sample_count": 0,
        "region_refused_count": 0,
    }
    for root in _species_roots(data_root):
        if root.name == "homo_sapiens":
            continue
        sample_rows = _load_sample_rows(root)
        if not sample_rows:
            continue
        species_name = str(sample_rows[0].get("species_latin_name", "")).strip()
        common_name = str(sample_rows[0].get("species_common_name", "")).strip()
        tracked_sample_ids = {
            _nested_string(row, "identity", "stable_token")
            for row in sample_rows
            if _nested_string(row, "identity", "stable_token")
        }
        mapped_sample_ids = mapped_sample_ids_by_species.get(species_name, set())
        unresolved_sample_count = sum(
            1
            for row in sample_rows
            if str(row.get("inclusion_status", "")).strip() == "sample_context_blocked"
        )
        region_refused_count = sum(
            1
            for row in _load_coordinate_provenance_rows(root)
            if str(row.get("mapping_posture", "")).strip() == "refused_region_only"
        )
        country_published_sample_count = len(
            country_sample_ids_by_species.get(species_name, set())
        )
        blocked_sample_count = len(tracked_sample_ids - mapped_sample_ids)
        row: HonestyRow = {
            "species_latin_name": species_name,
            "species_common_name": common_name,
            "tracked_sample_count": len(tracked_sample_ids),
            "mapped_sample_count": len(mapped_sample_ids),
            "blocked_sample_count": blocked_sample_count,
            "unresolved_sample_count": unresolved_sample_count,
            "country_published_sample_count": country_published_sample_count,
            "region_refused_count": region_refused_count,
        }
        rows.append(row)
        totals["tracked_sample_count"] += row["tracked_sample_count"]
        totals["mapped_sample_count"] += row["mapped_sample_count"]
        totals["blocked_sample_count"] += row["blocked_sample_count"]
        totals["unresolved_sample_count"] += row["unresolved_sample_count"]
        totals["country_published_sample_count"] += row[
            "country_published_sample_count"
        ]
        totals["region_refused_count"] += row["region_refused_count"]
    return {
        "schema_version": "animal-output-honesty.v1",
        "totals": totals,
        "rows": rows,
    }
