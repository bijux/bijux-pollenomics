from __future__ import annotations

from collections.abc import Mapping
import csv
import math
from pathlib import Path
from typing import Any, cast


def _markdown_number(value: object) -> str:
    if value is None:
        return "N/A"
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise TypeError(f"Modeled value must be numeric or None: {value!r}")
    return f"{value:.3f}"


def write_json(path: Path, payload: dict[str, object], *, json_module: Any) -> None:
    path.write_text(json_module.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, payload: dict[str, object]) -> None:
    rows = cast(list[dict[str, Any]], payload["rows"])
    fieldnames = tuple(rows[0]) if rows else ()
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, object]) -> str:
    decisions = cast(list[dict[str, Any]], payload["target_decisions"])
    target_rows = "\n".join(
        f"| {row['requested_name']} | {row['target_class']} | {row['lake_decision']} | "
        f"{row['registry_id'] or 'not_applicable'} | {row['lake_area_km2'] if row['lake_area_km2'] is not None else 'not_applicable'} | "
        f"{row['landclim_coverage_posture']} | {row['landclim_window_count']} | "
        f"{row['decision_reason']} |"
        for row in decisions
    )
    most_recent_rows: dict[str, dict[str, Any]] = {}
    rows = cast(list[dict[str, Any]], payload["rows"])
    for row in rows:
        target_name = str(row["target_name"])
        if target_name not in most_recent_rows or int(row["time_start_bp"]) < int(
            most_recent_rows[target_name]["time_start_bp"]
        ):
            most_recent_rows[target_name] = row
    recent_rows = sorted(most_recent_rows.values(), key=lambda row: row["target_name"])
    synthesis_rows = "\n".join(
        f"| {row['target_name']} | {row['time_label']} | {row['quality_class']} | "
        f"{_markdown_number(row['forest_cover'])} | "
        f"{_markdown_number(row['open_land_cover'])} | "
        f"{_markdown_number(row['agricultural_land_cover'])} | "
        f"{_markdown_number(row['cereal_type_pollen_cover'])} | "
        f"{_markdown_number(row['rye_pollen_cover'])} | "
        f"{row['sead_site_count_20km']} | {row['human_adna_locality_count_20km']} | "
        f"{row['animal_adna_locality_count_20km']} | {row['cross_proxy_posture']} |"
        for row in recent_rows
    )
    methodology = cast(Mapping[str, object], payload["methodology"])
    return f"""# Southern Sweden temporal land-use synthesis

This surface joins published LandClim time windows to temporally compatible
archaeology and ancient-DNA context around the complete ranked Sweden lake set
and the governed southern Sweden wetland contexts. It makes both modeled-grid
coverage and lake inclusion explicit instead of silently dropping targets.

The governed LandClim grid covers **{payload["landclim_covered_target_count"]} of
{payload["target_count"]} targets**. The remaining
**{payload["landclim_uncovered_target_count"]} targets** stay visible below with
no modeled windows rather than receiving inferred values.

## Governed Target Decisions

| Requested target | Class | Decision | SVAR ID | Area km² | LandClim coverage | Windows | Reason |
| --- | --- | --- | --- | ---: | --- | ---: | --- |
{target_rows}

Gullåkra and Vesums mossar remain in this synthesis because the Höje å
archaeological report documents them as wetland project areas with archaeological
context. They are excluded only from the lake-sampling ranking.

## Reading The Joined Evidence

- {methodology["land_cover_rule"]}
- {methodology["cereal_rule"]}
- {methodology["temporal_join_rule"]}
- {methodology["target_coverage_rule"]}
- {methodology["interpretation_rule"]}

## Most Recent Modeled Window

| Target | Window | Quality | Forest | Open land | Agricultural land | Cerealia-type pollen | Rye pollen | SEAD sites | Human aDNA localities | Animal aDNA localities | Posture |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{synthesis_rows}

This compact table shows one recent modeled window per covered target. The
machine-readable JSON and CSV retain all **{payload["time_row_count"]}** published
target-window rows for time navigation and analysis.
"""
