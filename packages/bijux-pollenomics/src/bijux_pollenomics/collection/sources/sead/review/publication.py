from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.core.files import write_json

from .access import build_sead_access_model_packet, render_sead_access_model_markdown
from .inventory import validate_site_identities
from .legibility import (
    build_sead_evidence_legibility_review,
    render_sead_evidence_legibility_review_markdown,
)
from .recovery import (
    build_sead_recovery_requirements,
    render_sead_recovery_requirements_markdown,
)
from .temporal import build_sead_temporal_review, render_sead_temporal_review_markdown

_LINEAGE_FIELDS = (
    "source_run_id",
    "build_id",
    "acquisition_manifest_sha256",
    "parent_admission_sha256",
)


def write_sead_review_outputs(
    output_root: Path,
    *,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
    lineage: Mapping[str, object] | None = None,
    generated_on: date | None = None,
) -> dict[str, str]:
    """Write SEAD review surfaces beside raw and normalized outputs."""
    validate_site_identities(rows)
    lineage_fields = _review_lineage_fields(lineage)
    review_root = Path(output_root) / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    temporal_review = build_sead_temporal_review(
        rows, records, generated_on=generated_on
    )
    access_model = build_sead_access_model_packet(rows, generated_on=generated_on)
    evidence_review = build_sead_evidence_legibility_review(
        rows, records, generated_on=generated_on
    )
    recovery_requirements = build_sead_recovery_requirements(
        access_model_packet=access_model,
        evidence_legibility_review=evidence_review,
        generated_on=generated_on,
    )
    for payload in (
        temporal_review,
        access_model,
        evidence_review,
        recovery_requirements,
    ):
        payload["lineage"] = dict(lineage_fields)
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


def review_lineage_from_admission(
    admission: Mapping[str, object],
) -> dict[str, str]:
    """Bind review outputs to one validated raw-acquisition admission."""
    lineage = {
        "source_run_id": admission.get("run_id"),
        "build_id": admission.get("build_id"),
        "acquisition_manifest_sha256": admission.get("acquisition_manifest_sha256"),
        "parent_admission_sha256": admission.get("parent_admission_sha256"),
    }
    return cast(dict[str, str], _review_lineage_fields(lineage, allow_null=False))


def _review_lineage_fields(
    lineage: Mapping[str, object] | None,
    *,
    allow_null: bool = True,
) -> dict[str, object]:
    if lineage is None:
        if not allow_null:
            raise ValueError("SEAD review lineage is required")
        return dict.fromkeys(_LINEAGE_FIELDS)
    normalized: dict[str, object] = {}
    for field in _LINEAGE_FIELDS:
        value = lineage.get(field)
        if value is None and allow_null:
            normalized[field] = None
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"SEAD review lineage {field} is missing")
        normalized[field] = value.strip()
    return normalized


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
