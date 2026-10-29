"""Frozen taxa structural custody does not grant human or scientific acceptance."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.taxa_package_custody import (
    OWNER,
    REPORT,
    REPORT_BYTES,
    REPORT_SHA256,
    validate_package_custody,
    validated_taxa_package_custody,
)

REPOSITORY = Path(__file__).absolute().parents[5]


def _owner() -> JsonObject:
    return {
        "owner_id": OWNER,
        "role": "retained_source",
        "paths": [REPORT],
        "producer_paths": [],
        "producer_inputs": [],
    }


def test_actual_frozen_taxa_aggregate() -> None:
    entry = InventoryEntry(
        REPORT.removeprefix("docs/report/"),
        "file",
        REPORT_BYTES,
        REPORT_SHA256,
        REPORT_SHA256,
    )
    accepted, evidence = validated_taxa_package_custody(
        REPOSITORY, {REPORT: entry}, [_owner()]
    )
    assert accepted == (entry,)
    assert evidence["private_product_hash_entries"] == 20
    assert evidence["qualified_human_decisions"] == 0
    assert evidence["historical_structural_readiness_owner_admitted"] is False


def test_changed_taxa_owner_refused() -> None:
    entry = InventoryEntry(
        REPORT.removeprefix("docs/report/"),
        "file",
        REPORT_BYTES,
        REPORT_SHA256,
        REPORT_SHA256,
    )
    owner = _owner()
    owner["role"] = "maintained_configuration"
    with pytest.raises(ReportRebuildError):
        validated_taxa_package_custody(REPOSITORY, {REPORT: entry}, [owner])


def test_changed_taxa_product_identity_refused() -> None:
    payload = json.loads((REPOSITORY / REPORT).read_bytes())
    next(iter(payload["products"].values()))["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError):
        validate_package_custody(payload)


def test_taxa_acceptance_escalation_refused() -> None:
    original = json.loads((REPOSITORY / REPORT).read_bytes())
    for key, value in {
        "accepted_samples": 1,
        "received_qualified_human_decisions": 1,
        "rights_admission": "accepted",
        "scientific_acceptance": "accepted",
        "publication_allowed": True,
        "canonical_import_allowed": True,
        "historical_missing_bundle_restored": True,
    }.items():
        payload = copy.deepcopy(original)
        payload[key] = value
        with pytest.raises(ReportRebuildError):
            validate_package_custody(payload)
