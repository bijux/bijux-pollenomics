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
    source_paths = (
        data_root / "sead" / "review" / "evidence_legibility_review.json",
        data_root / "sead" / "review" / "access_model.json",
        data_root / "sead" / "review" / "recovery_requirements.json",
        data_root / "sead" / "review" / "temporal_review.json",
    )
    present = tuple(path.is_file() for path in source_paths)
    if any(present) and not all(present):
        raise ValueError("SEAD legibility review source set is incomplete")
    evidence_review = _load_json_or_default(source_paths[0])
    access_model = _load_json_or_default(source_paths[1])
    recovery_requirements = _load_json_or_default(source_paths[2])
    temporal_review = _load_json_or_default(source_paths[3])
    row_count = _nonnegative_count(evidence_review.get("row_count", 0), "row_count")
    normalization_risk_counts = _count_fields(
        evidence_review.get("normalization_risk_counts", {}),
        "normalization_risk_counts",
    )
    access_visibility_counts = _count_fields(
        access_model.get("access_visibility_counts", {}),
        "access_visibility_counts",
    )
    comparability_posture_counts = _count_fields(
        temporal_review.get("comparability_posture_counts", {}),
        "comparability_posture_counts",
    )
    requirement_rows = _requirement_rows(recovery_requirements.get("rows", []))
    if (
        sum(normalization_risk_counts.values()) != row_count
        or sum(access_visibility_counts.values()) != row_count
        or sum(comparability_posture_counts.values()) != row_count
        or _nonnegative_count(access_model.get("row_count", 0), "access row_count")
        != row_count
        or _nonnegative_count(temporal_review.get("row_count", 0), "temporal row_count")
        != row_count
        or _nonnegative_count(
            recovery_requirements.get("row_count", 0), "recovery row_count"
        )
        != len(requirement_rows)
    ):
        raise ValueError("SEAD legibility review source counts do not reconcile")
    return {
        "schema_version": "repository-sead-legibility-review.v1",
        "source_family": "sead",
        "display_name": "SEAD archaeology context",
        "current_posture": "contextual_archaeology_layer_with_explicit_temporal_and_access_limits",
        "row_count": row_count,
        "normalization_risk_counts": normalization_risk_counts,
        "access_visibility_counts": access_visibility_counts,
        "comparability_posture_counts": comparability_posture_counts,
        "direct_links": {
            "source_page": "docs/public/pollenomics-data/sources/sead.md",
            "handbook_page": "docs/public/pollenomics-data/sources/sead-handbook.md",
            "normalized_output_page": "docs/public/pollenomics-data/publications/sead-exports.md",
            "access_model": "data/sead/review/access_model.json",
            "evidence_review": "data/sead/review/evidence_legibility_review.json",
            "recovery_requirements": "data/sead/review/recovery_requirements.json",
        },
        "requirement_rows": requirement_rows,
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
        _count_fields(
            payload.get("normalization_risk_counts", {}), "normalization_risk_counts"
        ).items()
    ):
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "## Access Visibility",
            "",
        ]
    )
    for key, value in sorted(
        _count_fields(
            payload.get("access_visibility_counts", {}), "access_visibility_counts"
        ).items()
    ):
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "## Temporal Postures",
            "",
        ]
    )
    for key, value in sorted(
        _count_fields(
            payload.get("comparability_posture_counts", {}),
            "comparability_posture_counts",
        ).items()
    ):
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "## Direct Links",
            "",
        ]
    )
    for key, link_text in _text_fields(
        payload.get("direct_links", {}), "direct_links"
    ).items():
        lines.append(f"- {key}: `{link_text}`")
    lines.extend(
        [
            "",
            "## Recovery Requirements",
            "",
            "| Requirement | Required evidence | Satisfaction signal |",
            "| --- | --- | --- |",
        ]
    )
    for row in _requirement_rows(payload.get("requirement_rows", [])):
        lines.append(
            f"| {row.get('requirement_key', '')} | {row.get('required_evidence', '')} | {row.get('satisfaction_signal', '')} |"
        )
    lines.append("")
    return "\n".join(lines)


def _load_json_or_default(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(
            f"SEAD legibility review source must be an object: {path.name}"
        )
    fields: dict[str, object] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise ValueError(
                f"SEAD legibility review source key is invalid: {path.name}"
            )
        fields[key] = value
    return fields


def _nonnegative_count(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(
            f"SEAD legibility review {field} must be a nonnegative integer"
        )
    return value


def _count_fields(value: object, field: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError(f"SEAD legibility review {field} must be an object")
    counts: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"SEAD legibility review {field} key is invalid")
        counts[key] = _nonnegative_count(count, field)
    return counts


def _text_fields(value: object, field: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"SEAD legibility review {field} must be an object")
    links: dict[str, str] = {}
    for key, text in value.items():
        if not isinstance(key, str) or not isinstance(text, str):
            raise ValueError(f"SEAD legibility review {field} entry is invalid")
        links[key] = text
    return links


def _requirement_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("SEAD legibility review requirement_rows must be a list")
    rows: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("SEAD legibility review requirement row must be an object")
        row: dict[str, object] = {}
        for key, member in item.items():
            if not isinstance(key, str):
                raise ValueError("SEAD legibility review requirement key is invalid")
            row[key] = member
        for field in ("requirement_key", "required_evidence", "satisfaction_signal"):
            if not isinstance(row.get(field), str):
                raise ValueError(f"SEAD legibility review {field} must be text")
        rows.append(row)
    return rows
