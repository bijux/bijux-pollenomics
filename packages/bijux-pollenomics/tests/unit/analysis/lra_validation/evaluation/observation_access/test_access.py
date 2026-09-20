"""Challenge value-free planning and durable first-access persistence."""

from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_access import (
    HeldoutPollenSourceLocator,
    MeasuredVegetationSourceLocator,
    ObservationAccessPlan,
    ObservationSourceLocators,
    OutcomeAccessStartReceipt,
    build_observation_access_plan,
    reopen_observation_access_plan,
    reopen_outcome_access_start_receipt,
    start_outcome_access,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_access import (
    receipt as receipt_module,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.prediction_product import (
    SixCellPredictionProduct,
)

from ..prediction_product.test_product import _build as build_prediction_product


def _sources(
    tmp_path: Path,
    *,
    vegetation_reference: str = "synthetic-measured-reference",
    vegetation_path: Path | None = None,
    pollen_path: Path | None = None,
) -> ObservationSourceLocators:
    return ObservationSourceLocators(
        MeasuredVegetationSourceLocator(
            tmp_path / "vegetation-source"
            if vegetation_path is None
            else vegetation_path,
            "a" * 64,
            "measured-vegetation-reader-v1",
            "b" * 64,
            vegetation_reference,
        ),
        HeldoutPollenSourceLocator(
            tmp_path / "pollen-source" if pollen_path is None else pollen_path,
            "c" * 64,
            "heldout-pollen-count-reader-v1",
            "d" * 64,
            "synthetic-heldout-pollen-reference",
        ),
    )


def _plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[SixCellPredictionProduct, ObservationAccessPlan]:
    product = build_prediction_product(tmp_path, monkeypatch)
    return product, build_observation_access_plan(product, sources=_sources(tmp_path))


def test_plan_derives_exact_model_free_target_specific_denominator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, plan = _plan(tmp_path, monkeypatch)
    payload = json.loads(plan.canonical_plan_json)
    assert len(plan.assignments) * 2 == len(product.outcome_free_rows)
    assert "model_id" not in plan.canonical_plan_json
    assert "observation_value" not in plan.canonical_plan_json
    assert payload["outcome_values_present"] is False
    assert payload["empirical_evaluation_performed"] is False
    scopes = {
        protocol.protocol_id: {site.record_id: site for site in protocol.scope.sites}
        for protocol in product.protocols
    }
    for assignment in plan.assignments:
        site = scopes[assignment.protocol_id][assignment.record_id]
        expected = (
            site.vegetation_observation_id
            if assignment.target == "vegetation_cover"
            else site.pollen_observation_id
        )
        assert assignment.observation_id == expected
    assert not plan.sources.vegetation.path.exists()
    assert not plan.sources.pollen.path.exists()


def test_plan_private_construction_and_untyped_sources_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, plan = _plan(tmp_path, monkeypatch)
    with pytest.raises(ValidationRefusal, match="governed factory"):
        ObservationAccessPlan(
            plan.canonical_plan_json,
            plan.plan_sha256,
            product,
            plan.sources,
            plan.assignments,
        )
    with pytest.raises(ValidationRefusal, match="fixed typed source"):
        build_observation_access_plan(
            product,
            sources={"vegetation": "caller material"},  # type: ignore[arg-type]
        )


def test_duplicate_swapped_and_unadmitted_locators_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = build_prediction_product(tmp_path, monkeypatch)
    shared = tmp_path / "shared"
    with pytest.raises(ValidationRefusal, match="remain distinct"):
        _sources(tmp_path, vegetation_path=shared, pollen_path=shared)
    ordinary = _sources(tmp_path)
    with pytest.raises(ValidationRefusal, match="typed target-specific"):
        ObservationSourceLocators(
            ordinary.pollen,  # type: ignore[arg-type]
            ordinary.vegetation,  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationRefusal, match="absent from a protocol policy"):
        build_observation_access_plan(
            product,
            sources=_sources(tmp_path, vegetation_reference="modeled-not-admitted"),
        )
    modeled = MeasuredVegetationSourceLocator(
        tmp_path / "modeled-vegetation",
        "a" * 64,
        "hyde-modeled-land-use-v1",
        "b" * 64,
        "synthetic-measured-reference",
    )
    with pytest.raises(ValidationRefusal, match="fixed governed reader"):
        ObservationSourceLocators(modeled, ordinary.pollen)


def test_plan_canonical_bytes_digest_and_locator_binding_refuse_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, plan = _plan(tmp_path, monkeypatch)
    with pytest.raises(ValidationRefusal):
        reopen_observation_access_plan(
            plan.canonical_plan_json + " ",
            plan.plan_sha256,
            prediction_product=product,
            sources=plan.sources,
        )
    with pytest.raises(ValidationRefusal):
        reopen_observation_access_plan(
            plan.canonical_plan_json,
            "f" * 64,
            prediction_product=product,
            sources=plan.sources,
        )
    payload = json.loads(plan.canonical_plan_json)
    payload["sources"]["heldout_pollen_counts"]["path"] = str(tmp_path / "changed")
    changed = canonical_json(payload)
    with pytest.raises(ValidationRefusal, match="source locators"):
        reopen_observation_access_plan(
            changed,
            manifest_sha256(payload),
            prediction_product=product,
            sources=plan.sources,
        )


def test_start_is_durable_exclusive_and_reopens_without_outcome_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, plan = _plan(tmp_path, monkeypatch)
    destination = tmp_path / "access-start.json"
    receipt = start_outcome_access(plan, destination=destination)
    original = destination.read_bytes()
    assert original == (receipt.canonical_receipt_json + "\n").encode()
    payload = json.loads(receipt.canonical_receipt_json)
    assert payload["status"] == "started"
    assert payload["outcome_bytes_read"] is False
    assert payload["actual_outcome_reads"] == []
    assert payload["historical_human_nonaccess_authenticated"] is False
    reopened = reopen_outcome_access_start_receipt(
        destination,
        plan=plan,
        expected_receipt_sha256=receipt.receipt_sha256,
    )
    assert reopened == receipt
    with pytest.raises(ValidationRefusal, match="already exists"):
        start_outcome_access(plan, destination=destination)
    assert destination.read_bytes() == original


def test_policy_lock_must_strictly_precede_internally_captured_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, plan = _plan(tmp_path, monkeypatch)
    policy = json.loads(
        plan.prediction_product.protocols[0].policy.canonical_policy_json
    )
    locked = datetime.fromisoformat(
        cast(str, policy["locked_at"]).replace("Z", "+00:00")
    )
    monkeypatch.setattr(receipt_module, "_utc_now", lambda: locked)
    destination = tmp_path / "too-early.json"
    with pytest.raises(ValidationRefusal, match="strictly before"):
        start_outcome_access(plan, destination=destination)
    assert not destination.exists()


@pytest.mark.parametrize("offset", [timedelta(0), timedelta(microseconds=-1)])
def test_equal_or_late_prediction_freeze_refuses_before_persistence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    offset: timedelta,
) -> None:
    product, plan = _plan(tmp_path, monkeypatch)
    latest = max(
        cast(datetime, row.prediction_frozen_at)
        for row in product.outcome_free_rows
        if row.status == "predicted"
    )
    monkeypatch.setattr(receipt_module, "_utc_now", lambda: latest + offset)
    destination = tmp_path / "late.json"
    with pytest.raises(ValidationRefusal, match="freeze before"):
        start_outcome_access(plan, destination=destination)
    assert not destination.exists()


def test_receipt_tampering_or_wrong_digest_refuses_reopen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, plan = _plan(tmp_path, monkeypatch)
    destination = tmp_path / "access-start.json"
    receipt = start_outcome_access(plan, destination=destination)
    with pytest.raises(ValidationRefusal, match="identity"):
        reopen_outcome_access_start_receipt(
            destination,
            plan=plan,
            expected_receipt_sha256="f" * 64,
        )
    payload = json.loads(receipt.canonical_receipt_json)
    payload["actual_outcome_reads"] = ["forged"]
    destination.write_text(canonical_json(payload) + "\n")
    with pytest.raises(ValidationRefusal):
        reopen_outcome_access_start_receipt(
            destination,
            plan=plan,
            expected_receipt_sha256=manifest_sha256(payload),
        )


def test_receipt_private_constructor_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, plan = _plan(tmp_path, monkeypatch)
    receipt = start_outcome_access(plan, destination=tmp_path / "access-start.json")
    with pytest.raises(ValidationRefusal, match="governed producer"):
        OutcomeAccessStartReceipt(
            receipt.canonical_receipt_json,
            receipt.receipt_sha256,
            receipt.access_started_at_utc,
            plan,
        )


def test_missing_receipt_parent_refuses_without_raw_filesystem_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, plan = _plan(tmp_path, monkeypatch)
    destination = tmp_path / "absent" / "access-start.json"
    with pytest.raises(ValidationRefusal, match="Cannot create"):
        start_outcome_access(plan, destination=destination)
    assert not destination.exists()
