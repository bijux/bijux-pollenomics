"""Current physical custody is independent from historical native execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.method_certification import (
    native_r_comparison as consumer,
)


@pytest.fixture
def ownership(tmp_path: Path) -> dict[str, Any]:
    code = [f"packages/own/source_{i}.py" for i in range(116)]
    data = [
        consumer._POLICY,
        "data/method-certification/native-r-finite-covariance/capture/capture.json",
        *[f"data/own/metadata_{i}.json" for i in range(288)],
    ]
    for relative in code + data:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"Own synthetic custody input\n")
    return {
        "owner_id": consumer._OWNER,
        "role": "generated_owner",
        "paths": sorted(consumer._OUTPUTS),
        "producer_paths": code,
        "producer_inputs": data,
    }


def collect(tmp_path: Path, ownership: dict[str, Any]) -> dict[str, Any]:
    (tmp_path / consumer._POLICY).write_text(json.dumps({"owners": [ownership]}))
    return dict(consumer._consumer_inputs(tmp_path, "a" * 64, "finite-covariance"))


def test_current_physical_roles_keep_the_declared_native_profile(
    tmp_path: Path, ownership: dict[str, Any]
) -> None:
    inputs = collect(tmp_path, ownership)
    assert len(inputs["code_sha256"]) == 116
    assert len(inputs["data_sha256"]) == 290
    assert inputs["capture_profile"] == "finite-covariance"
    assert inputs["capture_manifest_sha256"] == "a" * 64
    assert not consumer._OUTPUTS.intersection(inputs["code_sha256"])
    assert not consumer._OUTPUTS.intersection(inputs["data_sha256"])


@pytest.mark.parametrize("role", ["producer_paths", "producer_inputs"])
@pytest.mark.parametrize("defect", ["missing", "extra", "duplicate", "output"])
def test_current_physical_inventory_refuses_role_or_population_drift(
    tmp_path: Path, ownership: dict[str, Any], role: str, defect: str
) -> None:
    if defect == "missing":
        ownership[role].pop()
    elif defect == "extra":
        ownership[role].append("packages/own/extra.py")
    elif defect == "duplicate":
        ownership[role][-1] = ownership[role][0]
    else:
        ownership[role][-1] = sorted(consumer._OUTPUTS)[0]
    with pytest.raises(ValueError, match="Exact disjoint"):
        collect(tmp_path, ownership)
