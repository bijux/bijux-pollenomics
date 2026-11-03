"""Exercise real geographic, nominal, serialization and scoring boundaries."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
from types import FrameType
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer import (
    predictions,
    study,
)

from .test_scoring import complete_candidate


def _put(root: Path, name: str, value: Any) -> dict[str, Any]:
    raw = json.dumps(value, allow_nan=False, sort_keys=True).encode()
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def portable_source(
    repository: Path, *, counts: tuple[int, int] = (2, 8)
) -> tuple[dict[str, Any], Path]:
    """Place the toy at its saved equatorial WGS84 distances, in metres."""
    repository.mkdir(parents=True, exist_ok=True)
    (repository / "artifacts").mkdir()
    candidate = complete_candidate()
    metadata = {
        "sample_id": "held-out",
        "site_id": "fixture-site",
        "bin_id": "cal-bp-2700-3200",
        "age_type": "calendar_bp",
        "age_support_bp": [[2700, 3200]],
    }
    geometry = _put(
        repository, "observations/held-out-geometry.json", {"sample_metadata": metadata}
    )
    raw = _put(
        repository,
        "observations/held-out-raw.json",
        {
            "data_kind": "source_observations",
            "taxa": ["Betula", "Ulmus"],
            "sample": {**metadata, "counts": list(counts)},
        },
    )
    distances = {
        "local-far": 400000.0,
        "local-near": 200000.0,
        "regional": 600000.0,
        "held-out": 0.0,
    }
    sites: list[dict[str, Any]] = [
        {
            "owner_id": owner,
            "place_id": owner,
            "block_id": "solsoe" if owner == "held-out" else "sweden",
            "target_eligible": owner != "regional",
            "latitude": 0.0,
            "longitude": distance / 6378137.0 * 180 / math.pi,
            "source_radius_m": 100000.0,
            "target_radius_m": None if owner == "regional" else 1000.0,
            "coordinate_uncertainty_m": 0.0,
        }
        for owner, distance in distances.items()
    ]
    roles = []
    for site in sites:
        if not site["target_eligible"]:
            continue
        owner = site["owner_id"]
        required = [
            "regional",
            *(value for value in distances if value not in {owner, "regional"}),
        ]
        roles.append(
            {
                "case_id": candidate["case"]["case_id"]
                if owner == "held-out"
                else "case:" + owner,
                "target_id": owner,
                "heldout_block_id": site["block_id"],
                "required_source_owner_ids": required,
            }
        )
    invalid = {
        "path": "forbidden/observation-must-not-open",
        "bytes": 1,
        "sha256": "f" * 64,
    }
    packet = {
        "schema_version": "krageholm-geographic-transfer-inputs.v1",
        "axis": ["Betula", "Ulmus"],
        "replicates": 4,
        "sites": sites,
        "target_roles": roles,
        "candidate_cases": [candidate],
        "observation_refs": [
            {"target_id": "held-out", "raw": raw, "geometry": geometry},
            *(
                {"target_id": owner, "raw": dict(invalid), "geometry": dict(invalid)}
                for owner in ("local-far", "local-near")
            ),
        ],
        "prior_dispositions": [
            {"status": "refused" if index >= 9 else "predicted", "prior_slot": index}
            for index in range(54)
        ],
        "sources": [],
        "summary": {"raw_target_files_decoded": 0},
    }
    policy = {
        "blocks": {
            "sweden": ["local-far", "local-near", "regional"],
            "solsoe": ["held-out"],
        },
        "target_places": ["local-far", "local-near", "held-out"],
        "source_only_places": ["regional"],
        "source_radius_m": 100000.0,
        "target_radius_m": 1000.0,
        "coordinate_uncertainty_m": 0.0,
        "minimum_buffer_m": 20000.0,
    }
    protocol = {
        "model": {"scales_km": [20.0, 100.0]},
        "geography": policy,
        "limits": {
            "producer_wall_seconds": 60,
            "observer_wall_seconds": 60,
            "max_rss_bytes": 512 * 1024**2,
            "max_output_bytes": 16 * 1024**2,
        },
    }
    protocol_path = repository / "protocol.json"
    protocol_path.write_text(json.dumps(protocol))
    return packet, protocol_path


def _intake(monkeypatch: pytest.MonkeyPatch, packet: dict[str, Any]) -> None:
    monkeypatch.setattr(study, "load_inputs", lambda *_: deepcopy(packet))
    monkeypatch.setattr(
        study,
        "code_state",
        lambda *_: {"head": "fixture", "index_sha256": "0" * 64, "python_files": {}},
    )
    monkeypatch.setattr(study, "check_sources", lambda *_: None)


def test_complete_workflow_authenticates_every_member_before_one_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    packet, protocol = portable_source(repository)
    _intake(monkeypatch, packet)
    output = repository / "artifacts/result"
    original_read = Path.read_bytes
    reads: list[Path] = []
    target_raw = repository / packet["observation_refs"][0]["raw"]["path"]

    def observed(path: Path) -> bytes:
        if path == target_raw:
            manifest_path = output / "prediction-manifest.json"
            assert manifest_path in reads
            manifest = json.loads(original_read(manifest_path))
            assert set(manifest["files"]) == {
                "inputs",
                "admission",
                "nominal_handoff",
                "predictions",
            }
            after_manifest = reads[reads.index(manifest_path) + 1 :]
            for pin in manifest["files"].values():
                member = output / pin["path"]
                assert member in after_manifest
                raw = original_read(member)
                assert (
                    len(raw) == pin["bytes"]
                    and hashlib.sha256(raw).hexdigest() == pin["sha256"]
                )
        reads.append(path)
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", observed)
    result = study.produce(repository, protocol, output)
    assert result["source_guards_passed"] is True
    assert reads.count(target_raw) == 1
    rows = json.loads(original_read(output / "predictions.json"))
    assert len(rows) == 6
    assert sum(row["prediction"] is None for row in rows) == 4
    computed = [row["prediction"] for row in rows if row["prediction"] is not None]
    assert len(computed) == 2
    assert all(
        row["ensemble"]["valid_mask"] == [True, True, True, False] for row in computed
    )
    assert all(
        row["ensemble"]["inherited_undefined_replicates"] == 1 for row in computed
    )
    access = json.loads(original_read(output / "observation-access.json"))
    assert len(access) == 1 and access[0]["target_id"] == "held-out"
    assert (
        access[0]["prediction_freeze_sha256"] == result["prediction_manifest"]["sha256"]
    )
    scores = json.loads(original_read(output / "scores.json"))
    assert (
        sum(row["status"] == "not_executed_geographic_refusal" for row in scores) == 4
    )
    assert all(
        len(row["comparisons"]) == 6
        for row in scores
        if row["status"] == "evaluated_admitted_observation"
    )


@pytest.mark.parametrize("tamper", ["predictions.json", "prediction-manifest.json"])
def test_closed_byte_tampering_prevents_any_observation_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    repository = tmp_path / "repository"
    packet, protocol = portable_source(repository)
    _intake(monkeypatch, packet)
    output = repository / "artifacts/result"
    original_read = Path.read_bytes
    touched, observed = False, []

    def altered(path: Path) -> bytes:
        nonlocal touched
        if path == output / "prediction-manifest.json" and not touched:
            touched = True
            member = output / tamper
            member.write_bytes(original_read(member) + b" ")
        if path.name.endswith("-raw.json"):
            observed.append(path)
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", altered)
    with pytest.raises(ValueError, match="Serialized scientific member changed"):
        study.produce(repository, protocol, output)
    assert touched and observed == []
    assert not (output / "scores.json").exists()


def test_failed_nominal_gate_preserves_three_failures_and_never_calls_new_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    packet, protocol = portable_source(repository)
    for row in packet["candidate_cases"][0]["nominal"]["reference_predictions"]:
        row["pollen_fraction"] = [0.99, 0.01]
    _intake(monkeypatch, packet)
    output = repository / "artifacts/result"
    calls = []
    old_profile = sys.getprofile()

    def track(frame: FrameType, event: str, _: Any) -> None:
        if event == "call" and frame.f_code is predictions.predict_candidate.__code__:
            calls.append(frame.f_code.co_name)

    try:
        sys.setprofile(track)
        with pytest.raises(ValueError, match="Nominal source correspondence failed"):
            study.produce(repository, protocol, output)
    finally:
        sys.setprofile(old_profile)
    facts = json.loads((output / "nominal-handoff.json").read_bytes())
    assert len(facts) == 1 and facts[0]["passed"] is False
    assert len(facts[0]["failures"]) == facts[0]["forward_calls"] == 3
    assert calls == []
    assert not (output / "predictions.json").exists()
    assert not (output / "observation-access.json").exists()


def test_changed_held_label_changes_only_postfreeze_scores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed = []
    for name, counts in (("first", (2, 8)), ("second", (8, 2))):
        repository = tmp_path / name
        packet, protocol = portable_source(repository, counts=counts)
        _intake(monkeypatch, packet)
        output = repository / "artifacts/result"
        study.produce(repository, protocol, output)
        observed.append(
            (
                (output / "predictions.json").read_bytes(),
                json.loads((output / "scores.json").read_bytes()),
            )
        )
    assert observed[0][0] == observed[1][0]
    assert observed[0][1] != observed[1][1]
