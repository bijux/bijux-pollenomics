from __future__ import annotations

from typing import cast


def _build_farming_history_scenario(
    *,
    coverage_payload: dict[str, object],
    human_overlap_payload: dict[str, object],
    pollen_overlap_payload: dict[str, object],
    first_appearance_payload: dict[str, object],
) -> dict[str, object]:
    coverage_rows = [
        row
        for row in cast(list[object], coverage_payload.get("rows", []))
        if isinstance(row, dict)
    ]
    human_rows = [
        row
        for row in cast(list[object], human_overlap_payload.get("rows", []))
        if isinstance(row, dict)
    ]
    pollen_rows = [
        row
        for row in cast(list[object], pollen_overlap_payload.get("rows", []))
        if isinstance(row, dict)
    ]
    first_rows = [
        row
        for row in cast(list[object], first_appearance_payload.get("rows", []))
        if isinstance(row, dict)
    ]

    support: list[str] = []
    weak_support: list[str] = []
    non_support: list[str] = []

    domesticated_first_rows = [
        row for row in first_rows if str(row.get("animal_scope")) == "domesticated_core"
    ]
    if domesticated_first_rows:
        earliest = max(
            domesticated_first_rows,
            key=lambda row: int(cast(str, row["first_signal_bp"])),
        )
        support.append(
            f"The current Nordic publication surface can now name one first animal signal: "
            f"`{earliest['species_latin_name']}` in `{earliest['country']}` with a tracked "
            f"window of `{earliest['time_label']}` from `{earliest['project_accession']}`."
        )
    for row in coverage_rows:
        if str(row.get("assignment_confidence")) == "regional_projection":
            weak_support.append(
                f"`{row['species_latin_name']}` contributes `{row['country']}` evidence only "
                "through a regional projection, not a country-exact excavation label."
            )
        if str(row.get("animal_scope")) == "comparator":
            weak_support.append(
                f"`{row['species_latin_name']}` remains comparator-only in `{row['country']}` "
                "and cannot be promoted into domesticated-core farming support."
            )
        if str(row.get("animal_scope")) == "wild_or_progenitor_context":
            weak_support.append(
                f"`{row['species_latin_name']}` contributes wild or progenitor context in "
                f"`{row['country']}` and cannot be promoted into domesticated-core farming support."
            )
    represented_species = {
        str(row["species_latin_name"])
        for row in coverage_rows
        if str(row.get("animal_scope")) == "domesticated_core"
    }
    for species_name in (
        "Equus caballus",
        "Sus scrofa domesticus",
        "Bos taurus",
        "Capra hircus",
        "Canis lupus familiaris",
        "Felis catus",
        "Camelus dromedarius",
        "Equus asinus",
    ):
        if species_name not in represented_species:
            non_support.append(
                f"The shipped Nordic country outputs still do not support a country-localized "
                f"claim for `{species_name}`."
            )
    if not support:
        support.append(
            "The repo now has a real country-resolved animal publication surface, but it "
            "still supports only a narrow set of Nordic-facing claims."
        )
    return {
        "schema_version": "nordic-farming-history-scenario.v1",
        "question": (
            "What does the currently shipped Nordic animal aDNA surface actually support "
            "about early farming history?"
        ),
        "support_statements": support,
        "weak_support_statements": _deduplicate_lines(weak_support),
        "non_support_statements": _deduplicate_lines(non_support),
        "evidence_anchors": {
            "country_species_coverage_rows": len(coverage_rows),
            "animal_human_overlap_rows": len(human_rows),
            "animal_pollen_overlap_rows": len(pollen_rows),
            "first_appearance_rows": len(first_rows),
        },
    }


def _deduplicate_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        unique.append(line)
    return unique
