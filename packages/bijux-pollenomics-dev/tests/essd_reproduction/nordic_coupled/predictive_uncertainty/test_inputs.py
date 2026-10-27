"""Bind saved owners and refuse changed roles without source or model jobs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty import (
    inputs,
)


def saved_inputs(root: Path) -> dict[str, Any]:
    """Write a complete portable six-window source/prediction fixture."""
    value: Any

    def put(name: str, value: Any, *, raw: bool = False) -> dict[str, Any]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        body = value.encode() if raw else json.dumps(value, allow_nan=False).encode()
        path.write_bytes(body)
        return {
            "path": name,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }

    parameters = deepcopy(list(inputs.PARAMETERS))
    declarations: dict[str, dict[str, Any]] = {
        core: {
            "id": core,
            "site": values[0],
            "dataset": values[1],
            "collection_unit": values[2],
            "chronology": values[3],
            "radius_m": radius,
            "longitude": 12.0 + index,
            "latitude": 55.0 + index,
        }
        for index, ((core, values), radius) in enumerate(
            zip(inputs.NATIVE.items(), [80.0, 69.0, 89.0, 837.0], strict=True)
        )
    }
    audit = put("audit.json", {"source": "qualified synthetic source accounting"})
    coupled = put(
        "coupled.json",
        {
            "axis": list(inputs.AXIS),
            "parameters": parameters,
            "small_cores": [declarations[c] for c in inputs.SMALL],
            "krag_geometry": declarations["KRAGMJNY"],
            "krag_audit": audit,
        },
    )
    members = []
    experiments = []
    raw_by_name: dict[tuple[str, str], dict[str, Any]] = {}
    geometry_by_name: dict[tuple[str, str], dict[str, Any]] = {}
    for name in inputs.NAMES:
        younger = float(name.split("-")[2])
        window = [younger, younger + 500]
        ids = {c: inputs._owner_id(c, name) for c in inputs.CORES}
        projections = []
        for core in inputs.CORES:
            declaration = declarations[core]
            radius = declaration["radius_m"]
            metadata = {
                "sample_id": ids[core],
                "site_id": f"neotoma-site-{inputs.NATIVE[core][0]}",
                "bin_id": name,
                "age_type": "calendar_bp",
                "age_support_bp": [window],
                "coordinate": younger,
                "chronology_evidence_id": "chronology",
            }
            raw: dict[str, Any] = {
                "data_kind": "source_observations",
                "taxa": list(inputs.AXIS),
                "sample": {**metadata, "counts": [8, 2]},
            }
            raw_by_name[(name, ids[core])] = raw
            geometry: dict[str, Any] = {
                "basin": {"diameter_m": 2 * radius, "site_type": "lake"},
                "sample_metadata": metadata,
                "longitude": declaration["longitude"],
                "latitude": declaration["latitude"],
            }
            if core != "KRAGMJNY":
                for field, edges in [
                    ("inversion_rings", [radius + 1, 500.0, 1000.0]),
                    ("forward_rings", [radius, 500.0, 1000.0, 10000.0, 100000.0]),
                ]:
                    geometry[field] = [
                        {
                            "inner_m": lo,
                            "outer_m": hi,
                            "mean_m": (lo + hi) / 2,
                            "ring_area_m2": 1.0,
                            "terrestrial_area_m2": 1.0,
                        }
                        for lo, hi in zip(edges[:-1], edges[1:], strict=True)
                    ]
            geometry_by_name[(name, ids[core])] = geometry
            for kind, value in [("raw", raw), ("geometry", geometry)]:
                pin = put(f"inputs/{name}/{core}-{kind}.json", value)
                members.append({**pin, "path": f"{name}/{core}-{kind}.json"})
            site, dataset, unit, chronology = inputs.NATIVE[core]
            projection = {
                "core": core,
                "native_site": site,
                "native_dataset": dataset,
                "native_collection_unit": unit,
                "selected_chronology": chronology,
                "projected_panel_N": 10,
            }
            if core == "KRAGMJNY":
                projection.update(
                    native_collection_default_reference=13365,
                    source_default_flags={"13365": True, "13366": True},
                    reported_pollen_N=15,
                    excluded_pollen_N=5,
                )
            else:
                projection.update(
                    record_id=ids[core],
                    projected_axis=list(inputs.AXIS),
                    source_panel_N=15,
                    excluded_panel_N=5,
                    source_support_sha256="a" * 64,
                    qualified_source_support={
                        "native_sample_count": 2,
                        "source_support_sha256": "a" * 64,
                        "window": window,
                    },
                )
            projections.append(projection)
        experiment = {
            "target_record_ids": [ids[c] for c in inputs.SMALL],
            "regional_priority": [ids["KRAGMJNY"]],
            "request_template": {"parameters": parameters, "taxa": list(inputs.AXIS)},
        }
        for member, value in [
            ("experiment", experiment),
            ("projection", projections),
            *[
                (
                    key,
                    {
                        "role": key,
                        **({"parameters": parameters} if key == "parameters" else {}),
                    },
                )
                for key in [
                    "chronology",
                    "taxa",
                    "parameters",
                    "dependency_lock",
                    "decision",
                ]
            ],
        ]:
            pin = put(f"inputs/{name}/{member}.json", value)
            members.append({**pin, "path": f"{name}/{member}.json"})
            if member == "experiment":
                experiments.append(
                    {
                        "directory": name,
                        "experiment": {
                            "path": "experiment.json",
                            "sha256": pin["sha256"],
                        },
                        "target_record_ids": experiment["target_record_ids"],
                        "regional_source_record_id": ids["KRAGMJNY"],
                    }
                )
    index = put(
        "inputs/inputs.json",
        {
            "protocol": coupled,
            "members": members,
            "experiments": experiments,
            "qualified_source_inputs": [audit],
            "krag_audit": audit,
            "source_population": {"scope": "retained source accounting"},
        },
    )
    bins = []
    dispositions = []
    for name in inputs.NAMES:
        ids = {c: inputs._owner_id(c, name) for c in inputs.CORES}
        regional = ids["KRAGMJNY"]
        groups = {owner: "group:" + owner for owner in ids.values()}
        folds = []
        preparations = []
        operations = []
        training = []
        predictions = []
        for target_core in inputs.SMALL:
            target = ids[target_core]
            allowed = sorted(set(ids.values()) - {target})
            local = sorted(set(allowed) - {regional})
            fold_id = groups[target]
            fold = {
                "fold_id": fold_id,
                "test_record_ids": [target],
                "test_group_ids": [fold_id],
                "train_record_ids": allowed,
                "train_group_ids": sorted(groups[o] for o in allowed),
            }
            folds.append(fold)
            status = "predicted" if name == inputs.NAMES[0] else "refused"
            for method in inputs.METHODS:
                dispositions.append(
                    {
                        "bin": name,
                        "fold_id": fold_id,
                        "method": method,
                        "status": status,
                        **(
                            {
                                "reason_code": "invalid_composition",
                                "detail": "original refusal",
                            }
                            if status == "refused"
                            else {}
                        ),
                    }
                )
            if status == "refused":
                continue
            items = []
            for owner in local:
                base = f"predictions/{name}/cache/{owner}"
                geometry = geometry_by_name[(name, owner)]
                request: dict[str, Any] = {
                    "taxa": list(inputs.AXIS),
                    "pollen_unit": "count",
                    "parameters": parameters,
                    "data_kind": "source_observations",
                    "local": {
                        "samples": [
                            {
                                **raw_by_name[(name, owner)]["sample"],
                                "raw_evidence_id": "raw:" + owner,
                            }
                        ]
                    },
                    "regional": {
                        "samples": [
                            {
                                **raw_by_name[(name, regional)]["sample"],
                                "raw_evidence_id": "raw:" + regional,
                            }
                        ]
                    },
                    "rings": [
                        {**r, "geometry_evidence_id": "geometry:" + owner}
                        for r in geometry["inversion_rings"]
                    ],
                }
                files = {}
                request_pin = put(base + "/request.json", request)
                files["request.json"] = request_pin["sha256"]
                for table in ["aux_Kloc", "aux_Kreg"]:
                    text = "index,Betula,Ulmus\n" + "".join(
                        f"{r['mean_m']},0.2,0.3\n" for r in request["rings"]
                    )
                    filename = "numerical/local_love/" + table + ".csv"
                    files[filename] = put(base + "/" + filename, text, raw=True)[
                        "sha256"
                    ]
                filename = "numerical/regional_reveals/deposition_factors.csv"
                files[filename] = put(
                    base + "/" + filename, "index,K\nBetula,0.4\nUlmus,0.5\n", raw=True
                )["sha256"]
                request_sha = hashlib.sha256(inputs._canonical(request)).hexdigest()
                native_manifest = put(
                    base + "/manifest.json",
                    {
                        "schema_version": "lra-product.v1",
                        "scientific_content_sha256": "b" * 64,
                        "retained_taxa": list(inputs.AXIS),
                        "request_sha256": request_sha,
                        "files": files,
                    },
                )
                items.append(
                    {
                        "item_id": owner,
                        "item_status": "completed",
                        "request_sha256": request_sha,
                        "product": {
                            "directory": str(root / base),
                            "manifest_sha256": native_manifest["sha256"],
                            "scientific_content_sha256": "b" * 64,
                        },
                    }
                )
            operations.append({"fold_id": fold_id, "batch": {"items": items}})
            geometry = geometry_by_name[(name, target)]
            target_pin = next(
                p for p in members if p["path"] == f"{name}/{target_core}-geometry.json"
            )
            forward: dict[str, Any] = {
                "local_k": [[0.2, 0.3], [0.1, 0.2]],
                "terrestrial_fraction": [1.0, 1.0],
                "ppe": [5.106, 1.27],
            }
            preparations.append(
                {
                    "fold_id": fold_id,
                    "outer_fold": fold,
                    "regional_value_source_record_ids": [regional],
                    "regional_identity_source_record_ids": allowed,
                    "target_geometry_sha256": target_pin["sha256"],
                    "declared_target_forward_rings": geometry["forward_rings"],
                    "declared_target_inversion_rings": geometry["inversion_rings"],
                    "ring_bounds_m": [
                        [r["inner_m"], r["outer_m"]] for r in geometry["forward_rings"]
                    ],
                    "full_k": [*forward["local_k"], [0.1, 0.2], [0.2, 0.1]],
                    "full_terrestrial_fraction": [1.0] * 4,
                    "forward_inputs": forward,
                    "regional_cover": [0.6, 0.4],
                    "distances_km": {groups[local[0]]: 10.0, groups[local[1]]: 20.0},
                }
            )
            training.append(
                {
                    "fold_id": fold_id,
                    "training_products": [
                        {"record_id": o, "group_id": groups[o]} for o in local
                    ],
                }
            )
            for method in inputs.METHODS:
                manifest = {
                    "fold": fold,
                    "forward_inputs": forward,
                    "allowed_input_closure": [*allowed, "target-geometry"],
                    "input_lineage": {o: [] for o in allowed},
                }
                predictions.append(
                    {
                        "fold_id": fold_id,
                        "baseline": method,
                        "record_id": target,
                        "bin_id": name,
                        "prediction_manifest": manifest,
                        "prediction_manifest_sha256": hashlib.sha256(
                            inputs._canonical(manifest)
                        ).hexdigest(),
                        "pollen_fraction": {"Betula": 0.6, "Ulmus": 0.4},
                        "vegetation_fraction": {"Betula": 0.7, "Ulmus": 0.3},
                    }
                )
        retained = {}
        for filename, value in [
            ("preparations.json", preparations),
            ("operations.json", operations),
            ("predictions.json", predictions),
            ("training.json", training),
        ]:
            retained[filename] = put(f"predictions/{name}/{filename}", value)["sha256"]
        manifest = put(
            f"predictions/{name}/manifest.json",
            {"scientific_content_sha256": "c" * 64, "files": retained},
        )
        bins.append(
            {
                "bin": name,
                "folds": folds,
                "prediction": {
                    "directory": str(root / "predictions" / name),
                    "manifest_sha256": manifest["sha256"],
                    "scientific_content_sha256": "c" * 64,
                    "interrupted": False,
                    "retained_tables": retained,
                },
            }
        )
    batch = put(
        "predictions/batch.json",
        {
            "operation": "prepare",
            "all_bins_accounted": True,
            "requested_folds": 18,
            "requested_method_dispositions": 54,
            "status_counts": {"predicted": 9, "refused": 45},
            "bins": bins,
            "method_dispositions": dispositions,
            "input_index": {**index, "path": str(root / index["path"])},
            "protocol": coupled,
        },
    )
    return {
        "sources": {
            "coupled_protocol": coupled,
            "input_index": index,
            "prediction_batch": batch,
        },
        "sampling": {
            "replicates": 1024,
            "seed": 20261027,
            "taxa": list(inputs.AXIS),
            "ppe_means": [5.106, 1.27],
            "ppe_sds": [0.303, 0.05],
        },
    }


@pytest.fixture(scope="module")
def saved(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    root = tmp_path_factory.mktemp("qualified-saved-inputs")
    return root, saved_inputs(root)


def test_complete_packet_has_three_target_free_cases_and_every_refusal(
    saved: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, protocol = saved
    original = Path.read_bytes

    def guarded(path: Path) -> bytes:
        assert "score" not in path.name
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    packet = inputs.load_inputs(root, protocol)
    assert (
        len(packet.owners),
        len(packet.cases),
        len(packet.folds),
        len(packet.dispositions),
        len(packet.nominal_predictions),
    ) == (24, 3, 18, 54, 9)
    assert sum(r["status"] == "refused" for r in packet.dispositions) == 45
    assert len(packet.accounting["active_draw_owner_ids"]) == 4
    for case in packet.cases:
        allowed = {case.regional_owner_id, *(o.owner_id for o in case.local_owners)}
        assert case.target_id not in allowed
        fold = next(r for r in packet.folds if r["case_id"] == case.case_id)
        assert {Path(r["path"]).name for r in fold["scientific_count_refs"]} == {
            packet.accounting["owner_lineage"][o]["core"] + "-raw.json" for o in allowed
        }
        assert "counts" not in asdict(case)
        assert all(
            packet.accounting["owner_lineage"][o]["panel_N"] == 10 for o in allowed
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("replicates", True),
        ("replicates", 1023),
        ("seed", 1),
        ("taxa", ["Ulmus", "Betula"]),
        ("ppe_means", [5.107, 1.27]),
        ("ppe_sds", [0.303, False]),
    ],
)
def test_sampling_and_axis_are_frozen(
    saved: tuple[Path, dict[str, Any]], field: str, value: Any
) -> None:
    root, protocol = saved
    changed = deepcopy(protocol)
    changed["sampling"][field] = value
    with pytest.raises(inputs.InputError):
        inputs.load_inputs(root, changed)


@pytest.mark.parametrize(
    "values",
    [[True, 2], [1.5, 2], [-1, 2], [0, 0], [1], [1, 2, 3], [2**53, 1], [None, 1]],
)
def test_materialized_counts_refuse_noninteger_missing_and_invalid_N(
    saved: tuple[Path, dict[str, Any]], values: Any
) -> None:
    root, _ = saved
    raw = json.loads((root / "inputs" / inputs.NAMES[0] / "BOKE-raw.json").read_text())
    raw["sample"]["counts"] = values
    with pytest.raises(inputs.InputError):
        inputs._counts(raw, "BOKE", inputs.NAMES[0])


@pytest.mark.parametrize(
    "field,value",
    [
        ("projected_panel_N", 11),
        ("source_panel_N", 14),
        ("native_site", True),
        ("selected_chronology", 13366),
    ],
)
def test_original_projection_mass_and_native_owner_are_not_reinvented(
    saved: tuple[Path, dict[str, Any]], field: str, value: Any
) -> None:
    root, _ = saved
    row = json.loads(
        (root / "inputs" / inputs.NAMES[0] / "projection.json").read_text()
    )[0]
    row[field] = value
    with pytest.raises(inputs.InputError):
        inputs._projection(row, (8, 2), "BOKE", inputs.NAMES[0])


@pytest.mark.parametrize(
    "text",
    [
        "index,Ulmus,Betula\n295,0.1,0.2\n750,0.2,0.3\n",
        "index,Betula,Ulmus\n750,0.1,0.2\n295,0.2,0.3\n",
        "index,Betula,Ulmus\n295,nan,0.2\n750,0.2,0.3\n",
    ],
)
def test_saved_kernel_axis_order_and_finiteness(text: str) -> None:
    with pytest.raises(inputs.InputError):
        inputs._matrix_csv(text.encode(), [{"mean_m": 295.0}, {"mean_m": 750.0}])


@pytest.mark.parametrize(
    "mutation",
    [
        "target_training",
        "duplicate_disposition",
        "revive_nominal_refusal",
        "missing_fold",
        "foreign_window",
    ],
)
def test_count_free_nominal_roles_and_full_population_fail_closed(
    saved: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    root, protocol = saved
    path = root / protocol["sources"]["prediction_batch"]["path"]
    original = path.read_bytes()
    batch = json.loads(original)
    if mutation == "target_training":
        batch["bins"][0]["folds"][0]["train_record_ids"][0] = batch["bins"][0]["folds"][
            0
        ]["test_record_ids"][0]
    elif mutation == "duplicate_disposition":
        batch["method_dispositions"][1] = batch["method_dispositions"][0]
    elif mutation == "revive_nominal_refusal":
        batch["method_dispositions"][9]["status"] = "predicted"
    elif mutation == "missing_fold":
        batch["bins"][0]["folds"].pop()
    else:
        batch["bins"][0]["bin"] = "foreign-window"
    raw = json.dumps(batch).encode()
    changed = deepcopy(protocol)
    changed["sources"]["prediction_batch"].update(
        bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()
    )
    try:
        path.write_bytes(raw)
        with pytest.raises(inputs.InputError):
            inputs.load_inputs(root, changed)
    finally:
        path.write_bytes(original)


def test_missing_or_changed_saved_bytes_refuse(
    saved: tuple[Path, dict[str, Any]],
) -> None:
    root, protocol = saved
    changed = deepcopy(protocol)
    changed["sources"]["prediction_batch"]["sha256"] = "0" * 64
    with pytest.raises(inputs.InputError, match="digest"):
        inputs.load_inputs(root, changed)
    changed = deepcopy(protocol)
    changed["sources"]["prediction_batch"]["path"] = "absent.json"
    with pytest.raises(inputs.InputError):
        inputs.load_inputs(root, changed)


def test_duplicate_json_keys_and_nonfinite_literals_are_not_accepted() -> None:
    for raw in [b'{"owner":1,"owner":2}', b'{"value":NaN}']:
        with pytest.raises(inputs.InputError):
            inputs._decode(raw)
