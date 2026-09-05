from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.core.files import write_json

from .access import build_sead_access_model_packet, render_sead_access_model_markdown
from .legibility import (
    build_sead_evidence_legibility_review,
    render_sead_evidence_legibility_review_markdown,
)
from .recovery import (
    build_sead_recovery_requirements,
    render_sead_recovery_requirements_markdown,
)
from .temporal import build_sead_temporal_review, render_sead_temporal_review_markdown


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
    evidence_review = build_sead_evidence_legibility_review(rows, records)
    recovery_requirements = build_sead_recovery_requirements(
        access_model_packet=access_model,
        evidence_legibility_review=evidence_review,
    )
    payload_specs = (
        (
            "temporal_review",
            temporal_review,
            render_sead_temporal_review_markdown(temporal_review),
            render_review_csv(cast(list[dict[str, object]], temporal_review["rows"])),
        ),
        (
            "access_model",
            access_model,
            render_sead_access_model_markdown(access_model),
            render_review_csv(cast(list[dict[str, object]], access_model["rows"])),
        ),
        (
            "evidence_legibility_review",
            evidence_review,
            render_sead_evidence_legibility_review_markdown(evidence_review),
            render_review_csv(cast(list[dict[str, object]], evidence_review["rows"])),
        ),
        (
            "recovery_requirements",
            recovery_requirements,
            render_sead_recovery_requirements_markdown(recovery_requirements),
            render_review_csv(
                cast(list[dict[str, object]], recovery_requirements["rows"])
            ),
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


def render_review_csv(rows: list[dict[str, object]]) -> str:
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
