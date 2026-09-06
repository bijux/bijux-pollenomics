from __future__ import annotations

from typing import cast

from ....adna.governance.audit_catalogs.contracts import AnimalOutputHonesty


def _render_country_species_coverage_markdown(payload: dict[str, object]) -> str:
    rows = [
        row
        for row in cast(list[object], payload.get("rows", []))
        if isinstance(row, dict)
    ]
    lines = [
        "# Animal country species coverage",
        "",
        "| Country | Species | Scope | Sample rows | Localities | Sample evidence | Site evidence | Chronology evidence | Coordinate evidence | Exact coordinates | Approximate coordinates | Unresolved rows | Assignment posture |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append(
            "| No country-resolved animal rows yet | - | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |"
        )
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | {row['animal_scope']} | "
                f"{row['sample_row_count']} | {row['mapped_locality_count']} | "
                f"{row['sample_lineage_backed_sample_count']} | "
                f"{row['site_evidence_backed_sample_count']} | "
                f"{row['chronology_provenance_backed_sample_count']} | "
                f"{row['coordinate_provenance_backed_sample_count']} | "
                f"{row['exact_coordinate_sample_count']} | "
                f"{row['approximate_coordinate_sample_count']} | "
                f"{row['unresolved_sample_count']} | "
                f"{row['assignment_confidence']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_human_overlap_markdown(payload: dict[str, object]) -> str:
    rows = [
        row
        for row in cast(list[object], payload.get("rows", []))
        if isinstance(row, dict)
    ]
    lines = [
        "# Animal versus human chronology overlap",
        "",
        _comparison_disposition_line(payload),
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
    rows = [
        row
        for row in cast(list[object], payload.get("rows", []))
        if isinstance(row, dict)
    ]
    lines = [
        "# Animal versus pollen chronology overlap",
        "",
        _comparison_disposition_line(payload),
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


def _comparison_disposition_line(payload: dict[str, object]) -> str:
    contract = payload.get("comparison_contract")
    disposition = payload.get("comparison_disposition")
    if not isinstance(contract, dict) or not isinstance(disposition, dict):
        raise ValueError("comparison payload is missing its governing contract")
    return (
        f"- Contract: `{contract['contract_id']}@{contract['contract_version']}`; "
        f"status: `{disposition['status']}`; right-record comparison denominator: "
        f"`{disposition['right_record_comparison_denominator']}`; comparable "
        "right-record comparison denominator: "
        f"`{disposition['comparable_right_record_comparison_denominator']}`; this "
        "exploratory comparison requires "
        "qualified scientific review and cannot establish migration or causation."
    )


def _render_first_appearance_markdown(payload: dict[str, object]) -> str:
    rows = [
        row
        for row in cast(list[object], payload.get("rows", []))
        if isinstance(row, dict)
    ]
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


def _render_animal_atlas_readiness_markdown(payload: dict[str, object]) -> str:
    rows = [
        row
        for row in cast(list[object], payload.get("rows", []))
        if isinstance(row, dict)
    ]
    lines = [
        "# Animal atlas readiness",
        "",
        f"- Status counts: `{payload.get('status_counts', {})}`",
        "",
        "| Species | Status | Candidate points | Mapped samples | Blocked samples | Unresolved samples | Mappable coordinate provenance | Refused coordinate provenance | Coordinate-provenance denominator | Mappable share | Publication share of mappable coordinates | Reason |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append(
            "| No readiness rows yet | absent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | N/A | N/A | no tracked sample rows |"
        )
    else:
        for row in rows:
            lines.append(
                f"| {row['species_latin_name']} | {row['readiness_status']} | "
                f"{row['candidate_point_count']} | {row['mapped_sample_count']} | "
                f"{row['blocked_sample_count']} | {row['unresolved_sample_count']} | "
                f"{row['coordinate_mappable_provenance_count']} | "
                f"{row['coordinate_refused_provenance_count']} | "
                f"{row['coordinate_provenance_denominator']} | "
                f"{_format_nullable_share(row['coordinate_mappable_share'])} | "
                f"{_format_nullable_share(row['publication_share_of_mappable_coordinates'])} | "
                f"{row['status_reason']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _format_nullable_share(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (float, int, str)):
        return f"{float(value):.4f}"
    raise TypeError(f"Expected numeric share, got {type(value).__name__}")


def _render_output_honesty_markdown(payload: AnimalOutputHonesty) -> str:
    lines = [
        "# Animal output honesty",
        "",
        f"- Tracked sample rows: `{payload['totals']['tracked_sample_count']}`",
        f"- Mapped sample rows: `{payload['totals']['mapped_sample_count']}`",
        f"- Blocked sample rows: `{payload['totals']['blocked_sample_count']}`",
        f"- Unresolved sample rows: `{payload['totals']['unresolved_sample_count']}`",
        "",
        "| Species | Tracked samples | Mapped samples | Blocked samples | Unresolved samples | Country-published samples |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['tracked_sample_count']} | "
            f"{row['mapped_sample_count']} | {row['blocked_sample_count']} | "
            f"{row['unresolved_sample_count']} | {row['country_published_sample_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_animal_atlas_exclusion_report_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal atlas exclusion report",
        "",
        f"- Excluded tracked sample rows: `{payload['row_count']}`",
        "",
        "| Species | Project | Sample record | Locality | Inclusion status | Mapping posture | Exclusion reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    rows = [
        row
        for row in cast(list[object], payload.get("rows", []))
        if isinstance(row, dict)
    ]
    if not rows:
        lines.append("| No excluded rows | - | - | - | - | - | - |")
    else:
        for row in rows:
            lines.append(
                f"| {row['species_latin_name']} | {row['project_accession']} | "
                f"{row['sample_record_id']} | {row['locality']} | "
                f"{row['inclusion_status']} | {row['mapping_posture']} | "
                f"{row['exclusion_reason']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_scenario_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Nordic farming history scenario",
        "",
        cast(str, payload["question"]),
        "",
        "## Support",
        "",
    ]
    lines.extend(
        f"- {line}" for line in cast(list[str], payload.get("support_statements", []))
    )
    lines.extend(["", "## Weak support", ""])
    lines.extend(
        f"- {line}"
        for line in cast(list[str], payload.get("weak_support_statements", []))
    )
    lines.extend(["", "## Non-support", ""])
    lines.extend(
        f"- {line}"
        for line in cast(list[str], payload.get("non_support_statements", []))
    )
    lines.append("")
    return "\n".join(lines)
