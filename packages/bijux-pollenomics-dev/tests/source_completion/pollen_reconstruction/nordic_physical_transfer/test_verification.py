"""Analytical independent transfer, cohort and strict source-custody controls."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path
from typing import Any

import pytest

from .algebra import (
    PRECISION,
    compare,
    count_vector,
    direct_prediction,
    inverse,
    metrics,
    number,
    predict,
)
from .population import cohort, loss_summary, plan
from .verification import json_value, pointer, response_identity, responses

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/nordic-physical-transfer/protocol.json"
)


def profile() -> dict[str, Any]:
    value = json.loads(PROTOCOL.read_bytes())
    assert isinstance(value, dict)
    return value


def source(
    counts: list[int], coefficients: list[float], weight: float = 1.0
) -> dict[str, Any]:
    return {"counts": counts, "coefficients": coefficients, "weight": weight}


def test_hand_calculated_inverse_forward_and_direct_are_different() -> None:
    with localcontext() as context:
        context.prec = PRECISION
        value = predict([source([10, 20], [0.25, 0.5])], [0.5, 0.25], [2, 1])
        assert value["individual"][0]["preclosure"] == [Decimal(20), Decimal(40)]
        assert value["individual"][0]["cover"] == [Decimal(1) / 3, Decimal(2) / 3]
        compare(value["physical"], [Decimal(2) / 3, Decimal(1) / 3])
        assert value["direct"] == [Decimal(1) / 3, Decimal(2) / 3]
        loss = metrics(value["physical"], [10, 20])
        compare(loss["mae_fraction"], Decimal(1) / 3)
        assert loss["mae_fraction"] == loss["total_variation"]
        compare(loss["signed_error_by_taxon"], [Decimal(1) / 3, -Decimal(1) / 3])
        compare(loss["hellinger_stable"], (1 - 2 * Decimal(2).sqrt() / 3).sqrt())


@pytest.mark.parametrize("ppe", [[2, 1], [7, 0.03], [0.1, 80]])
def test_single_source_ppe_cancels_and_common_geometry_is_identity(
    ppe: list[float],
) -> None:
    first = predict([source([3, 17], [0.2, 0.6])], [0.4, 0.3], ppe)
    compare(
        first["physical"],
        [Decimal(6) / Decimal("14.5"), Decimal("8.5") / Decimal("14.5")],
    )
    identity = predict([source([3, 17], [0.2, 0.6])], [0.2, 0.6], ppe)
    compare(identity["physical"], identity["direct"])


def test_multiple_sources_have_identity_only_for_common_axis_response_product() -> None:
    owners = [source([1, 9], [0.25, 0.5], 0.25), source([8, 2], [0.25, 0.5], 0.75)]
    equal_product = predict(owners, [0.25, 0.5], [2, 1])
    compare(equal_product["physical"], equal_product["direct"])
    mixed = predict(owners, [0.25, 0.5], [1, 1])
    assert abs(mixed["physical"][0] - mixed["direct"][0]) > Decimal(".01")


@pytest.mark.parametrize("multiplier", [2, 10**10])
def test_per_source_count_scale_and_common_ppe_scale_preserve_point_prediction(
    multiplier: int,
) -> None:
    a = [source([2, 7], [0.2, 0.3], 0.5), source([9, 1], [0.4, 0.1], 0.5)]
    original = predict(a, [0.3, 0.4], [3, 5])
    altered = deepcopy(a)
    altered[0]["counts"] = [v * multiplier for v in a[0]["counts"]]
    changed = predict(altered, [0.3, 0.4], [3 * multiplier, 5 * multiplier])
    compare(changed["physical"], original["physical"])
    compare(changed["direct"], original["direct"])


@pytest.mark.parametrize("counts", [[0, 5], [5, 0]])
def test_measured_zero_is_exact_not_missing_or_pseudocount(counts: list[int]) -> None:
    out = inverse(counts, [0.2, 0.3], [3, 5])
    zero = counts.index(0)
    assert out["preclosure"][zero] == out["cover"][zero] == 0
    value = predict([source(counts, [0.2, 0.3])], [0.3, 0.4], [3, 5])
    assert value["physical"][zero] == value["direct"][zero] == 0
    assert metrics(value["physical"], counts)["hellinger_stable"] == 0


@pytest.mark.parametrize(
    "bad", [[1.0, 2], [True, 2], [None, 2], [-1, 2], [0, 0], [1], [1, 2, 3]]
)
def test_count_domain_never_repairs_missing_fractional_boolean_or_zero_panel(
    bad: Any,
) -> None:
    with pytest.raises(ValueError):
        count_vector(bad)


@pytest.mark.parametrize("bad", [0, -1, None, True, float("nan"), float("inf")])
def test_response_failure_cannot_disable_the_count_only_direct_channel(
    bad: Any,
) -> None:
    owners = [source([2, 3], [bad, 0.5])]
    compare(direct_prediction(owners), [Decimal(".4"), Decimal(".6")])
    with pytest.raises(ValueError):
        predict(owners, [0.5, 0.5], [1, 1])


def test_all_requested_contexts_and_native_family_exclusions_are_metadata_only() -> (
    None
):
    p = profile()
    contexts = plan(p)
    assert len(contexts) == 216
    assert all(
        len([row for row in contexts if row["profile"] == q["id"]]) == 72
        for q in p["profiles"]
    )
    assert (
        len(
            {
                (
                    r["profile"],
                    r["experiment"],
                    r["target_core"],
                    *r["window_cal_bp"],
                    r["scope"],
                )
                for r in contexts
            }
        )
        == 216
    )
    for q in p["profiles"]:
        for target in q["cores"]:
            required, excluded = cohort(p, q, target, "outside_target_country")
            declarations = {r["key"]: r for r in p["cores"]}
            assert all(
                declarations[r["core"]]["country"] != declarations[target]["country"]
                for r in required
            )
            assert {r["core"] for r in required}.isdisjoint(
                {r["core"] for r in excluded}
            )
            assert len(required) + len(excluded) == 7
            if target.startswith("solsoe"):
                assert not any(r["core"].startswith("solsoe") for r in required)


def test_country_weights_derive_only_from_structural_training_countries() -> None:
    p = profile()
    required, _ = cohort(p, p["profiles"][1], "abborrtjarnen", "pooled_nordic")
    weights = {r["core"]: Fraction(r["weight_exact"]) for r in required}
    assert weights == {
        "bokesjon": Fraction(1, 8),
        "bussjosjon": Fraction(1, 8),
        "solsoe83": Fraction(1, 4),
        "laihalampi": Fraction(1, 4),
        "dalmutladdo": Fraction(1, 4),
    }
    swedish, _ = cohort(p, p["profiles"][1], "abborrtjarnen", "swedish_only")
    assert {r["core"]: r["weight_exact"] for r in swedish} == {
        "bokesjon": "1/2",
        "bussjosjon": "1/2",
    }
    country, _ = cohort(p, p["profiles"][1], "abborrtjarnen", "outside_target_country")
    assert {r["weight_exact"] for r in country} == {"1/3"}


def test_standalone_cohort_uses_decimal80_without_changing_callers_context() -> None:
    p = profile()
    with localcontext() as caller:
        caller.prec = 9
        required, _ = cohort(
            p, p["profiles"][1], "abborrtjarnen", "outside_target_country"
        )
        assert caller.prec == 9
    assert all(r["weight_decimal"] == Decimal("0." + "3" * 80) for r in required)


@pytest.mark.parametrize(
    "counts,accepted",
    [
        ([2**53 - 1, 0], True),
        ([2**53 - 2, 1], True),
        ([2**53 - 1, 1], False),
        ([2**53, 0], False),
    ],
)
def test_native_count_boundary_is_exact_and_not_rounded(
    counts: list[int], accepted: bool
) -> None:
    if accepted:
        assert count_vector(counts) == counts
    else:
        with pytest.raises(ValueError, match="below"):
            count_vector(counts)


def test_native_owner_weighting_is_separate_from_equal_target_window_means() -> None:
    rows = []
    for target, losses, owners in (("a", [0, 1], [1, 9]), ("b", [0.2], [10])):
        for loss, n in zip(losses, owners, strict=True):
            rows.append(
                {
                    "identity": {"target_core": target},
                    "status": "scored",
                    "metrics": dict.fromkeys(
                        ("mae_fraction", "hellinger_stable", "total_variation"), loss
                    ),
                    "target_owner_count": n,
                }
            )
    rows.append(
        {
            "identity": {"target_core": "b"},
            "status": "prediction_refused",
            "metrics": None,
            "target_owner_count": 99,
        }
    )
    macro, weighted = loss_summary(rows)
    assert macro is not None and macro["mae_fraction"] == Decimal(".35")
    assert weighted["owner_denominator"] == 20
    assert weighted["metrics"]["mae_fraction"] == Decimal(".55")


def test_json_integer_tokens_and_duplicate_member_refusals_remain_distinct() -> None:
    result = json_value(b'{"a":[1,1.0]}')
    assert type(result["a"][0]) is int and type(result["a"][1]) is Decimal
    with pytest.raises(ValueError):
        json_value(b'{"a":1,"a":2}')
    with pytest.raises(ValueError):
        json_value(b'{"a":NaN}')


def test_response_pointer_never_substitutes_another_case() -> None:
    body = {"cores": [{"factors": [[0.1, 0.2]]}, {"factors": [[0.3, 0.4]]}]}
    assert pointer(body, "/cores/1/factors/0/1") == 0.4
    with pytest.raises((ValueError, IndexError, KeyError)):
        pointer(body, "/cores/2/factors/0/1")


def response_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    p = profile()
    rows = []
    for original in [*p["retained_responses"], *p["new_response_requests"]]:
        old = "source" in original
        factor, error = (
            (original["factor"], original["estimated_absolute_error"])
            if old
            else (0.25, 1e-9)
        )
        rows.append(
            {
                "response_id": response_identity(
                    original["receiver_radius_m"], original["fall_speed_m_s"], p
                ),
                "receiver_radius_m": original["receiver_radius_m"],
                "inner_radius_m": original["receiver_radius_m"],
                "outer_radius_m": 100000,
                "fall_speed_m_s": original["fall_speed_m_s"],
                "transport": p["transport"],
                "factor": factor,
                "estimated_absolute_error": error,
                "rigorous_error_bound": False,
                "status": "available",
                "origin": "retained" if old else "current",
                "refusal": None,
                "diagnostics": None
                if old
                else {"factor": factor, "estimated_absolute_error": error},
                "source_ref": {
                    "pin": p["scientific_sources"][original["source"]],
                    "factor_pointer": original["factor_pointer"],
                    "error_pointer": original["error_pointer"],
                }
                if old
                else None,
            }
        )
    return p, {
        "schema_version": "nordic-physical-responses.v1",
        "taxa": p["taxa"],
        "transport": p["transport"],
        "rows": rows,
    }


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "drop",
        "duplicate",
        "factor",
        "geometry",
        "origin",
        "refusal",
        "id",
        "extra",
    ],
)
def test_all_retained_and_current_response_records_are_closed(
    damage: str | None,
) -> None:
    p, value = response_fixture()
    if damage == "drop":
        value["rows"].pop()
    elif damage == "duplicate":
        value["rows"][-1] = deepcopy(value["rows"][-2])
    elif damage == "factor":
        value["rows"][0]["factor"] += 0.01
    elif damage == "geometry":
        value["rows"][-1]["inner_radius_m"] = 88
    elif damage == "origin":
        value["rows"][-1]["origin"] = "retained"
    elif damage == "refusal":
        value["rows"][-1]["factor"] = None
    elif damage == "id":
        value["rows"][-1]["response_id"] = "foreign"
    elif damage == "extra":
        value["rows"][-1]["unreported"] = 1
    if damage is None:
        assert len(responses(value, p)) == 12
    else:
        with pytest.raises(ValueError):
            responses(value, p)


@pytest.mark.parametrize("factor", [0, 1])
def test_available_response_upper_probability_boundary(factor: int) -> None:
    p, value = response_fixture()
    row = value["rows"][-1]
    row["factor"] = factor
    row["diagnostics"]["factor"] = factor
    if factor == 1:
        assert (
            responses(value, p)[
                (number(row["receiver_radius_m"]), number(row["fall_speed_m_s"]))
            ]["factor"]
            == 1
        )
    else:
        with pytest.raises(ValueError):
            responses(value, p)


def source_arrangement(repository: Path) -> tuple[dict[str, Any], Path]:
    """Complete the shared artificial archive with source-owned row evidence."""
    from .fixtures import saved_inputs, write_pin

    p, path = saved_inputs(repository)
    original = json.loads((repository / p["upstream_protocol"]["path"]).read_bytes())
    upstream = json.loads(
        Path(
            "reports/science/pollen-reconstruction/nordic-author-window-support/protocol.json"
        ).read_bytes()
    )
    original.update(cores=upstream["cores"], author_sources=upstream["author_sources"])
    p["upstream_protocol"] = write_pin(
        repository, p["upstream_protocol"]["path"], original
    )
    for index, declaration in enumerate(p["cores"]):
        key = declaration["key"]
        ledger = json.loads(
            (repository / p["qualified_products"][key]["path"]).read_bytes()
        )
        for sample in ledger["samples"]:
            matching = [
                w for w in ledger["windows"] if sample["sample_id"] in w["sample_ids"]
            ]
            sample.update(
                window=matching[0]["window"] if matching else None,
                panel_counts=[index + 2, 9 - index],
            )
        p["qualified_products"][key] = write_pin(
            repository, p["qualified_products"][key]["path"], ledger
        )
    params = json.loads(
        (repository / p["qualified_products"]["parameters"]["path"]).read_bytes()
    )
    params["source_pins"] = original["author_sources"]
    p["qualified_products"]["parameters"] = write_pin(
        repository, p["qualified_products"]["parameters"]["path"], params
    )
    imports = json.loads(
        (repository / p["scientific_sources"]["swedish_imports"]["path"]).read_bytes()
    )
    by_path = {pin["path"]: pin for pin in p["scientific_sources"].values()}
    for row in imports["module_origins"]:
        row["bytes"] = by_path[row["relative_path"]]["bytes"]
    p["scientific_sources"]["swedish_imports"] = write_pin(
        repository, p["scientific_sources"]["swedish_imports"]["path"], imports
    )
    result = json.loads(
        (repository / p["qualified_products"]["result"]["path"]).read_bytes()
    )
    result["protocol"] = p["upstream_protocol"]
    for key in result["products"]:
        pin = p["qualified_products"][key]
        result["products"][key] = {**pin, "path": Path(pin["path"]).name}
    p["qualified_products"]["result"] = write_pin(
        repository, p["qualified_products"]["result"]["path"], result
    )
    facts = json.loads(
        (repository / p["qualified_products"]["verification"]["path"]).read_bytes()
    )
    facts["producer_result_sha256"] = p["qualified_products"]["result"]["sha256"]
    p["qualified_products"]["verification"] = write_pin(
        repository, p["qualified_products"]["verification"]["path"], facts
    )
    path.write_text(json.dumps(p))
    return p, path


@pytest.mark.parametrize("factor", [0, 0.2, 1.1])
def test_refused_raw_response_diagnostic_is_never_promoted(factor: float) -> None:
    p, value = response_fixture()
    row = value["rows"][-1]
    row.update(
        status="refused",
        factor=None,
        estimated_absolute_error=None,
        diagnostics={"factor": factor, "estimated_absolute_error": 1e-9},
        refusal={
            "error_type": "ValidationError",
            "reason_code": "nonpositive_receiver_response"
            if factor == 0
            else "invalid_receiver_response",
            "message": "Controlled response domain refusal",
        },
    )
    if factor == 0.2:
        with pytest.raises(ValueError):
            responses(value, p)
    else:
        assert (
            responses(value, p)[
                (number(row["receiver_radius_m"]), number(row["fall_speed_m_s"]))
            ]["factor"]
            is None
        )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "source_bytes",
        "parameter",
        "country",
        "family",
        "pointer",
        "epoch",
        "rights",
    ],
)
def test_qualified_source_bindings_and_retained_origins_refuse_tampering(
    tmp_path: Path, damage: str | None
) -> None:
    from .verification import source_binding

    repository = tmp_path / "repository"
    repository.mkdir()
    p, _ = source_arrangement(repository)
    if damage == "source_bytes":
        target = repository / p["qualified_products"]["bokesjon"]["path"]
        target.write_bytes(target.read_bytes() + b" ")
    elif damage == "parameter":
        p["parameters"]["alpha_text"][0] = "5.106"
    elif damage == "country":
        p["cores"][0]["country"] = "DK"
    elif damage == "family":
        p["cores"][0]["physical_family"] = p["cores"][1]["physical_family"]
    elif damage == "pointer":
        p["retained_responses"][0]["factor_pointer"] = (
            "/cores/1/quadrature/0/factors/0/0"
        )
    elif damage == "epoch":
        p["upstream_source_commit"] = "f" * 40
    elif damage == "rights":
        p["cores"][0]["metadata_raw"]["DataRestricted/NotRestriced"] = "changed"
    if damage is None:
        value = source_binding(repository, p)
        assert len(value["cores"]) == 7
        assert sum(len(c["samples"]) for c in value["cores"].values()) == 542
        assert (
            sum(
                w["status"] == "supported"
                for c in value["cores"].values()
                for w in c["windows"]
            )
            == 41
        )
    else:
        with pytest.raises(ValueError):
            source_binding(repository, p)


def closed_predictions(
    p: dict[str, Any], bound: dict[str, Any], response: dict[str, Any]
) -> list[dict[str, Any]]:
    """Artificial wire rows use the independent algebra, never producer callbacks."""
    from hashlib import sha256

    from .verification import canonical, kernels

    table = responses(response, p)
    declarations = {c["key"]: c for c in p["cores"]}
    out = []
    families: dict[str, dict[str, Any]]
    for spec in plan(p):
        target = declarations[spec["target_core"]]
        window = spec["window_cal_bp"]
        index = p["windows"].index(window)
        ppe = [float(v) for v in p["parameters"]["alpha_text"]]
        tk, tids = kernels(target, p, table)
        target_row = {
            "core": target["key"],
            "site": target["identity"]["site_id"],
            "dataset": target["identity"]["dataset_id"],
            "collection_unit": target["identity"]["collection_unit_id"],
            "country": target["country"],
            "physical_family": target["physical_family"],
            "window_cal_bp": window,
            "axis": p["taxa"],
            "ppe": ppe,
            "kernels": tk,
            "response_ids": tids,
            "receiver_radius_m": target["radius_m"],
            "metadata_source_locator": target["metadata_source_locator"],
        }
        required, numeric, failures = [], [], []
        for r in spec["required"]:
            core = declarations[r["core"]]
            cell = bound["cores"][r["core"]]["windows"][index]
            k, ids = kernels(core, p, table)
            row = {
                "core": core["key"],
                "country": core["country"],
                "physical_family": core["physical_family"],
                "site": core["identity"]["site_id"],
                "dataset": core["identity"]["dataset_id"],
                "collection_unit": core["identity"]["collection_unit_id"],
                "window_cal_bp": window,
                "weight_exact": r["weight_exact"],
                "weight": float(r["weight_decimal"]),
                "window_status": cell["status"],
                "counts": cell["panel_counts"],
                "panel_N": cell["panel_N"],
                "sample_ids": cell["sample_ids"],
                "source_ref": {
                    "ledger": core["key"],
                    "window_index": index,
                    "window_sha256": sha256(canonical(cell)).hexdigest(),
                },
                "kernels": k,
                "response_ids": ids,
                "ppe": ppe,
                "inverse": {
                    "status": "not_run",
                    "cover": None,
                    "preclosure": None,
                    "refusal": None,
                },
            }
            required.append(row)
            numeric.append(
                {
                    "counts": cell["panel_counts"],
                    "coefficients": k,
                    "weight": r["weight_decimal"],
                }
            )
            if cell["status"] != "supported":
                failures.append(
                    {
                        "operation": "training_window",
                        "core": core["key"],
                        "reason_code": cell["status"],
                        "message": cell["status"],
                    }
                )
        if failures:
            families = {
                m: {
                    "status": "refused",
                    "pollen_fraction": None,
                    "cover": None,
                    "preclosure": None,
                    "reason": "required_training_source_unavailable",
                    "refusals": failures,
                }
                for m in ("physical_forward", "direct_panel_mean")
            }
        elif any(v is None for v in tk) or any(
            v is None for r in required for v in r["kernels"]
        ):
            refusals = [
                {
                    "operation": "source_response",
                    "core": r["core"],
                    "reason_code": "response_unavailable",
                    "message": "Required source response unavailable",
                }
                for r in required
                if any(v is None for v in r["kernels"])
            ]
            for r in required:
                own = [f for f in refusals if f["core"] == r["core"]]
                if own:
                    r["inverse"].update(status="refused", refusal=own[0])
            if any(v is None for v in tk):
                refusals.append(
                    {
                        "operation": "target_response",
                        "core": target["key"],
                        "reason_code": "response_unavailable",
                        "message": "Target response unavailable",
                    }
                )
            families = {
                "physical_forward": {
                    "status": "refused",
                    "pollen_fraction": None,
                    "cover": None,
                    "preclosure": None,
                    "reason": "response_unavailable",
                    "refusals": refusals,
                },
                "direct_panel_mean": {
                    "status": "predicted",
                    "pollen_fraction": direct_prediction(numeric),
                    "cover": None,
                    "preclosure": None,
                    "reason": None,
                    "refusals": [],
                },
            }
        else:
            computed = predict(numeric, tk, ppe)
            for r, inverse_row in zip(required, computed["individual"], strict=True):
                r["inverse"] = {"status": "computed", **inverse_row, "refusal": None}
            families = {
                "physical_forward": {
                    "status": "predicted",
                    "pollen_fraction": computed["physical"],
                    "cover": computed["weighted_cover"],
                    "preclosure": computed["forward_preclosure"],
                    "reason": None,
                    "refusals": [],
                },
                "direct_panel_mean": {
                    "status": "predicted",
                    "pollen_fraction": computed["direct"],
                    "cover": None,
                    "preclosure": None,
                    "reason": None,
                    "refusals": [],
                },
            }
        identity = {
            k: spec[k]
            for k in ("profile", "experiment", "target_core", "window_cal_bp", "scope")
        }
        identity.update(
            physical_family=target["physical_family"],
            country=target["country"],
            axis=p["taxa"],
        )
        cid = f"{spec['profile']}/{spec['experiment']}/{spec['target_core']}/{window[0]}-{window[1]}/{spec['scope']}"
        out.append(
            {
                "context_id": cid,
                "identity": identity,
                "target": target_row,
                "required_sources": required,
                "excluded_sources": spec["excluded"],
                "families": families,
            }
        )
    return out


def closed_scores(
    p: dict[str, Any], bound: dict[str, Any], contexts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    from hashlib import sha256

    from .verification import canonical

    out = []
    for context in contexts:
        identity = context["identity"]
        index = p["windows"].index(identity["window_cal_bp"])
        cell = bound["cores"][identity["target_core"]]["windows"][index]
        for method, family in context["families"].items():
            status = (
                "unavailable_target_observation"
                if cell["status"] != "supported"
                else (
                    "prediction_refused" if family["status"] == "refused" else "scored"
                )
            )
            out.append(
                {
                    "context_id": context["context_id"],
                    "identity": identity,
                    "method": method,
                    "status": status,
                    "reason": None
                    if status == "scored"
                    else cell["status"]
                    if status == "unavailable_target_observation"
                    else family["reason"],
                    "target_counts": cell["panel_counts"],
                    "target_panel_N": cell["panel_N"],
                    "target_sample_ids": cell["sample_ids"],
                    "target_owner_count": cell["member_count"],
                    "target_source_ref": {
                        "ledger": identity["target_core"],
                        "window_index": index,
                        "window_sha256": sha256(canonical(cell)).hexdigest(),
                    },
                    "pollen_fraction": family["pollen_fraction"],
                    "metrics": metrics(family["pollen_fraction"], cell["panel_counts"])
                    if status == "scored"
                    else None,
                }
            )
    return out


def closed_summary(rows: list[dict[str, Any]], p: dict[str, Any]) -> dict[str, Any]:
    from itertools import combinations

    from .population import METRICS, channel, channel_key

    def group(items: list[dict[str, Any]]) -> dict[str, Any]:
        targets = sorted({r["identity"]["target_core"] for r in items})
        per = []
        for target in targets:
            selected = [r for r in items if r["identity"]["target_core"] == target]
            predicted = sum(r["pollen_fraction"] is not None for r in selected)
            per.append(
                {
                    "target_core": target,
                    "physical_family": selected[0]["identity"]["physical_family"],
                    "requested": len(selected),
                    "predicted": predicted,
                    "refused": len(selected) - predicted,
                    "scored": sum(r["status"] == "scored" for r in selected),
                    "macro": loss_summary(selected)[0],
                }
            )
        predicted = sum(r["pollen_fraction"] is not None for r in items)
        macro, owner = loss_summary(items)
        return {
            "requested": len(items),
            "predicted": predicted,
            "refused": len(items) - predicted,
            "unavailable_targets": sum(
                r["status"] == "unavailable_target_observation" for r in items
            ),
            "scored": sum(r["status"] == "scored" for r in items),
            "target_count": len(targets),
            "per_target": per,
            "macro": macro,
            "native_owner_weighted": owner,
        }

    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        for country in (row["identity"]["country"], "ALL"):
            groups.setdefault((*channel_key(channel(row)), country), []).append(row)
    group_rows = [
        {
            **dict(
                zip(
                    ("profile", "experiment", "scope", "method", "country"),
                    key,
                    strict=True,
                )
            ),
            **group(items),
        }
        for key, items in groups.items()
    ]
    configurations = [
        ("swedish_scope_methods:" + q["id"], [q["id"]]) for q in p["profiles"]
    ]
    configurations += [
        ("density_sensitivity_swedish", [p["profiles"][i]["id"] for i in (0, 1)]),
        ("core_sensitivity_swedish", [p["profiles"][i]["id"] for i in (0, 2)]),
    ]
    matched = []
    for name, profiles in configurations:
        channels = [
            {
                "profile": q,
                "experiment": "swedish_training_scope",
                "scope": scope,
                "method": method,
            }
            for q in profiles
            for scope in ("swedish_only", "pooled_nordic")
            for method in ("physical_forward", "direct_panel_mean")
        ]
        tables = [
            {
                (r["identity"]["target_core"], *r["identity"]["window_cal_bp"]): r
                for r in rows
                if channel(r) == c
            }
            for c in channels
        ]
        requested = list(tables[0])
        common = [
            key
            for key in requested
            if all(t[key]["status"] == "scored" for t in tables)
        ]
        channel_rows = []
        for c, t in zip(channels, tables, strict=True):
            g = group([t[k] for k in common])
            channel_rows.append(
                {
                    "channel": c,
                    "physical_targets": g["target_count"],
                    "matched_windows": len(common),
                    "macro": g["macro"],
                    "native_owner_weighted": g["native_owner_weighted"],
                    "per_target": [
                        {
                            "target_core": r["target_core"],
                            "physical_family": r["physical_family"],
                            "matched_windows": r["scored"],
                            "macro": r["macro"],
                        }
                        for r in g["per_target"]
                    ],
                }
            )
        matched.append(
            {
                "comparison_id": name,
                "channels": channels,
                "requested_target_windows": 18,
                "matched_target_windows": len(common),
                "unmatched": [
                    {
                        "target_core": k[0],
                        "physical_family": tables[0][k]["identity"]["physical_family"],
                        "window_cal_bp": list(k[1:]),
                        "reason": "incomplete_common_support",
                    }
                    for k in requested
                    if k not in common
                ],
                "channels_summary": channel_rows,
                "pairwise": [
                    {
                        "first": a["channel"],
                        "second": b["channel"],
                        "mean_difference": None
                        if a["macro"] is None
                        else {m: a["macro"][m] - b["macro"][m] for m in METRICS},
                    }
                    for a, b in combinations(channel_rows, 2)
                ],
            }
        )
    return {
        "schema_version": "nordic-physical-summary.v1",
        "groups": group_rows,
        "matched": matched,
    }


def closed_arrangement(base: Path) -> tuple[Path, Path, Path, dict[str, Any]]:
    from hashlib import sha256

    from .verification import source_binding

    repository = base / "repository"
    repository.mkdir()
    p, protocol_path = source_arrangement(repository)
    bound = source_binding(repository, p)
    out = repository / "artifacts" / "study"
    out.mkdir(parents=True)
    _, response = response_fixture()
    for row, spec in zip(response["rows"][:9], p["retained_responses"], strict=True):
        row["source_ref"]["pin"] = p["scientific_sources"][spec["source"]]
    state = {"head": "a" * 40, "index_sha256": "b" * 64, "python_files": {}}

    def store(name: str, value: Any) -> dict[str, Any]:
        raw = (
            json.dumps(value, sort_keys=True, allow_nan=False, default=float) + "\n"
        ).encode()
        (out / name).write_bytes(raw)
        return {"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}

    pp = {
        "path": "protocol.json",
        "bytes": protocol_path.stat().st_size,
        "sha256": sha256(protocol_path.read_bytes()).hexdigest(),
    }
    pins = {"responses": store("responses.json", response)}
    contexts = closed_predictions(p, bound, response)
    pins["prediction_freeze"] = store(
        "prediction-freeze.json",
        {
            "schema_version": "nordic-physical-predictions.v1",
            "source_commit": state["head"],
            "protocol": pp,
            "response_file": pins["responses"],
            "contexts": contexts,
        },
    )
    # Interpret outcomes only after every artificial forecast is serialized.
    rows = closed_scores(p, bound, contexts)
    pins["scores"] = store(
        "scores.json",
        {
            "schema_version": "nordic-physical-scores.v1",
            "prediction_file": pins["prediction_freeze"],
            "rows": rows,
        },
    )
    pins["summary"] = store("summary.json", closed_summary(rows, p))
    store(
        "result.json",
        {
            "schema_version": "nordic-physical-transfer-result.v1",
            "status": "produced_awaiting_independent_verification",
            "source_commit": state["head"],
            "index_sha256": state["index_sha256"],
            "protocol": pp,
            "sourcepins": [
                p["upstream_protocol"],
                *p["qualified_products"].values(),
                *p["scientific_sources"].values(),
            ],
            "products": pins,
            "source_guards_passed": True,
            "resources": {
                "elapsed_seconds": 1.0,
                "peak_rss_bytes": 1024**2,
                "output_bytes": sum(pin["bytes"] for pin in pins.values()),
            },
            "scope": p["claim"],
            "previously_exposed_development": True,
            "uncertainty_evaluated": False,
            "scientific_or_field_admission": False,
        },
    )
    return repository, protocol_path, out, state


@pytest.mark.parametrize("foreign_refusal", [False, True])
def test_full_response_refusal_keeps_direct_and_every_common_support_slot(
    foreign_refusal: bool,
) -> None:
    from .fixtures import packet_fixture
    from .population import summaries
    from .verification import forecasts, score_population

    packet, p, response = packet_fixture()
    row = next(
        r
        for r in response["rows"]
        if r["origin"] == "current" and r["receiver_radius_m"] == 80
    )
    row.update(
        status="refused",
        factor=None,
        estimated_absolute_error=None,
        diagnostics=None,
        refusal={
            "error_type": "ValidationError",
            "reason_code": "numerical_error",
            "message": "Controlled unavailable response",
        },
    )
    bound = {"cores": packet["cores"]}
    contexts = closed_predictions(p, bound, response)
    if foreign_refusal:
        contexts[0]["families"]["physical_forward"]["refusals"][0]["core"] = "foreign"
        with pytest.raises(ValueError):
            forecasts({"contexts": contexts}, p, bound, responses(response, p))
    else:
        observed = forecasts({"contexts": contexts}, p, bound, responses(response, p))
        rows = closed_scores(p, bound, contexts)
        score_population(
            {
                "schema_version": "nordic-physical-scores.v1",
                "prediction_file": {},
                "rows": rows,
            },
            p,
            bound,
            observed,
        )
        summaries(closed_summary(rows, p), p, rows)
        assert len(rows) == 432 and any(
            r["status"] == "prediction_refused" for r in rows
        )
        swedish = [
            c
            for c in contexts
            if c["identity"]["experiment"] == "swedish_training_scope"
            and c["identity"]["profile"] == "equal_place_solsoe83"
        ]
        assert all(
            c["families"]["direct_panel_mean"]["status"] == "predicted" for c in swedish
        )
        assert all(
            c["families"]["physical_forward"]["status"] == "refused" for c in swedish
        )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "member_bytes",
        "extra",
        "held_count",
        "inverse",
        "score",
        "denominator",
        "epoch",
    ],
)
def test_closed_full_population_and_exclusive_readback_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str | None
) -> None:
    from hashlib import sha256

    from . import verification as audit

    repository, protocol_path, out, state = closed_arrangement(tmp_path)
    monkeypatch.setattr(audit, "code_state", lambda _: deepcopy(state))
    monkeypatch.setattr(audit, "committed_protocol", lambda *_: None)
    if damage == "member_bytes":
        path = out / "prediction-freeze.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif damage == "extra":
        (out / "foreign.json").write_text("{}")
    elif damage == "epoch":
        state["head"] = "c" * 40
    elif damage in {"held_count", "inverse", "score", "denominator"}:
        result = json.loads((out / "result.json").read_bytes())
        key = (
            "prediction_freeze"
            if damage in {"held_count", "inverse"}
            else "scores"
            if damage == "score"
            else "summary"
        )
        path = out / result["products"][key]["path"]
        value = json.loads(path.read_bytes())
        if damage == "held_count":
            value["contexts"][0]["target"]["counts"] = [1, 2]
        elif damage == "inverse":
            value["contexts"][0]["required_sources"][0]["inverse"]["cover"][0] += 0.01
        elif damage == "score":
            next(r for r in value["rows"] if r["status"] == "scored")["metrics"][
                "mae_fraction"
            ] += 0.01
        else:
            value["groups"][0]["native_owner_weighted"]["owner_denominator"] += 1
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        result["products"][key].update(bytes=len(raw), sha256=sha256(raw).hexdigest())
        if key == "prediction_freeze":
            score_path = out / "scores.json"
            scores = json.loads(score_path.read_bytes())
            scores["prediction_file"] = result["products"][key]
            score_raw = json.dumps(scores).encode()
            score_path.write_bytes(score_raw)
            result["products"]["scores"].update(
                bytes=len(score_raw), sha256=sha256(score_raw).hexdigest()
            )
        result["resources"]["output_bytes"] = sum(
            pin["bytes"] for pin in result["products"].values()
        )
        (out / "result.json").write_text(json.dumps(result))
    if damage is None:
        facts = audit.verify(repository, protocol_path, out)
        assert (
            facts["status"] == "verified"
            and facts["contexts_checked"] == 216
            and facts["method_slots_checked"] == 432
        )
    else:
        with pytest.raises(ValueError):
            audit.verify(repository, protocol_path, out)
