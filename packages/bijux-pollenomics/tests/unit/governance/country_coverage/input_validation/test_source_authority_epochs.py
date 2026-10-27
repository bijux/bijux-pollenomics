"""Closed source-capture authority reuse and current member-profile boundaries."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any

import pytest

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_EVIDENCE_SCOPE_ID,
)
from bijux_pollenomics.governance.country_coverage.boundaries import (
    _validate_boundary_evidence,
)
from bijux_pollenomics.governance.country_coverage.constants import INPUT_PATHS
from bijux_pollenomics.governance.country_coverage.decoding import _sead_canonical_bytes
from bijux_pollenomics.governance.country_coverage.evidence.model import _cell
from bijux_pollenomics.governance.country_coverage.evidence.neotoma import (
    publication_boundary_digest,
)
from bijux_pollenomics.governance.country_coverage.evidence.partitions import (
    _empty_counts,
    assignment_basis,
    assignment_scope_reasons,
)
from bijux_pollenomics.governance.country_coverage.evidence.sead_decisions import (
    derive_sead_country_decisions,
    retained,
)
from bijux_pollenomics.governance.country_coverage.evidence.snapshots import (
    _source_snapshot_ids,
)

_DIGEST = "sha256:bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f"
_AUTHORITY: dict[str, Any] = {
    "schema": "nordic-boundary-authority-identity.v1",
    "artifact_digest": _DIGEST,
    "normalized_artifact_sha256": _DIGEST.removeprefix("sha256:"),
    "authority_id": "sha256:e67d7e498df146bcdd65c398f67cdf2372298258288bcba9af734486fa2fe8d0",
    "manifest_sha256": "3855c31c227b8e9600d4f3956ea2f4f866a62cb55620f39d9e979834528b7373",
    "source_asset_sha256": "239eec57ac17f100a11e2536cffc56752c318b50ae765b0918ff7aab4ce8f255",
    "version": "5.1.1",
    "country_artifact_sha256": {
        "Denmark": "90b4fb95c8368020620ccd1e94182304530bc79b4251b115fc496b52a35098b3",
        "Finland": "2aa1b2df5366ac377a6835b3e6667743f9c9c57a077ea79066c187d487104316",
        "Norway": "c51db9962996c0cd570c1e0b5c9528413b387f80f77a5fe96f8e8c9b57f5317a",
        "Sweden": "20e2ca00f348cddb95a41ca8e8f22a92390a8210618a525e2cef98d3069fc00d",
    },
}


def _record(index: int, status: str) -> dict[str, Any]:
    assigned = status == "assigned"
    review = status == "review"
    return {
        "site_id": index,
        "site_uuid": f"00000000-0000-4000-8000-{index:012d}",
        "latitude_dd": 1.0,
        "longitude_dd": 1.0,
        "governed_country_code": "SE" if assigned else "UNASSIGNED",
        "decision": {
            "ambiguity_reason": "near_boundary_without_containment" if review else None,
            "boundary_artifact_digest": _DIGEST,
            "boundary_version": "natural-earth:5.1.1",
            "candidate_countries": ["Sweden"] if assigned or review else [],
            "decision_method": "strict_boundary_containment"
            if assigned
            else "boundary_proximity"
            if review
            else "no_boundary_containment",
            "decision_status": status,
            "derived_country": "Sweden" if assigned else None,
            "raw_country": None,
            "raw_country_comparison": "not_supplied",
            "refusal_reason": "outside_governed_boundaries"
            if status == "unassigned"
            else None,
        },
    }


def _documents() -> tuple[dict[str, Any], dict[str, Any]]:
    decisions = {
        "run_id": "constructed-parent",
        "boundary_authority": deepcopy(_AUTHORITY),
        "bbox": [0, 0, 4, 4],
        "bbox_site_count": 3,
        "decisions": [
            _record(1, "assigned"),
            _record(2, "review"),
            _record(3, "unassigned"),
        ],
        "decision_status_counts": {"assigned": 1, "review": 1, "unassigned": 1},
        "decision_method_counts": {
            "strict_boundary_containment": 1,
            "boundary_proximity": 1,
            "no_boundary_containment": 1,
        },
        "country_counts": {"SE": 1, "UNASSIGNED": 2},
    }
    assignment = [
        {"site_id": i, "country_code": "SE" if i == 1 else "UNASSIGNED"}
        for i in (1, 2, 3)
    ]
    admission = {
        "source_family": "sead",
        "scope_id": SEAD_GOVERNED_EVIDENCE_SCOPE_ID,
        "build_id": "sha256:" + "a" * 64,
        "run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "parent_run_id": "constructed-parent",
        "declared_scope": {
            "scope_key": "full_evidence_relations",
            "table_count": 61,
            "join_count": 86,
        },
        "country_accounting": {
            "boundary_authority_id": _AUTHORITY["authority_id"],
            "country_assignment_sha256": hashlib.sha256(
                _sead_canonical_bytes(assignment)
            ).hexdigest(),
            "bbox_site_count": 3,
            "admitted_site_count": 1,
            "review_site_count": 1,
            "unassigned_site_count": 1,
            "scope_excluded_count": 2,
            "country_counts": {"SE": 1, "DK": 0, "NO": 0, "FI": 0},
            "reconciles": True,
        },
    }
    return admission, decisions


def _pinned_arguments(
    monkeypatch: pytest.MonkeyPatch,
    admission: dict[str, Any],
    decisions: dict[str, Any],
) -> dict[str, Any]:
    """Pin an explicitly artificial capture; production pins are never broadened."""
    decision_bytes = _sead_canonical_bytes(decisions)
    sites = b'{"constructed_sites":true}\n'
    copied = [
        {
            "path": path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload),
        }
        for path, payload in (
            ("country-decisions.json", decision_bytes),
            ("payloads/tbl_sites.json", sites),
        )
    ]
    admission["copied_files"] = copied
    admission["acquisition_bundle_sha256"] = (
        "sha256:" + hashlib.sha256(_sead_canonical_bytes(copied)).hexdigest()
    )
    admission_bytes = _sead_canonical_bytes(admission)
    monkeypatch.setattr(
        retained,
        "SEAD_GOVERNED_ADMISSION_SHA256",
        hashlib.sha256(admission_bytes).hexdigest(),
    )
    monkeypatch.setattr(
        retained,
        "SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256",
        hashlib.sha256(decision_bytes).hexdigest(),
    )
    return {
        "admission_payload": admission_bytes,
        "decision_payload": decision_bytes,
        "site_payload": sites,
        "admitted_sites": {1: (_record(1, "assigned")["site_uuid"], 1.0, 1.0)},
    }


def test_closed_capture_reconciles_all_dispositions_without_current_geometry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admission, decisions = _documents()
    evidence = retained.retained_sead_decision_evidence(
        **_pinned_arguments(monkeypatch, admission, decisions)
    )
    assert evidence.governed == {"SE": 1, "UNASSIGNED": 1, "OUTSIDE": 1}
    assert evidence.statuses == {"assigned": 1, "review": 1, "unassigned": 1}
    assert len(evidence.decisions) == 3
    assert (
        evidence.country_assignment_sha256
        == admission["country_accounting"]["country_assignment_sha256"]
    )


@pytest.mark.parametrize(
    "field", ["admission_payload", "decision_payload", "site_payload"]
)
def test_changed_source_bytes_fail_closed(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    args = _pinned_arguments(monkeypatch, *_documents())
    args[field] += b" "
    with pytest.raises(ValueError, match="identity changed|byte count differs"):
        retained.retained_sead_decision_evidence(**args)


@pytest.mark.parametrize(
    "change",
    [
        "authority",
        "row_field",
        "duplicate_id",
        "duplicate_uuid",
        "state",
        "country",
        "row_authority",
        "assignment",
        "summary",
        "scope",
        "copied",
    ],
)
def test_retained_accounting_still_checks_structure_and_meaning(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    admission, decisions = _documents()
    if change == "authority":
        decisions["boundary_authority"]["manifest_sha256"] = "f" * 64
    elif change == "row_field":
        decisions["decisions"][0]["extra"] = True
    elif change == "duplicate_id":
        decisions["decisions"][1]["site_id"] = 1
    elif change == "duplicate_uuid":
        decisions["decisions"][1]["site_uuid"] = decisions["decisions"][0]["site_uuid"]
    elif change == "state":
        decisions["decisions"][0]["decision"]["refusal_reason"] = "invented"
    elif change == "country":
        decisions["decisions"][0]["governed_country_code"] = "FI"
    elif change == "row_authority":
        decisions["decisions"][0]["decision"]["boundary_artifact_digest"] = (
            "sha256:" + "f" * 64
        )
    elif change == "assignment":
        admission["country_accounting"]["country_assignment_sha256"] = "f" * 64
    elif change == "summary":
        decisions["decision_status_counts"]["assigned"] = 2
    elif change == "scope":
        admission["declared_scope"]["table_count"] = 60
    args = _pinned_arguments(monkeypatch, admission, decisions)
    if change == "copied":
        admission["copied_files"][0]["sha256"] = "f" * 64
        args["admission_payload"] = _sead_canonical_bytes(admission)
        monkeypatch.setattr(
            retained,
            "SEAD_GOVERNED_ADMISSION_SHA256",
            hashlib.sha256(args["admission_payload"]).hexdigest(),
        )
    with pytest.raises(ValueError):
        retained.retained_sead_decision_evidence(**args)


def test_retained_capture_requires_exact_admitted_identities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _pinned_arguments(monkeypatch, *_documents())
    args["admitted_sites"] = {}
    with pytest.raises(ValueError, match="identities and coordinates"):
        retained.retained_sead_decision_evidence(**args)


def test_ordinary_path_still_replays_current_geometry() -> None:
    _, decisions = _documents()
    decisions["decisions"] = decisions["decisions"][:1]
    _, normalized = _boundaries()
    geometry = {
        "Sweden": {"type": "FeatureCollection", "features": normalized["features"][:1]}
    }
    admitted = {1: (_record(1, "assigned")["site_uuid"], 1.0, 1.0)}
    # A same-authority, source-compatible fixture still performs a spatial replay.
    assert derive_sead_country_decisions(
        decisions,
        admitted_sites=admitted,
        boundary_collections=geometry,
        boundary_digest=_DIGEST,
        boundary_version="natural-earth:5.1.1",
    ).governed == {"SE": 1}
    with pytest.raises(ValueError, match="governed geometry"):
        derive_sead_country_decisions(
            decisions,
            admitted_sites=admitted,
            boundary_collections=geometry,
            boundary_digest="sha256:" + "f" * 64,
            boundary_version="natural-earth:5.1.1",
        )


def _boundaries() -> tuple[dict[str, Any], dict[str, Any]]:
    codes = {"Sweden": "SWE", "Denmark": "DNK", "Norway": "NOR", "Finland": "FIN"}
    manifest = {
        "schema_version": "natural-earth-boundary-receipt.v2",
        "country_selection_profile": "nordic-four-country-admin0-with-aland",
        "country_admin0_members": {
            name: [code, "ALD"] if name == "Finland" else [code]
            for name, code in codes.items()
        },
        "country_codes": codes,
        "version": "5.1.1",
        "country_artifacts": {
            name: {"sha256": "a" * 64, "feature_count": 2 if name == "Finland" else 1}
            for name in codes
        },
        "normalized_artifact": {"feature_count": 4},
    }
    normalized = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"country": name, "name": name},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]],
                },
            }
            for name in codes
        ],
    }
    return manifest, normalized


def test_raw_members_and_public_artifacts_have_distinct_units() -> None:
    manifest, normalized = _boundaries()
    _, counts, _ = _validate_boundary_evidence(manifest, normalized)
    assert counts == {"SE": 1, "DK": 1, "NO": 1, "FI": 1}
    assert (
        sum(
            record["feature_count"] for record in manifest["country_artifacts"].values()
        )
        == 5
    )
    assert assignment_scope_reasons(
        "boundaries", "source_reported", materialized=True
    ) == ["counts_are_named_public_country_artifacts_not_admin0_features"]


@pytest.mark.parametrize(
    "change", ["missing_member", "duplicate_member", "wrong_count", "unknown_profile"]
)
def test_new_profile_cannot_hide_an_invalid_member_inventory(change: str) -> None:
    manifest, normalized = _boundaries()
    if change == "missing_member":
        manifest["country_admin0_members"]["Finland"] = ["FIN"]
    elif change == "duplicate_member":
        manifest["country_admin0_members"]["Finland"] = ["FIN", "ALD", "ALD"]
    elif change == "wrong_count":
        manifest["country_artifacts"]["Finland"]["feature_count"] = 1
    else:
        manifest["country_selection_profile"] = "unknown"
    with pytest.raises(ValueError):
        _validate_boundary_evidence(manifest, normalized)


def test_legacy_single_member_receipt_remains_valid() -> None:
    manifest, normalized = _boundaries()
    manifest["schema_version"] = "natural-earth-boundary-receipt.v1"
    del manifest["country_selection_profile"], manifest["country_admin0_members"]
    manifest["country_artifacts"]["Finland"]["feature_count"] = 1
    assert sum(_validate_boundary_evidence(manifest, normalized)[1].values()) == 4


def test_publication_retains_named_authority_or_explicitly_has_none() -> None:
    def feature(value: object) -> dict[str, Any]:
        return {
            "properties": {
                "popup_rows": []
                if value is None
                else [{"label": "Boundary digest", "value": value}]
            }
        }

    assert publication_boundary_digest({"features": [feature(_DIGEST)]}) == _DIGEST
    assert publication_boundary_digest({"features": [feature(None)]}) is None
    for features in (
        [feature(_DIGEST), feature(None)],
        [feature("bad")],
        [feature(_DIGEST), feature("sha256:" + "f" * 64)],
    ):
        with pytest.raises(ValueError):
            publication_boundary_digest({"features": features})
    assert (
        assignment_basis("neotoma", "governed_assignment", materialized=True)
        == "retained-neotoma-country-reconciliation.v1"
    )
    assert (
        assignment_basis("landclim", "governed_assignment", materialized=False)
        == "governed-country-assignment-not-materialized.v1"
    )


@pytest.mark.parametrize(
    "source,dimension,digest,method",
    [
        (
            "sead",
            "governed_assignment",
            _DIGEST,
            "retained-sead-capture-country-assignment.v1",
        ),
        ("sead", "publication", _DIGEST, "product-country-publication-partition.v1"),
        (
            "neotoma",
            "governed_assignment",
            None,
            "retained-neotoma-country-reconciliation.v1",
        ),
        ("neotoma", "publication", _DIGEST, "product-country-publication-partition.v1"),
        ("landclim", "publication", None, "product-country-publication-partition.v1"),
        (
            "animal_adna",
            "publication",
            None,
            "product-country-publication-partition.v1",
        ),
    ],
)
def test_source_scoped_cell_metadata_preserves_denominators(
    source: str, dimension: str, digest: str | None, method: str
) -> None:
    counts = {**_empty_counts(), "sites": 1}
    cell = _cell(
        source_family=source,
        dimension=dimension,
        country_code="SE",
        evidence={(source, dimension, "SE"): counts},
        stage={
            "authority_status": "accepted",
            "blocking_reasons": [],
            "authority_reasons": [],
        },
        snapshot_id="sha256:" + "a" * 64,
        boundary_digest=digest,
        config_digest="sha256:" + "b" * 64,
        build_id="sha256:" + "c" * 64,
    )
    assert cell["boundary_artifact_digest"] == digest
    assert cell["country_assignment_method"] == method
    assert cell["counts"] == counts
    assert cell["lifecycle_status"] == "admitted"
    assert cell["availability_status"] == "available_collected"


def test_only_boundary_snapshot_moves_to_current_member_receipt() -> None:
    old = "a" * 64
    collection = {
        "source_hashes": {
            source: {"snapshot_sha256": old}
            for source in (
                "landclim",
                "neotoma",
                "sead",
                "raa",
                "boundaries",
                "svar",
                "aadr",
            )
        }
    }
    documents = {
        "data/neotoma/relational/reconciliation.json": {
            "source_snapshot_id": "sha256:" + "b" * 64
        },
        INPUT_PATHS[5]: {"acquisition_bundle_sha256": "sha256:" + "c" * 64},
    }
    receipt = b'{"country_selection_profile":"nordic-four-country-admin0-with-aland"}\n'
    animal = b"retained animal source bytes"
    snapshots = _source_snapshot_ids(
        collection,
        documents,
        {
            "data/boundaries/raw/source_manifest.json": receipt,
            INPUT_PATHS[14]: animal,
        },
    )
    assert snapshots["boundaries"] == "sha256:" + hashlib.sha256(receipt).hexdigest()
    for source in ("landclim", "raa", "svar", "aadr"):
        assert snapshots[source] == "sha256:" + old
    assert snapshots["neotoma"] == "sha256:" + "b" * 64
    assert snapshots["sead"] == "sha256:" + "c" * 64
    assert snapshots["animal_adna"] == "sha256:" + hashlib.sha256(animal).hexdigest()
    assert snapshots["hyde"] is None
