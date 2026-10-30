"""Required-cohort point predictions with count-free held-out receivers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from copy import deepcopy
from fractions import Fraction
import math
from typing import Any

from bijux_pollenomics_lra.models.errors import ValidationError

from ..inputs import require
from ..prediction import Target, _closed, _forward
from .inputs import AXIS, METHODS, counts, response_id, semantic_sha


def native_inverse(
    vector: tuple[int, int],
    kernels: tuple[float, ...],
    ppe: tuple[float, ...],
    covariance: tuple[tuple[float, ...], ...],
) -> tuple[float, ...]:
    """Use the selected covariance directly; uncertainty outputs are not consumed."""
    import numpy as np

    from bijux_pollenomics_lra.api import fixed_site_cover_covariance

    exact = counts(list(vector))
    result = fixed_site_cover_covariance(
        np.asarray([exact], dtype=np.int64),
        np.asarray([kernels]),
        np.asarray(ppe),
        np.asarray(covariance),
        taxon_measured=np.ones((1, 2), dtype=bool),
    )
    return _closed(result.cover, 2)


def structural_sources(
    profile: dict[str, Any],
    experiment: str,
    target: dict[str, Any],
    scope: str,
    protocol: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted = []
    excluded = []
    for core in protocol["cores"]:
        reason = None
        if core["key"] not in profile["cores"]:
            reason = "outside_profile_core_selection"
        elif core["physical_family"] == target["physical_family"]:
            reason = "whole_target_physical_family_excluded"
        elif experiment == "country_holdout" and core["country"] == target["country"]:
            reason = "whole_target_country_excluded"
        elif scope == "swedish_only" and core["country"] != "SE":
            reason = "outside_declared_training_scope"
        if reason:
            excluded.append(
                {
                    "core": core["key"],
                    "physical_family": core["physical_family"],
                    "country": core["country"],
                    "reason": reason,
                }
            )
        else:
            accepted.append(core)
    require(
        bool(accepted)
        and len({c["physical_family"] for c in accepted}) == len(accepted),
        "Unique nonempty structural physical cohort required",
    )
    require(
        (
            experiment == "swedish_training_scope"
            and scope in {"swedish_only", "pooled_nordic"}
        )
        or (experiment == "country_holdout" and scope == "outside_target_country"),
        "Unknown held-out experiment/scope",
    )
    return accepted, excluded


def weights(sources: list[dict[str, Any]], weighting: str) -> list[Fraction]:
    require(
        weighting in {"equal_physical_place", "equal_country_then_place"},
        "Unknown fixed weighting",
    )
    countries = Counter(c["country"] for c in sources)
    values = [
        Fraction(1, len(sources))
        if weighting == "equal_physical_place"
        else Fraction(1, len(countries) * countries[c["country"]])
        for c in sources
    ]
    require(
        sum(values) == 1 and all(w > 0 for w in values),
        "Complete fixed source weights required",
    )
    return values


def _receiver(
    core: dict[str, Any],
    window: list[int],
    packet: dict[str, Any],
    protocol: dict[str, Any],
    responses: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ids = [
        response_id(
            {
                "receiver_radius_m": core["radius_m"],
                "inner_radius_m": core["radius_m"],
                "outer_radius_m": protocol["transport"]["outer_radius_m"],
                "fall_speed_m_s": float(v),
            },
            protocol,
        )
        for v in protocol["parameters"]["fall_speed_m_s_text"]
    ]
    rows = [responses[k] for k in ids]
    return {
        "core": core["key"],
        "site": core["identity"]["site_id"],
        "dataset": core["identity"]["dataset_id"],
        "collection_unit": core["identity"]["collection_unit_id"],
        "country": core["country"],
        "physical_family": core["physical_family"],
        "window_cal_bp": deepcopy(window),
        "axis": list(AXIS),
        "ppe": list(packet["ppe"]),
        "kernels": [r["factor"] if r["status"] == "available" else None for r in rows],
        "response_ids": ids,
        "receiver_radius_m": core["radius_m"],
        "metadata_source_locator": core["metadata_source_locator"],
    }


def _family() -> dict[str, Any]:
    return {
        "status": "refused",
        "pollen_fraction": None,
        "cover": None,
        "preclosure": None,
        "reason": None,
        "refusals": [],
    }


def predict_context(
    packet: dict[str, Any],
    protocol: dict[str, Any],
    response_packet: dict[str, Any],
    profile: dict[str, Any],
    experiment: str,
    target_key: str,
    window: list[int],
    scope: str,
    cache: dict[str, dict[str, Any]],
    *,
    inverse: Callable[..., tuple[float, ...]] = native_inverse,
    forward: Callable[[Target, tuple[float, ...]], tuple[float, ...]] = _forward,
) -> dict[str, Any]:
    declarations = {c["key"]: c for c in protocol["cores"]}
    target_core = declarations[target_key]
    require(
        target_key in profile["cores"] and window in protocol["windows"],
        "Declared profile target/window required",
    )
    responses = {r["response_id"]: r for r in response_packet["rows"]}
    require(
        len(responses) == 12 == len(response_packet["rows"]),
        "Closed unique response population required",
    )
    target = _receiver(target_core, window, packet, protocol, responses)
    allowed, excluded = structural_sources(
        profile, experiment, target_core, scope, protocol
    )
    values = weights(allowed, profile["weighting"])
    identity = {
        "profile": profile["id"],
        "experiment": experiment,
        "target_core": target_key,
        "physical_family": target_core["physical_family"],
        "country": target_core["country"],
        "window_cal_bp": deepcopy(window),
        "axis": list(AXIS),
        "scope": scope,
    }
    context_id = (
        f"{profile['id']}/{experiment}/{target_key}/{window[0]}-{window[1]}/{scope}"
    )
    required = []
    window_refusals = []
    for core, weight in zip(allowed, values, strict=True):
        index = protocol["windows"].index(window)
        cell = packet["cores"][core["key"]]["windows"][index]
        require(cell["window"] == window, "Exact source window required")
        receiver = _receiver(core, window, packet, protocol, responses)
        row = {
            k: receiver[k]
            for k in (
                "core",
                "country",
                "physical_family",
                "site",
                "dataset",
                "collection_unit",
                "window_cal_bp",
                "kernels",
                "response_ids",
                "ppe",
            )
        }
        row.update(
            weight_exact=str(weight),
            weight=float(weight),
            window_status=cell["status"],
            counts=deepcopy(cell["panel_counts"]),
            panel_N=cell["panel_N"],
            sample_ids=deepcopy(cell["sample_ids"]),
            source_ref={
                "ledger": core["key"],
                "window_index": index,
                "window_sha256": semantic_sha(cell),
            },
            inverse={
                "status": "not_run",
                "preclosure": None,
                "cover": None,
                "refusal": None,
            },
        )
        if cell["status"] != "supported":
            window_refusals.append(
                {
                    "operation": "training_window",
                    "core": core["key"],
                    "reason_code": cell["status"],
                    "message": cell["status"],
                }
            )
        else:
            vector = counts(cell["panel_counts"])
            require(
                type(cell["panel_N"]) is int and sum(vector) == cell["panel_N"],
                "Source panel count denominator differs",
            )
        required.append(row)
    families = {name: _family() for name in METHODS}
    context = {
        "context_id": context_id,
        "identity": identity,
        "target": target,
        "required_sources": required,
        "excluded_sources": excluded,
        "families": families,
    }
    if window_refusals:
        for family in families.values():
            family.update(
                reason="required_training_source_unavailable",
                refusals=deepcopy(window_refusals),
            )
        return context
    direct = _closed(
        [
            math.fsum(
                float(weight) * r["counts"][i] / r["panel_N"]
                for r, weight in zip(required, values, strict=True)
            )
            for i in range(2)
        ],
        2,
    )
    families["direct_panel_mean"].update(
        status="predicted", pollen_fraction=list(direct)
    )
    response_refusals = [
        {
            "operation": "source_response",
            "core": r["core"],
            "reason_code": "response_unavailable",
            "message": "Required source response unavailable",
        }
        for r in required
        if any(k is None for k in r["kernels"])
    ]
    if any(k is None for k in target["kernels"]):
        response_refusals.append(
            {
                "operation": "target_response",
                "core": target_key,
                "reason_code": "response_unavailable",
                "message": "Target response unavailable",
            }
        )
    if response_refusals:
        for row in required:
            own = [
                r
                for r in response_refusals
                if r["operation"] == "source_response" and r["core"] == row["core"]
            ]
            if own:
                row["inverse"].update(status="refused", refusal=deepcopy(own[0]))
        families["physical_forward"].update(
            reason="response_unavailable", refusals=response_refusals
        )
        return context
    inverse_refusals = []
    for row in required:
        vector = counts(row["counts"])
        key = semantic_sha(
            {
                "source": row["source_ref"],
                "counts": row["counts"],
                "kernels": row["kernels"],
                "ppe": packet["ppe"],
                "covariance": packet["covariance"],
            }
        )
        try:
            if key not in cache:
                cover = _closed(
                    inverse(
                        vector,
                        tuple(row["kernels"]),
                        packet["ppe"],
                        packet["covariance"],
                    ),
                    2,
                )
                preclosure = [
                    float(vector[i]) * (1.0 / (row["kernels"][i] * packet["ppe"][i]))
                    for i in range(2)
                ]
                require(
                    all(math.isfinite(v) and v >= 0 for v in preclosure),
                    "Finite inverse preclosure required",
                )
                cache[key] = {
                    "status": "computed",
                    "preclosure": preclosure,
                    "cover": list(cover),
                    "refusal": None,
                }
            row["inverse"] = deepcopy(cache[key])
        except ValidationError as exc:
            refusal = {
                "operation": "source_inverse",
                "core": row["core"],
                "reason_code": exc.reason_code,
                "message": str(exc),
            }
            row["inverse"].update(status="refused", refusal=refusal)
            inverse_refusals.append(refusal)
    if inverse_refusals:
        families["physical_forward"].update(
            reason="source_inverse_refused", refusals=inverse_refusals
        )
        return context
    cover = _closed(
        [
            math.fsum(
                float(w) * r["inverse"]["cover"][i]
                for r, w in zip(required, values, strict=True)
            )
            for i in range(2)
        ],
        2,
    )
    try:
        native_target = Target(
            target_key,
            target["site"],
            target["dataset"],
            target["collection_unit"],
            (float(window[0]), float(window[1])),
            AXIS,
            tuple(packet["ppe"]),
            tuple(target["kernels"]),
        )
        pollen = _closed(forward(native_target, cover), 2)
        preclosure = [
            target["kernels"][i] * (cover[i] * packet["ppe"][i]) for i in range(2)
        ]
        families["physical_forward"].update(
            status="predicted",
            pollen_fraction=list(pollen),
            cover=list(cover),
            preclosure=preclosure,
        )
    except ValidationError as exc:
        families["physical_forward"].update(
            reason="target_forward_refused",
            refusals=[
                {
                    "operation": "target_forward",
                    "core": target_key,
                    "reason_code": exc.reason_code,
                    "message": str(exc),
                }
            ],
        )
    return context


def context_specs(
    protocol: dict[str, Any],
) -> list[tuple[dict[str, Any], str, str, list[int], str]]:
    result = []
    for profile in protocol["profiles"]:
        for experiment in protocol["experiments"]:
            targets = [
                "solsoe81" if t == "solsoe83" and "solsoe81" in profile["cores"] else t
                for t in experiment["targets"]
            ]
            for target in targets:
                for window in protocol["windows"]:
                    for scope in experiment["scopes"]:
                        result.append(
                            (profile, experiment["id"], target, window, scope)
                        )
    return result


def predict_all(
    packet: dict[str, Any],
    protocol: dict[str, Any],
    responses: dict[str, Any],
    **callbacks: Any,
) -> list[dict[str, Any]]:
    contexts = []
    cache: dict[str, dict[str, Any]] = {}
    for profile, experiment, target, window, scope in context_specs(protocol):
        contexts.append(
            predict_context(
                packet,
                protocol,
                responses,
                profile,
                experiment,
                target,
                window,
                scope,
                cache,
                **callbacks,
            )
        )
    require(
        len(contexts) == 216
        and len({r["context_id"] for r in contexts}) == 216
        and sum(len(r["families"]) for r in contexts) == 432,
        "All216 contexts/432 dispositions required",
    )
    return contexts
