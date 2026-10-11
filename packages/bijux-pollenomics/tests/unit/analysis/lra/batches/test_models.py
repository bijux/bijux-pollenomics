"""Requests are owned identities, never mutable batch checkpoints."""

from __future__ import annotations

import pytest

from bijux_pollenomics.analysis.lra.batches.models import LRABatchItem, LRABatchLimits
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal


def test_item_preserves_nested_request_identity() -> None:
    payload = {"configuration": {"seed": 7}}
    item = LRABatchItem("point-1", payload)
    payload["configuration"]["seed"] = 12
    assert item.payload()["configuration"]["seed"] == 7
    changed_copy = item.payload()
    changed_copy["configuration"]["seed"] = 13
    assert item.payload()["configuration"]["seed"] == 7
    assert item.request_sha256 != LRABatchItem("point-1", payload).request_sha256


@pytest.mark.parametrize("payload", [{"value": float("nan")}, {"value": object()}])
def test_non_json_request_is_refused(payload: dict[str, object]) -> None:
    with pytest.raises(LRARefusal) as error:
        LRABatchItem("point", payload)
    assert error.value.reason_code == "invalid_lra_batch_payload"


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_resource_limits_require_positive_integers(value: object) -> None:
    with pytest.raises(LRARefusal):
        LRABatchLimits(max_workers=value)  # type: ignore[arg-type]
