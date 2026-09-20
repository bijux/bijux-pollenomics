"""Two-site synthetic component closure with real host products."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

from bijux_pollenomics.analysis.lra.batches.models import (
    LRABatchItem,
    LRABatchItemResult,
    LRABatchResult,
    canonical_json,
)
from bijux_pollenomics.analysis.lra.batches.receipts import finish_attempt
from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
from bijux_pollenomics.analysis.lra.outputs.identity import capture_code_identity
from bijux_pollenomics.analysis.lra.outputs.publication import publish_result
from bijux_pollenomics.analysis.lra.regional_components import RegionalComponentPlan

from ..support import request_fixture


class _Manifest:
    def scientific_identity(self) -> dict[str, str]:
        return {"identity": "regional-component-test"}


class _Result:
    manifest = _Manifest()

    def __init__(self, coordinate: float, basin_type: str) -> None:
        self.coordinate = coordinate
        self.basin_type = basin_type

    def write(self, root: Path) -> None:
        root.mkdir()
        (root / "reconstruction.csv").write_text(
            "Distance.weighting,Basin.type,coordinate,Alnus.mean,Betula.mean,"
            "Alnus.median,Betula.median,Alnus.q90,Betula.q90,"
            "Alnus.q10,Betula.q10,Alnus.sd,Betula.sd\n"
            f"lsm unstable,{self.basin_type},{self.coordinate:g},"
            "50,50,50,50,50,50,50,50,0,0\n"
        )
        (root / "deposition_factors.csv").write_text("index,K\nAlnus,1\nBetula,1\n")
        (root / "result_contract.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "result_type": "reveals",
                    "primary_artifact": "reconstruction.csv",
                    "units": {"cover": "percent", "distance": "metre"},
                }
            )
        )


def _binding(root: Path) -> EngineBinding:
    code = root / "installed"
    code.mkdir()
    (code / "api.py").write_text('"""Synthetic installed module."""\n')
    api = ModuleType("synthetic_components")
    api.__file__ = str(code / "api.py")
    return EngineBinding("bijux-pollenomics-lra", "0.2.0", "python-numpy-scipy", api)


def _request(root: Path, index: int) -> dict[str, Any]:
    payload = request_fixture(root)
    sample = payload["regional"]["samples"][0]
    sample.update(
        {
            "sample_id": f"sample-{index}",
            "site_id": f"site-{index}",
            "coordinate": index,
        }
    )
    payload["regional"]["basin"]["diameter_m"] = 200 + index * 100
    return payload


def component_fixture(
    root: Path, *, second_status: Literal["completed", "refused"] = "completed"
) -> tuple[
    Path,
    tuple[LRABatchItem, ...],
    LRABatchResult,
    RegionalComponentPlan,
]:
    input_root = root / "inputs"
    input_root.mkdir()
    grouping = b"synthetic reviewed grouping declaration\n"
    (input_root / "grouping.json").write_bytes(grouping)
    payloads = [_request(input_root, index) for index in (1, 2)]
    items = tuple(
        LRABatchItem(f"component-{index}", payload)
        for index, payload in enumerate(payloads)
    )
    binding = _binding(root)
    identity = capture_code_identity(binding)
    products = [
        publish_result(
            _Result(float(index), "lake"),
            binding,
            validate_request(payload, input_root=input_root),
            destination=root / "products" / f"component-{index}",
            input_root=input_root,
            code_identity=identity,
        )
        for index, payload in enumerate(payloads, 1)
    ]
    outcomes = [
        LRABatchItemResult(
            0,
            items[0].item_id,
            items[0].request_sha256,
            "completed",
            products[0],
            items[0].request_sha256,
            False,
        )
    ]
    if second_status == "completed":
        outcomes.append(
            LRABatchItemResult(
                1,
                items[1].item_id,
                items[1].request_sha256,
                "completed",
                products[1],
                items[1].request_sha256,
                False,
            )
        )
    else:
        outcomes.append(
            LRABatchItemResult(
                1,
                items[1].item_id,
                items[1].request_sha256,
                "refused",
                canonical_error=canonical_json(
                    {
                        "status": "refused",
                        "reason_code": "synthetic_refusal",
                        "detail": "retained test refusal",
                    }
                ),
            )
        )
    identity_rows = [
        {"item_id": item.item_id, "request_sha256": item.request_sha256}
        for item in items
    ]
    batch_sha256 = hashlib.sha256(canonical_json(identity_rows).encode()).hexdigest()
    report = root / "batch"
    batch = LRABatchResult(batch_sha256, report, tuple(outcomes), False)
    finish_attempt(batch)
    summary = (report / "summary/receipt.json").read_bytes()
    plan = RegionalComponentPlan(
        component_set_id="synthetic-components",
        regional_support_id="region-1",
        bin_id="test-bin",
        bin_bounds_bp=(5400, 5600),
        ordered_item_ids=tuple(item.item_id for item in items),
        grouping_evidence_path="grouping.json",
        grouping_evidence_sha256=hashlib.sha256(grouping).hexdigest(),
        batch_summary_sha256=hashlib.sha256(summary).hexdigest(),
    )
    return input_root, items, batch, plan
