"""Challenge fixed post-start measured vegetation and pollen source products."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest
from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_access import (
    HeldoutPollenSourceLocator,
    MeasuredVegetationSourceLocator,
    ObservationSourceLocators,
    build_observation_access_plan,
    start_outcome_access,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_sources import (
    HeldoutPollenCountSourceProduct,
    MeasuredVegetationSourceProduct,
    ObservationSourceCompletionReceipt,
    governed_reader_code_sha256,
    read_observation_source_products,
    reopen_observation_source_completion_receipt,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.prediction_product import (
    SixCellPredictionProduct,
)

from ..prediction_product import test_product as prediction_fixture
from ..prediction_product.test_product import _build as build_prediction_product
from ..test_release import _protocols as base_release_protocols

Mutation = Callable[[dict[str, Any], dict[str, Any]], None]


def _supported_protocols() -> tuple[Any, Any]:
    return base_release_protocols(supported_observations=True)


def _prediction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> SixCellPredictionProduct:
    protocols = _supported_protocols()
    monkeypatch.setattr(prediction_fixture, "release_protocols", lambda: protocols)
    return build_prediction_product(tmp_path, monkeypatch)


def _metadata(kind: str, profile: str, reference: str) -> dict[str, Any]:
    return {
        "schema_version": (
            "pollenomics-measured-vegetation-source.v1"
            if kind == "independent_measured_vegetation"
            else "pollenomics-heldout-pollen-count-source.v1"
        ),
        "source_kind": kind,
        "evidence_role": kind,
        "reader_profile": profile,
        "reader_code_sha256": governed_reader_code_sha256(),
        "provider_id": "fixture-provider",
        "dataset_id": f"fixture-{kind}",
        "release_id": "fixture-release-v1",
        "source_snapshot_sha256": "1" * 64,
        "source_member": f"{kind}.jsonl",
        "source_member_sha256": "2" * 64,
        "citation": "fixture-citation-not-scientific-evidence",
        "license": "fixture-only",
        "rights_status": "admitted",
        "rights_evidence_sha256": "5" * 64,
        "release_disposition": "admitted_for_final_evaluation",
        "source_reference_id": reference,
        "taxon_mapping_sha256": "3" * 64,
        "taxon_mapping_review_id": "fixture-reviewed-mapping",
        "normalization_profile": "fixture-exact-normalization-v1",
        "normalization_code_sha256": "4" * 64,
    }


def _source_payloads(
    product: SixCellPredictionProduct,
) -> tuple[dict[str, Any], dict[str, Any]]:
    scope = product.protocols[0].scope
    taxa = list(scope.taxa)
    vegetation = _metadata(
        "independent_measured_vegetation",
        "measured-vegetation-reader-v1",
        "synthetic-measured-reference",
    )
    pollen = _metadata(
        "heldout_pollen_counts",
        "heldout-pollen-count-reader-v1",
        "synthetic-heldout-pollen-reference",
    )
    vegetation.update(field_method="fixture-field-survey", taxa=taxa, units=[])
    pollen.update(counting_method="fixture-grain-count", taxa=taxa, units=[])
    for index, site in enumerate(scope.sites):
        common = {
            "record_id": site.record_id,
            "site_id": site.site_id,
            "group_id": site.group_id,
            "block_id": site.block_id,
            "bin_id": site.bin_id,
            "source_sample_id": f"sample:{site.record_id}",
            "source_row_id": f"row:{site.record_id}",
            "support": asdict(site.support),
        }
        if index == 0:
            vegetation_values = {taxa[0]: None, taxa[1]: 0.4}
            vegetation_status, vegetation_reason = "missing", "partial_source_null"
        elif index == 1:
            vegetation_values = {taxa[0]: 0.0, taxa[1]: 1.0}
            vegetation_status, vegetation_reason = "available", None
        elif index == 2:
            vegetation_values = {taxa[0]: None, taxa[1]: None}
            vegetation_status, vegetation_reason = "refused", "source_row_refused"
        else:
            vegetation_values = {taxa[0]: 0.6, taxa[1]: 0.4}
            vegetation_status, vegetation_reason = "available", None
        vegetation["units"].append(
            {
                **common,
                "observation_id": site.vegetation_observation_id,
                "source_reference_id": vegetation["source_reference_id"],
                "status": vegetation_status,
                "reason_code": vegetation_reason,
                "values": vegetation_values,
            }
        )
        if index == 0:
            pollen_values = {taxa[0]: 0, taxa[1]: 0}
            pollen_status, pollen_reason, effort = "available", None, 0
        elif index == 1:
            pollen_values = {taxa[0]: None, taxa[1]: 2}
            pollen_status, pollen_reason, effort = "missing", "partial_count", 5
        else:
            pollen_values = {taxa[0]: 3, taxa[1]: 2}
            pollen_status, pollen_reason, effort = "available", None, 5
        pollen["units"].append(
            {
                **common,
                "observation_id": site.pollen_observation_id,
                "source_reference_id": pollen["source_reference_id"],
                "status": pollen_status,
                "reason_code": pollen_reason,
                "pollen_channel_input_id": f"pollen:{site.record_id}",
                "pollen_channel_source_sha256": "e" * 64,
                "counting_effort": effort,
                "all_zero_count": index == 0,
                "values": pollen_values,
            }
        )
    return vegetation, pollen


def _store(path: Path, payload: dict[str, Any]) -> str:
    content = (canonical_json(payload) + "\n").encode()
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _started(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: Mutation | None = None,
    *,
    reader_code: str | None = None,
) -> tuple[Any, Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    product = _prediction(tmp_path, monkeypatch)
    vegetation, pollen = _source_payloads(product)
    if mutation is not None:
        mutation(vegetation, pollen)
    code = reader_code or governed_reader_code_sha256()
    vegetation["reader_code_sha256"] = code
    pollen["reader_code_sha256"] = code
    vegetation_path = tmp_path / "vegetation.jsonl"
    pollen_path = tmp_path / "pollen.jsonl"
    sources = ObservationSourceLocators(
        MeasuredVegetationSourceLocator(
            vegetation_path,
            _store(vegetation_path, vegetation),
            "measured-vegetation-reader-v1",
            code,
            "synthetic-measured-reference",
        ),
        HeldoutPollenSourceLocator(
            pollen_path,
            _store(pollen_path, pollen),
            "heldout-pollen-count-reader-v1",
            code,
            "synthetic-heldout-pollen-reference",
        ),
    )
    plan = build_observation_access_plan(product, sources=sources)
    start = start_outcome_access(plan, destination=tmp_path / "access-start.json")
    return start, vegetation_path, pollen_path


def test_fixed_factory_persists_two_distinct_complete_products(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start, _, _ = _started(tmp_path, monkeypatch)
    destination = tmp_path / "source-completion.json"
    receipt = read_observation_source_products(
        start, completion_destination=destination
    )
    assert receipt.products is not None
    vegetation, pollen = receipt.products
    assert (
        len(vegetation.units)
        == len(pollen.units)
        == len(start.plan.prediction_product.protocols[0].scope.sites)
    )
    assert vegetation.units[0].status == "missing"
    assert dict(vegetation.units[1].values)["a"] == 0.0
    assert vegetation.units[2].status == "refused"
    assert pollen.units[0].all_zero_count is True
    assert pollen.units[1].status == "missing"
    payload = json.loads(receipt.canonical_receipt_json)
    assert [row["source_kind"] for row in payload["actual_outcome_reads"]] == [
        "independent_measured_vegetation",
        "heldout_pollen_counts",
    ]
    assert payload["empirical_evaluation_performed"] is False
    reopened = reopen_observation_source_completion_receipt(
        destination,
        start_receipt=start,
        expected_receipt_sha256=receipt.receipt_sha256,
    )
    assert reopened == receipt


@pytest.mark.parametrize(
    "mutation",
    [
        "modeled_vegetation",
        "wrong_owner",
        "support",
        "taxa",
        "omit_unit",
        "local_pollen",
        "boolean_count",
        "fractional_count",
        "negative_count",
        "zero_flag",
    ],
)
def test_semantic_source_attacks_persist_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    def change(vegetation: dict[str, Any], pollen: dict[str, Any]) -> None:
        if mutation == "modeled_vegetation":
            vegetation["source_kind"] = vegetation["evidence_role"] = "modeled_land_use"
        elif mutation == "wrong_owner":
            vegetation["units"][0]["group_id"] = "other-group"
        elif mutation == "support":
            vegetation["units"][0]["support"]["radius_m"] = 10.0001
        elif mutation == "taxa":
            vegetation["taxa"] = ["a"]
        elif mutation == "omit_unit":
            vegetation["units"].pop()
        elif mutation == "local_pollen":
            pollen["source_kind"] = pollen["evidence_role"] = "local_assimilated_pollen"
        elif mutation == "boolean_count":
            pollen["units"][2]["values"]["a"] = True
        elif mutation == "fractional_count":
            pollen["units"][2]["values"]["a"] = 1.5
        elif mutation == "negative_count":
            pollen["units"][2]["values"]["a"] = -1
        else:
            pollen["units"][0]["all_zero_count"] = False

    start, _, _ = _started(tmp_path, monkeypatch, change)
    destination = tmp_path / "failed.json"
    with pytest.raises(ValidationRefusal):
        read_observation_source_products(start, completion_destination=destination)
    payload = json.loads(destination.read_text())
    assert payload["status"] == "failed"
    assert payload["products"] is None
    assert payload["failure"]["reason_code"] == "invalid_final_evaluation"
    assert 1 <= len(payload["actual_outcome_reads"]) <= 2


def test_changed_bytes_and_wrong_reader_code_fail_with_exact_read_accounting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start, vegetation_path, _ = _started(tmp_path / "changed", monkeypatch)
    vegetation_path.write_bytes(vegetation_path.read_bytes() + b" ")
    changed_destination = tmp_path / "changed" / "failed.json"
    with pytest.raises(ValidationRefusal, match="bytes differ"):
        read_observation_source_products(
            start, completion_destination=changed_destination
        )
    changed = json.loads(changed_destination.read_text())
    assert len(changed["actual_outcome_reads"]) == 1
    assert changed["actual_outcome_reads"][0]["source_sha256"] != (
        start.plan.sources.vegetation.expected_source_sha256
    )

    wrong_root = tmp_path / "wrong-code"
    wrong_root.mkdir()
    wrong, _, _ = _started(wrong_root, monkeypatch, reader_code="f" * 64)
    wrong_destination = wrong_root / "failed.json"
    with pytest.raises(ValidationRefusal, match="different governed reader code"):
        read_observation_source_products(
            wrong, completion_destination=wrong_destination
        )
    assert json.loads(wrong_destination.read_text())["actual_outcome_reads"] == []


def test_products_and_completion_receipt_are_factory_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start, _, _ = _started(tmp_path, monkeypatch)
    receipt = read_observation_source_products(
        start, completion_destination=tmp_path / "complete.json"
    )
    assert receipt.products is not None
    vegetation, pollen = receipt.products
    with pytest.raises(ValidationRefusal, match="governed reader"):
        MeasuredVegetationSourceProduct(
            vegetation.canonical_product_json,
            vegetation.product_sha256,
            vegetation.units,
        )
    with pytest.raises(ValidationRefusal, match="governed reader"):
        HeldoutPollenCountSourceProduct(
            pollen.canonical_product_json, pollen.product_sha256, pollen.units
        )
    with pytest.raises(ValidationRefusal, match="governed producer"):
        ObservationSourceCompletionReceipt(
            receipt.canonical_receipt_json,
            receipt.receipt_sha256,
            receipt.completed_at_utc,
            start,
        )


def test_rehashed_embedded_product_and_actual_read_cannot_forge_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start, _, _ = _started(tmp_path, monkeypatch)
    destination = tmp_path / "complete.json"
    receipt = read_observation_source_products(
        start, completion_destination=destination
    )
    payload = json.loads(receipt.canonical_receipt_json)
    embedded = payload["products"]["independent_measured_vegetation"]
    product = json.loads(embedded["canonical_product_json"])
    product["available_units"] += 1
    embedded["canonical_product_json"] = canonical_json(product)
    embedded["product_sha256"] = manifest_sha256(product)
    payload["actual_outcome_reads"][0]["path"] = str(tmp_path / "other")
    destination.write_text(canonical_json(payload) + "\n")
    with pytest.raises(ValidationRefusal):
        reopen_observation_source_completion_receipt(
            destination,
            start_receipt=start,
            expected_receipt_sha256=manifest_sha256(payload),
        )


def test_destination_refuses_before_any_outcome_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start, _, _ = _started(tmp_path, monkeypatch)
    destination = tmp_path / "existing.json"
    destination.write_text("do-not-replace")
    monkeypatch.setattr(
        "bijux_pollenomics.analysis.lra_validation.evaluation."
        "observation_sources.receipt._read_source_bytes",
        lambda *_args, **_kwargs: pytest.fail("outcome source was read"),
    )
    with pytest.raises(ValidationRefusal, match="new and writable"):
        read_observation_source_products(start, completion_destination=destination)
    assert destination.read_text() == "do-not-replace"


def test_reopen_refuses_non_utc_completion_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start, _, _ = _started(tmp_path, monkeypatch)
    destination = tmp_path / "complete.json"
    receipt = read_observation_source_products(
        start, completion_destination=destination
    )
    payload = json.loads(receipt.canonical_receipt_json)
    payload["completed_at_utc"] = payload["completed_at_utc"].replace("+00:00", "")
    destination.write_text(canonical_json(payload) + "\n")
    with pytest.raises(ValidationRefusal, match="identity or claim boundary"):
        reopen_observation_source_completion_receipt(
            destination,
            start_receipt=start,
            expected_receipt_sha256=manifest_sha256(payload),
        )
