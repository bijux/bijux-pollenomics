"""Source admission keeps pooled support and explicit design authority distinct."""

import json
from importlib import import_module
from pathlib import Path

import pytest
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal

from .support import fixture, store


def admit(root, plan, workspace):
    api = import_module("bijux_pollenomics.analysis.lra.source_cases.admission")
    from bijux_pollenomics.analysis.lra.source_cases.contracts import SourceCasePlan

    return api.admit_source_cases(
        SourceCasePlan.from_dict(plan), input_root=root, workspace=workspace
    )


def test_design_mass_does_not_supply_native_pollen_denominator(tmp_path: Path):
    root = tmp_path / "inputs"
    _, plan = fixture(root)
    with admit(root, plan, tmp_path / "private") as accepted:
        assert accepted.masses == {"comparison": "3/4", "nominal": "1/4"}
        assert all(
            row["native_full_pollen_N"] is None
            and row["excluded_native_pollen_N"] is None
            for row in accepted.coverage
        )
        assert {row["record_kind"] for row in accepted.coverage} == {
            "pooled_source_bin"
        }
        assert (
            accepted.requests["nominal"].payload()["regional"]["samples"][0][
                "sample_id"
            ]
            == "pooled-regional-bin"
        )


@pytest.mark.parametrize("damage", ["counts", "stationarity", "law", "alias", "bytes"])
def test_admission_refuses_source_or_support_changes(tmp_path: Path, damage: str):
    root = tmp_path / "inputs"
    _, plan = fixture(root)
    case = plan["cases"][0]
    if damage in {"counts", "stationarity"}:
        request = json.loads((root / case["request_ref"]["path"]).read_bytes())
        if damage == "counts":
            request["local"]["samples"][0]["counts"] = [71, 29]
        else:
            request["temporal_matching"]["bins"][0]["younger_bp"] = 5401
        case["request_ref"] = store(root, case["request_ref"]["path"], request)
    elif damage == "law":
        law = json.loads((root / "law.json").read_bytes())
        law["masses"][0]["numerator"] = 2
        plan["design"]["law_ref"] = store(root, "law.json", law)
    elif damage == "alias":
        original = root / "base.json"
        original.rename(root / "hidden.json")
        original.symlink_to("hidden.json")
    else:
        (root / "base.json").write_bytes(b"changed")
    with pytest.raises((LRARefusal, ValueError)):
        with admit(root, plan, tmp_path / "private"):
            pass


def test_source_replacement_is_detected_after_admission(tmp_path: Path):
    root = tmp_path / "inputs"
    _, plan = fixture(root)
    with pytest.raises((LRARefusal, ValueError)):
        with admit(root, plan, tmp_path / "private") as accepted:
            (root / "base.json").write_bytes(b"changed")
            accepted.check()


@pytest.mark.parametrize("budget", [8, 31])
def test_covariance_bound_covers_both_full_joint_estimands(tmp_path: Path, budget: int):
    root = tmp_path / "inputs"
    request, plan = fixture(root)
    dimension = len(request["taxa"]) * (
        1 + request["configuration"]["love"]["max_ring"]
    )
    assert 2 * dimension * dimension == 32
    plan["limits"]["max_covariance_cells"] = budget
    with pytest.raises(LRARefusal):
        with admit(root, plan, tmp_path / "private"):
            pass
