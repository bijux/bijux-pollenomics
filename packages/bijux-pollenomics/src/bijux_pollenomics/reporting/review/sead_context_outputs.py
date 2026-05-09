from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "build_repository_sead_legibility_review",
    "render_repository_sead_legibility_review_markdown",
]


def build_repository_sead_legibility_review(data_root: Path) -> dict[str, object]:
    """Build one report-root review of current SEAD legibility and access posture."""
    data_root = Path(data_root)
    evidence_review = _load_json_or_default(
        data_root / "sead" / "review" / "evidence_legibility_review.json"
    )
    access_model = _load_json_or_default(
        data_root / "sead" / "review" / "access_model.json"
    )
    recovery_roadmap = _load_json_or_default(
        data_root / "sead" / "review" / "recovery_roadmap.json"
    )
    temporal_review = _load_json_or_default(
        data_root / "sead" / "review" / "temporal_review.json"
    )
    return {
        "schema_version": "repository-sead-legibility-review.v1",
        "source_family": "sead",
        "display_name": "SEAD archaeology context",
        "current_posture": "contextual_archaeology_layer_with_explicit_temporal_and_access_limits",
        "row_count": int(evidence_review.get("row_count", 0)),
        "normalization_risk_counts": dict(
            evidence_review.get("normalization_risk_counts", {})
            if isinstance(evidence_review.get("normalization_risk_counts"), dict)
            else {}
        ),
        "access_visibility_counts": dict(
            access_model.get("access_visibility_counts", {})
            if isinstance(access_model.get("access_visibility_counts"), dict)
            else {}
        ),
        "comparability_posture_counts": dict(
            temporal_review.get("comparability_posture_counts", {})
            if isinstance(temporal_review.get("comparability_posture_counts"), dict)
            else {}
        ),
        "direct_links": {
            "source_page": "docs/02-bijux-pollenomics-data/sources/sead.md",
            "handbook_page": "docs/02-bijux-pollenomics-data/sources/sead-handbook.md",
            "normalized_output_page": "docs/02-bijux-pollenomics-data/outputs/normalized-sead.md",
            "access_model": "data/sead/review/access_model.json",
            "evidence_review": "data/sead/review/evidence_legibility_review.json",
            "recovery_roadmap": "data/sead/review/recovery_roadmap.json",
        },
        "roadmap_rows": list(recovery_roadmap.get("rows", []))
        if isinstance(recovery_roadmap.get("rows"), list)
        else [],
    }


def render_repository_sead_legibility_review_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository SEAD legibility review",
        "",
        "This report-root packet explains what the repository can currently claim about SEAD and what still depends on thinner source capture or upstream inspection.",
        "",
        f"- Source family: `{payload['display_name']}`",
        f"- Current posture: `{payload['current_posture']}`",
        f"- Reviewed rows: `{payload['row_count']}`",
        "",
        "## Normalization Risk",
        "",
    ]
    for key, value in sorted(
        dict(payload.get("normalization_risk_counts", {})).items()
    ):
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "## Access Visibility",
            "",
        ]
    )
    for key, value in sorted(dict(payload.get("access_visibility_counts", {})).items()):
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "## Temporal Postures",
            "",
        ]
    )
    for key, value in sorted(
        dict(payload.get("comparability_posture_counts", {})).items()
    ):
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "## Direct Links",
            "",
        ]
    )
    for key, value in dict(payload.get("direct_links", {})).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Recovery Roadmap",
            "",
            "| Deliverable | Goal | Completion signal |",
            "| --- | --- | --- |",
        ]
    )
    for row in payload.get("roadmap_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| {row.get('deliverable_key', '')} | {row.get('goal', '')} | {row.get('completion_signal', '')} |"
        )
    lines.append("")
    return "\n".join(lines)


def _load_json_or_default(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}
