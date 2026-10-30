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
    """Construct inert own files for the complete declared physical source roles."""
    required_code = set(consumer._LAYOUT_CODE_INPUTS)
    code = sorted(required_code) + [
        f"packages/own/source_{i}.py" for i in range(116 - len(required_code))
    ]
    required_data = {
        *consumer._LAYOUT_STATIC_DATA,
        consumer._POLICY,
        "data/method-certification/native-r-finite-covariance/capture/capture.json",
        "data/method-certification/native-r-finite-covariance/source-transport.json",
    }
    data = sorted(required_data) + [
        f"data/own/metadata_{i}.json" for i in range(290 - len(required_data))
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


@pytest.mark.parametrize("defect", ["missing_file", "replaced_declaration"])
def test_selected_finite_transport_is_required_at_unchanged_cardinality(
    tmp_path: Path, ownership: dict[str, Any], defect: str
) -> None:
    """A valid baseline must refuse a missing or substituted selected descriptor."""
    collect(tmp_path, ownership)
    descriptor = (
        "data/method-certification/native-r-finite-covariance/source-transport.json"
    )
    assert descriptor in ownership["producer_inputs"]
    if defect == "missing_file":
        (tmp_path / descriptor).unlink()
        expected = "independently owned regular file"
    else:
        replacement = "data/own/replacement-transport.json"
        (tmp_path / replacement).write_bytes(b"Own unrelated descriptor\n")
        inputs = ownership["producer_inputs"]
        inputs[inputs.index(descriptor)] = replacement
        expected = "Exact disjoint native consumer code/data declaration"
    assert len(ownership["producer_inputs"]) == 290
    with pytest.raises(ValueError, match=expected):
        collect(tmp_path, ownership)
