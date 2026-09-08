from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import cast


def _build_report_narrative_quality_review(
    *,
    output_root: Path,
    existing_rows: list[dict[str, object]],
    portal_pages: dict[str, str],
) -> dict[str, object]:
    review_rows: list[dict[str, object]] = []
    markdown_paths = [
        cast(str, row["repository_path"]).removeprefix("docs/report/")
        for row in existing_rows
        if str(row["format"]) == "md"
    ]
    for relative_path in sorted(markdown_paths):
        text = (output_root / relative_path).read_text(encoding="utf-8")
        review_rows.append(_build_quality_row(relative_path, text))
    for relative_path, text in sorted(portal_pages.items()):
        if not relative_path.endswith(".md"):
            continue
        review_rows.append(_build_quality_row(relative_path, text))

    posture_counts = Counter(str(row["quality_posture"]) for row in review_rows)
    return {
        "schema_version": "report-narrative-quality-review.v1",
        "page_count": len(review_rows),
        "quality_posture_counts": dict(sorted(posture_counts.items())),
        "rows": review_rows,
    }


def _build_quality_row(relative_path: str, text: str) -> dict[str, object]:
    prose_paragraph_count = _count_prose_paragraphs(text)
    link_bullet_count = sum(
        1 for line in text.splitlines() if line.lstrip().startswith("- [")
    )
    bullet_sentence_count = sum(
        1 for line in text.splitlines() if _looks_like_sentence_bullet(line.strip())
    )
    heading_count = sum(1 for line in text.splitlines() if line.startswith("#"))
    table_line_count = sum(
        1 for line in text.splitlines() if line.strip().startswith("|")
    )
    quality_posture = "reader_ready"
    note = "Page explains its purpose before or alongside artifact links."
    if link_bullet_count > 14 and prose_paragraph_count < 2:
        quality_posture = "link_farm_risk"
        note = (
            "Page carries many artifact links without enough explanation around them."
        )
    elif prose_paragraph_count == 0 and table_line_count >= 4:
        quality_posture = "structured_reference"
        note = "Page is table-heavy, but it behaves like a reference surface rather than a loose link dump."
    elif prose_paragraph_count == 0 and bullet_sentence_count >= 3:
        quality_posture = "structured_reference"
        note = "Page is bullet-led, but those bullets still explain posture and evidence role."
    elif prose_paragraph_count == 0:
        quality_posture = "link_farm_risk"
        note = (
            "Page lacks explanatory prose and risks reading like a bare artifact index."
        )
    elif heading_count < 2:
        quality_posture = "thin_structure"
        note = "Page explains itself but still needs stronger internal wayfinding."
    return {
        "repository_path": f"docs/report/{relative_path}",
        "prose_paragraph_count": prose_paragraph_count,
        "link_bullet_count": link_bullet_count,
        "bullet_sentence_count": bullet_sentence_count,
        "heading_count": heading_count,
        "table_line_count": table_line_count,
        "quality_posture": quality_posture,
        "note": note,
    }


def _count_prose_paragraphs(text: str) -> int:
    paragraphs = 0
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if _looks_like_prose_block(current):
                paragraphs += 1
            current = []
            continue
        current.append(line)
    if _looks_like_prose_block(current):
        paragraphs += 1
    return paragraphs


def _looks_like_prose_block(lines: list[str]) -> bool:
    if not lines:
        return False
    first = lines[0]
    if first.startswith(("#", "|", "```", "<")):
        return False
    if first.startswith("- ") and not any(
        _looks_like_sentence_bullet(line) for line in lines
    ):
        return False
    joined = " ".join(lines)
    alpha_count = sum(1 for char in joined if char.isalpha())
    return alpha_count >= 60


def _looks_like_sentence_bullet(line: str) -> bool:
    if not line.startswith("- "):
        return False
    if line.startswith(("- `", "- [")):
        return False
    alpha_count = sum(1 for char in line if char.isalpha())
    return alpha_count >= 24
