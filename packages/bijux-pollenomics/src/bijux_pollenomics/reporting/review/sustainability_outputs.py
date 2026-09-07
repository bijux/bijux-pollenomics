"""Publish generated-output sustainability evidence."""

from __future__ import annotations

import json
from pathlib import Path

from ...governance import (
    build_repository_output_sustainability_review,
    render_repository_output_sustainability_review_markdown,
)

__all__ = ["publish_repository_output_sustainability_review"]


def publish_repository_output_sustainability_review(
    output_root: Path,
    *,
    data_root: Path,
    docs_root: Path,
) -> None:
    """Write balance counts from the complete report tree visible at call time."""
    payload = build_repository_output_sustainability_review(
        data_root=Path(data_root),
        docs_root=Path(docs_root),
        report_root=Path(output_root),
    )
    (output_root / "repository_output_sustainability_review.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    (output_root / "repository_output_sustainability_review.md").write_text(
        render_repository_output_sustainability_review_markdown(payload),
        encoding="utf-8",
    )
