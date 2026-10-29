"""Inspect admitted starts or prove a source-bound 500 m saved-value projection."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
from typing import Any

ROOT = Path(__file__).absolute().parents[4]
PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/nested-transport/"


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def checked(row: dict[str, Any]) -> bytes:
    path = Path(row["path"])
    path = path if path.is_absolute() else ROOT / path
    require(
        ".." not in path.parts
        and not any(p.is_symlink() for p in (path, *path.parents))
        and path.is_file()
        and path.stat().st_nlink == 1
        and path.stat().st_size <= 256 * 1024**2,
        "Exact physical bounded input required",
    )
    raw = path.read_bytes()
    require(
        len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
        "Scientific input changed",
    )
    return raw


def load(row: dict[str, Any]) -> dict[str, Any]:
    checked(row)
    path = Path(row["path"])
    return runpy.run_path(str(path if path.is_absolute() else ROOT / path))


def handoff(
    common: dict[str, Any],
    libraries: dict[str, Any],
    training_math: dict[str, Any],
    nested: dict[str, Any],
    descriptor: dict[str, Any],
    scientific: dict[str, Any],
    projection: dict[str, Any],
) -> dict[str, Any]:
    nominal = next(
        row for row in descriptor["shards"] if row["method"] == "gpm neutral"
    )
    cert = common["decode"](common["checked"](ROOT, nominal["saved_product_admission"]))
    scientific["admit_shard"](
        common, ROOT, nominal, cert["candidate"], nested["training_protocol_sha256"]
    )
    require(
        cert["summary"]["numerical_requests"] == 39
        and cert["summary"]["unique_attempts"] == 2496,
        "Actual admitted nominal39/2496 authority",
    )
    training = common["decode"](common["checked"](ROOT, nominal["training"]))
    prior, _ = training_math["previous"](common, ROOT, nested, libraries)
    for row in training["new_attempts"]:
        prior.setdefault((row["request_sha256"], row["ring_index"]), []).append(row)
    population = projection["saved_population"](training["numerical_requests"], prior)
    return {
        "nominal": nominal,
        "certificate": cert,
        "training": training,
        "attempts": prior,
        "population": population,
    }


def verify(
    common: dict[str, Any],
    libraries: dict[str, Any],
    request_math: dict[str, Any],
    projection: dict[str, Any],
    equivalent: dict[str, Any],
    prepared: Path,
    nested: dict[str, Any],
    saved: dict[str, Any],
    freeze: dict[str, Any],
) -> dict[str, Any]:
    experiment = common["decode"](
        common["checked"](
            prepared,
            next(row for row in nested["inputs"] if row["path"] == "experiment.json"),
        )
    )
    original_experiment = request_math["weighted_experiment"](experiment, "gpm neutral")
    support_experiment = deepcopy(original_experiment)
    support_experiment["local_ring_count"] = 1
    support_experiment["local_support_radius_m"] = 500
    support_experiment["request_template"]["configuration"]["love"]["max_ring"] = 1
    original_spec = libraries["original"]["SourceExperimentSpec"](original_experiment)
    support_spec = libraries["original"]["SourceExperimentSpec"](support_experiment)
    contexts, groups = request_math["contexts"](libraries["original"], original_spec)
    support_contexts, support_groups = request_math["contexts"](
        libraries["original"], support_spec
    )
    require(groups == support_groups, "Physical groups unchanged")
    original, logical = request_math["requests"](
        libraries["original"], original_spec, prepared, contexts
    )
    support, support_logical = request_math["requests"](
        libraries["original"], support_spec, prepared, support_contexts
    )
    records = saved["training"]["numerical_requests"]
    require(
        set(original) == set(records)
        and common["digest"](logical)
        == common["digest"](saved["training"]["logical_requests"]),
        "Exact original39requests/2715fold ancestry",
    )
    regional_sites = {
        site.record.site_id: site.record.record_id for site in original_spec.sites
    }

    def pairs(items: dict[str, Any]) -> dict[tuple[str, str], Any]:
        return {
            (
                item.item_id,
                regional_sites[item.payload()["regional"]["samples"][0]["site_id"]],
            ): item
            for item in items.values()
        }

    old_pairs, new_pairs = pairs(original), pairs(support)
    require(
        set(old_pairs) == set(new_pairs) and len(new_pairs) == 39,
        "Thirty-nine original/support pairs",
    )
    bridges, aliases = [], {}
    for pair, item in sorted(old_pairs.items()):
        other = new_pairs[pair]
        old_payload = libraries["original"]["validate_lra_inputs"](
            item.payload(), input_root=prepared
        ).payload()
        new_payload = libraries["original"]["validate_lra_inputs"](
            other.payload(), input_root=prepared
        ).payload()
        binding = libraries["original"]["load_engine"](
            required_capability=libraries["original"][
                "required_capability_for_profile"
            ](old_payload["method_profile"])
        )
        proof = projection["ring_arguments"](
            equivalent,
            libraries,
            old_payload,
            new_payload,
            records[item.request_sha256],
            saved["attempts"][(item.request_sha256, 0)],
            binding,
        )
        require(
            proof["original_request_sha256"] == item.request_sha256
            and proof["support_request_sha256"] == other.request_sha256,
            "Exact distinct request projection hashes",
        )
        bridges.append(proof)
        aliases[item.request_sha256] = other.request_sha256
    reverse = {value: key for key, value in aliases.items()}
    normalized = [
        {**row, "request_sha256": reverse[row["request_sha256"]]}
        for row in support_logical
    ]
    require(
        common["digest"](normalized) == common["digest"](logical),
        "Every outer/inner support alias retains original fold",
    )
    ring0 = {key: rows for (key, ring), rows in saved["attempts"].items() if ring == 0}
    population = equivalent["bind_ring0_population"](bridges, records, ring0)
    require(
        saved["population"]["equal_selected_covers"] == 39,
        "Do not infer prediction reuse from objective equality",
    )
    geometries, geometry_proofs = {}, []
    inputs = {row["path"]: row for row in nested["inputs"]}
    for site in original_spec.sites:
        ref = inputs[site.geometry.path]
        data = common["decode"](common["checked"](prepared, ref))
        geometry_proofs.append(
            {
                "record_id": site.record.record_id,
                "source_sha256": ref["sha256"],
                **equivalent["forward_geometry_bridge"](data),
            }
        )
        geometries[site.record.record_id] = {"data": data, "sha256": ref["sha256"]}
    slots = [slot for slot in freeze["slots"] if slot["method"] == "gpm neutral"]
    prediction = projection["prediction_projection"](
        slots,
        contexts,
        groups,
        records,
        {pair: item.request_sha256 for pair, item in old_pairs.items()},
        aliases,
        geometries,
        original_experiment["request_template"]["taxa"],
        tuple(original_spec.baselines),
        [row["ppe"] for row in original_experiment["request_template"]["parameters"]],
        original_experiment["request_template"]["temporal_matching"],
    )
    return {
        "request_bridges": bridges,
        "ring0_projection": population,
        "support_request_aliases_validated": 39,
        "saved_ring0_attempt_aliases_validated": 1248,
        "selected_support_compositions": [
            {
                "support_request_sha256": aliases[key],
                "original_request_sha256": key,
                "original_selection_sha256": common["digest"](row["selections"][0]),
                "composition": row["selections"][0]["composition"],
                "derivation": "Exact admitted original ring-zero selected composition; no new fit",
            }
            for key, row in sorted(records.items())
        ],
        "selected_cover_handoff": saved["population"],
        "geometry_proofs": geometry_proofs,
        "prediction_value_projection": prediction,
        "original_native_exit": 1,
        "original_native_qualification": "refused_post_scientific_body_origin",
        "new_optimizer_calls": 0,
        "new_kernel_calls": 0,
        "new_forward_calls": 0,
        "new_score_calls": 0,
        "proof_kind": "Actual saved identities plus pinned deterministic operator congruence; not a repeated model evaluation",
        "scientific_acceptance": "not_evaluated",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--mode", choices=("inspect", "verify"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.protocol.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == args.protocol_sha256,
        "Frozen consumer protocol",
    )
    protocol = json.loads(raw)
    require(
        protocol["schema_version"] == "author-love-admitted-ring-support-protocol.v1"
        and set(protocol["sources"]) == {"replay", "projection"},
        "Finite saved support protocol",
    )
    checked(protocol["sources"]["replay"])
    require(
        protocol["sources"]["replay"]["path"] == str(Path(__file__).absolute()),
        "Exact consumer entry",
    )
    if args.mode == "verify":
        plan_path = Path(os.environ["BIJUX_ATLAS_REGISTERED_PLAN"])
        plan_raw = plan_path.read_bytes()
        require(
            hashlib.sha256(plan_raw).hexdigest()
            == os.environ["BIJUX_ATLAS_REGISTERED_SHA256"],
            "Same registered plan buffer",
        )
        plan = json.loads(plan_raw)
        require(
            plan["candidate"] == protocol["source_candidate"]
            and plan["scientific_mode"] == "ring_support_saved_equivalence"
            and plan["scientific_arguments"] == sys.argv[1:]
            and plan["scientific_protocol"]["sha256"] == args.protocol_sha256,
            "Registered finite support consumer",
        )
    metadata_root = Path(protocol["source_metadata_root"])
    require(
        {str(p.absolute()) for p in metadata_root.rglob("*") if p.is_file()}
        == {row["path"] for row in protocol["source_metadata"]},
        "Exact reused source-only distribution metadata projection",
    )
    for row in protocol["source_metadata"]:
        checked(row)
    sys.path.insert(0, str(metadata_root))
    common = load(protocol["canonical_sources"]["common"])
    nested = common["decode"](checked(protocol["nested_protocol"]))
    prepared = Path(protocol["prepared_inputs"])
    directory = ROOT / PREFIX / "source"
    common["guard"](ROOT, prepared, directory, nested)
    for row in [
        *protocol["sources"].values(),
        *protocol["canonical_sources"].values(),
        *protocol["operator_sources"],
        protocol["nested_protocol"],
        protocol["equivalence_source"],
        protocol["publication_authority"],
        protocol["admitted_descriptor"],
    ]:
        checked(row)
    for row in protocol["operator_sources"]:
        checked(row)
    libraries = common["libraries"](ROOT)
    training_math = load(protocol["canonical_sources"]["training"])
    scientific = load(protocol["canonical_sources"]["replay"])
    request_math = load(protocol["canonical_sources"]["requests"])
    projection = load(protocol["sources"]["projection"])
    descriptor = common["decode"](checked(protocol["admitted_descriptor"]))
    saved = handoff(
        common, libraries, training_math, nested, descriptor, scientific, projection
    )
    if args.mode == "inspect":
        result = {
            "inspection_only": True,
            "nominal_certificate": saved["nominal"]["saved_product_admission"],
            "summary": saved["population"],
            "new_support_aliases_admitted": False,
            "kernel_optimizer_forward_or_score_calls": 0,
        }
    else:
        equivalent = load(protocol["equivalence_source"])
        authority = common["decode"](checked(protocol["publication_authority"]))
        require(
            authority["independent_semantics"]["approved"] is True
            and authority["independent_semantics"]["scientific_saved_products_admitted"]
            is True,
            "Original independent saved-output authority",
        )
        reference = protocol["candidate_freeze"]
        require(
            {key: reference[key] for key in ("sha256", "bytes")}
            == authority["raw_trace_products"][
                "evaluation:candidate-prediction-freeze.json"
            ],
            "Admitted original complete candidate freeze",
        )
        freeze = common["decode"](checked(reference))
        result = verify(
            common,
            libraries,
            request_math,
            projection,
            equivalent,
            prepared,
            nested,
            saved,
            freeze,
        )
    common["guard"](ROOT, prepared, directory, nested)
    result.update(
        schema_version="author-love-admitted-ring-support.v1",
        source_candidate=protocol["source_candidate"],
        protocol_sha256=args.protocol_sha256,
        original_source_candidate=saved["certificate"]["candidate"],
    )
    output = args.output.absolute()
    require(
        output.is_relative_to(ROOT / "artifacts")
        and not output.exists()
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "Fresh owned support receipt",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(
            (
                json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
            ).encode()
        )
    print(
        json.dumps(
            {"output": str(output), "mode": args.mode, "new_optimizer_calls": 0},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
