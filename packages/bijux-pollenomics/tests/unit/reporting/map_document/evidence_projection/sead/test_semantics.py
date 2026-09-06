"""Scientific and serialized behavior tests for SEAD atlas projection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection import (
    sead as sead_projection,
)
from tests.support.sead_evidence import (
    install_sead_projection_fixture,
    sead_projection_layers,
)

from ..fixtures.common import _decode_dictionary_table, _decode_sead_claim_table

_CANONICAL_PROJECTION_SHA256 = (
    "60a17d55baa42eef324b0a60d44bbde239b092355024a13c3bfeaeac0d4c2652"
)


def _projection(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    install_sead_projection_fixture(root, monkeypatch)
    layers = sead_projection_layers()[1:]
    records, accounting = sead_projection._project_sead(root, layers)
    return records, accounting, layers


def test_projection_preserves_canonical_serialized_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records, accounting, layers = _projection(tmp_path.absolute(), monkeypatch)
    payload = (
        json.dumps(
            {"records": records, "accounting": accounting, "layers": layers},
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()

    assert len(payload) == 17_662
    assert hashlib.sha256(payload).hexdigest() == _CANONICAL_PROJECTION_SHA256


def test_projection_keeps_null_zero_chronology_and_refusal_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records, accounting, _ = _projection(tmp_path.absolute(), monkeypatch)
    details = {str(row["record_id"]): row for row in records}
    site_tabs = cast(dict[str, object], details["sead:site:2"]["tabs"])
    chronology = cast(dict[str, object], site_tabs["chronology"])
    claim = _decode_sead_claim_table(chronology)[0]
    composition = cast(dict[str, object], site_tabs["pollen_composition"])
    observations = {
        cast(str, row["observation_id"]): row
        for row in _decode_dictionary_table(composition)
    }

    assert chronology["interval_semantics"] == "[younger_bp, older_bp]"
    assert chronology["null_semantics"] == "source null remains null"
    assert claim["chronology_eligibility"] == "eligible"
    assert claim["propagation_eligibility"] == "refused"
    assert claim["younger_bp"] == claim["older_bp"] == 100
    assert observations["sead-observation:null"]["source_value"] is None
    assert observations["sead-observation:null"]["source_value_state"] == "source_null"
    assert observations["sead-observation:zero"]["source_value"] == 0
    assert observations["sead-observation:zero"]["source_value_state"] == "reported"
    assert accounting["eligible_event_count"] == 0
    assert accounting["propagation_status"] == "refused"


def test_projection_retains_unresolved_locator_popup_and_country_attribution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_sead_projection_fixture(tmp_path.absolute(), monkeypatch)
    layers = sead_projection_layers()[1:]
    unresolved = cast(list[dict[str, object]], layers[1]["features"])[0]
    popup = [{"label": "Context", "value": "unresolved"}]
    unresolved["popup_rows"] = popup

    _, accounting = sead_projection._project_sead(tmp_path.absolute(), layers)

    assert unresolved["evidence_row_id"] == "1:unresolved:discovery"
    assert unresolved["record_id"] == "sead:site:1"
    assert unresolved["popup_rows"] == popup
    assert accounting["country_site_counts"] == {
        "Denmark": 1,
        "Finland": 1,
        "Norway": 1,
        "Sweden": 1,
    }
    assert accounting["map_feature_country_counts"] == {
        "Denmark": 1,
        "Finland": 1,
        "Norway": 1,
        "Sweden": 2,
    }
