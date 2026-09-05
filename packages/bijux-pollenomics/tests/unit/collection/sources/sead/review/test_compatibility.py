from __future__ import annotations

import inspect

from bijux_pollenomics.collection.sources.sead import review


def test_review_import_path_is_a_package_facade() -> None:
    assert review.__file__ is not None
    assert review.__file__.endswith("sead/review/__init__.py")
    assert review.__all__ == [
        "build_sead_access_model_packet",
        "build_sead_evidence_legibility_review",
        "build_sead_recovery_requirements",
        "build_sead_temporal_review",
        "render_sead_access_model_markdown",
        "render_sead_evidence_legibility_review_markdown",
        "render_sead_recovery_requirements_markdown",
        "render_sead_temporal_review_markdown",
        "write_sead_review_outputs",
    ]


def test_public_signatures_remain_stable() -> None:
    assert str(inspect.signature(review.build_sead_temporal_review)) == (
        "(rows: 'list[dict[str, object]]', "
        "records: 'list[ContextPointRecord]') -> 'dict[str, object]'"
    )
    assert str(inspect.signature(review.write_sead_review_outputs)) == (
        "(output_root: 'Path', *, rows: 'list[dict[str, object]]', "
        "records: 'list[ContextPointRecord]') -> 'dict[str, str]'"
    )


def test_private_policy_seams_remain_reachable() -> None:
    for name in (
        "_duration_posture_for",
        "_inventory_summary",
        "_normalization_risk_for",
        "_render_review_csv",
        "_review_note_for",
        "_sead_row_capture_posture",
        "_temporal_strength_for",
    ):
        assert callable(getattr(review, name))
