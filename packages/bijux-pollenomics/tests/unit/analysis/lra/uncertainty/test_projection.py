"""Independent endpoint, coupling and original-source preservation checks."""

from pathlib import Path

from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
from bijux_pollenomics.analysis.lra.uncertainty.admission import admit
from bijux_pollenomics.analysis.lra.uncertainty.contracts import JointLRAPlan
from bijux_pollenomics.analysis.lra.uncertainty.projection import projections

from .test_contracts import fixture


def test_coupling_preserves_source_and_deterministic_children(tmp_path: Path) -> None:
    base, p = fixture(tmp_path)
    a = admit(JointLRAPlan.from_dict(p), tmp_path)
    rows = projections(a)
    assert [r[0]["selected_samples"]["local"] for r in rows] == [
        ["local2"],
        ["local2"],
        ["local1"],
        ["local1"],
    ]
    for row, child, files in rows:
        assert child is not None
        for name, data in files.items():
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        valid = validate_request(child, input_root=tmp_path)
        assert valid.sha256 == row["child_request_sha256"]
        assert child["configuration"]["reveals"]["iterations"] == 1
        assert child["configuration"]["love"]["repeats"] == 1
        assert child["configuration"]["couple_regional_draws"] is True
        assert (
            child["local"]["samples"][0]["counts"]
            == child["regional"]["samples"][0]["counts"]
        )
    assert a.base() == base


def test_half_open_excludes_source_closed_upper_endpoint(tmp_path: Path) -> None:
    _, p = fixture(tmp_path)
    p["bins"][0].update(younger_bp=50, older_bp=150)
    rows = projections(admit(JointLRAPlan.from_dict(p), tmp_path))
    assert [r[0]["status"] for r in rows] == ["ready", "ready", "refused", "refused"]
    assert all(r[0]["reason_code"] == "missing_role_in_bin" for r in rows[2:])


def test_ambiguous_no_pooling_and_order(tmp_path: Path) -> None:
    _, p = fixture(tmp_path)
    p["bins"][0].update(younger_bp=50, older_bp=251)
    a = projections(admit(JointLRAPlan.from_dict(p), tmp_path))
    assert all(r[0]["reason_code"] == "ambiguous_role_in_bin" for r in a)
    p["realizations"].reverse()
    b = projections(admit(JointLRAPlan.from_dict(p), tmp_path))
    assert [x[0] for x in a] == [x[0] for x in b]
