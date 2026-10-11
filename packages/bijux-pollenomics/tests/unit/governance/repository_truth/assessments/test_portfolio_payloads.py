"""Keep portfolio rendering and unavailable-count refusals precisely typed."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics.governance.repository_truth.portfolio import (
    build_repository_claim_audit,
    render_repository_claim_audit_markdown,
    render_repository_docs_recovery_review_markdown,
    render_repository_truth_posture_markdown,
)
from bijux_pollenomics.governance.repository_truth.portfolio_payloads import (
    object_mapping,
)

REPOSITORY = Path(__file__).resolve().parents[7]


def _payload(stem: str) -> dict[str, object]:
    raw = json.loads(
        (REPOSITORY / "docs/report" / f"{stem}.json").read_text(encoding="utf-8")
    )
    return dict(object_mapping(raw, "retained test fixture"))


@pytest.mark.parametrize(
    "field",
    [
        "primary_domains",
        "contextual_domains",
        "claim_freeze_reasons",
        "recovery_priorities",
        "do_not_repeat",
    ],
)
@pytest.mark.parametrize("value", [None, "single string", ("tuple",), ["valid", 2]])
def test_truth_renderer_refuses_non_json_string_lists(
    field: str, value: object
) -> None:
    payload = _payload("repository_truth_posture")
    payload[field] = value
    with pytest.raises(TypeError, match="Repository portfolio"):
        render_repository_truth_posture_markdown(payload)


@pytest.mark.parametrize(
    "field",
    [
        "counts",
        "primary_domains",
        "contextual_domains",
        "recovery_review_overview",
        "claim_freeze_reasons",
        "recovery_priorities",
        "do_not_repeat",
    ],
)
def test_truth_renderer_retains_missing_field_refusal(field: str) -> None:
    payload = _payload("repository_truth_posture")
    del payload[field]
    with pytest.raises(KeyError) as caught:
        render_repository_truth_posture_markdown(payload)
    assert caught.value.args == (field,)


def test_count_mapping_refusal_precedes_missing_text_fields() -> None:
    with pytest.raises(TypeError, match="Repository truth counts must be a mapping"):
        render_repository_truth_posture_markdown({"counts": []})
    with pytest.raises(
        TypeError, match="Repository claim-audit counts must be a mapping"
    ):
        render_repository_claim_audit_markdown({"counts": []})


def test_unavailable_animal_surfaces_stay_unavailable_without_zero_inference() -> None:
    payload = _payload("repository_truth_posture")
    counts = dict(object_mapping(payload["counts"], "counts"))
    counts.update(
        {
            "animal_sample_database_review_available": False,
            "animal_map_readiness_available": False,
            "published_atlas_point_count": None,
            "animal_unresolved_sample_count": None,
            "animal_tracked_sample_count": None,
            "animal_coordinate_refused_provenance_count": None,
            "animal_coordinate_provenance_count": None,
        }
    )
    payload["counts"] = counts
    markdown = render_repository_truth_posture_markdown(payload)
    assert "- Published animal atlas points: `unavailable`" in markdown
    assert "- Unresolved animal samples: `unavailable`" in markdown
    assert "- Refused animal coordinate-provenance rows: `unavailable`" in markdown
    assert counts["published_atlas_point_count"] is None


@pytest.mark.parametrize("value", [True, -1, 3.5, "3", None])
def test_available_animal_count_refusal_is_preserved(value: object) -> None:
    payload = _payload("repository_truth_posture")
    counts = dict(object_mapping(payload["counts"], "counts"))
    counts["animal_sample_database_review_available"] = True
    counts["published_atlas_point_count"] = value
    payload["counts"] = counts
    with pytest.raises(
        ValueError, match="published_atlas_point_count must be a nonnegative integer"
    ):
        render_repository_truth_posture_markdown(payload)


@pytest.mark.parametrize("value", ["false", 0, 1, None])
def test_claim_renderer_refuses_coerced_boolean_decisions(value: object) -> None:
    payload = _payload("repository_claim_audit")
    payload["checks"] = [
        {"check_id": "source_depth", "passed": value, "finding_count": 0}
    ]
    with pytest.raises(TypeError, match="claim decision must be a boolean"):
        render_repository_claim_audit_markdown(payload)


@pytest.mark.parametrize("value", [True, -1, 2.5, "2", None])
def test_claim_renderer_refuses_invalid_finding_counts(value: object) -> None:
    payload = _payload("repository_claim_audit")
    payload["checks"] = [
        {"check_id": "source_depth", "passed": False, "finding_count": value}
    ]
    with pytest.raises(ValueError, match="finding_count must be a nonnegative integer"):
        render_repository_claim_audit_markdown(payload)


@pytest.mark.parametrize(
    "field,value",
    [("dimension_key", 2), ("score", True), ("score", -1), ("finding", [])],
)
def test_docs_renderer_refuses_malformed_dimension_fields(
    field: str, value: object
) -> None:
    payload = _payload("repository_docs_recovery_review")
    row: dict[str, object] = {
        "dimension_key": "source_depth",
        "score": 4,
        "finding": "retained scope",
    }
    row[field] = value
    payload["rows"] = [row]
    with pytest.raises((TypeError, ValueError)):
        render_repository_docs_recovery_review_markdown(payload)


def test_rendering_preserves_input_payload_bytes() -> None:
    payload = _payload("repository_truth_posture")
    before = deepcopy(payload)
    render_repository_truth_posture_markdown(payload)
    assert payload == before


def test_missing_repository_context_retains_partial_claim_scope(tmp_path: Path) -> None:
    data_root, docs_root, report_root = (
        tmp_path / "data",
        tmp_path / "docs",
        tmp_path / "docs/report",
    )
    for root in (data_root, docs_root, report_root):
        root.mkdir(parents=True, exist_ok=True)
    payload = build_repository_claim_audit(
        data_root=data_root, docs_root=docs_root, report_root=report_root
    )
    assert payload["audit_scope"] == "partial_context"
    assert payload["overall_ok"] is True
    counts = object_mapping(payload["counts"], "counts")
    assert counts["published_atlas_point_count"] is None
    assert counts["animal_sample_database_review_available"] is False
    assert "partial_context_assumed" in json.dumps(payload)
