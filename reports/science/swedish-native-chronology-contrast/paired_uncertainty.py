"""Declared per-aliquot counting uncertainty for retained native chronology contrasts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

from bijux_pollenomics_lra import api

DOMAIN = Path(__file__).resolve().parent
JsonMap = dict[str, Any]


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Maintained source module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def qualify(source_root: Path, output_root: Path) -> JsonMap:
    source_root = source_root.absolute()
    require(
        not any(x.is_symlink() for x in (source_root, *source_root.parents)),
        "Symlink source root",
    )
    require(
        not output_root.exists()
        and not output_root.is_symlink()
        and not any(x.is_symlink() for x in output_root.parents),
        "Output must be absent with regular parents",
    )
    require(
        not output_root.resolve().is_relative_to(source_root.resolve()),
        "Output overlaps source",
    )
    protocol: JsonMap = read(DOMAIN / "aliquot-protocol.json")
    original = load_module("retained_native_chronology", DOMAIN / "qualify.py")
    old, private = original.qualify(source_root)
    custody: JsonMap = protocol["input_custody"]
    require(old["source_custody"] == custody, "Original source universe differs")
    root = DOMAIN.parents[2]
    old_path = (
        root
        / "docs/report/pollen-reconstruction/swedish-native-chronology-contrast/report.json"
    )
    old_bytes = old_path.read_bytes()
    require(
        hashlib.sha256(old_bytes).hexdigest()
        == protocol["protected_existing_controls"][
            "docs/report/pollen-reconstruction/swedish-native-chronology-contrast/report.json"
        ]["sha256"],
        "Historical report identity differs",
    )
    require(
        read(old_path) == old,
        "Retained chronology producer no longer reproduces the original scientific report",
    )
    require(
        all(x["paired_standard_error"] is None for x in old["window_rows"]),
        "Historical paired-null population differs",
    )
    native: JsonMap = read(source_root / "native-results.json")
    original_protocol: JsonMap = read(source_root / "protocol.json")
    edges = original_protocol["age_window_edges_cal_bp"]
    ppe = np.asarray(native["ppe"])
    cp = np.diag(np.square(np.asarray(native["ppe_SD"])))
    require(
        native["ppe"] == protocol["ppe_model"]["ppe"]
        and native["ppe_SD"] == protocol["ppe_model"]["sd"],
        "Original PPE magnitudes differ",
    )
    require(
        api.joint_aliquot_covariance.__module__
        == "bijux_pollenomics_lra.reconstruction.joint_aliquot_covariance",
        "Public aliquot API origin differs",
    )
    params = tuple(protocol["literal_axis"])
    observations: list[api.AliquotCountInput] = []
    requests: list[api.AliquotResultInput] = []
    contexts: list[JsonMap] = []
    native_primitive: list[JsonMap] = []
    position: dict[tuple[int, int, int], int] = {}
    for pair in protocol["fixed_domain"]["pairs"]:
        did, uid = pair["dataset_id"], pair["collection_unit_id"]
        samples: list[JsonMap] = read(
            source_root / f"dataset-{did}-sample-eligibility.json"
        )
        sample_by_id = {x["native_sample_id"]: x for x in samples}
        bins: dict[int, list[list[int]]] = {}
        for cid in (pair["reference_chronology_id"], pair["alternative_chronology_id"]):
            bins[cid] = [[] for _ in range(25)]
            for sample in samples:
                w, _, refusal = original.select(sample, cid, edges)
                if refusal is None:
                    require(w is not None, "Selected source has no window")
                    bins[cid][w].append(sample["native_sample_id"])
        union = sorted(
            {sid for groups in bins.values() for members in groups for sid in members}
        )
        for sid in union:
            s = sample_by_id[sid]
            oid = f"{uid}:{did}:{sid}"
            counts = [
                s["strict_unique_literal_parameter_counts"][t]["count"] for t in params
            ]
            observations.append(
                api.AliquotCountInput(
                    oid,
                    uid,
                    did,
                    sid,
                    custody[f"dataset-{did}-sample-eligibility.json"]["sha256"],
                    params,
                    np.asarray(counts),
                    np.ones(2, dtype=bool),
                )
            )
            native_primitive.append(
                {
                    "observation_id": oid,
                    "collection_unit_id": uid,
                    "dataset_id": did,
                    "native_sample_id": sid,
                    "native_analysis_unit_id": s["native_analysis_unit_id"],
                    "counts": counts,
                    "reported_pollen_NISP": s["reported_pollen_NISP"],
                    "source_ages": s["typed_calibrated_source_ages"],
                }
            )
        for cid in bins:
            profile = next(
                p
                for p in native["single_dataset_profiles"]
                if p["selected_source_profile"]["native_dataset_id"] == did
                and p["selected_source_profile"]["native_chronology_id"] == cid
            )
            require(
                profile["selected_source_profile"]["static_workbook_radius_candidates"]
                == pair["static_radius_candidates"],
                "Static radius provenance differs",
            )
            saved = {
                x["window_index"]: x
                for x in profile["conditional_results"]
                if x["physical_profile"] == "metadata_radius_wind_3"
            }
            for w, members in enumerate(bins[cid]):
                if not members:
                    require(w not in saved, "Missing source result was imputed")
                    continue
                require(
                    saved[w]["deposition"] == [pair["deposition"]],
                    "Saved physical response differs",
                )
                require(
                    sorted(members)
                    == sorted(saved[w]["source_support"]["native_sample_ids"]),
                    "Saved native membership differs",
                )
                rowid = f"{did}:{cid}:{w}"
                position[(did, cid, w)] = len(requests)
                requests.append(
                    api.AliquotResultInput(
                        rowid,
                        tuple(f"{uid}:{did}:{sid}" for sid in sorted(members)),
                        params,
                        np.asarray(pair["deposition"]),
                    )
                )
                contexts.append(
                    {
                        "result_id": rowid,
                        "dataset_id": did,
                        "chronology_id": cid,
                        "window_index": w,
                        "observation_ids": list(requests[-1].observation_ids),
                        "deposition": pair["deposition"],
                        "saved": saved[w],
                    }
                )
    joint = api.joint_aliquot_covariance(
        tuple(observations),
        tuple(requests),
        parameter_ids=params,
        ppe=ppe,
        ppe_covariance=cp,
        assume_distinct_aliquot_count_independence=True,
        assume_count_ppe_independence=True,
    )
    require(
        len(contexts) == 221 and len(joint.cover) == 442 and len(observations) == 432,
        "Declared native/joint population differs",
    )
    require(
        len(private["sample_migrations"]) == 449,
        "Original raw source population differs",
    )
    indices: list[tuple[int, int]] = []
    slots: list[JsonMap] = []
    D = np.zeros((212, 442))
    for row in old["window_rows"]:
        entry = {
            key: row[key]
            for key in (
                "native_dataset_id",
                "window_index",
                "status",
                "reference_samples",
                "alternative_samples",
                "shared_sample_count",
            )
        }
        if row["status"] == "matched_saved_outputs":
            a, b = (
                position[(row["native_dataset_id"], row[key], row["window_index"])]
                for key in ("reference_chronology_id", "alternative_chronology_id")
            )
            c = len(indices)
            D[c * 2 : c * 2 + 2, joint.result_slices[a]] = -np.eye(2)
            D[c * 2 : c * 2 + 2, joint.result_slices[b]] = np.eye(2)
            entry["contrast_index"] = c
            indices.append((a, b))
        else:
            entry["paired_standard_error"] = None
            entry["paired_standard_error_refusal"] = row[
                "paired_standard_error_refusal"
            ]
        slots.append(entry)
    matrices = {
        "counting": joint.counting_covariance,
        "ppe": joint.ppe_covariance,
        "total": joint.total_covariance,
    }
    contrasts = {key: D @ value @ D.T for key, value in matrices.items()}
    require(
        all(np.diag(x).min() >= -1e-18 for x in contrasts.values()),
        "Contrast negative variance exceeds roundoff bound",
    )
    difference = D @ joint.cover
    output_root.mkdir(parents=True)
    payload: JsonMap = {
        "schema_version": "swedish-paired-chronology-aliquot-covariance.v1",
        "profile": joint.profile,
        "ppe": ppe.tolist(),
        "ppe_covariance": cp.tolist(),
        "observations": native_primitive,
        "results": contexts,
        "cover": joint.cover.tolist(),
        "count_jacobian": joint.count_jacobian.tolist(),
        "ppe_jacobian": joint.ppe_jacobian.tolist(),
        "covariance": {k: v.tolist() for k, v in matrices.items()},
        "contrast_covariance": {k: v.tolist() for k, v in contrasts.items()},
        "contrast_pairs": indices,
        "contrast_cover": difference.tolist(),
        "slots": slots,
    }
    audit = load_module(
        "independent_aliquot_oracle", DOMAIN / "independent_aliquot.py"
    ).review(source_root, protocol, payload)
    for c, (_a, _b) in enumerate(indices):
        entry = next(x for x in slots if x.get("contrast_index") == c)
        entry["alternative_minus_reference_cover"] = difference[
            c * 2 : c * 2 + 2
        ].tolist()
        entry["conditional_paired_standard_error"] = np.sqrt(
            np.maximum(0, np.diag(contrasts["total"])[c * 2 : c * 2 + 2])
        ).tolist()
    summary: JsonMap = {
        "schema_version": "swedish-paired-chronology-aliquot-uncertainty.v1",
        "model_profile": joint.profile,
        "source_custody": custody,
        "protocol_sha256": hashlib.sha256(
            (DOMAIN / "aliquot-protocol.json").read_bytes()
        ).hexdigest(),
        "original_report_sha256": hashlib.sha256(old_bytes).hexdigest(),
        "original_paired_SEs_preserved_null": 125,
        "native_samples": 449,
        "selected_aliquot_primitives": len(observations),
        "occupied_profile_windows": len(contexts),
        "joint_axes": len(joint.cover),
        "paired_windows": len(indices),
        "unpaired_windows": 19,
        "contrast_axes": len(difference),
        "independent_oracle": audit,
        "assumptions": {
            k: protocol[k]
            for k in ("count_model", "ppe_model", "age_selection", "physical_model")
        },
        "interpretation_limits": protocol["acceptance_limits"],
        "slots": slots,
    }
    write(output_root / "private-joint-covariance.json", payload)
    write(output_root / "independent-audit.json", audit)
    write(output_root / "report.json", summary)
    after, _ = original.qualify(source_root)
    require(
        after == old, "Source or retained historical result changed during consumer"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    summary = qualify(args.source_root, args.output_root)
    print(
        json.dumps(
            {
                "status": "passed",
                "matched": summary["paired_windows"],
                "joint_axes": summary["joint_axes"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
