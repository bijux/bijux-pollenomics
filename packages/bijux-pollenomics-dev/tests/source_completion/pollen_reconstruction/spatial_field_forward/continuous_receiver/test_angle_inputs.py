"""Original exact-law metadata, opaque predecessor bindings and unchanged limits."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments import (
    inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.contracts import (
    OWNERS,
)

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/spatial-field-forward/continuous-receiver/receiver-angle-moments.json"
)


def profile() -> dict[str, Any]:
    return inputs.decode(PROTOCOL.read_bytes())


def test_maintained_protocol_satisfies_its_own_contract() -> None:
    inputs.validate_protocol(profile())


@pytest.mark.parametrize("value", [0.1, True, 1, "0.1", "2/4", "01", "1/-2"])
def test_original_fraction_requires_exact_canonical_spelling(value: object) -> None:
    with pytest.raises(ValueError):
        inputs.rational(value)


def test_original_binary64_ratio_is_never_decimal_rounded() -> None:
    exact = "5420552529561581/9007199254740992"
    assert inputs.rational(exact) == Fraction(5420552529561581, 9007199254740992)
    assert inputs.rational(exact) != Fraction(str(float(Fraction(exact))))


@pytest.mark.parametrize(
    "group,key,value",
    [
        ("resources", "integration_work_seconds", 161),
        ("resources", "wall_seconds", 181),
        ("resources", "all_output_bytes", 5000001),
        ("independent_resources", "wall_seconds", 181),
        ("numerical_contract", "epsilon_exact", "1/100000000"),
        ("numerical_contract", "coefficient_population", 17),
        ("law", "native_prefix_recapture", 0),
        ("law", "historical_A_authenticated", True),
    ],
)
def test_protocol_cannot_relax_original_law_or_budgets(
    group: str, key: str, value: object
) -> None:
    candidate = profile()
    candidate[group][key] = value
    with pytest.raises(ValueError):
        inputs.validate_protocol(candidate)


def synthetic_inputs(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    """Use invalid-JSON predecessor bodies to prove they are bound opaquely."""
    original = profile()
    pins: dict[str, Any] = {}
    for name in inputs.PUBLIC_INPUTS:
        body = b"opaque predecessor: intentionally not JSON nor a target fixture"
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        pins[name] = inputs.identity(body)
    old_name = "reports/captured-continuous-protocol.json"
    old = root / old_name
    old.write_bytes(b"opaque capture protocol")
    geometry = {
        "coefficient_A": "1/2",
        "receiver_radius_m": "1",
        "outer_radius_m": "4",
        "first_anchor_xy_m": ["1000", "0"],
        "second_anchor_xy_m": ["2000", "0"],
    }
    frozen = {
        "schema_version": "continuous-receiver-input-freeze.v1",
        "source_commit": inputs.CAPTURE_SOURCE,
        "historical_A_authenticated": False,
        "input_files": pins,
        "protocol_file": {"path": old_name, **inputs.identity(old.read_bytes())},
        "native_prefix": [
            {"taxon": taxon, "A": {"numerator": 1, "denominator": 2}}
            for taxon in ("Betula", "Ulmus")
        ],
        "cases": [
            {
                "case_index": index,
                "core": core,
                "taxon": taxon,
                "geometry": deepcopy(geometry),
            }
            for index, (core, taxon) in enumerate(OWNERS)
        ],
    }
    body = json.dumps(frozen, separators=(",", ":")).encode()
    assert len(body) < 3915
    body += b" " * (3915 - len(body))
    sha = hashlib.sha256(body).hexdigest()
    monkeypatch.setattr(inputs, "FREEZE_SHA", sha)
    original["input_freeze"]["sha256"] = sha
    freeze = root / inputs.FREEZE
    freeze.parent.mkdir(parents=True)
    freeze.write_bytes(body)
    protocol = root / PROTOCOL
    protocol.parent.mkdir(parents=True, exist_ok=True)
    protocol.write_text(json.dumps(original))
    return protocol, frozen


def test_authenticated_reader_uses_only_original_rational_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol, frozen = synthetic_inputs(tmp_path, monkeypatch)
    result = inputs.read_inputs(tmp_path, protocol)
    assert len(result.geometries) == 6
    assert result.freeze == frozen
    assert all(model.coefficient == Fraction(1, 2) for model in result.geometries)
    assert len(result.identities) == 5
    predecessor = tmp_path / inputs.PUBLIC_INPUTS[0]
    predecessor.write_bytes(predecessor.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="oversized|identity differs"):
        inputs.read_inputs(tmp_path, protocol)


def test_metadata_duplicate_and_nonfinite_values_are_refused() -> None:
    for raw in (b'{"owner":1,"owner":2}', b'{"value":NaN}', b'{"value":1e999}'):
        with pytest.raises(ValueError):
            inputs.decode(raw)


def test_symbolic_input_route_is_refused(tmp_path: Path) -> None:
    (tmp_path / "actual").write_bytes(b"owned")
    (tmp_path / "alias").symlink_to("actual")
    with pytest.raises(ValueError, match="Symbolic"):
        inputs.read_regular(tmp_path, "alias", 100)
