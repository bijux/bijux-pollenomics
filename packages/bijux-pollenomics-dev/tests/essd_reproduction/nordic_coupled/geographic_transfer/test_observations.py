"""Role-specific original observation custody after a prediction freeze."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.observations import (
    ObservationReader,
)

from .test_workflow import _put, portable_source


def _reader(
    repository: Path, packet: dict[str, Any], freeze: str = "a" * 64
) -> ObservationReader:
    admission = {
        "roles": [
            {
                "target_id": target,
                "status": "admitted" if target == "held-out" else "refused",
            }
            for target in ("held-out", "local-far", "local-near")
        ]
    }
    return ObservationReader(repository, packet, admission, freeze)


def test_valid_observation_has_one_counted_denominator_and_exact_freeze_identity(
    tmp_path: Path,
) -> None:
    packet, _ = portable_source(tmp_path)
    reader = _reader(tmp_path, packet, "b" * 64)
    assert reader.read("held-out") == {"Betula": 2, "Ulmus": 8}
    assert len(reader.accesses) == 1
    assert reader.accesses[0]["prediction_freeze_sha256"] == "b" * 64
    assert reader.accesses[0]["raw_reference"] == packet["observation_refs"][0]["raw"]
    assert (
        reader.accesses[0]["scope"]
        == "previously_exposed_role_specific_access_not_globally_unread"
    )
    with pytest.raises(ValueError, match="One scoring-role"):
        reader.read("held-out")
    assert len(reader.accesses) == 1


@pytest.mark.parametrize("freeze", ["", "a" * 63, "z" * 64])
def test_unbound_freeze_string_is_refused(tmp_path: Path, freeze: str) -> None:
    packet, _ = portable_source(tmp_path)
    with pytest.raises(ValueError, match="Authenticated new prediction freeze"):
        _reader(tmp_path, packet, freeze)


def test_refused_target_is_rejected_before_any_file_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet, _ = portable_source(tmp_path)
    reader = _reader(tmp_path, packet)
    reads = []
    original = Path.read_bytes

    def observed(path: Path) -> bytes:
        reads.append(path)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", observed)
    with pytest.raises(ValueError, match="geographically refused"):
        reader.read("local-far")
    assert reads == [] and reader.accesses == []


def test_changed_original_bytes_are_not_accepted_as_a_new_observation(
    tmp_path: Path,
) -> None:
    packet, _ = portable_source(tmp_path)
    reader = _reader(tmp_path, packet)
    raw = tmp_path / packet["observation_refs"][0]["raw"]["path"]
    raw.write_bytes(raw.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Original scoring object changed"):
        reader.read("held-out")
    assert reader.accesses == []


@pytest.mark.parametrize(
    "mutation",
    [
        "axis",
        "boolean",
        "fractional",
        "negative",
        "empty_mass",
        "unsafe_integer",
        "dimension",
        "missing_metadata",
        "extra_metadata",
        "wrong_owner",
        "renamed_both",
        "wrong_time_both",
        "wrong_age_type_both",
        "data_kind",
    ],
)
def test_authenticated_source_still_requires_exact_owner_axis_support_and_counts(
    tmp_path: Path, mutation: str
) -> None:
    packet, _ = portable_source(tmp_path)
    ref = packet["observation_refs"][0]
    raw = json.loads((tmp_path / ref["raw"]["path"]).read_bytes())
    geometry = json.loads((tmp_path / ref["geometry"]["path"]).read_bytes())
    sample = raw["sample"]
    if mutation == "axis":
        raw["taxa"] = ["Ulmus", "Betula"]
    elif mutation in {"boolean", "fractional", "negative", "unsafe_integer"}:
        sample["counts"][0] = {
            "boolean": True,
            "fractional": 0.5,
            "negative": -1,
            "unsafe_integer": 2**53 + 1,
        }[mutation]
    elif mutation == "empty_mass":
        sample["counts"] = [0, 0]
    elif mutation == "dimension":
        sample["counts"] = [1, 2, 3]
    elif mutation == "missing_metadata":
        del sample["site_id"]
    elif mutation == "extra_metadata":
        sample["invented"] = "unbound"
    elif mutation == "wrong_owner":
        sample["sample_id"] = "other-source"
    elif mutation == "renamed_both":
        sample["sample_id"] = geometry["sample_metadata"]["sample_id"] = "other-source"
    elif mutation == "wrong_time_both":
        sample["age_support_bp"] = geometry["sample_metadata"]["age_support_bp"] = [
            [2700, 3300]
        ]
    elif mutation == "wrong_age_type_both":
        sample["age_type"] = geometry["sample_metadata"]["age_type"] = (
            "uncalibrated_radiocarbon"
        )
    else:
        raw["data_kind"] = "modeled_estimate"
    ref["raw"] = _put(tmp_path, ref["raw"]["path"], raw)
    ref["geometry"] = _put(tmp_path, ref["geometry"]["path"], geometry)
    reader = _reader(tmp_path, packet)
    with pytest.raises(ValueError):
        reader.read("held-out")
    assert reader.accesses == []
