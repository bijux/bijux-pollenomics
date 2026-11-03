"""Independent native-pair, target-forward and retained-reference projection."""

from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Any

from .predictions import BASELINES, compare, contexts, digest, number, require, same

STATIC_FORWARD = (
    "preparation_profile",
    "forward_method_profile",
    "geometry_profile",
    "deposition_units",
    "full_k",
    "full_terrestrial_fraction",
    "ring_bounds_m",
    "regional_cutoff_m",
    "target_geometry_sha256",
    "support_profile",
    "local_support_radius_m",
    "declared_target_inversion_rings",
    "declared_target_forward_rings",
)


def audit_projection(
    protocol: dict[str, Any],
    packet: dict[str, Any],
    upstream: dict[str, Any],
    experiment: dict[str, Any],
    expected_geometry: dict[str, Any],
    native: dict[str, Any],
    old_protocol: dict[str, Any],
    documents: dict[str, Any],
    counts: dict[str, dict[str, int]],
) -> dict[str, Any]:
    """Check new source closures against independently authenticated old data."""
    roles = contexts(packet, protocol)
    selected = packet["cohort"]["selected"]
    same(
        packet["observation_refs"],
        [
            next(r for r in upstream["observation_refs"] if r["record_id"] == o)
            for o in selected
        ],
    )
    require(
        len(native["numerical_requests"]) == 39
        and digest(native["logical_requests"])
        == old_protocol["logical_ancestry_sha256"],
        "native source request catalogue",
    )
    pair_requests: dict[tuple[str, str], str] = {}
    for link in native["logical_requests"]:
        pair = (link["local_record_id"], link["regional_anchor_record_id"])
        if pair in pair_requests:
            require(
                pair_requests[pair] == link["request_sha256"],
                "source pair request ambiguity",
            )
        pair_requests[pair] = link["request_sha256"]
    ppe = [r["ppe"] for r in experiment["request_template"]["parameters"]]
    used: dict[tuple[str, str], Any] = {}
    for row in roles.values():
        target, anchor = row["target"], row["anchor"]
        train = row["fold"]["train_record_ids"]
        require(
            anchor == next(o for o in experiment["regional_priority"] if o in train),
            "original regional source priority",
        )
        same(
            row["context_id"],
            "author-thinning:"
            + digest(
                {
                    "fold": row["fold"],
                    "selected": selected,
                    "forbidden": sorted(packet["groups"].keys() - set(train)),
                }
            ),
        )
        regional = None
        for predictor in row["predictors"]:
            local = predictor["record_id"]
            request = pair_requests[(local, anchor)]
            original = native["numerical_requests"][request]
            require(
                original["request_sha256"] == request
                and original["item_id"] == local
                and original["taxa"] == packet["taxa"],
                "native local owner and axis",
            )
            attempts = [s["selected_attempt_sha256"] for s in original["selections"]]
            expected = {
                "record_id": local,
                "group_id": packet["groups"][local],
                "covers_by_ring": [
                    [s["composition"][t] for t in packet["taxa"]]
                    for s in original["selections"]
                ],
                "request_sha256": request,
                "selected_attempt_sha256s": attempts,
                "fit_refs": [
                    "nominal-fit:" + digest({"request": request, "selected_attempt": a})
                    for a in attempts
                ],
                "scientific_parent_ids": [local, anchor],
            }
            same(predictor, expected)
            if regional is None:
                regional = original["regional_cover"]
            same(original["regional_cover"], regional)
            used[(local, anchor)] = {
                "local_record_id": local,
                "regional_anchor_record_id": anchor,
                **{
                    k: expected[k]
                    for k in (
                        "request_sha256",
                        "selected_attempt_sha256s",
                        "fit_refs",
                        "scientific_parent_ids",
                    )
                },
            }
        assert regional is not None
        originals = [
            c
            for c in upstream["contexts"]
            if c["target"] == target and c["anchor"] == anchor
        ]
        require(bool(originals), "source target/anchor forward packet")
        forward = row["forward"]
        require(
            set(forward)
            == set(STATIC_FORWARD)
            | {
                "outer_fold",
                "regional_anchor_record_id",
                "regional_anchor_group_id",
                "regional_value_source_record_ids",
                "regional_identity_source_record_ids",
                "regional_identity_policy",
                "predictor_group_ids",
                "distances_km",
                "regional_cover",
                "forward_inputs",
            },
            "closed fresh forward lineage",
        )
        require(
            forward["regional_anchor_group_id"] == packet["groups"][anchor]
            and forward["regional_identity_policy"]
            == "conservative_all_training_fit_receipts",
            "fresh forward group/policy",
        )
        same(
            forward["predictor_group_ids"],
            sorted(p["group_id"] for p in row["predictors"]),
        )
        expected_forward = {key: originals[0]["forward"][key] for key in STATIC_FORWARD}
        target_originals = [c for c in upstream["contexts"] if c["target"] == target]
        for original in target_originals:
            same(
                {key: original["forward"][key] for key in STATIC_FORWARD},
                expected_forward,
            )
        with localcontext() as ctx:
            ctx.prec = 80

            def d(value: Any) -> Decimal:
                return Decimal.from_float(number(value))

            regional_deposition = [
                float(
                    d(ppe[t])
                    * d(regional[t])
                    * sum(
                        (
                            d(k[t]) * d(f)
                            for k, f in zip(
                                expected_forward["full_k"][2:],
                                expected_forward["full_terrestrial_fraction"][2:],
                                strict=True,
                            )
                        ),
                        Decimal(0),
                    )
                )
                for t in range(30)
            ]
        for key in STATIC_FORWARD:
            same(forward[key], expected_forward[key])
        inputs = forward["forward_inputs"]
        exogenous = (
            "parameter_input_ids",
            "geometry_input_ids",
            "temporal_support_id",
            "method_profile",
            "engine_build_id",
        )
        require(
            set(inputs)
            == {
                "taxa",
                "ppe",
                "regional_deposition",
                "local_k",
                "terrestrial_fraction",
                "regional_input_ids",
                *exogenous,
            },
            "closed numerical and exogenous forward packet",
        )
        for key in exogenous:
            for original in target_originals:
                same(inputs[key], original["forward"]["forward_inputs"][key])
        same(
            inputs["geometry_input_ids"],
            ["experiment-geometry:" + packet["geometry_refs"][target]["sha256"]],
        )
        same(
            inputs["parameter_input_ids"],
            [
                "experiment-parameters:"
                + digest(
                    {
                        "parameters": experiment["request_template"]["parameters"],
                        "evidence": experiment["request_template"]["evidence"],
                    }
                )
            ],
        )
        same(
            inputs["temporal_support_id"],
            "experiment-time:"
            + digest(
                {
                    "metadata": expected_geometry[target]["sample_metadata"],
                    "matching": experiment["request_template"]["temporal_matching"],
                }
            ),
        )
        same(
            inputs["regional_input_ids"],
            [
                "thinning-regional:"
                + digest(
                    {
                        "regional_owner_id": anchor,
                        "regional_cover": regional,
                        "support_id": "experiment-support:" + digest(packet["support"]),
                    }
                )
            ],
        )
        same(inputs["ppe"], ppe)
        same(forward["regional_cover"], regional)
        same(inputs["local_k"], expected_forward["full_k"][:2])
        same(
            inputs["terrestrial_fraction"],
            expected_forward["full_terrestrial_fraction"][:2],
        )
        compare(inputs["regional_deposition"], regional_deposition, 1e-12, 1e-10)
        for original in originals:
            compare(
                inputs["regional_deposition"],
                original["forward"]["forward_inputs"]["regional_deposition"],
                1e-12,
                1e-10,
            )
        same(
            forward["distances_km"],
            {
                p["group_id"]: packet["cohort"]["distance_matrix_m"][target][
                    p["record_id"]
                ]
                / 1000
                for p in row["predictors"]
            },
        )
        same(
            row["coordinates"],
            {
                o: packet["cohort"]["coordinates"][o]
                for o in sorted({target, *[p["record_id"] for p in row["predictors"]]})
            },
        )
    require(
        len(used) == protocol["cohort"]["expected_distinct_pairs"] == 17,
        "complete seventeen source pairs",
    )
    same(packet["pair_catalogue"], [used[key] for key in sorted(used)])
    references, metrics = [], {}
    old_scores = {r["outer_target"]: r for r in documents["outer_scores"]}
    for target in selected:
        outer = next(
            c
            for c in upstream["contexts"]
            if c["target"] == c["outer_target"] == target
        )
        old_score = old_scores[target]
        require(
            old_score["status"] == "scored"
            and old_score["selected_scale_km"] == 20.0
            and old_score["observed_count"] == sum(counts[target].values()),
            "qualified retained score and count correspondence",
        )
        same(
            old_score["observed_reference"],
            next(r for r in packet["observation_refs"] if r["record_id"] == target),
        )
        metrics[target] = {
            **old_score["matched_baselines"],
            "hellinger_20km": old_score["metrics"],
        }
        for method in (*BASELINES, "hellinger_20km"):
            if method in BASELINES:
                original = next(
                    r for r in outer["reference_baselines"] if r["baseline"] == method
                )
                cover, pollen = [
                    [original[field][t] for t in packet["taxa"]]
                    for field in ("vegetation_fraction", "pollen_fraction")
                ]
            else:
                original = next(
                    r
                    for r in documents["candidates"]
                    if r["context_id"] == outer["context_id"]
                    and r["length_scale_km"] == 20.0
                )
                require(
                    original["status"] == "predicted", "retained Hellinger reference"
                )
                same(original["scientific_refs"], outer["scientific_refs"])
                cover, pollen = (
                    original["vegetation_fraction"],
                    original["pollen_fraction"],
                )
            references.append(
                {
                    "target": target,
                    "method_id": method,
                    "status": "predicted",
                    "vegetation_fraction": cover,
                    "pollen_fraction": pollen,
                    "source_channel": "full_fifteen_"
                    + (method if method in BASELINES else "h20"),
                    "original_context_id": outer["context_id"],
                    "scientific_refs": outer["scientific_refs"],
                }
            )
    same(packet["retained_reference_predictions"], references)
    same(
        packet["summary"],
        {
            "contexts": 10,
            "training_owners_per_fold": 9,
            "local_predictors_per_fold": 8,
            "cached_pairs": 17,
            "retained_references": 40,
            "upstream_nominal_slots_reused": 675,
            "new_inverse_fits": 0,
            "new_kernel_calls": 0,
            "new_forward_calls": 0,
            "new_random_draws": 0,
            "outcomes_decoded": 0,
        },
    )
    return metrics
