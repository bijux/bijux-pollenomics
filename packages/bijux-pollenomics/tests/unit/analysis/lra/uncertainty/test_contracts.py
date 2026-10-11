"""Strict declaration and immutable exact-mass boundaries."""

from copy import deepcopy
from importlib.util import find_spec
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.uncertainty.contracts import (
    JointLRAPlan,
    canonical,
    digest,
)

from ..support import request_fixture

requires_engine = pytest.mark.skipif(
    find_spec("bijux_pollenomics_lra") is None,
    reason="Actual optional installed LRA engine required",
)


def fixture(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=True)
    base = request_fixture(root, "series")
    base["temporal_matching"]["bins"] = [
        {"bin_id": "source", "younger_bp": 50, "older_bp": 250}
    ]
    for role in ("regional", "local"):
        original = base[role]["samples"][0]
        base[role]["samples"] = [
            {
                **original,
                "sample_id": role + str(i),
                "bin_id": "source",
                "coordinate": i,
                "counts": counts,
                "age_support_bp": support,
            }
            for i, counts, support in (
                (1, [1, 3], [[50, 150]]),
                (2, [3, 1], [[150, 250]]),
            )
        ]
    for p in base["parameters"]:
        p.update(ppe=1, fallspeed_m_s=0.05)
    base["configuration"]["reveals"].update(iterations=1)
    base["configuration"]["love"].update(repeats=1)
    draws = []
    for shift, ages in enumerate(((50, 150), (150, 250))):
        for ppe in (1, 3):
            draws.append(
                {
                    "draw_id": f"d{shift}-{ppe}",
                    "mass": {"numerator": 1, "denominator": 4},
                    "ppe_realization_id": f"ppe{ppe}",
                    "ppe_by_taxon": {"Alnus": ppe, "Betula": 1},
                    "chronology_realization_id": f"core{shift}",
                    "ages_by_sample_id": {
                        role + str(i): age
                        for role in ("regional", "local")
                        for i, age in enumerate(ages, 1)
                    },
                    "count_realization_id": "counts",
                    "counts_by_sample_id": {
                        s["sample_id"]: s["counts"]
                        for role in ("regional", "local")
                        for s in base[role]["samples"]
                    },
                }
            )
    (root / "base.json").write_bytes(canonical(base))
    (root / "law.txt").write_text(
        "Explicit synthetic finite law; source and scientific authenticity unverified.\n"
    )
    plan = {
        "schema_version": "lra-joint-realizations.v1",
        "profile": "synthetic-explicit-joint-analytical-v1",
        "purpose": "exploratory",
        "data_kind": "synthetic",
        "base_request_ref": {
            "path": "base.json",
            "sha256": digest((root / "base.json").read_bytes()),
        },
        "law_evidence_ref": {
            "path": "law.txt",
            "sha256": digest((root / "law.txt").read_bytes()),
        },
        "bins": [
            {
                "bin_id": "target",
                "younger_bp": 100,
                "older_bp": 200,
                "membership": "younger_closed_older_open",
            }
        ],
        "realizations": draws,
        "limits": {
            "max_realizations": 64,
            "max_child_runs": 512,
            "max_draw_cells": 1000000,
            "max_covariance_cells": 1000000,
        },
    }
    return base, plan


def update_base(root: Path, base: dict[str, Any], plan: dict[str, Any]) -> None:
    (root / "base.json").write_bytes(canonical(base))
    plan["base_request_ref"]["sha256"] = digest((root / "base.json").read_bytes())


@pytest.mark.parametrize("value", [None, 1, [], {}, True])
def test_constructor_nonstring(value: Any) -> None:
    with pytest.raises(LRARefusal):
        JointLRAPlan(value)


@pytest.mark.parametrize(
    "kind",
    [
        "bool_mass",
        "zero_mass",
        "sum",
        "float_count",
        "negative_ppe",
        "infinite_age",
        "unsafe_age",
        "same_component",
        "duplicate",
        "overlap",
        "empty",
        "limits",
        "empirical",
    ],
)
def test_malformed_plan(tmp_path: Path, kind: str) -> None:
    _, p = fixture(tmp_path)
    row = p["realizations"][0]
    if kind == "bool_mass":
        row["mass"]["numerator"] = True
    elif kind == "zero_mass":
        row["mass"]["numerator"] = 0
    elif kind == "sum":
        row["mass"]["denominator"] = 5
    elif kind == "float_count":
        row["counts_by_sample_id"]["local1"] = [1.0, 3]
    elif kind == "negative_ppe":
        row["ppe_by_taxon"]["Alnus"] = -1
    elif kind == "infinite_age":
        row["ages_by_sample_id"]["local1"] = float("inf")
    elif kind == "unsafe_age":
        row["ages_by_sample_id"]["local1"] = 10**400
    elif kind == "same_component":
        p["realizations"][1]["ppe_realization_id"] = row["ppe_realization_id"]
    elif kind == "duplicate":
        p["realizations"][1]["draw_id"] = row["draw_id"]
    elif kind == "overlap":
        p["bins"].append({**p["bins"][0], "bin_id": "other"})
    elif kind == "empty":
        p["realizations"] = []
    elif kind == "limits":
        p["limits"]["max_child_runs"] = 1
    else:
        p["data_kind"] = "empirical"
    with pytest.raises(LRARefusal):
        JointLRAPlan.from_dict(p)


def test_plan_owns_bytes(tmp_path: Path) -> None:
    _, p = fixture(tmp_path)
    plan = JointLRAPlan.from_dict(p)
    before = plan.sha256
    p["realizations"].clear()
    copy = plan.payload()
    copy["realizations"].clear()
    assert len(plan.payload()["realizations"]) == 4 and plan.sha256 == before
    other = deepcopy(plan.payload())
    other["realizations"].reverse()
    assert JointLRAPlan.from_dict(other).sha256 != before
