"""Challenge the model-free authenticated observation product."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_product import (
    AuthenticatedObservationProduct,
    build_authenticated_observation_product,
    reopen_authenticated_observation_product,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_sources import (
    read_observation_source_products,
    reopen_observation_source_completion_receipt,
)

from ..observation_sources.test_sources import _started


def _product(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AuthenticatedObservationProduct:
    start, _, _ = _started(tmp_path, monkeypatch)
    completion = read_observation_source_products(
        start, completion_destination=tmp_path / "source-completion.json"
    )
    return build_authenticated_observation_product(completion)


def test_factory_rederives_complete_model_free_assignment_denominator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _product(tmp_path, monkeypatch)
    plan = product.completion_receipt.start_receipt.plan
    payload = json.loads(product.canonical_product_json)
    assert len(product.assignments) == len(plan.assignments)
    ordered = sorted(
        plan.assignments,
        key=lambda item: (
            item.protocol_id,
            item.cell_id,
            item.fold_id,
            item.record_id,
        ),
    )
    assert all(
        value.matches_plan(planned)
        for value, planned in zip(product.assignments, ordered, strict=True)
    )
    assert payload["status_counts"] == {
        status: sum(value.status == status for value in product.assignments)
        for status in ("available", "missing", "refused")
    }
    assert sum(payload["status_counts"].values()) == len(product.assignments)
    assert payload["empirical_evaluation_performed"] is False
    assert payload["scientific_acceptance"] == "not_evaluated"


def test_same_observation_reuses_one_authenticated_source_unit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _product(tmp_path, monkeypatch)
    identities: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for assignment in product.assignments:
        identities.setdefault(
            (assignment.observation_kind, assignment.observation_id), set()
        ).add((assignment.source_product_sha256, assignment.source_unit_sha256))
    assert identities
    assert all(len(value) == 1 for value in identities.values())
    payload = json.loads(product.canonical_product_json)
    assert len(payload["source_units"]) == len(identities)
    required = {
        "record_id",
        "site_id",
        "group_id",
        "block_id",
        "bin_id",
        "target",
        "support",
        "taxa",
        "values",
        "source_snapshot_sha256",
        "source_member_sha256",
        "reviewed_taxon_mapping_sha256",
        "normalization_code_sha256",
        "rights_evidence_sha256",
    }
    assert all(required <= set(value) for value in payload["source_units"])


def test_constructor_and_coherently_rehashed_wrapper_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _product(tmp_path, monkeypatch)
    with pytest.raises(ValidationRefusal, match="governed factory"):
        AuthenticatedObservationProduct(
            product.canonical_product_json,
            product.product_sha256,
            product.completion_receipt,
        )
    payload = json.loads(product.canonical_product_json)
    payload["assignments"][0]["status"] = "missing"
    payload["assignments"][0]["reason"] = "forged_missing"
    with pytest.raises(ValidationRefusal, match="bytes or parents"):
        reopen_authenticated_observation_product(
            canonical_json(payload),
            manifest_sha256(payload),
            completion_receipt=product.completion_receipt,
        )


def test_failed_source_completion_cannot_be_promoted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def omit_unit(vegetation: dict[str, Any], _pollen: dict[str, Any]) -> None:
        units = vegetation["units"]
        assert isinstance(units, list)
        units.pop()

    start, _, _ = _started(tmp_path, monkeypatch, omit_unit)
    destination = tmp_path / "failed-completion.json"
    with pytest.raises(ValidationRefusal):
        read_observation_source_products(start, completion_destination=destination)
    payload = json.loads(destination.read_text())
    completion = reopen_observation_source_completion_receipt(
        destination,
        start_receipt=start,
        expected_receipt_sha256=manifest_sha256(payload),
    )
    assert completion.products is None
    with pytest.raises(ValidationRefusal, match="successful source completion"):
        build_authenticated_observation_product(completion)
