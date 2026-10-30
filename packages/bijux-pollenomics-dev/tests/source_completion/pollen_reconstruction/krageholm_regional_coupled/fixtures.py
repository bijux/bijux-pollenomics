"""Closed artificial products for observer controls, with no retained measurements."""

from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .lineage import digest
from .scalar import AXIS, METHODS


def write_product(
    directory: Path, scientific: dict[str, Any], members: dict[str, Any], *, phase: str
) -> dict[str, Any]:
    """Write a synthetic product and return its manifest identity."""
    directory.mkdir(parents=True)
    inventory = {}
    for name, value in members.items():
        body = json.dumps(value).encode()
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        inventory[name] = sha256(body).hexdigest()
    manifest = {
        "schema_version": "lra-experiment-product.v1",
        "phase": phase,
        "scientific_acceptance": "not_evaluated",
        "scientific_payload": scientific,
        "scientific_content_sha256": digest(scientific),
        "files": inventory,
    }
    body = json.dumps(manifest).encode()
    (directory / "manifest.json").write_bytes(body)
    return {
        "directory": str(directory),
        "manifest_sha256": sha256(body).hexdigest(),
        "scientific_content_sha256": digest(scientific),
    }


def prediction_fixture(
    repository: Path, *, refused: bool = False
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build synthetic fixed-regional predictions and their source context."""
    ids = dict.fromkeys(("BOKE", "BUS", "SOLSOE83", "KRAGMJNY"))
    ids = {code: code for code in ids}
    sites: list[dict[str, Any]] = [
        {
            "record_id": code,
            "site_id": "site:" + code,
            "identity_keys": ["site:" + code, "collection:" + code],
            "raw": {"path": code + "-raw.json", "sha256": digest(code + "raw")},
            "geometry": {
                "path": code + "-geometry.json",
                "sha256": digest(code + "geometry"),
            },
        }
        for code in ids
    ]
    template = {
        "taxa": list(AXIS),
        "parameters": [{"ppe": 1}, {"ppe": 1}],
        "evidence": [],
        "configuration": {"synthetic": True},
    }
    spec: dict[str, Any] = {
        "profile": "source-observations-withheld-site-baselines-v1",
        "sites": sites,
        "target_record_ids": list(ids)[:-1],
        "regional_priority": ["KRAGMJNY"],
        "request_template": template,
        "local_ring_count": 2,
        "local_support_radius_m": 1000,
        "support_profile": "same-outer-radius-homogeneous-v1",
    }
    members = {
        code + "-raw.json": {
            "sample": {"sample_id": code, "counts": [2, 1], "bin_id": "synthetic-bin"}
        }
        for code in ids
    }
    context = {"experiment": spec, "ids": ids, "members": members}
    fixture_groups = {
        record: "site-group:"
        + sha256(json.dumps([record], separators=(",", ":")).encode()).hexdigest()
        for record in ids
    }
    folds: list[dict[str, Any]] = [
        {
            "fold_id": fixture_groups[target],
            "train_record_ids": sorted(set(ids) - {target}),
            "test_record_ids": [target],
            "train_group_ids": sorted(
                fixture_groups[record] for record in ids if record != target
            ),
            "test_group_ids": [fixture_groups[target]],
        }
        for target in spec["target_record_ids"]
    ]
    folds.sort(key=lambda row: row["fold_id"])
    fits, preparations, predictions, failures = [], [], [], []
    native = {}
    for fold_index, fold in enumerate(folds):
        fold_id, target = fold["fold_id"], fold["test_record_ids"][0]
        local = sorted(set(fold["train_record_ids"]) - {"KRAGMJNY"})
        groups = {record: fixture_groups[record] for record in local}
        identity = [
            {
                "record_id": record,
                "group_id": groups[record],
                "composition": {"Betula": 0.75, "Ulmus": 0.25},
                "request_sha256": digest(record + "request"),
                "scientific_content_sha256": digest(record + "content"),
                "scientific_identity_sha256": digest(record + "identity"),
            }
            for record in local
        ]
        native[fold_id] = {
            record: {
                "cover": (Q(3, 4), Q(1, 4)),
                "regional": (Q(1, 2), Q(1, 2)),
                "request_sha256": digest(record + "request"),
                "scientific_content_sha256": digest(record + "content"),
                "scientific_identity_sha256": digest(record + "identity"),
            }
            for record in local
        }
        if refused and fold_index == 0:
            native[fold_id][local[0]]["cover"] = (Q(5, 4), Q(-1, 4))
            failures.append(
                {
                    "fold_id": fold_id,
                    "record_ids": [target],
                    "status": "refused",
                    "reason_code": "invalid_composition",
                    "detail": "Synthetic signed local output",
                    "exception_type": "ValidationRefusal",
                }
            )
            continue
        group_ids = sorted(groups.values())
        anchor_group = fixture_groups["KRAGMJNY"]
        fit = {
            "fold_id": fold_id,
            "outer_fold": fold,
            "regional_anchor_record_id": "KRAGMJNY",
            "regional_anchor_group_id": anchor_group,
            "predictor_group_ids": group_ids,
            "training_products": identity,
        }
        fits.append(fit)
        regional_id, params_id, geometry_id, time_id = (
            prefix + fold_id
            for prefix in ("regional:", "parameters:", "geometry:", "time:")
        )
        forward_inputs = {
            "taxa": list(AXIS),
            "ppe": [1, 1],
            "local_k": [[1, 1], [1, 1]],
            "terrestrial_fraction": [1.0, 1.0],
            "regional_deposition": [1.0, 1.0],
            "regional_input_ids": [regional_id],
            "parameter_input_ids": [params_id],
            "geometry_input_ids": [geometry_id],
            "temporal_support_id": time_id,
        }
        distances = dict(zip(group_ids, [2.0, 4.0], strict=True))
        preparations.append(
            {
                "fold_id": fold_id,
                "outer_fold": fold,
                "regional_anchor_record_id": "KRAGMJNY",
                "regional_anchor_group_id": anchor_group,
                "predictor_group_ids": group_ids,
                "regional_cover": [0.5, 0.5],
                "full_k": [[1, 1]] * 4,
                "full_terrestrial_fraction": [1.0] * 4,
                "forward_inputs": forward_inputs,
                "distances_km": distances,
            }
        )
        graph: dict[str, list[str]] = {
            record: [] for record in fold["train_record_ids"]
        }
        graph.update(
            {
                regional_id: fold["train_record_ids"],
                params_id: [],
                geometry_id: [],
                time_id: [],
            }
        )
        for method in METHODS:
            vegetation, pollen = (
                {"Betula": 0.75, "Ulmus": 0.25},
                {"Betula": 0.625, "Ulmus": 0.375},
            )
            published = {
                "target_group_id": fold["test_group_ids"][0],
                "spatial_method": method,
                "fold": fold,
                "forward_inputs": forward_inputs,
                "vegetation_fraction": vegetation,
                "pollen_fraction": pollen,
                "input_lineage": graph,
                "allowed_input_closure": sorted(graph),
                "predictor_group_ids": group_ids,
            }
            predictions.append(
                {
                    "fold_id": fold_id,
                    "record_id": target,
                    "bin_id": "synthetic-bin",
                    "baseline": method,
                    "vegetation_fraction": vegetation,
                    "pollen_fraction": pollen,
                    "prediction_manifest": published,
                    "prediction_manifest_sha256": digest(published),
                }
            )
    science = {
        "folds": folds,
        "baselines": list(METHODS),
        "split_manifest_sha256": digest(folds),
        "requested_folds": 3,
        "requested_predictions": 9,
        "training": fits,
        "preparations": preparations,
        "predictions": predictions,
        "failures": failures,
    }
    saved = {
        key + ".json": science[key]
        for key in ("predictions", "training", "preparations", "failures")
    }
    saved["experiment.json"] = {
        "profile": spec["profile"],
        "source_catalogue": [
            {
                "record_id": site["record_id"],
                "site_id": site["site_id"],
                "identity_keys": sorted(set(site["identity_keys"])),
                "raw_path": site["raw"]["path"],
                "raw_sha256": site["raw"]["sha256"],
                "geometry_path": site["geometry"]["path"],
                "geometry_sha256": site["geometry"]["sha256"],
            }
            for site in sites
        ],
        "target_record_ids": spec["target_record_ids"],
        "regional_priority": spec["regional_priority"],
        "request_template": template,
        "local_ring_count": 2,
        "local_support_radius_m": 1000.0,
        "support_profile": "same-outer-radius-homogeneous-v1",
    }
    dispositions = []
    for fold in folds:
        failure = next(
            (row for row in failures if row["fold_id"] == fold["fold_id"]), None
        )
        for method in METHODS:
            dispositions.append(
                {
                    "fold_id": fold["fold_id"],
                    "method": method,
                    **(
                        {
                            key: failure[key]
                            for key in (
                                "status",
                                "reason_code",
                                "detail",
                                "exception_type",
                            )
                        }
                        if failure
                        else {"status": "predicted"}
                    ),
                }
            )
    pin = write_product(
        repository / "artifacts/predictions", science, saved, phase="predictions"
    )
    pin["method_dispositions"] = dispositions
    return pin, context, native, science
