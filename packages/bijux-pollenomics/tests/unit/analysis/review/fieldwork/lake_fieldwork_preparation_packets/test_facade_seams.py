"""Tests for compatibility monkeypatch seams across package boundaries."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest
from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)
from bijux_pollenomics.analysis.review.fieldwork import (
    lake_fieldwork_preparation_packets as packets,
)


def test_payload_uses_surface_selection_and_row_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assessment = cast(LakeEvidenceRichnessAssessment, object())
    report = cast(LakeEvidenceRichnessReport, SimpleNamespace(country="Sweden"))

    def select_rows(
        selected_report: LakeEvidenceRichnessReport, *, top_n: int
    ) -> list[LakeEvidenceRichnessAssessment]:
        assert selected_report is report
        assert top_n == 7
        return [assessment]

    def build_row(
        selected_assessment: LakeEvidenceRichnessAssessment, *, fieldwork_rank: int
    ) -> dict[str, object]:
        assert selected_assessment is assessment
        assert fieldwork_rank == 1
        return {"stable": True}

    monkeypatch.setattr(packets, "fieldwork_rows", select_rows)
    monkeypatch.setattr(packets, "_build_fieldwork_preparation_row", build_row)

    payload = packets.build_lake_fieldwork_preparation_payload(report, top_n=7)

    assert payload["row_count"] == 1
    assert payload["rows"] == [{"stable": True}]


def test_private_posture_adapter_resolves_the_surface_at_call_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(packets, "identity_posture", lambda flags: "patched")

    assert packets._identity_posture(("duplicate_sweden_name",)) == "patched"
