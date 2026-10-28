"""Outcome-role freezes and raw byte, owner, support and count admission."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.outcomes import (
    OutcomeReader,
)

PREDICTION_FREEZE = "a" * 64
SELECTION_FREEZE = "b" * 64


def store_object(archive: Path, name: str, value: Any) -> dict[str, Any]:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    sha = hashlib.sha256(raw).hexdigest()
    target = archive / "objects" / sha[:2] / sha
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {"path": name, "bytes": len(raw), "sha256": sha}


def saved_outcomes(
    root: Path, *, owners: int = 15, first_counts: tuple[int, int] = (3, 1)
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Keep the complete source fixture small and independent of count-free fits."""
    archive = root / "archive"
    archive.mkdir(parents=True)
    refs, geometries = [], []
    for index in range(owners):
        name = f"site-{index:02}"
        metadata = {
            "site_id": name,
            "bin_id": "author-TW5",
            "coordinate": 1500,
            "age_type": "calendar_bp",
            "age_support_bp": [[1250, 1750]],
        }
        geometries.append(
            store_object(
                archive, name + "-geometry.json", {"sample_metadata": metadata}
            )
        )
        counts = list(first_counts if index == 0 else (3, 1))
        reference = store_object(
            archive,
            name + "-raw.json",
            {
                "data_kind": "source_observations",
                "taxa": ["a", "b"],
                "sample": {**metadata, "counts": counts},
            },
        )
        refs.append({**reference, "record_id": "owner:" + name})
    return (
        archive,
        {"taxa": ["a", "b"], "observation_refs": refs},
        {"author_inputs": geometries},
    )


def changed_observation(archive: Path, packet: dict[str, Any], mutation: str) -> None:
    reference = packet["observation_refs"][0]
    path = archive / "objects" / reference["sha256"][:2] / reference["sha256"]
    value = json.loads(path.read_bytes())
    if mutation == "boolean":
        value["sample"]["counts"] = [True, 1]
    elif mutation == "float":
        value["sample"]["counts"] = [3.0, 1]
    elif mutation == "negative":
        value["sample"]["counts"] = [-1, 1]
    elif mutation == "zero_total":
        value["sample"]["counts"] = [0, 0]
    elif mutation == "unsafe_total":
        value["sample"]["counts"] = [2**53, 1]
    elif mutation == "count_axis":
        value["sample"]["counts"] = [3, 1, 0]
    elif mutation == "taxon_order":
        value["taxa"].reverse()
    elif mutation == "foreign_taxon":
        value["taxa"][0] = "foreign"
    elif mutation == "owner":
        value["sample"]["site_id"] = "another-site"
    elif mutation == "chronology":
        value["sample"]["age_type"] = "radiocarbon_bp"
    elif mutation == "support":
        value["sample"]["age_support_bp"] = [[1000, 2000]]
    elif mutation == "coordinate":
        value["sample"]["coordinate"] = 1499
    elif mutation == "extra_field":
        value["sample"]["unadmitted"] = "field"
    elif mutation == "kind":
        value["data_kind"] = "model_prediction"
    else:
        raise AssertionError("Unknown fixture mutation")
    packet["observation_refs"][0] = {
        **store_object(archive, reference["path"], value),
        "record_id": reference["record_id"],
    }


def test_role_specific_freezes_and_access_journal(tmp_path: Path) -> None:
    archive, packet, protocol = saved_outcomes(tmp_path, owners=2)
    reader = OutcomeReader(archive, packet, protocol, PREDICTION_FREEZE)
    first, second = [row["record_id"] for row in packet["observation_refs"]]
    assert reader.read(second, outer_target=first, role="inner_training") == {
        "a": 3,
        "b": 1,
    }
    assert reader.accesses[0]["freeze_sha256"] == PREDICTION_FREEZE
    for record, role in (
        (first, "inner_training"),
        (first, "outer_scoring"),
        (second, "outer_scoring"),
        (second, "unknown"),
    ):
        with pytest.raises(ValueError):
            reader.read(record, outer_target=first, role=role)
    assert len(reader.accesses) == 1
    reader.selection_freeze = SELECTION_FREEZE
    assert reader.read(first, outer_target=first, role="outer_scoring") == {
        "a": 3,
        "b": 1,
    }
    assert reader.accesses[-1]["freeze_sha256"] == SELECTION_FREEZE
    assert reader.accesses[-1]["observed_record_id"] == first
    assert reader.accesses[-1]["role"] == "outer_scoring"


@pytest.mark.parametrize("freeze", ["", "a" * 63, "a" * 65, "G" * 64])
def test_prediction_freeze_identity_required(tmp_path: Path, freeze: str) -> None:
    archive, packet, protocol = saved_outcomes(tmp_path, owners=2)
    with pytest.raises(ValueError, match="freeze"):
        OutcomeReader(archive, packet, protocol, freeze)


@pytest.mark.parametrize("freeze", [None, "", "a" * 63, "a" * 65, "G" * 64])
def test_outer_selection_freeze_identity_required(
    tmp_path: Path, freeze: str | None
) -> None:
    archive, packet, protocol = saved_outcomes(tmp_path, owners=2)
    reader = OutcomeReader(archive, packet, protocol, PREDICTION_FREEZE)
    reader.selection_freeze = freeze
    with pytest.raises(ValueError, match="freeze"):
        reader.read(
            packet["observation_refs"][0]["record_id"],
            outer_target=packet["observation_refs"][0]["record_id"],
            role="outer_scoring",
        )
    assert reader.accesses == []


@pytest.mark.parametrize(
    "mutation",
    [
        "boolean",
        "float",
        "negative",
        "zero_total",
        "unsafe_total",
        "count_axis",
        "taxon_order",
        "foreign_taxon",
        "owner",
        "chronology",
        "support",
        "coordinate",
        "extra_field",
        "kind",
    ],
)
def test_raw_count_owner_axis_and_support_admission(
    tmp_path: Path, mutation: str
) -> None:
    archive, packet, protocol = saved_outcomes(tmp_path, owners=2)
    changed_observation(archive, packet, mutation)
    reader = OutcomeReader(archive, packet, protocol, PREDICTION_FREEZE)
    with pytest.raises(ValueError, match="owner|support|chronology|denominator"):
        reader.read(
            packet["observation_refs"][0]["record_id"],
            outer_target=packet["observation_refs"][1]["record_id"],
            role="inner_training",
        )
    assert reader.accesses == []


@pytest.mark.parametrize("mutation", ["hash", "bytes", "missing", "symlink"])
def test_scoring_source_physical_identity(tmp_path: Path, mutation: str) -> None:
    archive, packet, protocol = saved_outcomes(tmp_path, owners=2)
    reference = packet["observation_refs"][0]
    path = archive / "objects" / reference["sha256"][:2] / reference["sha256"]
    if mutation == "hash":
        original = path.read_bytes()
        path.write_bytes(original.replace(b'"counts":[3,1]', b'"counts":[2,2]'))
        assert path.stat().st_size == len(original)
    elif mutation == "bytes":
        reference["bytes"] += 1
    elif mutation == "missing":
        path.unlink()
    else:
        other = tmp_path / "redirected.json"
        other.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(other)
    reader = OutcomeReader(archive, packet, protocol, PREDICTION_FREEZE)
    with pytest.raises(ValueError, match="identity|ordinary"):
        reader.read(
            reference["record_id"],
            outer_target=packet["observation_refs"][1]["record_id"],
            role="inner_training",
        )
    assert reader.accesses == []


def test_zero_taxon_is_retained_and_input_pins_unchanged(tmp_path: Path) -> None:
    archive, packet, protocol = saved_outcomes(tmp_path, owners=2, first_counts=(0, 4))
    before = deepcopy(packet), deepcopy(protocol)
    reader = OutcomeReader(archive, packet, protocol, PREDICTION_FREEZE)
    assert reader.read(
        packet["observation_refs"][0]["record_id"],
        outer_target=packet["observation_refs"][1]["record_id"],
        role="inner_training",
    ) == {"a": 0, "b": 4}
    assert (packet, protocol) == before
