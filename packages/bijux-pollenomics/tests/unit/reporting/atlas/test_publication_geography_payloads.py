"""Published geography payload rendering and malformed-container refusals."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.geography import (
    build_geography_onboarding_contract,
    render_geography_onboarding_contract_markdown,
    render_geography_scope_registry_markdown,
    render_geography_subset_validation_markdown,
)

_RENDERERS: tuple[tuple[str, Callable[[dict[str, object]], str]], ...] = (
    ("publication_geography_registry", render_geography_scope_registry_markdown),
    (
        "publication_geography_subset_validation",
        render_geography_subset_validation_markdown,
    ),
    (
        "publication_country_onboarding_contract",
        render_geography_onboarding_contract_markdown,
    ),
)


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "docs/report/publication_geography_registry.md").is_file():
            return parent
    raise AssertionError("publication geography fixtures are unavailable")


@pytest.mark.parametrize(("stem", "render"), _RENDERERS)
def test_geography_markdown_matches_tracked_bytes(
    stem: str, render: Callable[[dict[str, object]], str]
) -> None:
    report_root = _repository_root() / "docs" / "report"
    payload = json.loads((report_root / f"{stem}.json").read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert render(payload).encode() == (report_root / f"{stem}.md").read_bytes()


def test_geography_row_renderers_refuse_nonrow_containers() -> None:
    for renderer, field in (
        (render_geography_scope_registry_markdown, "scopes"),
        (render_geography_subset_validation_markdown, "rows"),
    ):
        with pytest.raises(ValueError, match="list of rows"):
            renderer({field: [object()]})
        with pytest.raises(KeyError):
            renderer({})


def test_onboarding_renderer_refuses_nonstring_contract_sections() -> None:
    payload = build_geography_onboarding_contract(published_countries=("Sweden",))
    for field in (
        "required_surfaces",
        "code_contracts",
        "data_contracts",
        "docs_contracts",
        "test_contracts",
        "published_country_roster",
    ):
        malformed = dict(payload)
        malformed[field] = [object()]
        with pytest.raises(ValueError, match="list of strings"):
            render_geography_onboarding_contract_markdown(malformed)
