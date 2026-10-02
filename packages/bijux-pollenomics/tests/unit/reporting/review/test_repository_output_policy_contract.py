"""Repository output policy rows retain their renderer and field contract."""

from __future__ import annotations

from typing import cast

import pytest

from bijux_pollenomics.reporting.review.repository_truth_outputs import (
    _build_repository_generated_output_policy,
    _render_repository_generated_output_policy_markdown,
    _repository_output_spec,
    _RepositoryOutputSpec,
    _validate_repository_output_specs,
)


def test_spec_preserves_callable_renderer_and_policy_rows() -> None:
    spec = _repository_output_spec(
        stem="source_review",
        payload={"schema_version": "source-review.v1"},
        render_markdown=lambda payload: str(payload["schema_version"]),
        audience="maintainer_diagnostic",
        information_role="source review",
        coexistence_rule="coexists with source evidence",
        docs_anchor="docs/report/source-review.md",
        test_anchor="tests/unit/source-review.py",
    )
    _validate_repository_output_specs([spec])

    assert spec["render_markdown"](spec["payload"]) == "source-review.v1"
    policy = _build_repository_generated_output_policy([spec])
    markdown = _render_repository_generated_output_policy_markdown(policy)
    assert policy["row_count"] == 2
    assert "| `source_review` | `maintainer_diagnostic` |" in markdown


def test_duplicate_output_stem_keeps_refusal() -> None:
    spec = _repository_output_spec(
        stem="source_review",
        payload={},
        render_markdown=lambda payload: "ok",
        audience="maintainer_diagnostic",
        information_role="source review",
        coexistence_rule="coexists with source evidence",
        docs_anchor="docs/report/source-review.md",
        test_anchor="tests/unit/source-review.py",
    )
    with pytest.raises(ValueError, match="Duplicate repository truth output stem"):
        _validate_repository_output_specs([spec, spec])


def test_missing_output_spec_field_keeps_refusal() -> None:
    spec = _repository_output_spec(
        stem="source_review",
        payload={},
        render_markdown=lambda payload: "ok",
        audience="maintainer_diagnostic",
        information_role="source review",
        coexistence_rule="coexists with source evidence",
        docs_anchor="docs/report/source-review.md",
        test_anchor="tests/unit/source-review.py",
    )
    malformed = dict(spec)
    del malformed["test_anchor"]
    with pytest.raises(ValueError, match="missing fields: test_anchor"):
        _validate_repository_output_specs([cast(_RepositoryOutputSpec, malformed)])


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ("invalid", "rows must be a list"),
        (["invalid"], "row must be an object"),
        ([{"stem": "source_review"}], "audience must be text"),
    ],
)
def test_policy_renderer_refuses_malformed_rows(rows: object, message: str) -> None:
    payload: dict[str, object] = {
        "rule": "sources require review",
        "row_count": 1,
        "rows": rows,
    }
    with pytest.raises(ValueError, match=message):
        _render_repository_generated_output_policy_markdown(payload)
