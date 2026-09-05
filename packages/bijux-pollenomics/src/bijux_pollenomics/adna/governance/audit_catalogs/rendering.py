from __future__ import annotations

from .contracts import (
    AnimalOutputHonesty,
    AtlasAccountability,
    CoordinateCaveatSurface,
    PublicAnimalOutputAudit,
)


def render_public_animal_output_audit_markdown(payload: PublicAnimalOutputAudit) -> str:
    """Render the shipped public animal-output audit as reader-facing markdown."""
    rows = payload["species_rows"]
    atlas_locality_total = sum(row["atlas_locality_count"] for row in rows)
    country_output_total = sum(row["country_output_count"] for row in rows)
    lines = [
        "# Animal output audit",
        "",
        f"- Report root: `{payload['report_root']}`",
        f"- Atlas bundle present: `{str(payload['atlas_bundle_present']).lower()}`",
        f"- Country bundle count: `{payload['country_bundle_count']}`",
        f"- Point candidate count: `{payload['point_candidate_count']}`",
        f"- Candidate rows with full traceability: `{payload['candidate_rows_with_full_traceability']}`",
        f"- Tracked sample rows: `{payload['tracked_sample_count']}`",
        f"- Mapped sample rows: `{payload['mapped_sample_count']}`",
        f"- Blocked sample rows: `{payload['blocked_sample_count']}`",
        f"- Unresolved sample rows: `{payload['unresolved_sample_count']}`",
        f"- Country-published sample rows: `{payload['country_published_sample_count']}`",
        "",
        "## Species output counts",
        "",
        "| Species | Atlas localities | Country outputs | Locality artifact shipped | Nordic lead count |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['species_latin_name']} | {row['atlas_locality_count']} | "
            f"{row['country_output_count']} | "
            f"{str(row['normalized_locality_artifact_present']).lower()} | "
            f"{row['nordic_unmapped_lead_count']} |"
        )
    lines.append("")
    if atlas_locality_total == 0 and country_output_total == 0:
        lines.extend(
            [
                (
                    "The current public report tree still ships no mapped non-human animal atlas "
                    "localities or country bundles. The species rows above stay zero until those "
                    "artifacts become real tracked report outputs."
                ),
                "",
            ]
        )
    elif payload["point_candidate_count"] <= 2:
        lines.extend(
            [
                (
                    f"The atlas still rests on only `{payload['point_candidate_count']}` candidate "
                    "row(s), so the public surface must be read as a traceable pilot rather than "
                    "a broad animal coverage claim."
                ),
                "",
            ]
        )
    elif country_output_total == 0:
        lines.extend(
            [
                (
                    f"The current public report tree ships `{atlas_locality_total}` mapped "
                    "non-human animal atlas localities across the species table above, but "
                    "country-bundle animal outputs remain zero until those narrower surfaces "
                    "become real tracked report outputs."
                ),
                "",
            ]
        )
    else:
        lines.extend(
            [
                (
                    f"The current public report tree ships `{atlas_locality_total}` mapped "
                    "non-human animal atlas localities and "
                    f"`{country_output_total}` country-resolved animal output hits across the "
                    "species table above. Those counts still need to be read beside blocked and "
                    "unresolved sample totals rather than as a standalone readiness claim."
                ),
                "",
            ]
        )
    return "\n".join(lines)


def render_public_animal_output_honesty_markdown(payload: AnimalOutputHonesty) -> str:
    """Render one honesty review for tracked versus published animal sample counts."""
    totals = payload["totals"]
    rows = payload["rows"]
    lines = [
        "# Animal output honesty",
        "",
        f"- Tracked sample rows: `{totals['tracked_sample_count']}`",
        f"- Mapped sample rows: `{totals['mapped_sample_count']}`",
        f"- Blocked sample rows: `{totals['blocked_sample_count']}`",
        f"- Unresolved sample rows: `{totals['unresolved_sample_count']}`",
        f"- Country-published sample rows: `{totals['country_published_sample_count']}`",
        "",
        "| Species | Tracked samples | Mapped samples | Blocked samples | Unresolved samples | Country-published samples | Region-refused rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not rows:
        lines.append("| No tracked animal sample rows yet | 0 | 0 | 0 | 0 | 0 | 0 |")
    else:
        for row in rows:
            lines.append(
                f"| {row['species_latin_name']} | {row['tracked_sample_count']} | "
                f"{row['mapped_sample_count']} | {row['blocked_sample_count']} | "
                f"{row['unresolved_sample_count']} | {row['country_published_sample_count']} | "
                f"{row['region_refused_count']} |"
            )
    lines.append("")
    return "\n".join(lines)


def render_animal_atlas_candidate_accountability_markdown(
    payload: AtlasAccountability,
) -> str:
    """Render one accountability table for final atlas candidate rows."""
    lines = [
        "# Animal atlas candidate accountability",
        "",
        f"- Candidate rows: `{payload['candidate_row_count']}`",
        f"- Fully accountable rows: `{payload['passed_row_count']}`",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        "",
        "| Species | Project | Sample rows | Sample lineage | Site evidence | Chronology evidence | Coordinate evidence | Locality match |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{str(row['sample_rows_present']).lower()} | "
            f"{str(row['sample_lineage_present']).lower()} | "
            f"{str(row['site_evidence_present']).lower()} | "
            f"{str(row['chronology_evidence_present']).lower()} | "
            f"{str(row['coordinate_provenance_present']).lower()} | "
            f"{str(row['sample_locality_matches_site_record']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_coordinate_confidence_scale_markdown() -> str:
    """Render the reader-visible animal coordinate confidence scale."""
    return (
        "# Coordinate confidence scale\n\n"
        "- `exact`: direct published coordinates or explicit archive coordinate pairs.\n"
        "- `approximate`: named-place geocoding where the place is explicit but the "
        "archived source does not ship the exact point pair.\n"
        "- `inferred`: indirect coordinate derivation retained only for non-public "
        "internal context.\n"
        "- `withheld`: the repository refuses point-level mapping because the current "
        "geography is unresolved or region-only.\n"
        "- `unknown`: legacy or foreign records where the confidence basis is not yet "
        "normalized.\n\n"
        "Animal point publication is currently allowed only for rows whose coordinate "
        "provenance keeps an explicit basis and whose mapping posture is "
        "`mappable_point`."
    )


def render_coordinate_caveat_surface_markdown(
    payload: CoordinateCaveatSurface,
) -> str:
    """Render grouped animal coordinate caveats as reader-facing markdown."""
    lines = [
        "# Coordinate caveat surface",
        "",
        f"- Direct-coordinate points: `{len(payload['direct_coordinates'])}`",
        f"- Place-name resolved points: `{len(payload['place_name_resolution'])}`",
        f"- Still-weak geography rows: `{len(payload['still_weak_geography'])}`",
        "",
        "## Direct-coordinate points",
        "",
        "| Species | Project | Site | Basis | Confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["direct_coordinates"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['site_label']} | {row['coordinate_basis']} | {row['coordinate_confidence']} |"
        )
    lines.extend(
        [
            "",
            "## Place-name resolved points",
            "",
            "| Species | Project | Site | Basis | Confidence |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["place_name_resolution"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['site_label']} | {row['coordinate_basis']} | {row['coordinate_confidence']} |"
        )
    lines.extend(
        [
            "",
            "## Still-weak geography",
            "",
            "| Species | Project | Original place text | Resolved place | Posture |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["still_weak_geography"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['original_place_text']} | {row['resolved_place_text']} | "
            f"{row['mapping_posture']} |"
        )
    return "\n".join(lines)
