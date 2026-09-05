"""Species-owned dataset and project review loading for animal atlas rows."""

from __future__ import annotations

import json
from pathlib import Path


def _load_dataset_review(species_root: Path) -> dict[str, object]:
    payload = json.loads(
        (species_root / "reports" / "support_summary.json").read_text(encoding="utf-8")
    )
    review = payload.get("dataset_review", {})
    if not isinstance(review, dict):
        raise ValueError(f"Dataset review missing for {species_root}")
    return review


def _load_review_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(
        (species_root / "review" / "species_review.json").read_text(encoding="utf-8")
    )
    lookup: dict[str, dict[str, str]] = {}
    for key in (
        "accepted_projects",
        "rejected_projects",
        "too_weak_projects",
        "comparator_projects",
        "nordic_unmapped_leads",
    ):
        rows = payload.get(key, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            accession = str(row.get("project_accession", "")).strip()
            if accession:
                lookup[accession] = {
                    "support_class": str(row.get("support_class", "")),
                    "reason": str(row.get("reason", "")),
                    "paper_title": _optional_str(row.get("paper_title")) or "",
                    "paper_doi": _optional_str(row.get("paper_doi")) or "",
                    "nordic_relevance": str(row.get("nordic_relevance", "")),
                    "nordic_relevance_reason": str(
                        row.get("nordic_relevance_reason", "")
                    ),
                }
    return lookup


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
