"""Portable qualified-source projections without random draws or native models."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer import (
    inputs,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.inputs import (
    _Reader,
)

_AXIS = ["Betula", "Ulmus"]
_METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
_WINDOW = "cal-bp-2700-3200"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, allow_nan=False, sort_keys=True).encode()


def _fixture(
    root: Path, *, failed_verification: bool = False
) -> tuple[Path, dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=True)
    source_files: list[dict[str, Any]] = []

    def put(
        name: str, value: Any, *, raw: bool = False, original: bool = False
    ) -> dict[str, Any]:
        data = value if raw else _bytes(value)
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        pin = {
            "path": name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        if original:
            source_files.append(pin)
        return pin

    owners = {
        core: f"neotoma-{core}-{_WINDOW}"
        for core in ("KRAGMJNY", "BOKE", "BUS", "SOLSOE83")
    }
    coupled = put("original/coupled.json", {"axis": _AXIS}, original=True)
    lineage, geometry_pins = {}, {}
    for index, (core, owner) in enumerate(owners.items()):
        raw = put(
            f"original/{_WINDOW}/{core}-raw.json",
            b"UNDECODED SOURCE OBSERVATIONS\n",
            raw=True,
            original=True,
        )
        geometry: dict[str, Any] = {
            "basin": {"diameter_m": 160.0, "site_type": "lake"},
            "sample_metadata": {"sample_id": owner},
            "latitude": 55.0 + index / 10,
            "longitude": 13.0 + index / 10,
        }
        if core != "KRAGMJNY":
            geometry["inversion_rings"] = [
                {"outer_m": 500, "mean_m": 250.0},
                {"outer_m": 1000, "mean_m": 750.0},
            ]
            geometry["forward_rings"] = [{"outer_m": 1000}, {"outer_m": 100000}]
        geometry_pins[owner] = put(
            f"original/{_WINDOW}/{core}-geometry.json", geometry, original=True
        )
        lineage[owner] = {"core": core, "raw": raw}
    native_refs = []
    for core in ("BUS", "BOKE"):
        directory = "original/native/" + core
        request = put(
            directory + "/request.json",
            {
                "taxa": _AXIS,
                "local": {"samples": [{"sample_id": owners[core]}]},
                "regional": {"samples": [{"sample_id": owners["KRAGMJNY"]}]},
            },
            original=True,
        )
        kernel = put(
            directory + "/numerical/local_love/aux_Kloc.csv",
            b"saved kernel\n",
            raw=True,
            original=True,
        )
        cover = (
            b"index,Betula,Ulmus\n250.0,-0.1,1.1\n750.0,0.2,0.8\n"
            if core == "BOKE"
            else b"index,Betula,Ulmus\n250.0,0.8,0.2\n750.0,0.8,0.2\n"
        )
        cover_pin = put(
            directory + "/numerical/local_love/cover_mean.csv", cover, raw=True
        )
        regional = put(
            directory + "/numerical/regional_reveals/reconstruction.csv",
            b"Distance.weighting,Basin.type,coordinate,Betula.mean,Ulmus.mean\ngpm neutral,lake,2700.0,70.0,30.0\n",
            raw=True,
        )
        manifest = {
            "schema_version": "lra-product.v1",
            "retained_taxa": _AXIS,
            "files": {
                "request.json": request["sha256"],
                "numerical/local_love/cover_mean.csv": cover_pin["sha256"],
                "numerical/regional_reveals/reconstruction.csv": regional["sha256"],
            },
        }
        put(directory + "/manifest.json", manifest, original=True)
        native_refs.append({**kernel, "local_owner_id": owners[core]})
    put(
        f"original/{_WINDOW}/preparations.json",
        [
            {"regional_cutoff_m": 100000.0, "local_support_radius_m": 1000.0}
            for _ in range(3)
        ],
        original=True,
    )
    while len(source_files) < 141:
        index = len(source_files)
        put(
            f"original/source-{index}.bin",
            f"qualified original {index}".encode(),
            raw=True,
            original=True,
        )
    parent_pin = put("parent-protocol.json", {"sources": {"coupled_protocol": coupled}})
    parent = json.loads((root / parent_pin["path"]).read_bytes())
    ppe = [[5.106, 1.27] for _ in range(1024)]
    ppe_hash = hashlib.sha256(struct.pack("<dd", 5.106, 1.27) * 1024).hexdigest()
    samples = [[8, 2] for _ in range(1024)]
    count_hash = hashlib.sha256(struct.pack("<qq", 8, 2) * 1024).hexdigest()
    draws: dict[str, Any] = {
        "replicates": 1024,
        "seed": 20261027,
        "ppe_means": [5.106, 1.27],
        "ppe_sds": [0.303, 0.05],
        "ppe": ppe,
        "owners": [
            {
                "owner_id": owner,
                "counts": [8, 2],
                "stream_index": [index] * 8,
                "samples": samples,
            }
            for index, owner in enumerate(owners.values())
        ],
    }
    count_owners = {
        row["owner_id"]: {
            key: row[key] for key in ("owner_id", "counts", "stream_index")
        }
        | {"samples_sha256": count_hash}
        for row in draws["owners"]
    }
    cases: list[dict[str, Any]] = []
    cached: list[dict[str, Any]] = []
    folds: list[dict[str, Any]] = []
    nominal: list[dict[str, Any]] = []
    for core in ("BOKE", "BUS", "SOLSOE83"):
        target = owners[core]
        local_ids = sorted(
            owner for place, owner in owners.items() if place not in {core, "KRAGMJNY"}
        )
        if core == "SOLSOE83":
            local_ids = [owners["BUS"], owners["BOKE"]]
        case: dict[str, Any] = {
            "case_id": _WINDOW + ":" + core,
            "target_id": target,
            "regional_owner_id": owners["KRAGMJNY"],
            "local_owners": [
                {
                    "owner_id": owner,
                    "local_k": [[0.1, 0.1], [0.1, 0.1]],
                    "regional_k": [[0.2, 0.2], [0.2, 0.2]],
                }
                for owner in local_ids
            ],
            "regional_deposition": [0.2, 0.2],
            "forward_local_k": [[0.1, 0.1], [0.0, 0.0]],
            "forward_regional_k": [0.1, 0.1],
            "terrestrial_fraction": [1.0, 1.0],
            "distances_km": [300.0, 330.0],
            "selected_ring_index": 1,
        }
        cases.append(case)
        fold = {
            "case_id": case["case_id"],
            "target_id": target,
            "kernel_refs": native_refs if core == "SOLSOE83" else [],
        }
        folds.append(fold)
        mask = [index < 860 for index in range(1024)]
        method = {
            "valid_mask": mask,
            "refusals": [
                None if valid else "required_local_predictor_undefined"
                for valid in mask
            ],
            "summary": {"defined_replicates": 860},
            **{
                field: [[0.5, 0.5] if valid else [None, None] for valid in mask]
                for field in (
                    "cover",
                    "pollen",
                    "direct_pollen",
                    "physical_minus_direct",
                )
            },
        }
        allowed = {
            "case": case,
            "count_owners": [
                count_owners[owner] for owner in [owners["KRAGMJNY"], *local_ids]
            ],
            "ppe": {"samples_sha256": ppe_hash, "replicates": 1024},
        }
        cached.append(
            {
                "schema_version": "krageholm-predictive-ensemble.case.v1",
                "case_id": case["case_id"],
                "target_id": target,
                "axis": _AXIS,
                "replicates": 1024,
                "allowed_inputs": allowed,
                "regional_cover": [[0.7, 0.3] for _ in mask],
                "regional_refusals": [None] * 1024,
                "local_signed_cover": [
                    [[[0.8, 0.2], [0.8, 0.2]], [[-0.1, 1.1], [0.2, 0.8]]] for _ in mask
                ],
                "local_ring_refusals": [[[None, None], [None, None]] for _ in mask],
                "local_refusals": [
                    [None, None]
                    if valid
                    else ["local_selected_cover_out_of_bounds", None]
                    for valid in mask
                ],
                "methods": {name: deepcopy(method) for name in _METHODS},
            }
        )
        nominal.extend(
            {
                "case_id": case["case_id"],
                "method": name,
                "pollen_fraction": [0.5, 0.5],
                "vegetation_fraction": [0.5, 0.5],
                "regional_cover": [0.7, 0.3],
                "prediction_manifest_sha256": "a" * 64,
            }
            for name in _METHODS
        )
    folds.extend(
        {
            "case_id": "prior-refusal:" + str(index),
            "target_id": "prior-owner:" + str(index),
        }
        for index in range(15)
    )
    dispositions = [
        {
            "method": _METHODS[index % 3],
            "status": "predicted" if index < 9 else "refused",
        }
        for index in range(54)
    ]
    original = {
        "protocol": parent,
        "owners": [{"owner_id": owner, "counts": [8, 2]} for owner in owners.values()]
        + [
            {"owner_id": "other:" + str(index), "counts": [4, 1]} for index in range(20)
        ],
        "cases": cases,
        "folds": folds,
        "dispositions": dispositions,
        "nominal_predictions": nominal,
        "accounting": {
            "active_draw_owner_ids": list(owners.values()),
            "owner_lineage": lineage,
        },
        "source_files": source_files,
    }
    prediction_packet = {
        "schema_version": "krageholm-predictive-ensemble.v1",
        "cases": cached,
        "original_dispositions": dispositions,
    }
    directory = "qualified-parent/"
    products = {}
    for key, value in (
        ("inputs", original),
        ("draws", draws),
        ("predictions", prediction_packet),
        ("summary", {"old_score": "not decoded"}),
    ):
        pin = put(directory + key + ".json", value)
        products[key] = {**pin, "path": key + ".json"}
    manifest_pin = put(
        directory + "prediction-manifest.json",
        {
            "schema_version": "coupled-pollen-bootstrap-freeze.v1",
            "files": {key: products[key] for key in ("inputs", "draws", "predictions")},
        },
    )
    result_pin = put(
        directory + "result.json",
        {
            "schema_version": "coupled-pollen-bootstrap-result.v1",
            "status": "produced_awaiting_independent_verification",
            "source_guards_passed": True,
            "source_commit": "qualified-source",
            "protocol": parent_pin,
            "prediction_manifest": {**manifest_pin, "path": "prediction-manifest.json"},
            "products": products,
        },
    )
    verification = put(
        "qualified-verification.json",
        {
            "schema_version": "coupled-pollen-bootstrap-verification.v1",
            "source_commit": "qualified-source",
            "source_observation": {
                "status": "failed" if failed_verification else "passed",
                "source_files_verified": 141,
            },
            "numerical_observation": {"status": "passed", "accounting_verified": True},
        },
    )
    protocol = {
        "schema_version": "krageholm-geographic-transfer-protocol.v1",
        "sources": {
            "parent_protocol": parent_pin,
            "source_result": result_pin,
            "prediction_manifest": manifest_pin,
            "source_verification": verification,
        },
        "geography": {
            "blocks": {"sweden": ["BOKE", "BUS", "KRAGMJNY"], "solsoe": ["SOLSOE83"]},
            "source_only_places": ["KRAGMJNY"],
            "target_places": ["BOKE", "BUS", "SOLSOE83"],
            "source_radius_m": 100000.0,
            "target_radius_m": 1000.0,
            "coordinate_uncertainty_m": 0.0,
        },
    }
    return root, protocol


@pytest.fixture(scope="module")
def source(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    return _fixture(tmp_path_factory.mktemp("geographic-originals"))


def test_projection_keeps_only_role_disjoint_source_ensemble(
    source: tuple[Path, dict[str, Any]],
) -> None:
    packet = inputs.load_inputs(*source)
    assert len(packet["sites"]) == 4 and len(packet["target_roles"]) == 3
    assert len(packet["candidate_cases"]) == 1
    candidate = packet["candidate_cases"][0]
    assert "SOLSOE83" in candidate["case"]["target_id"]
    assert len(candidate["ppe_samples"]) == 1024
    assert sum(candidate["cached_fit"]["methods"]["training_mean"]["valid_mask"]) == 860
    assert candidate["nominal"]["local_covers_by_ring"][1][0][0] < 0
    assert len(packet["prior_dispositions"]) == 54
    assert packet["summary"]["prior_folds"] == 18
    assert packet["summary"]["raw_target_files_decoded"] == 0
    assert "owners" not in packet and "draws" not in packet
    assert all(
        row["owner_id"] != candidate["case"]["target_id"]
        for row in candidate["scientific_refs"]["allowed_inputs"]["count_owners"]
    )
    krag = next(row for row in packet["sites"] if row["place_id"] == "KRAGMJNY")
    assert krag["target_eligible"] is False and krag["target_radius_m"] is None
    inputs.check_sources(source[0], packet)


@pytest.mark.parametrize(
    "field",
    [
        "regional_cover",
        "regional_refusals",
        "local_signed_cover",
        "local_ring_refusals",
        "local_refusals",
        "valid_mask",
        "refusals",
    ],
)
def test_saved_source_array_truncation_refuses(
    source: tuple[Path, dict[str, Any]], field: str
) -> None:
    packet = inputs.load_inputs(*source)
    case = deepcopy(packet["candidate_cases"][0]["cached_fit"])
    target = (
        case["methods"]["training_mean"]
        if field in {"valid_mask", "refusals"}
        else case
    )
    target[field].pop()
    with pytest.raises(ValueError, match="source array shape"):
        inputs._case_arrays(case)


def test_old_source_qualification_must_be_passed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="existing independent"):
        inputs.load_inputs(*_fixture(tmp_path, failed_verification=True))


def test_every_old_raw_source_is_hashed_without_being_decoded(
    source: tuple[Path, dict[str, Any]],
) -> None:
    repository, protocol = source
    path = repository / f"original/{_WINDOW}/SOLSOE83-raw.json"
    raw = path.read_bytes()
    assert raw.startswith(b"UNDECODED")
    try:
        path.write_bytes(raw.replace(b"SOURCE", b"source"))
        with pytest.raises(ValueError, match="digest differs"):
            inputs.load_inputs(repository, protocol)
    finally:
        path.write_bytes(raw)


def test_stream_guard_does_not_reopen_json_decoder(
    source: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    packet = inputs.load_inputs(*source)

    def forbidden(*_: Any, **__: Any) -> Any:
        raise AssertionError("stream guard must not use a JSON reader")

    monkeypatch.setattr(_Reader, "read", forbidden)
    inputs.check_sources(source[0], packet)


def test_nominal_cover_bytes_cannot_change_outside_original_manifest(
    source: tuple[Path, dict[str, Any]],
) -> None:
    repository, protocol = source
    path = repository / "original/native/BOKE/numerical/local_love/cover_mean.csv"
    raw = path.read_bytes()
    try:
        path.write_bytes(raw.replace(b"0.2,0.8", b"0.3,0.7"))
        with pytest.raises(ValueError, match="digest differs"):
            inputs.load_inputs(repository, protocol)
    finally:
        path.write_bytes(raw)
