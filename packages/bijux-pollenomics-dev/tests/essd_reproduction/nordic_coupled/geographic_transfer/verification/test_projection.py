"""Literal cached-event examples, independent of the projection producer."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.verification import (
    audit_candidate,
)

METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


def summary(rows: list[list[Any]], mask: list[bool]) -> dict[str, Any]:
    selected = [row for row, keep in zip(rows, mask, strict=True) if keep]
    n, total, dimension = len(selected), len(rows), len(rows[0])
    conditional: dict[str, Any] = {
        "status": "unavailable_no_defined_replicates",
        "mean": None,
        "covariance": None,
        "sd": None,
        "empirical_quantiles": None,
        "mean_mcse": None,
        "mean_mcse_status": "unavailable_fewer_than_two_defined",
    }
    if n:
        mean = [sum(row[index] for row in selected) / n for index in range(dimension)]
        sums = [
            [
                sum(
                    (row[first] - mean[first]) * (row[second] - mean[second])
                    for row in selected
                )
                for second in range(dimension)
            ]
            for first in range(dimension)
        ]
        quantiles: dict[str, list[float]] = {}
        for q in (0.025, 0.5, 0.975):
            position = (n - 1) * q
            a, b = math.floor(position), math.ceil(position)
            quantiles[str(q)] = []
            for index in range(dimension):
                values = sorted(row[index] for row in selected)
                quantiles[str(q)].append(
                    values[a] + (position - a) * (values[b] - values[a])
                )
        conditional.update(
            status="defined",
            mean=mean,
            covariance=[[value / n for value in row] for row in sums],
            sd=[math.sqrt(sums[index][index] / n) for index in range(dimension)],
            empirical_quantiles=quantiles,
            mean_mcse=[
                math.sqrt(sums[index][index] / (n * (n - 1)))
                for index in range(dimension)
            ]
            if n > 1
            else None,
            mean_mcse_status="estimated_iid_conditional_expectation"
            if n > 1
            else "unavailable_fewer_than_two_defined",
        )
    return {
        "total_replicates": total,
        "defined_replicates": n,
        "undefined_replicates": total - n,
        "undefined_mass": (total - n) / total,
        "unconditional_status": "defined" if n == total else "refused_undefined_mass",
        "conditional": conditional,
        "covariance_divisor": "defined_replicates",
        "quantile_method": "linear",
        "mcse_scope": "IID conditional working-law expectation, not exact finite-ensemble mean error or field uncertainty",
    }


def identity(candidate: dict[str, Any], scale: float) -> str:
    cached, nominal = candidate["cached_fit"], candidate["nominal"]
    value = {
        "profile": "geographic-heldplace-hellinger",
        "axis": ["Betula", "Ulmus"],
        "case": candidate["case"],
        "scientific_refs": candidate["scientific_refs"],
        "length_scale_km": scale,
        "nominal_inputs": {
            "local_selected_covers": [
                row[1] for row in nominal["local_covers_by_ring"]
            ],
            "regional_cover": nominal["regional_cover"],
            "ppe": nominal["ppe"],
        },
        "cached_inputs": {
            "local_selected_covers": [
                [local[1] for local in row] for row in cached["local_signed_cover"]
            ],
            "regional_cover": cached["regional_cover"],
            "ppe_samples": candidate["ppe_samples"],
            "source_valid_mask": cached["methods"][METHODS[0]]["valid_mask"],
            "regional_refusals": cached["regional_refusals"],
            "local_refusals": cached["local_refusals"],
            "method_refusals": {
                method: cached["methods"][method]["refusals"] for method in METHODS
            },
        },
    }
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def miniature(
    count: int = 4, *, mask: list[bool] | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_mask = (
        mask if mask is not None else [index % 4 != 1 for index in range(count)]
    )
    ppe = [[1.0, 1.0], [2.0, 1.0], [1.0, 2.0], [3.0, 2.0]]
    ppe = [ppe[index % 4] for index in range(count)]
    case = {
        "case_id": "2700-3200:solsoe",
        "target_id": "solsoe",
        "regional_owner_id": "krag",
        "local_owners": [
            {
                "owner_id": owner,
                "local_k": [[1.0, 1.0]] * 2,
                "regional_k": [[0.1, 0.1]] * 2,
            }
            for owner in ("boke", "bus")
        ],
        "regional_deposition": [1.0, 1.0],
        "forward_local_k": [[1.0, 1.0]] * 2,
        "forward_regional_k": [1.0, 1.0],
        "terrestrial_fraction": [1.0, 1.0],
        "distances_km": [10.0, 10.0],
        "selected_ring_index": 1,
    }
    allowed = {
        "case": case,
        "count_owners": [
            {
                "owner_id": owner,
                "counts": [2, 1],
                "stream_index": [0] * 8,
                "samples_sha256": "b" * 64,
            }
            for owner in ("krag", "boke", "bus")
        ],
        "ppe": {
            "seed": 20261027,
            "replicates": count,
            "means": [1.0, 1.0],
            "sds": [0.0, 0.0],
            "samples_sha256": hashlib.sha256(
                b"".join(struct.pack("<d", value) for row in ppe for value in row)
            ).hexdigest(),
        },
    }
    vectors = [
        [5 * row[0] / (5 * row[0] + row[1]), row[1] / (5 * row[0] + row[1])]
        for row in ppe
    ]
    physical = [
        vector if valid else [None, None]
        for vector, valid in zip(vectors, source_mask, strict=True)
    ]
    cached = {
        "schema_version": "krageholm-predictive-ensemble.case.v1",
        "case_id": case["case_id"],
        "target_id": "solsoe",
        "axis": ["Betula", "Ulmus"],
        "replicates": count,
        "allowed_inputs": allowed,
        "regional_cover": [[0.5, 0.5]] * count,
        "regional_refusals": [None] * count,
        "local_signed_cover": [
            [[[-0.2, 1.2], [1.0, 0.0]], [[0.5, 0.5], [1.0, 0.0]]] for _ in range(count)
        ],
        "local_ring_refusals": [[[None, None], [None, None]] for _ in range(count)],
        "local_refusals": [[None, None] for _ in range(count)],
        "methods": {
            method: {
                "valid_mask": list(source_mask),
                "refusals": [
                    None if valid else "forward_engine_refused" for valid in source_mask
                ],
                "pollen": physical,
                "direct_pollen": [[0.5, 0.5]] * count,
            }
            for method in METHODS
        },
    }
    nominal = {
        "local_covers_by_ring": [[[-0.2, 1.2], [1.0, 0.0]], [[0.5, 0.5], [1.0, 0.0]]],
        "regional_cover": [0.5, 0.5],
        "ppe": [1.0, 1.0],
        "reference_predictions": [
            {
                "case_id": case["case_id"],
                "method": method,
                "regional_cover": [0.5, 0.5],
                "vegetation_fraction": [1.0, 0.0],
                "pollen_fraction": [5 / 6, 1 / 6],
            }
            for method in METHODS
        ],
    }
    candidate = {
        "case": case,
        "cached_fit": cached,
        "ppe_samples": ppe,
        "nominal": nominal,
        "scientific_refs": {
            "allowed_inputs": allowed,
            "nominal_fits": [
                {
                    "owner_id": owner,
                    "native_manifest": {},
                    "request": {},
                    "cover_csv": {},
                    "regional_csv": {},
                }
                for owner in ("boke", "bus")
            ],
        },
    }
    refusals = [
        None
        if valid
        else {
            "kind": "inherited_source_undefined",
            "regional_refusal": None,
            "local_refusals": [None, None],
            "method_refusals": dict.fromkeys(METHODS, "forward_engine_refused"),
        }
        for valid in source_mask
    ]
    covers = [[1.0, 0.0] if valid else [None, None] for valid in source_mask]
    produced = {
        "schema_version": "geographic-hellinger-prediction.v1",
        "case_id": case["case_id"],
        "target_id": "solsoe",
        "axis": ["Betula", "Ulmus"],
        "replicates": count,
        "length_scale_km": 20.0,
        "selection_status": "unselected_fixed_sensitivity",
        "weights": {"boke": 0.5, "bus": 0.5},
        "scientific_input_sha256": identity(candidate, 20.0),
        "scientific_refs": candidate["scientific_refs"],
        "source_diagnostics_reference": {
            "case_id": case["case_id"],
            "arrays": [
                "regional_cover",
                "regional_refusals",
                "local_signed_cover",
                "local_ring_refusals",
                "local_refusals",
            ],
            "selected_ring_index": 1,
        },
        "nominal": {
            "status": "predicted",
            "cover": [1.0, 0.0],
            "pollen": [5 / 6, 1 / 6],
            "refusal": None,
        },
        "ensemble": {
            "cover": covers,
            "pollen": physical,
            "valid_mask": list(source_mask),
            "refusals": refusals,
            "source_valid_mask": list(source_mask),
            "source_defined_replicates": sum(source_mask),
            "inherited_undefined_replicates": count - sum(source_mask),
            "additional_refusals": 0,
        },
        "pollen_summary": summary(physical, source_mask),
        "cover_summary": summary(covers, source_mask),
    }
    return candidate, produced


def test_exact_two_taxon_forward_and_unselected_signed_ring_diagnostic() -> None:
    candidate, produced = miniature()
    facts = audit_candidate(candidate, produced)
    assert facts["defined_replicates"] == 3
    assert facts["inherited_undefined_replicates"] == 1
    assert produced["ensemble"]["pollen"][2] == [5 / 7, 2 / 7]
    assert (
        produced["pollen_summary"]["unconditional_status"] == "refused_undefined_mass"
    )


def test_all1024_immutable_row_ids_preserve164_inherited_refusals_without_forcing860() -> (
    None
):
    candidate, produced = miniature(1024, mask=[index >= 164 for index in range(1024)])
    assert audit_candidate(candidate, produced)["defined_replicates"] == 860
    other, other_output = miniature(7, mask=[True] * 7)
    assert audit_candidate(other, other_output)["defined_replicates"] == 7


@pytest.mark.parametrize(
    "defect",
    [
        "source_mask",
        "rescued_source",
        "replicate_order",
        "ppe_identity",
        "weights",
        "invented_support",
        "pollen",
        "nominal",
        "summary",
        "mcse",
        "global_parent",
        "target_owner",
        "selected_refusal",
        "scientific_identity",
    ],
)
def test_source_masks_dependencies_and_numerical_outputs_are_not_repaired(
    defect: str,
) -> None:
    candidate, produced = miniature()
    if defect == "source_mask":
        candidate["cached_fit"]["methods"][METHODS[1]]["valid_mask"][0] = False
    elif defect == "rescued_source":
        produced["ensemble"]["valid_mask"][1] = True
    elif defect == "replicate_order":
        produced["ensemble"]["pollen"] = list(reversed(produced["ensemble"]["pollen"]))
    elif defect == "ppe_identity":
        candidate["ppe_samples"][0] = [2.0, 1.0]
    elif defect == "weights":
        produced["weights"]["boke"] = 0.6
    elif defect == "invented_support":
        produced["nominal"]["cover"] = [1.0, 1e-20]
    elif defect == "pollen":
        produced["ensemble"]["pollen"][0] = [0.5, 0.5]
    elif defect == "nominal":
        candidate["nominal"]["reference_predictions"][0]["pollen_fraction"] = [0.5, 0.5]
    elif defect == "summary":
        produced["pollen_summary"]["undefined_replicates"] = 0
    elif defect == "mcse":
        produced["pollen_summary"]["conditional"]["mean_mcse"] = [0.0, 0.0]
    elif defect == "global_parent":
        candidate["scientific_refs"]["whole_bank_sha256"] = "a" * 64
    elif defect == "target_owner":
        candidate["case"]["local_owners"][0]["owner_id"] = "solsoe"
    elif defect == "selected_refusal":
        candidate["cached_fit"]["local_ring_refusals"][0][0][1] = (
            "local_engine_nonfinite"
        )
    else:
        produced["scientific_input_sha256"] = "a" * 64
    with pytest.raises(ValueError):
        audit_candidate(candidate, produced)


def test_ring0_never_becomes_a_selected_domain_gate_or_a_new_digest_dependency() -> (
    None
):
    candidate, produced = miniature()
    candidate["cached_fit"]["local_signed_cover"][0][0][0] = [None, None]
    candidate["cached_fit"]["local_ring_refusals"][0][0][0] = "local_engine_nonfinite"
    assert identity(candidate, 20.0) == produced["scientific_input_sha256"]
    assert audit_candidate(candidate, produced)["defined_replicates"] == 3


def test_additional_weight_refusal_never_overwrites_the_inherited_source_reason() -> (
    None
):
    candidate, produced = miniature()
    candidate["case"]["distances_km"] = [0.0, 1000.0]
    produced["scientific_input_sha256"] = identity(candidate, 20.0)
    reason = {
        "kind": "additional_method_refusal",
        "stage": "spatial_weights",
        "reason": "hellinger_weight_underflow",
        "detail": "Positive relative weight lost",
    }
    produced["weights"] = None
    produced["nominal"] = {
        "status": "refused",
        "cover": None,
        "pollen": None,
        "refusal": reason,
    }
    ensemble = produced["ensemble"]
    ensemble["cover"] = ensemble["pollen"] = [[None, None]] * 4
    ensemble["refusals"] = [
        reason if valid else old
        for valid, old in zip(
            ensemble["source_valid_mask"], ensemble["refusals"], strict=True
        )
    ]
    ensemble["valid_mask"], ensemble["additional_refusals"] = [False] * 4, 3
    produced["pollen_summary"] = produced["cover_summary"] = summary(
        [[None, None]] * 4, [False] * 4
    )
    facts = audit_candidate(candidate, produced)
    assert facts["additional_refusals"] == 3
    assert facts["refusal_kinds"] == {
        "additional_method_refusal": 3,
        "inherited_source_undefined": 1,
    }


def test_covariance_row_sums_and_single_row_mcse_do_not_claim_extra_observations() -> (
    None
):
    candidate, produced = miniature(1, mask=[True])
    assert produced["pollen_summary"]["conditional"]["mean_mcse"] is None
    assert audit_candidate(candidate, produced)["defined_replicates"] == 1
    candidate, produced = miniature()
    assert all(
        abs(sum(row)) < 1e-15
        for row in produced["pollen_summary"]["conditional"]["covariance"]
    )


def refuse_defined_rows(produced: dict[str, Any], reason: dict[str, Any]) -> None:
    produced["nominal"] = {
        "status": "refused",
        "cover": None,
        "pollen": None,
        "refusal": reason,
    }
    rows = produced["replicates"]
    ensemble = produced["ensemble"]
    ensemble["cover"] = ensemble["pollen"] = [[None, None]] * rows
    ensemble["refusals"] = [
        reason if valid else old
        for valid, old in zip(
            ensemble["source_valid_mask"], ensemble["refusals"], strict=True
        )
    ]
    ensemble["valid_mask"] = [False] * rows
    ensemble["additional_refusals"] = sum(ensemble["source_valid_mask"])
    produced["pollen_summary"] = produced["cover_summary"] = summary(
        [[None, None]] * rows, [False] * rows
    )


def test_positive_geometry_weight_can_still_refuse_a_supported_mean_component() -> None:
    candidate, produced = miniature()
    candidate["case"]["distances_km"] = [0.0, 20 * math.sqrt(800)]
    candidate["nominal"]["local_covers_by_ring"][1][1] = [0.0, 1.0]
    for row in candidate["cached_fit"]["local_signed_cover"]:
        row[1][1] = [0.0, 1.0]
    for row in candidate["nominal"]["reference_predictions"]:
        row["vegetation_fraction"] = (
            [0.5, 0.5] if row["method"] == "training_mean" else [1.0, 0.0]
        )
        row["pollen_fraction"] = (
            [0.5, 0.5] if row["method"] == "training_mean" else [5 / 6, 1 / 6]
        )
    relative = math.exp(-400)
    produced["weights"] = {"boke": 1 / (1 + relative), "bus": relative / (1 + relative)}
    produced["scientific_input_sha256"] = identity(candidate, 20.0)
    refuse_defined_rows(
        produced,
        {
            "kind": "additional_method_refusal",
            "stage": "spatial_mean",
            "reason": "hellinger_composition_underflow",
            "detail": "Supported component is below the output range",
        },
    )
    assert audit_candidate(candidate, produced)["additional_refusals"] == 3


def test_new_mean_forward_overflow_is_an_additional_refusal_after_old_nominal_gate() -> (
    None
):
    candidate, produced = miniature()
    candidate["case"]["forward_local_k"] = [[1e308, 1.0], [0.0, 0.0]]
    candidate["case"]["forward_regional_k"] = [0.0, 0.0]
    selected = [[0.8, 0.2], [0.9, 0.1]]
    for owner in range(2):
        candidate["nominal"]["local_covers_by_ring"][owner][1] = selected[owner]
        for row in candidate["cached_fit"]["local_signed_cover"]:
            row[owner][1] = selected[owner]
    candidate["nominal"]["ppe"] = [2.11, 1.0]
    candidate["ppe_samples"] = [[2.11, 1.0]] * 4
    ppe_ref = candidate["scientific_refs"]["allowed_inputs"]["ppe"]
    ppe_ref["means"] = [2.11, 1.0]
    ppe_ref["samples_sha256"] = hashlib.sha256(
        b"".join(
            struct.pack("<d", value)
            for row in candidate["ppe_samples"]
            for value in row
        )
    ).hexdigest()
    for row in candidate["nominal"]["reference_predictions"]:
        row["vegetation_fraction"], row["pollen_fraction"] = [0.85, 0.15], [1.0, 0.0]
    produced["scientific_input_sha256"] = identity(candidate, 20.0)
    refuse_defined_rows(
        produced,
        {
            "kind": "additional_method_refusal",
            "stage": "native_forward",
            "reason": "forward_engine_refused",
            "native_reason_code": "invalid_input",
            "detail": "New weighted mean gives unrepresentable total deposition",
        },
    )
    assert audit_candidate(candidate, produced)["additional_refusals"] == 3
