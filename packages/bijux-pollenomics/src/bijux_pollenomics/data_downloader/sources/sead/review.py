from __future__ import annotations

from datetime import date
import json
from pathlib import Path

from ....core.files import write_json
from ...models import ContextPointRecord
from .access import build_sead_site_access_model

__all__ = [
    "build_sead_access_model_packet",
    "build_sead_evidence_legibility_review",
    "build_sead_recovery_roadmap",
    "build_sead_temporal_review",
    "render_sead_access_model_markdown",
    "render_sead_evidence_legibility_review_markdown",
    "render_sead_recovery_roadmap_markdown",
    "render_sead_temporal_review_markdown",
    "write_sead_review_outputs",
]


def build_sead_temporal_review(
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
) -> dict[str, object]:
    """Build one governed SEAD review of temporal semantics and uncertainty."""
    record_lookup = {record.record_id: record for record in records}
    review_rows: list[dict[str, object]] = []
    posture_counts: dict[str, int] = {}
    for row in rows:
        site_id = str(row.get("site_id", "")).strip()
        record = record_lookup.get(site_id)
        semantics = record.temporal_semantics if record is not None else {}
        posture = (
            str(semantics.get("comparability_posture", "")).strip() or "unresolved"
        )
        posture_counts[posture] = posture_counts.get(posture, 0) + 1
        review_rows.append(
            {
                "site_id": site_id,
                "site_name": str(row.get("site_name", "")).strip(),
                "country": str(record.country if record is not None else "").strip(),
                "comparability_posture": posture,
                "temporal_window_label": str(
                    semantics.get("temporal_window_label", "")
                ).strip(),
                "summary_label": str(semantics.get("summary_label", "")).strip(),
                "normalized_period_labels": list(
                    semantics.get("normalized_labels", [])
                    if isinstance(semantics.get("normalized_labels"), list)
                    else []
                ),
                "original_period_labels": list(
                    semantics.get("original_labels", [])
                    if isinstance(semantics.get("original_labels"), list)
                    else []
                ),
                "uncertainty_notes": list(
                    semantics.get("uncertainty_notes", [])
                    if isinstance(semantics.get("uncertainty_notes"), list)
                    else []
                ),
                "dating_range_count": len(row.get("dating_range_rows", []))
                if isinstance(row.get("dating_range_rows"), list)
                else 0,
                "relative_period_count": len(row.get("relative_period_rows", []))
                if isinstance(row.get("relative_period_rows"), list)
                else 0,
                "bibliography_count": len(row.get("bibliography_rows", []))
                if isinstance(row.get("bibliography_rows"), list)
                else 0,
                "comparison_note": str(semantics.get("comparison_note", "")).strip(),
            }
        )
    review_rows.sort(
        key=lambda row: (
            str(row["comparability_posture"]),
            str(row["site_name"]).casefold(),
            str(row["site_id"]),
        )
    )
    return {
        "schema_version": "sead-temporal-review.v1",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "comparability_posture_counts": posture_counts,
        "rows": review_rows,
    }


def build_sead_access_model_packet(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build one global explanation packet for SEAD access posture."""
    review_rows: list[dict[str, object]] = []
    access_visibility_counts: dict[str, int] = {}
    for row in rows:
        access_model = build_sead_site_access_model(row)
        visibility = str(access_model["access_visibility"])
        access_visibility_counts[visibility] = (
            access_visibility_counts.get(visibility, 0) + 1
        )
        review_rows.append(
            {
                "site_id": str(row.get("site_id", "")).strip(),
                "site_name": str(row.get("site_name", "")).strip(),
                "access_visibility": visibility,
                "site_page_url": str(access_model.get("site_page_url", "")).strip(),
                "reference_link_count": len(access_model.get("reference_links", []))
                if isinstance(access_model.get("reference_links"), list)
                else 0,
                "redistribution_posture": str(
                    access_model.get("redistribution_posture", "")
                ).strip(),
                "reader_action": str(access_model.get("reader_action", "")).strip(),
                "access_limits": list(access_model.get("access_limits", []))
                if isinstance(access_model.get("access_limits"), list)
                else [],
            }
        )
    review_rows.sort(
        key=lambda row: (row["access_visibility"], row["site_name"].casefold())
    )
    return {
        "schema_version": "sead-access-model.v1",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "repository_posture": "mirrored_site_inventory_and_normalized_context",
        "what_the_repository_mirrors": [
            "raw site inventory capture under data/sead/raw/",
            "normalized contextual point layers under data/sead/normalized/",
            "review packets under data/sead/review/",
        ],
        "what_the_repository_references": [
            "stable SEAD site pages when site identifiers are present",
            "stable bibliography or DOI links when they survive linked-table capture",
        ],
        "what_the_repository_does_not_redistribute": [
            "the full upstream relational SEAD database",
            "full source browsing experience beyond the linked site and reference pages",
        ],
        "access_visibility_counts": access_visibility_counts,
        "rows": review_rows,
    }


def build_sead_evidence_legibility_review(
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
) -> dict[str, object]:
    """Classify SEAD rows by temporal strength, duration weakness, access, and risk."""
    record_lookup = {record.record_id: record for record in records}
    review_rows: list[dict[str, object]] = []
    temporal_strength_counts: dict[str, int] = {}
    duration_posture_counts: dict[str, int] = {}
    access_visibility_counts: dict[str, int] = {}
    normalization_risk_counts: dict[str, int] = {}

    for row in rows:
        site_id = str(row.get("site_id", "")).strip()
        record = record_lookup.get(site_id)
        semantics = record.temporal_semantics if record is not None else {}
        posture = (
            str(semantics.get("comparability_posture", "")).strip() or "unresolved"
        )
        access_model = build_sead_site_access_model(row)
        temporal_strength = _temporal_strength_for(posture)
        duration_posture = _duration_posture_for(row, semantics)
        access_visibility = str(access_model.get("access_visibility", "")).strip()
        normalization_risk = _normalization_risk_for(
            row=row,
            posture=posture,
            access_visibility=access_visibility,
        )
        temporal_strength_counts[temporal_strength] = (
            temporal_strength_counts.get(temporal_strength, 0) + 1
        )
        duration_posture_counts[duration_posture] = (
            duration_posture_counts.get(duration_posture, 0) + 1
        )
        access_visibility_counts[access_visibility] = (
            access_visibility_counts.get(access_visibility, 0) + 1
        )
        normalization_risk_counts[normalization_risk] = (
            normalization_risk_counts.get(normalization_risk, 0) + 1
        )
        review_rows.append(
            {
                "site_id": site_id,
                "site_name": str(row.get("site_name", "")).strip(),
                "country": str(record.country if record is not None else "").strip(),
                "temporal_strength": temporal_strength,
                "duration_posture": duration_posture,
                "access_visibility": access_visibility,
                "normalization_risk": normalization_risk,
                "publication_posture": "context_layer_with_explicit_caveat",
                "site_page_url": str(access_model.get("site_page_url", "")).strip(),
                "summary_label": str(semantics.get("summary_label", "")).strip(),
                "review_note": _review_note_for(
                    temporal_strength=temporal_strength,
                    duration_posture=duration_posture,
                    access_visibility=access_visibility,
                    normalization_risk=normalization_risk,
                ),
            }
        )

    review_rows.sort(
        key=lambda row: (
            row["normalization_risk"],
            row["temporal_strength"],
            row["site_name"].casefold(),
        )
    )
    return {
        "schema_version": "sead-evidence-legibility-review.v1",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "temporal_strength_counts": temporal_strength_counts,
        "duration_posture_counts": duration_posture_counts,
        "access_visibility_counts": access_visibility_counts,
        "normalization_risk_counts": normalization_risk_counts,
        "rows": review_rows,
    }


def build_sead_recovery_roadmap(
    *,
    access_model_packet: dict[str, object],
    evidence_legibility_review: dict[str, object],
) -> dict[str, object]:
    """Turn current SEAD legibility gaps into concrete recovery deliverables."""
    high_risk_count = int(
        dict(evidence_legibility_review.get("normalization_risk_counts", {})).get(
            "high_thin_site_inventory", 0
        )
    )
    site_page_only_count = int(
        dict(access_model_packet.get("access_visibility_counts", {})).get(
            "site_page_only", 0
        )
    )
    rows = [
        {
            "deliverable_key": "linked_temporal_capture",
            "current_gap_count": high_risk_count,
            "goal": "Capture linked dating-range, relative-period, and uncertainty tables into checked-in raw SEAD inventory refreshes.",
            "completion_signal": "Checked-in raw SEAD rows carry temporal linked tables often enough that the thin-site-inventory risk no longer dominates the review packet.",
        },
        {
            "deliverable_key": "reference_link_capture",
            "current_gap_count": site_page_only_count,
            "goal": "Preserve stable bibliography or DOI links wherever SEAD linked records expose them, so readers do not have to begin every review from the generic site page.",
            "completion_signal": "The access review shows a meaningful shift away from site-page-only visibility.",
        },
        {
            "deliverable_key": "context_layer_republication",
            "current_gap_count": int(evidence_legibility_review.get("row_count", 0)),
            "goal": "Republish the normalized SEAD context layer with explicit temporal semantics, access posture, and context-only caveats on every feature.",
            "completion_signal": "Normalized and published SEAD GeoJSON no longer trigger missing-temporal-semantics findings in report review surfaces.",
        },
        {
            "deliverable_key": "published_scope_refresh",
            "current_gap_count": int(evidence_legibility_review.get("row_count", 0)),
            "goal": "Refresh published world, Europe-plus, and Nordic report bundles so SEAD appears as a bounded archaeology context layer rather than a generic environmental blob.",
            "completion_signal": "Published map and review bundles expose SEAD with stable caveats, access wording, and bounded contextual role labels.",
        },
    ]
    return {
        "schema_version": "sead-recovery-roadmap.v1",
        "generated_on": str(date.today()),
        "row_count": len(rows),
        "rows": rows,
    }


def write_sead_review_outputs(
    output_root: Path,
    *,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
) -> dict[str, str]:
    """Write SEAD review surfaces beside raw and normalized outputs."""
    review_root = Path(output_root) / "review"
    review_root.mkdir(parents=True, exist_ok=True)

    temporal_review = build_sead_temporal_review(rows, records)
    access_model = build_sead_access_model_packet(rows)
    evidence_legibility_review = build_sead_evidence_legibility_review(rows, records)
    recovery_roadmap = build_sead_recovery_roadmap(
        access_model_packet=access_model,
        evidence_legibility_review=evidence_legibility_review,
    )

    payload_specs = (
        (
            "temporal_review",
            temporal_review,
            render_sead_temporal_review_markdown(temporal_review),
            _render_review_csv(temporal_review["rows"]),
        ),
        (
            "access_model",
            access_model,
            render_sead_access_model_markdown(access_model),
            _render_review_csv(access_model["rows"]),
        ),
        (
            "evidence_legibility_review",
            evidence_legibility_review,
            render_sead_evidence_legibility_review_markdown(evidence_legibility_review),
            _render_review_csv(evidence_legibility_review["rows"]),
        ),
        (
            "recovery_roadmap",
            recovery_roadmap,
            render_sead_recovery_roadmap_markdown(recovery_roadmap),
            _render_review_csv(recovery_roadmap["rows"]),
        ),
    )
    artifact_paths: dict[str, str] = {}
    for stem, payload, markdown, csv_text in payload_specs:
        write_json(review_root / f"{stem}.json", payload)
        (review_root / f"{stem}.md").write_text(markdown, encoding="utf-8")
        (review_root / f"{stem}.csv").write_text(csv_text, encoding="utf-8")
        artifact_paths[f"{stem}_json"] = f"review/{stem}.json"
        artifact_paths[f"{stem}_markdown"] = f"review/{stem}.md"
        artifact_paths[f"{stem}_csv"] = f"review/{stem}.csv"
    return artifact_paths


def render_sead_temporal_review_markdown(payload: dict[str, object]) -> str:
    rows = payload["rows"]
    lines = [
        "# SEAD temporal review",
        "",
        "This review keeps SEAD honest about site-level time semantics. It distinguishes numeric site spans, mixed site spans plus cultural labels, and label-only rows that should not be read like sample-owned dates.",
        "",
        f"- Reviewed sites: `{payload['row_count']}`",
    ]
    posture_counts = payload.get("comparability_posture_counts", {})
    if isinstance(posture_counts, dict):
        for key in sorted(posture_counts):
            lines.append(f"- {key.replace('_', ' ')}: `{posture_counts[key]}`")
    lines.extend(
        [
            "",
            "| Site | Country | Comparability posture | Time summary | Normalized period labels | Uncertainty notes |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['site_name']} (`{row['site_id']}`) | {row['country']} | "
            f"{row['comparability_posture']} | {row['summary_label']} | "
            f"{', '.join(row['normalized_period_labels']) or 'None'} | "
            f"{' | '.join(row['uncertainty_notes']) or 'None'} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_sead_access_model_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# SEAD access model",
        "",
        "This packet states what the repository mirrors from SEAD, what it only references, and where readers still need to inspect upstream SEAD surfaces directly.",
        "",
        f"- Reviewed sites: `{payload['row_count']}`",
        f"- Repository posture: `{payload['repository_posture']}`",
        "",
        "## Repository Mirrors",
        "",
    ]
    for row in payload["what_the_repository_mirrors"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Repository References",
            "",
        ]
    )
    for row in payload["what_the_repository_references"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Repository Does Not Redistribute",
            "",
        ]
    )
    for row in payload["what_the_repository_does_not_redistribute"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Access Visibility",
            "",
        ]
    )
    counts = payload.get("access_visibility_counts", {})
    if isinstance(counts, dict):
        for key in sorted(counts):
            lines.append(f"- {key.replace('_', ' ')}: `{counts[key]}`")
    lines.extend(
        [
            "",
            "| Site | Access visibility | Reference links | Stable site page |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['site_name']} (`{row['site_id']}`) | {row['access_visibility']} | "
            f"{row['reference_link_count']} | {row['site_page_url'] or 'None'} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_sead_evidence_legibility_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# SEAD evidence legibility review",
        "",
        "This review classifies SEAD rows by temporal strength, duration posture, access visibility, and normalization risk so the contextual layer can be published honestly.",
        "",
        f"- Reviewed sites: `{payload['row_count']}`",
        "",
        "## Risk Counts",
        "",
    ]
    counts = payload.get("normalization_risk_counts", {})
    if isinstance(counts, dict):
        for key in sorted(counts):
            lines.append(f"- {key.replace('_', ' ')}: `{counts[key]}`")
    lines.extend(
        [
            "",
            "| Site | Temporal strength | Duration posture | Access visibility | Normalization risk | Review note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['site_name']} (`{row['site_id']}`) | {row['temporal_strength']} | "
            f"{row['duration_posture']} | {row['access_visibility']} | "
            f"{row['normalization_risk']} | {row['review_note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_sead_recovery_roadmap_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# SEAD recovery roadmap",
        "",
        "This roadmap turns SEAD from a merely present source family into a scientifically legible and operationally trustworthy context program.",
        "",
        "| Deliverable | Current gap count | Goal | Completion signal |",
        "| --- | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['deliverable_key']} | {row['current_gap_count']} | "
            f"{row['goal']} | {row['completion_signal']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_review_csv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "row_count\n"
    fieldnames = list(rows[0].keys())
    lines = [",".join(fieldnames)]
    for row in rows:
        values = []
        for field in fieldnames:
            value = row.get(field)
            if isinstance(value, list):
                values.append(json.dumps(value, ensure_ascii=False))
            else:
                text = str(value).replace('"', '""')
                values.append(f'"{text}"' if "," in text or '"' in text else text)
        lines.append(",".join(values))
    lines.append("")
    return "\n".join(lines)


def _temporal_strength_for(posture: str) -> str:
    if posture == "numeric_interval":
        return "numeric_site_span"
    if posture in {"numeric_interval_with_caveat", "mixed_interval_and_context"}:
        return "numeric_span_with_contextual_caveat"
    if posture == "contextual_label_only":
        return "period_label_only"
    return "inventory_only_or_unresolved"


def _duration_posture_for(
    row: dict[str, object],
    semantics: dict[str, object],
) -> str:
    time_start_bp = semantics.get("time_start_bp")
    time_end_bp = semantics.get("time_end_bp")
    if isinstance(time_start_bp, int) and isinstance(time_end_bp, int):
        if time_start_bp == time_end_bp:
            return "point_like_or_single_year"
        return "duration_span_visible"
    contextual_start = row.get("contextual_time_start_bp")
    contextual_end = row.get("contextual_time_end_bp")
    if isinstance(contextual_start, int) and isinstance(contextual_end, int):
        return "broad_context_duration"
    return "duration_not_available"


def _normalization_risk_for(
    *,
    row: dict[str, object],
    posture: str,
    access_visibility: str,
) -> str:
    if posture == "unresolved" and not isinstance(row.get("dating_range_rows"), list):
        return "high_thin_site_inventory"
    if posture == "contextual_label_only":
        return "medium_period_label_interpretation"
    if posture in {"numeric_interval_with_caveat", "mixed_interval_and_context"}:
        return "medium_contextual_numeric_mix"
    if access_visibility == "site_page_only":
        return "medium_access_constrained"
    return "low_contextually_bounded"


def _review_note_for(
    *,
    temporal_strength: str,
    duration_posture: str,
    access_visibility: str,
    normalization_risk: str,
) -> str:
    if normalization_risk == "high_thin_site_inventory":
        return "Current checked-in SEAD capture is too thin to support stronger temporal interpretation."
    if access_visibility == "site_page_only":
        return "Readers may need to inspect the upstream SEAD site page because the repository does not currently expose stronger reference links."
    if temporal_strength == "period_label_only":
        return "This row should stay a contextual period label, not a direct date."
    if duration_posture == "duration_span_visible":
        return "This row carries a visible site span, but the span still belongs to archaeology context rather than a sample-owned event."
    return "This row is publishable only as contextual archaeology support with its stated caveats."
