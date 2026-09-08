"""Verify release assessment ownership and compatibility."""

from __future__ import annotations

import inspect
from pathlib import Path

from bijux_pollenomics.governance.repository_truth import (
    documentation,
    integrity,
    metrics,
    release,
)
from bijux_pollenomics.governance.repository_truth.release import (
    credibility,
    extensibility,
    honesty,
    product_model,
    refusal,
    sustainability,
)


def test_release_facade_delegates_assessments_to_intent_owners() -> None:
    expected = [
        "build_repository_product_model",
        "render_repository_product_model_markdown",
        "build_repository_credibility_dashboard",
        "render_repository_credibility_dashboard_markdown",
        "build_repository_output_sustainability_review",
        "render_repository_output_sustainability_review_markdown",
        "build_repository_extension_review",
        "render_repository_extension_review_markdown",
        "build_repository_brutal_honesty_review",
        "render_repository_brutal_honesty_review_markdown",
        "build_repository_final_release_refusal",
        "render_repository_final_release_refusal_markdown",
    ]
    owners = {
        "build_repository_product_model": product_model,
        "render_repository_product_model_markdown": product_model,
        "build_repository_credibility_dashboard": credibility,
        "render_repository_credibility_dashboard_markdown": credibility,
        "build_repository_output_sustainability_review": sustainability,
        "render_repository_output_sustainability_review_markdown": sustainability,
        "build_repository_extension_review": extensibility,
        "render_repository_extension_review_markdown": extensibility,
        "build_repository_brutal_honesty_review": honesty,
        "render_repository_brutal_honesty_review_markdown": honesty,
        "build_repository_final_release_refusal": refusal,
        "render_repository_final_release_refusal_markdown": refusal,
    }

    assert release.__all__ == expected
    for name, owner in owners.items():
        assert getattr(release, name) is getattr(owner, name)


def test_release_facade_preserves_legacy_helpers_and_dependencies() -> None:
    assert release.Path is Path
    assert release.SCORE_MAX is metrics.SCORE_MAX
    assert release._build_core_counts is metrics._build_core_counts
    assert release._count_suffix_files is metrics._count_suffix_files
    assert release._count_tree_files is metrics._count_tree_files
    assert release._load_json_or_default is metrics._load_json_or_default
    assert (
        release.build_repository_docs_scope_validation
        is documentation.build_repository_docs_scope_validation
    )
    assert (
        release.build_repository_governance_artifact_review
        is integrity.build_repository_governance_artifact_review
    )
    assert release._credibility_row is credibility._credibility_row
    assert release._release_refusal_row is refusal._release_refusal_row


def test_release_callable_signatures_remain_stable() -> None:
    path_signature = "(*, data_root: 'Path', docs_root: 'Path', report_root: 'Path') -> 'dict[str, object]'"
    render_signature = "(payload: 'dict[str, object]') -> 'str'"

    for name in release.__all__:
        expected = render_signature if name.startswith("render_") else path_signature
        assert str(inspect.signature(getattr(release, name))) == expected


def test_release_package_has_bounded_cohesive_modules() -> None:
    package_root = Path(release.__file__).parent
    direct_modules = sorted(package_root.glob("*.py"))

    assert len(direct_modules) <= 10
    assert {path.stem for path in direct_modules} == {
        "__init__",
        "credibility",
        "extensibility",
        "honesty",
        "product_model",
        "refusal",
        "sustainability",
    }
    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= 220
        for path in direct_modules
    )
