"""Challenge source-product construction, rehash closure and chronology."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_sources import (
    read_observation_source_products,
    reopen_observation_source_completion_receipt,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_sources import (
    receipt as receipt_module,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_sources.reading import (
    SourceRead,
)

from .test_sources import _started


def test_source_read_carrier_is_factory_only(tmp_path: Path) -> None:
    with pytest.raises(ValidationRefusal, match="governed filesystem reader"):
        SourceRead("independent_measured_vegetation", tmp_path, b"", "0" * 64)


def test_coherently_rehashed_embedded_unit_refuses(
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
    product["units"][0]["group_id"] = "forged-group"
    embedded["canonical_product_json"] = canonical_json(product)
    embedded["product_sha256"] = manifest_sha256(product)
    destination.write_text(canonical_json(payload) + "\n")
    with pytest.raises(ValidationRefusal, match="pinned source bytes"):
        reopen_observation_source_completion_receipt(
            destination,
            start_receipt=start,
            expected_receipt_sha256=manifest_sha256(payload),
        )


def test_completion_must_be_strictly_after_access_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start, _, _ = _started(tmp_path, monkeypatch)
    monkeypatch.setattr(receipt_module, "_utc_now", lambda: start.access_started_at_utc)
    destination = tmp_path / "equal-time.json"
    with pytest.raises(ValidationRefusal, match="identity or claim boundary"):
        read_observation_source_products(start, completion_destination=destination)
    assert not destination.exists()
