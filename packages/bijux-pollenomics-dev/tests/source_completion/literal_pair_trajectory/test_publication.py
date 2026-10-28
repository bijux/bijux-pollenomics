"""Keep authenticated aggregate publication separate from native aliquot observations."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.literal_pair_trajectory.publication import (
    CAPTURE_SHA256,
    NATIVE_PLAN_SHA256,
    public_summary,
    read_capture,
)


def test_projection_preserves_aggregate_values_and_excludes_private_rows() -> None:
    original: dict[str, Any] = {key: {} for key in ("source", "scenario", "admissions")}
    original.update(
        taxa=["Alnus", "Plantago lanceolata"],
        family_native_sample_population=121,
        family_exact_max_error="1/20",
        binary64_confidence=0.9995867768595041,
        actual_union_bound_fraction="112589990684259/2251799813685248",
        coverage=[],
        transitions=[],
        joint_lake_relations=[],
        private_aliquot_witness_sha256="private",
        unexpected_native_aliquots=[1],
        bins=[
            {
                "dataset_id": "53995",
                "bin_id": 5,
                "point": [0.7431761786600496, 0.25682382133995035],
                "lower": [0.6408811038833098, 0.17006682536528694],
                "upper": [0.8299331746347131, 0.3591188961166902],
                "source_pointers": ["private"],
                "native_pair_datum": ["private"],
                "unexpected_future_detail": "private",
            }
        ],
    )
    saved = deepcopy(original)
    public = public_summary(original)
    assert original == saved
    assert public["bins"][0]["point"] == original["bins"][0]["point"]
    assert public["bins"][0]["lower"] == original["bins"][0]["lower"]
    assert public["bins"][0]["upper"] == original["bins"][0]["upper"]
    assert public["binary64_confidence"] == original["binary64_confidence"]
    assert (
        not {"source_pointers", "native_pair_datum", "unexpected_future_detail"}
        & public["bins"][0].keys()
    )
    assert (
        "private_aliquot_witness_sha256" not in public
        and "unexpected_native_aliquots" not in public
    )
    assert (
        public["contrast_direction"]["axis"]
        == "increasing native calendar BP, younger to older"
    )


def fake_capture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Construct a source-free receipt packet for native custody boundary tests."""
    payloads: dict[str, Any] = {
        "report.json": {
            "family_native_sample_population": 3,
            "coverage": [{"admitted_samples": 2}],
        },
        "terminal.json": {
            "native_exit": 0,
            "plan_sha256": NATIVE_PLAN_SHA256,
            "stages": [{"native_exit": 0} for _ in range(5)],
        },
        "independent-verification.json": {
            "native_exit": 0,
            "all_native_samples": 3,
            "actual_intervals_checked": 2,
        },
        "protocol.json": {},
    }
    for name, payload in payloads.items():
        if name == "independent-verification.json":
            payload["report_sha256"] = CAPTURE_SHA256["report.json"]
        path = tmp_path / name
        path.write_text(json.dumps(payload))
        monkeypatch.setitem(
            CAPTURE_SHA256, name, hashlib.sha256(path.read_bytes()).hexdigest()
        )
    (tmp_path / "method.md").write_text("Declared counting scenario")
    monkeypatch.setitem(
        CAPTURE_SHA256,
        "method.md",
        hashlib.sha256((tmp_path / "method.md").read_bytes()).hexdigest(),
    )
    return tmp_path


def test_complete_successful_receipt_packet_is_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture = fake_capture(tmp_path, monkeypatch)
    result = read_capture(capture)
    assert result["report.json"]["family_native_sample_population"] == 3


@pytest.mark.parametrize("name", list(CAPTURE_SHA256))
def test_any_capture_byte_change_refuses_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    capture = fake_capture(tmp_path, monkeypatch)
    with (capture / name).open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="hash differs"):
        read_capture(capture)


@pytest.mark.parametrize(
    "failure", ["producer", "observer", "population", "interval_population"]
)
def test_matching_hashes_cannot_replace_native_success_and_denominator_correspondence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    capture = fake_capture(tmp_path, monkeypatch)
    name = "terminal.json" if failure == "producer" else "independent-verification.json"
    payload = json.loads((capture / name).read_bytes())
    if failure in ("producer", "observer"):
        payload["native_exit"] = 1
    elif failure == "population":
        payload["all_native_samples"] = 4
    else:
        payload["actual_intervals_checked"] = 3
    (capture / name).write_text(json.dumps(payload))
    monkeypatch.setitem(
        CAPTURE_SHA256, name, hashlib.sha256((capture / name).read_bytes()).hexdigest()
    )
    with pytest.raises(ValueError, match="Successful native"):
        read_capture(capture)


def test_symlink_capture_is_not_accepted_as_physical_regular_source(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "other"
    raw.write_text("source")
    (tmp_path / "report.json").symlink_to(raw)
    with pytest.raises(ValueError, match="regular file"):
        read_capture(tmp_path)
