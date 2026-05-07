from __future__ import annotations

import json
from pathlib import Path

from ..models import CountryReport

__all__ = ["publish_public_animal_reporting_outputs"]


def publish_public_animal_reporting_outputs(
    output_root: Path,
    *,
    country_reports: tuple[CountryReport, ...],
    country_output_dirs: tuple[Path, ...],
    atlas_output_dir: Path,
) -> dict[str, str]:
    """Write public cross-country animal reporting outputs from generated bundles."""
    country_payloads = _load_country_payloads(country_reports, country_output_dirs)
    coverage_payload = _build_country_species_coverage(country_payloads)
    human_overlap_payload = _build_animal_human_chronology_overlap(
        country_payloads, country_reports
    )
    pollen_overlap_payload = _build_animal_pollen_chronology_overlap(
        country_payloads, atlas_output_dir
    )
    first_appearance_payload = _build_first_appearance_by_country(country_payloads)
    scenario_payload = _build_farming_history_scenario(
        coverage_payload=coverage_payload,
        human_overlap_payload=human_overlap_payload,
        pollen_overlap_payload=pollen_overlap_payload,
        first_appearance_payload=first_appearance_payload,
    )

    artifact_payloads = {
        "animal_country_species_coverage": coverage_payload,
        "animal_human_chronology_overlap": human_overlap_payload,
        "animal_pollen_chronology_overlap": pollen_overlap_payload,
        "animal_first_appearance_by_country": first_appearance_payload,
        "nordic_farming_history_scenario": scenario_payload,
    }
    for stem, payload in artifact_payloads.items():
        (output_root / f"{stem}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    (output_root / "animal_country_species_coverage.md").write_text(
        _render_country_species_coverage_markdown(coverage_payload),
        encoding="utf-8",
    )
    (output_root / "animal_human_chronology_overlap.md").write_text(
        _render_human_overlap_markdown(human_overlap_payload),
        encoding="utf-8",
    )
    (output_root / "animal_pollen_chronology_overlap.md").write_text(
        _render_pollen_overlap_markdown(pollen_overlap_payload),
        encoding="utf-8",
    )
    (output_root / "animal_first_appearance_by_country.md").write_text(
        _render_first_appearance_markdown(first_appearance_payload),
        encoding="utf-8",
    )
    (output_root / "nordic_farming_history_scenario.md").write_text(
        _render_scenario_markdown(scenario_payload),
        encoding="utf-8",
    )
    return {
        "animal_country_species_coverage_json": "animal_country_species_coverage.json",
        "animal_country_species_coverage_markdown": "animal_country_species_coverage.md",
        "animal_human_chronology_overlap_json": "animal_human_chronology_overlap.json",
        "animal_human_chronology_overlap_markdown": "animal_human_chronology_overlap.md",
        "animal_pollen_chronology_overlap_json": "animal_pollen_chronology_overlap.json",
        "animal_pollen_chronology_overlap_markdown": "animal_pollen_chronology_overlap.md",
        "animal_first_appearance_by_country_json": "animal_first_appearance_by_country.json",
        "animal_first_appearance_by_country_markdown": "animal_first_appearance_by_country.md",
        "nordic_farming_history_scenario_json": "nordic_farming_history_scenario.json",
        "nordic_farming_history_scenario_markdown": "nordic_farming_history_scenario.md",
    }


def _load_country_payloads(
    country_reports: tuple[CountryReport, ...],
    country_output_dirs: tuple[Path, ...],
) -> list[dict[str, object]]:
    by_dir = {path.name: path for path in country_output_dirs}
    payloads: list[dict[str, object]] = []
    for report in country_reports:
        country_dir = by_dir.get(report.output_dir.name)
        if country_dir is None:
            continue
        summary_path = country_dir / f"{country_dir.name}_animal_adna_{report.version}_summary.json"
        if not summary_path.is_file():
            continue
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _build_country_species_coverage(
    country_payloads: list[dict[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        for row in payload.get("species_rows", []):
            if not isinstance(row, dict):
                continue
            rows.append(row)
    rows.sort(key=lambda row: (str(row["country"]), str(row["species_latin_name"])))
    return {
        "schema_version": "animal-country-species-coverage.v1",
        "rows": rows,
    }


def _build_animal_human_chronology_overlap(
    country_payloads: list[dict[str, object]],
    country_reports: tuple[CountryReport, ...],
) -> dict[str, object]:
    report_by_country = {report.country: report for report in country_reports}
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        report = report_by_country.get(country)
        if report is None:
            continue
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            grouped.setdefault(str(row["species_latin_name"]), []).append(row)
        for species_name, species_rows in sorted(grouped.items()):
            overlapping = 0
            non_overlapping = 0
            noncomparable = 0
            for human_locality in report.localities:
                matched = False
                comparable = False
                for row in species_rows:
                    animal_interval = _interval_from_row(row)
                    human_interval = _interval_from_record(human_locality)
                    if animal_interval is None or human_interval is None:
                        continue
                    comparable = True
                    if _intervals_overlap(animal_interval, human_interval):
                        matched = True
                        break
                if matched:
                    overlapping += 1
                elif comparable:
                    non_overlapping += 1
                else:
                    noncomparable += 1
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(species_rows[0]["species_common_name"]),
                    "animal_scope": str(species_rows[0]["animal_scope"]),
                    "animal_locality_count": len(species_rows),
                    "human_locality_count": len(report.localities),
                    "overlapping_human_localities": overlapping,
                    "non_overlapping_human_localities": non_overlapping,
                    "noncomparable_human_localities": noncomparable,
                    "assignment_confidence": str(species_rows[0]["country_assignment_confidence"]),
                    "overlap_status": _overlap_status(overlapping, non_overlapping, noncomparable),
                }
            )
    return {
        "schema_version": "animal-human-chronology-overlap.v1",
        "rows": rows,
    }


def _build_animal_pollen_chronology_overlap(
    country_payloads: list[dict[str, object]],
    atlas_output_dir: Path,
) -> dict[str, object]:
    pollen_records = _load_pollen_records(atlas_output_dir)
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            grouped.setdefault(str(row["species_latin_name"]), []).append(row)
        country_pollen = [row for row in pollen_records if row["country"] == country]
        for species_name, species_rows in sorted(grouped.items()):
            overlapping = 0
            non_overlapping = 0
            noncomparable = 0
            for pollen_row in country_pollen:
                matched = False
                comparable = False
                pollen_interval = _interval_from_row(pollen_row)
                for row in species_rows:
                    animal_interval = _interval_from_row(row)
                    if animal_interval is None or pollen_interval is None:
                        continue
                    comparable = True
                    if _intervals_overlap(animal_interval, pollen_interval):
                        matched = True
                        break
                if matched:
                    overlapping += 1
                elif comparable:
                    non_overlapping += 1
                else:
                    noncomparable += 1
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(species_rows[0]["species_common_name"]),
                    "animal_scope": str(species_rows[0]["animal_scope"]),
                    "animal_locality_count": len(species_rows),
                    "pollen_record_count": len(country_pollen),
                    "overlapping_pollen_records": overlapping,
                    "non_overlapping_pollen_records": non_overlapping,
                    "noncomparable_pollen_records": noncomparable,
                    "assignment_confidence": str(species_rows[0]["country_assignment_confidence"]),
                    "overlap_status": _overlap_status(overlapping, non_overlapping, noncomparable),
                }
            )
    return {
        "schema_version": "animal-pollen-chronology-overlap.v1",
        "rows": rows,
    }


def _build_first_appearance_by_country(
    country_payloads: list[dict[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            grouped.setdefault(str(row["species_latin_name"]), []).append(row)
        for species_name, species_rows in sorted(grouped.items()):
            oldest_row = max(species_rows, key=_first_signal_bp)
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(oldest_row["species_common_name"]),
                    "animal_scope": str(oldest_row["animal_scope"]),
                    "first_signal_bp": _first_signal_bp(oldest_row),
                    "time_label": str(oldest_row["time_label"]),
                    "project_accession": str(oldest_row["project_accession"]),
                    "locality": str(oldest_row["locality"]),
                    "assignment_confidence": str(oldest_row["country_assignment_confidence"]),
                }
            )
    rows.sort(key=lambda row: (row["country"], -int(row["first_signal_bp"]), row["species_latin_name"]))
    return {
        "schema_version": "animal-first-appearance-by-country.v1",
        "rows": rows,
    }


def _build_farming_history_scenario(
    *,
    coverage_payload: dict[str, object],
    human_overlap_payload: dict[str, object],
    pollen_overlap_payload: dict[str, object],
    first_appearance_payload: dict[str, object],
) -> dict[str, object]:
    coverage_rows = [row for row in coverage_payload.get("rows", []) if isinstance(row, dict)]
    human_rows = [row for row in human_overlap_payload.get("rows", []) if isinstance(row, dict)]
    pollen_rows = [row for row in pollen_overlap_payload.get("rows", []) if isinstance(row, dict)]
    first_rows = [row for row in first_appearance_payload.get("rows", []) if isinstance(row, dict)]

    support: list[str] = []
    weak_support: list[str] = []
    non_support: list[str] = []

    if first_rows:
        earliest = first_rows[0]
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
    represented_species = {str(row["species_latin_name"]) for row in coverage_rows}
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


def _load_pollen_records(atlas_output_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for filename in (
        "nordic_pollen_sites.geojson",
        "nordic_pollen_site_sequences.geojson",
    ):
        path = atlas_output_dir / filename
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for feature in payload.get("features", []):
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties", {})
            if not isinstance(properties, dict):
                continue
            records.append(
                {
                    "country": str(properties.get("country", "")),
                    "time_start_bp": _optional_int(properties.get("time_start_bp")),
                    "time_end_bp": _optional_int(properties.get("time_end_bp")),
                    "time_mean_bp": _optional_int(properties.get("time_mean_bp")),
                    "time_label": str(properties.get("time_label", "")),
                    "source": str(properties.get("source", "")),
                    "name": str(properties.get("name", "")),
                }
            )
    return records


def _interval_from_record(record: object) -> tuple[int, int] | None:
    time_start = getattr(record, "time_start_bp", None)
    time_end = getattr(record, "time_end_bp", None)
    time_mean = getattr(record, "time_mean_bp", None)
    return _normalize_interval(time_start, time_end, time_mean)


def _interval_from_row(row: dict[str, object]) -> tuple[int, int] | None:
    return _normalize_interval(
        _optional_int(row.get("time_start_bp")),
        _optional_int(row.get("time_end_bp")),
        _optional_int(row.get("time_mean_bp")),
    )


def _normalize_interval(
    time_start: int | None,
    time_end: int | None,
    time_mean: int | None,
) -> tuple[int, int] | None:
    values = [value for value in (time_start, time_end) if value is not None]
    if values:
        return (min(values), max(values))
    if time_mean is not None:
        return (time_mean, time_mean)
    return None


def _intervals_overlap(
    left: tuple[int, int],
    right: tuple[int, int],
) -> bool:
    return max(left[0], right[0]) <= min(left[1], right[1])


def _overlap_status(
    overlapping: int,
    non_overlapping: int,
    noncomparable: int,
) -> str:
    if overlapping > 0:
        return "overlap_detected"
    if non_overlapping > 0:
        return "no_overlap_detected"
    if noncomparable > 0:
        return "chronology_not_comparable"
    return "no_context_rows"


def _first_signal_bp(row: dict[str, object]) -> int:
    candidates = [
        value
        for value in (
            _optional_int(row.get("time_start_bp")),
            _optional_int(row.get("time_end_bp")),
            _optional_int(row.get("time_mean_bp")),
        )
        if value is not None
    ]
    return max(candidates) if candidates else 0


def _optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        return int(value)
    return None


def _deduplicate_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        unique.append(line)
    return unique


def _render_country_species_coverage_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# Animal country species coverage",
        "",
        "| Country | Species | Scope | Projects | Localities | Assignment posture |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("| No country-resolved animal rows yet | - | - | 0 | 0 | - |")
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | {row['animal_scope']} | "
                f"{row['curated_project_count']} | {row['mapped_locality_count']} | "
                f"{row['assignment_confidence']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_human_overlap_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# Animal versus human chronology overlap",
        "",
        "| Country | Species | Human localities | Overlapping | Non-overlapping | Non-comparable | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("| No overlap rows | - | 0 | 0 | 0 | 0 | no_context_rows |")
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | "
                f"{row['human_locality_count']} | {row['overlapping_human_localities']} | "
                f"{row['non_overlapping_human_localities']} | {row['noncomparable_human_localities']} | "
                f"{row['overlap_status']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_pollen_overlap_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# Animal versus pollen chronology overlap",
        "",
        "| Country | Species | Pollen records | Overlapping | Non-overlapping | Non-comparable | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("| No overlap rows | - | 0 | 0 | 0 | 0 | no_context_rows |")
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | "
                f"{row['pollen_record_count']} | {row['overlapping_pollen_records']} | "
                f"{row['non_overlapping_pollen_records']} | {row['noncomparable_pollen_records']} | "
                f"{row['overlap_status']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_first_appearance_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# First animal appearance by country",
        "",
        "| Country | Species | First signal BP | Source project | Assignment posture |",
        "| --- | --- | ---: | --- | --- |",
    ]
    if not rows:
        lines.append("| No first-appearance rows | - | 0 | - | - |")
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | {row['first_signal_bp']} | "
                f"{row['project_accession']} | {row['assignment_confidence']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_scenario_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Nordic farming history scenario",
        "",
        payload["question"],
        "",
        "## Support",
        "",
    ]
    lines.extend(f"- {line}" for line in payload.get("support_statements", []))
    lines.extend(["", "## Weak support", ""])
    lines.extend(f"- {line}" for line in payload.get("weak_support_statements", []))
    lines.extend(["", "## Non-support", ""])
    lines.extend(f"- {line}" for line in payload.get("non_support_statements", []))
    lines.append("")
    return "\n".join(lines)
