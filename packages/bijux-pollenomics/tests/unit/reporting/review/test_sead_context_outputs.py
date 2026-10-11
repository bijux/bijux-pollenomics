"""SEAD review counts and rendered source claims stay tied to typed inputs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.review.sead_context_outputs import (
    build_repository_sead_legibility_review,
    render_repository_sead_legibility_review_markdown,
)


def _sources() -> dict[str, dict[str, object]]:
    return {
        "evidence_legibility_review": {
            "row_count": 2,
            "normalization_risk_counts": {"contextual": 1, "access": 1},
        },
        "access_model": {
            "row_count": 2,
            "access_visibility_counts": {"site_page_only": 2},
        },
        "temporal_review": {
            "row_count": 2,
            "comparability_posture_counts": {"unresolved": 1, "numeric_interval": 1},
        },
        "recovery_requirements": {
            "row_count": 1,
            "rows": [
                {
                    "requirement_key": "upstream_chronology",
                    "required_evidence": "Source chronology",
                    "satisfaction_signal": "Reviewed bounds",
                    "evidence_gap_count": 1,
                }
            ],
        },
    }


def _write_sources(data_root: Path, payloads: dict[str, dict[str, object]]) -> None:
    review = data_root / "sead" / "review"
    review.mkdir(parents=True)
    for name, payload in payloads.items():
        (review / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_build_and_render_preserve_review_counts_and_requirements(
    tmp_path: Path,
) -> None:
    _write_sources(tmp_path, _sources())

    payload = build_repository_sead_legibility_review(tmp_path)
    markdown = render_repository_sead_legibility_review_markdown(payload)

    assert payload["row_count"] == 2
    assert payload["normalization_risk_counts"] == {"contextual": 1, "access": 1}
    assert payload["access_visibility_counts"] == {"site_page_only": 2}
    assert payload["comparability_posture_counts"] == {
        "unresolved": 1,
        "numeric_interval": 1,
    }
    assert "| upstream_chronology | Source chronology | Reviewed bounds |" in markdown
    assert "- site page only: `2`" in markdown


@pytest.mark.parametrize(
    ("source", "field", "replacement", "message"),
    [
        ("evidence_legibility_review", "row_count", True, "row_count"),
        ("evidence_legibility_review", "row_count", "2", "row_count"),
        ("evidence_legibility_review", "row_count", -1, "row_count"),
        (
            "evidence_legibility_review",
            "normalization_risk_counts",
            ["contextual"],
            "normalization_risk_counts",
        ),
        (
            "access_model",
            "access_visibility_counts",
            {"site_page_only": True},
            "nonnegative integer",
        ),
        (
            "temporal_review",
            "comparability_posture_counts",
            {"unresolved": 1},
            "do not reconcile",
        ),
        ("recovery_requirements", "rows", ["unreviewed"], "requirement row"),
        ("recovery_requirements", "row_count", 2, "do not reconcile"),
    ],
)
def test_build_refuses_malformed_or_unreconciled_sources(
    tmp_path: Path,
    source: str,
    field: str,
    replacement: object,
    message: str,
) -> None:
    payloads = _sources()
    payloads[source][field] = replacement
    _write_sources(tmp_path, payloads)

    with pytest.raises(ValueError, match=message):
        build_repository_sead_legibility_review(tmp_path)


def test_build_refuses_partial_source_set(tmp_path: Path) -> None:
    payloads = _sources()
    del payloads["temporal_review"]
    _write_sources(tmp_path, payloads)

    with pytest.raises(ValueError, match="source set is incomplete"):
        build_repository_sead_legibility_review(tmp_path)


def test_build_refuses_non_object_source(tmp_path: Path) -> None:
    _write_sources(tmp_path, _sources())
    (tmp_path / "sead/review/access_model.json").write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="source must be an object"):
        build_repository_sead_legibility_review(tmp_path)


def test_empty_source_root_keeps_zero_count_fallback(tmp_path: Path) -> None:
    payload = build_repository_sead_legibility_review(tmp_path)

    assert payload["row_count"] == 0
    assert payload["requirement_rows"] == []


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("normalization_risk_counts", {"contextual": True}, "nonnegative integer"),
        ("direct_links", ["sead.md"], "direct_links must be an object"),
        ("requirement_rows", ["unreviewed"], "requirement row"),
    ],
)
def test_render_refuses_malformed_payload_fields(
    tmp_path: Path, field: str, replacement: object, message: str
) -> None:
    _write_sources(tmp_path, _sources())
    payload = build_repository_sead_legibility_review(tmp_path)
    payload[field] = replacement

    with pytest.raises(ValueError, match=message):
        render_repository_sead_legibility_review_markdown(payload)
