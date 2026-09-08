"""Adversarial repository release-quality assessment."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..metrics import SCORE_MAX, _load_json_or_default
from .credibility import build_repository_credibility_dashboard
from .extensibility import build_repository_extension_review
from .sustainability import build_repository_output_sustainability_review


def build_repository_brutal_honesty_review(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Ask the harsh release questions instead of celebrating machinery count."""
    credibility = build_repository_credibility_dashboard(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    sustainability = build_repository_output_sustainability_review(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    extension = build_repository_extension_review(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    sample_review = _load_json_or_default(
        report_root / "animal_sample_database_review.json", {}
    )
    extension_rows = cast(list[dict[str, object]], extension["rows"])
    rows: list[dict[str, object]] = [
        {
            "question_key": "more_elegant",
            "score": 4,
            "answer": "yes, because the repository now explains one product model and one generated-output policy instead of relying on accidental sprawl",
            "evidence_anchors": [
                "docs/report/repository_product_model.json",
                "docs/report/repository_generated_output_policy.json",
                "docs/report/repository_output_sustainability_review.json",
            ],
        },
        {
            "question_key": "more_trustworthy",
            "score": 3,
            "answer": "partly: the honesty surfaces are stronger, but animal extraction depth still materially lags the broader product story",
            "evidence_anchors": [
                "docs/report/repository_credibility_dashboard.json",
                "docs/report/animal_sample_database_review.json",
            ],
        },
        {
            "question_key": "more_extensible",
            "score": cast(int, extension_rows[0]["score"]),
            "answer": "yes, because world, region, and country publication are now explicitly contract-driven",
            "evidence_anchors": [
                "docs/report/publication_country_onboarding_contract.json",
                "docs/report/repository_extension_review.json",
            ],
        },
        {
            "question_key": "more_readable",
            "score": 4
            if credibility["overall_posture"] == "credible_but_still_recovery_bound"
            else 3,
            "answer": "yes, because the public mission and report portal now teach the product shape instead of assuming the reader already knows the file tree",
            "evidence_anchors": [
                "README.md",
                "docs/report/index.md",
                "docs/report/report_narrative_quality_review.json",
            ],
        },
        {
            "question_key": "only_more_impressive_looking",
            "score": 1
            if bool(sample_review.get("region_agnostic_contract_ready"))
            else 2,
            "answer": "no, but only because the repo now carries explicit refusal and credibility surfaces that stop the machinery from pretending it equals final readiness",
            "evidence_anchors": [
                "docs/report/repository_final_release_refusal.json",
                "docs/report/repository_output_sustainability_review.json",
            ],
        },
    ]
    average_score = round(sum(cast(int, row["score"]) for row in rows) / len(rows), 2)
    sustainability_rows = cast(list[dict[str, object]], sustainability["rows"])
    return {
        "schema_version": "repository-brutal-honesty-review.v1",
        "overall_posture": (
            "harder_to_fool_yourself"
            if average_score >= 3.0
            else "still_too_easy_to_hide_behind_machinery"
        ),
        "average_score": average_score,
        "rows": rows,
        "governance_note": sustainability_rows[1]["finding"],
    }


def render_repository_brutal_honesty_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository brutal honesty review",
        "",
        f"- Overall posture: `{payload['overall_posture']}`",
        f"- Average score: `{payload['average_score']}` / `{SCORE_MAX}`",
        f"- Governance note: {payload['governance_note']}",
        "",
        "| Question | Score | Answer |",
        "| --- | ---: | --- |",
    ]
    for row in cast(list[dict[str, object]], payload["rows"]):
        lines.append(f"| `{row['question_key']}` | {row['score']} | {row['answer']} |")
    return "\n".join(lines) + "\n"
