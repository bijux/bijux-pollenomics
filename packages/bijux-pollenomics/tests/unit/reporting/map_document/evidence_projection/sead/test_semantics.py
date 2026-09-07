"""Scientific and serialized behavior tests for SEAD atlas projection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.source_keys.validation import (
    validate_sead_source_key_ledger,
)
from bijux_pollenomics.evidence.sources.sead import SEAD_GOVERNED_EVIDENCE_RUN_ID
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    sead as sead_projection,
)
from tests.support.sead_evidence import (
    install_sead_projection_fixture,
    sead_projection_layers,
)

from ..fixtures.common import _decode_dictionary_table, _decode_sead_claim_table

_CANONICAL_PROJECTION_SHA256 = (
    "453d56a01a3f4f51763b8ee5df1526b6ec65f7019387cfd3cef86fa62d6c922d"
)


def _projection(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    install_sead_projection_fixture(root, monkeypatch)
    layers = sead_projection_layers()[1:]
    records, accounting = sead_projection._project_sead(root, layers)
    return records, accounting, layers


def test_projection_fixture_publishes_valid_unpartitioned_source_key_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_sead_projection_fixture(tmp_path.absolute(), monkeypatch)
    evidence_root = (
        tmp_path
        / "sead"
        / "normalized"
        / "acquisitions"
        / SEAD_GOVERNED_EVIDENCE_RUN_ID
    )
    manifest = json.loads(
        (evidence_root / "evidence_materialization_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    ledger = json.loads(
        (evidence_root / "source_key_ledger.json").read_text(encoding="utf-8")
    )

    validated = validate_sead_source_key_ledger(ledger)
    assert "source_key_ledger.json" not in manifest["multipart_documents"]
    assert "source_key_ledger.json" in {
        record["path"] for record in manifest["files"]
    }
    assert validated["source_run_id"] == manifest["source_run_id"]
    assert validated["build_id"] == manifest["build_id"]
    assert (
        validated["acquisition_manifest_sha256"]
        == manifest["acquisition_manifest_sha256"]
    )


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

    assert len(payload) == 18_517
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


def test_projection_exposes_stable_site_and_parent_admission_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records, accounting, layers = _projection(tmp_path.absolute(), monkeypatch)
    details = {str(row["record_id"]): row for row in records}
    detail = details["sead:site:2"]
    tabs = cast(dict[str, object], detail["tabs"])
    overview = cast(dict[str, object], tabs["overview"])
    provenance = cast(dict[str, object], tabs["provenance"])

    assert detail["site_uuid"] == "site-2"
    assert overview["site_uuid"] == "site-2"
    assert provenance["site_uuid"] == "site-2"
    assert provenance["parent_admission_sha256"] == "a" * 64
    assert accounting["source_site_uuid_denominator"] == 4
    assert accounting["parent_admission_sha256"] == "a" * 64
    assert {
        cast(str, feature["site_uuid"])
        for layer in layers
        for feature in cast(list[dict[str, object]], layer["features"])
    } == {"site-1", "site-2", "site-3", "site-4"}


def test_projection_rejects_normalized_site_uuid_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_sead_projection_fixture(tmp_path.absolute(), monkeypatch)
    sites_path = (
        tmp_path / "sead" / "normalized" / "nordic_environmental_sites.geojson"
    )
    sites = json.loads(sites_path.read_text(encoding="utf-8"))
    sites["features"][0]["properties"]["site_uuid"] = "wrong-site-uuid"
    sites_path.write_text(json.dumps(sites), encoding="utf-8")

    with pytest.raises(ValueError, match="UUID"):
        sead_projection._project_sead(
            tmp_path.absolute(), sead_projection_layers()[1:]
        )


def test_projection_rejects_atlas_feature_site_uuid_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_sead_projection_fixture(tmp_path.absolute(), monkeypatch)
    layers = sead_projection_layers()[1:]
    cast(list[dict[str, object]], layers[0]["features"])[0]["site_uuid"] = (
        "wrong-site-uuid"
    )

    with pytest.raises(ValueError, match="UUID"):
        sead_projection._project_sead(tmp_path.absolute(), layers)


def test_projection_rejects_parent_admission_lineage_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_sead_projection_fixture(tmp_path.absolute(), monkeypatch)
    manifest_path = (
        tmp_path
        / "sead"
        / "normalized"
        / "acquisitions"
        / SEAD_GOVERNED_EVIDENCE_RUN_ID
        / "evidence_materialization_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["parent_admission_sha256"] = "d" * 64
    payload = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    manifest_path.write_bytes(payload)
    monkeypatch.setattr(
        sead_projection,
        "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
        hashlib.sha256(payload).hexdigest(),
    )

    with pytest.raises(ValueError, match="parent admission identity diverges"):
        sead_projection._project_sead(
            tmp_path.absolute(), sead_projection_layers()[1:]
        )


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
    assert unresolved["site_uuid"] == "site-1"
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
