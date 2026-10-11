"""Source admission precedes numerical or outcome access."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.uncertainty.admission import admit, revalidate
from bijux_pollenomics.analysis.lra.uncertainty.contracts import JointLRAPlan

from .test_contracts import fixture, update_base


@pytest.mark.parametrize("value", [None, True, "1", 0, -1, 1.5, 10**400])
def test_max_ring_is_bounded_before_engine(tmp_path: Path, value: object) -> None:
    base, p = fixture(tmp_path)
    if value is None:
        del base["configuration"]["love"]["max_ring"]
    else:
        base["configuration"]["love"]["max_ring"] = value
    update_base(tmp_path, base, p)
    with pytest.raises(LRARefusal):
        admit(JointLRAPlan.from_dict(p), tmp_path)


@pytest.mark.parametrize(
    "kind",
    ["calibrated", "outside", "gap", "denominator", "missing_sample", "changed_source"],
)
def test_source_support_and_inventory(tmp_path: Path, kind: str) -> None:
    base, p = fixture(tmp_path)
    if kind == "calibrated":
        for role in ("regional", "local"):
            for s in base[role]["samples"]:
                s["age_type"] = "calibrated_bp"
    elif kind == "gap":
        base["regional"]["samples"][0]["age_support_bp"] = [[50, 60], [140, 150]]
    if kind in ("calibrated", "gap"):
        update_base(tmp_path, base, p)
    for row in p["realizations"]:
        if kind == "outside":
            row["ages_by_sample_id"]["regional1"] = 49
        elif kind == "gap":
            row["ages_by_sample_id"]["regional1"] = 100
        elif kind == "denominator":
            row["counts_by_sample_id"]["regional1"] = [1, 4]
        elif kind == "missing_sample":
            del row["counts_by_sample_id"]["regional1"]
    if kind == "changed_source":
        (tmp_path / "raw_snapshot.txt").write_text("changed")
    with pytest.raises(LRARefusal):
        admit(JointLRAPlan.from_dict(p), tmp_path)


def test_reread_detects_late_evidence_change(tmp_path: Path) -> None:
    _, p = fixture(tmp_path)
    a = admit(JointLRAPlan.from_dict(p), tmp_path)
    (tmp_path / "law.txt").write_text("late")
    with pytest.raises(LRARefusal, match="law.txt"):
        revalidate(a, tmp_path)
