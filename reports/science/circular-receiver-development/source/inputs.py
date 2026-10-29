"""Join authenticated nominal regional fractions to the fixed circular-receiver diagnostic geometry."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import runpy
from typing import Any


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def decode(raw: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            require(key not in result, "Duplicate scientific JSON member")
            result[key] = value
        return result

    def refuse(value: str) -> None:
        raise ValueError("Nonfinite scientific JSON: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=refuse)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def checked(root: Path, row: dict[str, Any]) -> bytes:
    name = Path(row["path"])
    path = root / name
    require(
        ".." not in name.parts
        and path.is_file()
        and path.stat().st_nlink == 1
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Independent declared scientific file required",
    )
    raw = path.read_bytes()
    require(
        type(row["bytes"]) is int
        and len(raw) == row["bytes"]
        and hashlib.sha256(raw).hexdigest() == row["sha256"],
        "Declared scientific file changed: " + str(path),
    )
    return raw


def regional(
    row: dict[str, Any], payload: dict[str, Any], checksum: str, item_id: str
) -> list[float]:
    taxa = payload["taxa"]
    values = row["regional_cover"]
    require(
        row["request_sha256"] == checksum
        and row["item_id"] == item_id
        and row["taxa"] == taxa
        and len(taxa) == len(set(taxa)) == 30
        and type(row["regional_percent_precision_decimals"]) is int
        and row["regional_percent_precision_decimals"] == 3
        and isinstance(values, list)
        and len(values) == len(taxa)
        and all(
            type(v) in (int, float)
            and math.isfinite(v)
            and 0 <= v <= 1
            and abs(v * 100 - round(v * 100, 3)) <= 1e-10
            for v in values
        ),
        "Exact labelled thirty-taxon source3decimal percent/fraction handoff required",
    )
    total = math.fsum(values)
    require(
        type(row["regional_fraction_sum"]) in (int, float)
        and math.isfinite(row["regional_fraction_sum"])
        and abs(total - row["regional_fraction_sum"]) <= 1e-12
        and abs(total - 1) <= 30 * 0.000005 + 1e-12,
        "Raw regional fraction mass differs; never normalize the background",
    )
    return list(values)


def load(
    repository: Path, prepared: Path, protocol: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from bijux_pollenomics.analysis.lra.api import LRABatchItem
    from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
    from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
        SourceExperimentSpec,
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        make_request,
    )
    from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

    for row in protocol["source_pins"]:
        checked(repository, row)
    borrowed = protocol["borrowed_sources"]
    for row in borrowed.values():
        checked(repository, row)
    common = runpy.run_path(str(repository / borrowed["common"]["path"]))
    admission = runpy.run_path(str(repository / borrowed["admission"]["path"]))
    descriptor = decode(
        checked(repository, protocol["prior_evidence"]["nominal_descriptor"])
    )
    rows = [row for row in descriptor["shards"] if row["method"] == "gpm neutral"]
    require(
        len(rows) == 1
        and rows[0]["training"] == protocol["prior_evidence"]["nominal_training"],
        "Exact nominal shard required",
    )
    authority = decode(
        checked(repository, protocol["prior_evidence"]["nominal_authority"])
    )
    require(
        authority["source_candidate"] == protocol["nominal_candidate"]
        and authority["independent_semantics"]["scientific_saved_products_admitted"]
        is True
        and authority["independent_semantics"]["approved"] is True,
        "Independent nominal saved-result authority required",
    )
    admitted = admission["admit_shard"](
        common,
        repository,
        rows[0],
        protocol["nominal_candidate"],
        protocol["nominal_training_protocol_sha256"],
    )
    require(
        len(protocol["inputs"]) == 37
        and {p.name for p in prepared.iterdir()}
        == {r["path"] for r in protocol["inputs"]},
        "Exact original37 input namespace required",
    )
    bodies = {r["path"]: checked(prepared, r) for r in protocol["inputs"]}
    require(
        len(bodies) == 37 and all(Path(name).name == name for name in bodies),
        "Unique original basename inputs required",
    )
    experiment = decode(bodies["experiment.json"])
    spec = SourceExperimentSpec(experiment)
    require(
        len(spec.sites) == 15
        and len(experiment["request_template"]["taxa"]) == 30
        and experiment["request_template"]["temporal_matching"]
        == protocol["temporal_matching"],
        "Exact15sites/30taxa/TW5 support required",
    )
    ancestry = runpy.run_path(str(repository / borrowed["requests"]["path"]))
    original = {
        "grouped_leave_one_out": grouped_leave_one_out,
        "make_request": make_request,
        "LRABatchItem": LRABatchItem,
    }
    contexts, groups = ancestry["contexts"](original, spec)
    numeric, logical = ancestry["requests"](original, spec, prepared, contexts)
    training = decode(
        checked(repository, protocol["prior_evidence"]["nominal_training"])
    )
    require(
        len(numeric) == 39
        and len(logical) == 2715
        and digest(logical) == digest(training["logical_requests"])
        and digest(logical) == protocol["logical_ancestry_sha256"]
        and set(numeric) == set(training["numerical_requests"]),
        "Full39request/2715ancestry closure changed",
    )
    result = []
    for checksum, item in sorted(numeric.items()):
        payload = validate_request(item.payload(), input_root=prepared).payload()
        require(item.request_sha256 == checksum, "Original request hash changed")
        local_ids = {
            row["local_record_id"]
            for row in logical
            if row["request_sha256"] == checksum
        }
        require(len(local_ids) == 1, "Exact numeric local identity required")
        vector = regional(
            training["numerical_requests"][checksum],
            payload,
            checksum,
            next(iter(local_ids)),
        )
        result.append(
            {
                "nominal_request_sha256": checksum,
                "payload": payload,
                "item_id": item.item_id,
                "selected_rings": training["numerical_requests"][checksum][
                    "selections"
                ],
                "regional_cover": vector,
            }
        )
    return result, {
        "original_native_exit": 1,
        "saved_products_admitted_separately": True,
        "nominal_candidate": protocol["nominal_candidate"],
        "logical_requests": 2715,
        "contexts": 225,
        "context_rows": [
            {
                "kind": row["kind"],
                "outer_target": row["outer"].test_record_ids[0],
                "target": row["target"],
                "fold": row["fold"].as_dict(),
                "anchor": row["anchor"],
                "predictors": list(row["predictors"]),
            }
            for row in contexts
        ],
        "groups": groups,
        "sites": experiment["sites"],
        "baselines": list(spec.baselines),
        "references": admitted["references"],
    }


def prediction_inputs(
    repository: Path,
    prepared: Path,
    protocol: dict[str, Any],
    pairs: list[dict[str, Any]],
    ancestry: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Join every original nominal prediction without evaluating its operator."""
    freeze = decode(checked(repository, protocol["candidate_freeze"]))
    require(
        freeze["profile"] == "author-love-nested-transport-development-diagnostic",
        "Exact previously admitted nominal freeze required",
    )
    slots = [row for row in freeze["slots"] if row["method"] == "gpm neutral"]
    require(len(slots) == 675, "Complete nominal675 frozen slots required")
    expected_contexts = {
        (row["kind"], row["outer_target"], row["target"]): row
        for row in ancestry["context_rows"]
    }
    require(len(expected_contexts) == 225, "Complete225 original contexts required")
    sites = {row["record_id"]: row for row in ancestry["sites"]}
    members = {row["path"]: row for row in protocol["inputs"]}
    geometries = {}
    for record, site in sites.items():
        reference = members[site["geometry"]["path"]]
        require(
            reference["sha256"] == site["geometry"]["sha256"],
            "Original target geometry identity differs",
        )
        geometries[record] = {
            "source": reference,
            "data": decode(checked(prepared, reference)),
        }
    by_pair = {}
    for pair in pairs:
        payload = pair["payload"]
        pair_key = (
            "author:" + payload["local"]["samples"][0]["site_id"],
            "author:" + payload["regional"]["samples"][0]["site_id"],
        )
        require(
            pair_key not in by_pair and pair["item_id"] == pair_key[0],
            "Unique original source local/anchor identity required",
        )
        by_pair[pair_key] = pair
    require(
        len(by_pair) == 39 and len(geometries) == 15,
        "Original39pairs/15target geometries required",
    )
    taxa = pairs[0]["payload"]["taxa"]
    parameters = pairs[0]["payload"]["parameters"]
    seen = set()
    output = []
    for slot in slots:
        key = (slot["kind"], slot["outer_target"], slot["target"], slot["baseline"])
        require(
            key not in seen
            and key[:3] in expected_contexts
            and slot["baseline"] in ancestry["baselines"]
            and slot["status"] == "predicted",
            "Exact original predicted baseline grid required",
        )
        seen.add(key)
        context = expected_contexts[key[:3]]
        geometry = geometries[slot["target"]]
        geo = slot["geometry"]
        require(
            digest(slot["fold"]) == digest(context["fold"])
            and digest(geo["outer_fold"]) == digest(context["fold"]),
            "Original fold ancestry differs",
        )
        selected = [
            by_pair[(record, context["anchor"])] for record in context["predictors"]
        ]
        require(
            all(
                len(pair["selected_rings"]) == 2
                and all(choice is not None for choice in pair["selected_rings"])
                and pair["regional_cover"] == geo["regional_cover"]
                and pair["payload"]["parameters"] == parameters
                and pair["payload"]["taxa"] == taxa
                for pair in selected
            ),
            "Exact admitted paired-ring/regional/PPE/taxon handoff required",
        )
        require(
            geo["target_geometry_sha256"] == geometry["source"]["sha256"]
            and geo["declared_target_forward_rings"]
            == geometry["data"]["forward_rings"]
            and geo["declared_target_inversion_rings"]
            == geometry["data"]["inversion_rings"]
            and geo["regional_anchor_record_id"] == context["anchor"]
            and geo["predictor_group_ids"]
            == [ancestry["groups"][record] for record in context["predictors"]]
            and geo["local_support_radius_m"] == 1000
            and geo["regional_cutoff_m"] == 100000,
            "Original target-specific support changed",
        )
        prediction = slot["prediction"]
        manifest = prediction["prediction_manifest"]
        require(
            digest(manifest) == prediction["prediction_manifest_sha256"]
            and digest(manifest["fold"]) == digest(context["fold"])
            and manifest["spatial_method"] == slot["baseline"]
            and manifest["predictor_group_ids"] == sorted(geo["predictor_group_ids"])
            and len(manifest["predictor_group_ids"])
            == len(set(geo["predictor_group_ids"]))
            and manifest["forward_inputs"] == geo["forward_inputs"]
            and manifest["vegetation_fraction"] == prediction["vegetation_fraction"]
            and manifest["pollen_fraction"] == prediction["pollen_fraction"],
            "Original manifest/source prediction differs",
        )
        inputs = geo["forward_inputs"]
        require(
            inputs["taxa"] == taxa
            and inputs["ppe"] == [row["ppe"] for row in parameters]
            and inputs["geometry_input_ids"]
            == ["experiment-geometry:" + geometry["source"]["sha256"]]
            and inputs["temporal_support_id"]
            == "experiment-time:"
            + digest(
                {
                    "metadata": geometry["data"]["sample_metadata"],
                    "matching": protocol["temporal_matching"],
                }
            )
            and inputs["local_k"] == geo["full_k"][:2]
            and inputs["terrestrial_fraction"] == geo["full_terrestrial_fraction"][:2],
            "Original forward axes/temporal identity changed",
        )
        require(
            set(prediction["vegetation_fraction"])
            == set(prediction["pollen_fraction"])
            == set(taxa),
            "Exact labelled30taxon prediction axis required",
        )
        output.append(
            {
                "kind": key[0],
                "outer_target": key[1],
                "target": key[2],
                "baseline": key[3],
                "source_slot_sha256": digest(slot),
                "source_prediction_manifest_sha256": prediction[
                    "prediction_manifest_sha256"
                ],
                "source_fold": slot["fold"],
                "source_request_sha256s": [
                    pair["nominal_request_sha256"] for pair in selected
                ],
                "vegetation_fraction": prediction["vegetation_fraction"],
                "saved_source_pollen_fraction": prediction["pollen_fraction"],
                "raw_regional_cover": geo["regional_cover"],
                "original_full_k": geo["full_k"],
                "temporal_support_id": inputs["temporal_support_id"],
            }
        )
    require(
        len(seen) == 675
        and sum(row["kind"] == "outer" for row in output) == 45
        and {key[:3] for key in seen} == set(expected_contexts),
        "Complete45outer/630inner diagnostic population required",
    )
    return output, {
        "taxa": taxa,
        "parameters": parameters,
        "geometries": geometries,
        "original_slots": 675,
        "outer_slots": 45,
        "inner_slots": 630,
        "new_reconstructions": 0,
        "new_spatial_fits": 0,
    }
