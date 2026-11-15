"""Adjusted six-window population custody and matched development scores."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.draws import (
    CountOwner,
    nominal_draw_bank,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.inputs import (
    InputError,
    InputPacket,
    load_inputs,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.predictions import (
    FoldCase,
    LocalKernel,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.scoring import (
    joint_predictions,
    score_diagnostics,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.study import (
    _nominal,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.verification import (
    audit,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.verification.sources import (
    bind_sources,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.verification.summaries import (
    reference_summaries,
)

from .test_inputs import saved_inputs
from .test_verification import complete_packets


def test_all_adjusted_folds_bind_every_window_and_preserve_original_refusals(
    tmp_path: Path,
) -> None:
    protocol = saved_inputs(tmp_path, all_adjusted=True)
    packet = load_inputs(tmp_path, protocol)
    assert len(packet.cases) == 18
    assert len(packet.nominal_predictions) == 54
    assert len(packet.accounting["active_draw_owner_ids"]) == 24
    assert sum(row["status"] == "refused" for row in packet.dispositions) == 45
    assert sum(row["nominal_status"] == "refused" for row in packet.folds) == 15
    assert all(
        case.target_id
        not in {
            case.regional_owner_id,
            *(local.owner_id for local in case.local_owners),
        }
        for case in packet.cases
    )
    observation = bind_sources(tmp_path, {"protocol": protocol, **asdict(packet)})
    assert observation["active_fold_kernels_verified"] == 18
    assert observation["nominal_predictions_verified"] == 54


@pytest.mark.parametrize(
    "defect", ["missing_window", "raw_policy", "unknown_profile", "swapped_manifest"]
)
def test_adjusted_population_requires_exact_manifest_windows_and_cover_policy(
    tmp_path: Path, defect: str
) -> None:
    protocol = saved_inputs(tmp_path, all_adjusted=True)
    if defect == "missing_window":
        protocol["adjusted_prediction_products"].pop("cal-bp-5200-5700")
    elif defect == "raw_policy":
        protocol["analytical_cover_policy"] = "source-raw"
    elif defect == "unknown_profile":
        protocol["population_profile"] = "arbitrary-folds"
    else:
        protocol["adjusted_prediction_products"]["cal-bp-5200-5700"] = protocol[
            "adjusted_prediction_products"
        ]["cal-bp-2700-3200"]
    with pytest.raises(InputError):
        load_inputs(tmp_path, protocol)


def test_all_window_audit_preserves_shared_draws_and_checks_last_target() -> None:
    packets = complete_packets(all_adjusted=True)
    result = audit(*packets)
    assert result["draw_owners"] == 24
    assert result["nominal_predictions_verified"] == 54
    assert result["replicate_method_slots_verified"] == 55296
    assert result["retained_nominal_refusals"] == 45
    packets[2]["cases"][-1]["methods"]["training_mean"]["pollen"][-1] = [0.9, 0.1]
    with pytest.raises(ValueError):
        audit(*packets)


def test_nominal_producer_matches_all_fifty_four_closed_adjusted_predictions() -> None:
    source = complete_packets(all_adjusted=True)[0]
    owners = tuple(
        CountOwner(row["owner_id"], (row["counts"][0], row["counts"][1]))
        for row in source["owners"]
    )
    cases = tuple(
        FoldCase(
            **{
                **row,
                "local_owners": tuple(
                    LocalKernel(**local) for local in row["local_owners"]
                ),
            }
        )
        for row in source["cases"]
    )
    packet = InputPacket(
        owners,
        cases,
        tuple(source["folds"]),
        tuple(source["dispositions"]),
        tuple(source["nominal_predictions"]),
        source["accounting"],
        (),
    )
    result = _nominal(
        packet,
        nominal_draw_bank(owners),
        1e-12,
        analytical_cover_policy="clip-and-renormalize",
    )
    assert len(result) == 54
    assert len({row["case_id"] for row in result}) == 18
    assert all(row["pollen_fraction"] == [1.0, 0.0] for row in result)
    assert sum(row["status"] == "refused" for row in packet.dispositions) == 45


def test_eighteen_target_scores_use_matched_denominators_and_independent_replay() -> (
    None
):
    packet: dict[str, Any] = {"owners": [], "accounting": {"owner_lineage": {}}}
    cases: list[dict[str, Any]] = []
    for index in range(18):
        owner = f"owner-{index:02}"
        packet["owners"].append(
            {"owner_id": owner, "counts": [0, 1] if index == 17 else [1, 0]}
        )
        packet["accounting"]["owner_lineage"][owner] = {
            "raw": {"path": owner + ".json"}
        }
        cases.append(
            {
                "case_id": owner,
                "target_id": owner,
                "replicates": 2,
                "methods": {
                    method: {
                        "pollen": [[0.8, 0.2]] * 2,
                        "direct_pollen": [[0.5, 0.5]] * 2,
                        "valid_mask": [True, True],
                    }
                    for method in (
                        "training_mean",
                        "nearest_site",
                        "inverse_distance_squared",
                    )
                },
            }
        )
    scored = score_diagnostics(packet, {"cases": cases})
    joint = joint_predictions(cases)
    for method, values in scored["aggregate"].items():
        assert values["physical"]["conditional"]["mean"][0] == pytest.approx(7 / 30)
        assert values["direct_on_physical_defined"]["conditional"]["mean"][
            0
        ] == pytest.approx(0.5)
        assert len(joint[method]["physical"]["conditional"]["mean"]) == 36
    expected = reference_summaries(cases, scored["observed"], {})
    assert expected["score_diagnostics"]["aggregate"]["training_mean"]["physical"][
        "conditional"
    ]["mean"][0] == pytest.approx(7 / 30)
    for values in cases[-1]["methods"].values():
        values["pollen"][1] = [None, None]
        values["valid_mask"][1] = False
    incomplete = joint_predictions(cases)
    for values in incomplete.values():
        assert values["physical"]["defined_replicates"] == 1
        assert values["direct_all_replicates"]["defined_replicates"] == 2
        assert values["direct_on_physical_defined"]["defined_replicates"] == 1
