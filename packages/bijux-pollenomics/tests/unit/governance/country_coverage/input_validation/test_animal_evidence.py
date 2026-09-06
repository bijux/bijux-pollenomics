"""Animal evidence uniqueness and disposition refusal tests."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from ..fixtures import _build, _replace_input_document


def test_duplicate_animal_evidence_row_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def duplicate_row(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows.append(deepcopy(rows[0]))

    _replace_input_document(
        monkeypatch, "docs/report/animal_country_species_coverage.json", duplicate_row
    )

    with pytest.raises(ValueError, match="duplicate evidence row"):
        _build()


def test_animal_evidence_totals_must_reconcile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_total(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows[0]["mapped_sample_count"] = (
            cast(int, rows[0]["mapped_sample_count"]) + 1
        )

    _replace_input_document(
        monkeypatch, "docs/report/animal_country_species_coverage.json", corrupt_total
    )

    with pytest.raises(ValueError, match="animal sample disposition"):
        _build()
