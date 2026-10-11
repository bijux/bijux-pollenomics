"""Public child execution, global failures and complete interruption accounting."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution.service import run_lra_request
from bijux_pollenomics.analysis.lra.uncertainty import workflow
from bijux_pollenomics.analysis.lra.uncertainty.api import (
    JointLRAPlan,
    run_joint_lra_ensemble,
)

from .test_contracts import fixture, requires_engine, update_base


@pytest.mark.parametrize("where", ["input", "output"])
def test_cache_cannot_mutate_source_or_output(tmp_path: Path, where: str) -> None:
    source = tmp_path / "source"
    _, p = fixture(source)
    target = tmp_path / "product"
    cache = (source if where == "input" else target) / "cache"
    with pytest.raises(LRARefusal, match="disjoint"):
        run_joint_lra_ensemble(
            JointLRAPlan.from_dict(p),
            input_root=source,
            destination=target,
            cache_directory=cache,
        )
    assert not cache.exists() and not target.exists()


@requires_engine
def test_invalid_original_configuration_not_overwritten(tmp_path: Path) -> None:
    source = tmp_path / "source"
    base, p = fixture(source)
    base["configuration"]["reveals"]["iterations"] = -1
    update_base(source, base, p)
    with pytest.raises(LRARefusal) as caught:
        run_joint_lra_ensemble(
            JointLRAPlan.from_dict(p),
            input_root=source,
            destination=tmp_path / "product",
        )
    assert caught.value.reason_code == "invalid_engine_configuration"
    assert not (tmp_path / "product").exists()


@pytest.mark.parametrize(
    "code",
    [
        "lra_extension_missing",
        "lra_output_busy",
        "lra_code_changed_during_run",
        "evidence_hash_mismatch",
    ],
)
@requires_engine
def test_infrastructure_failure_is_global(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: str
) -> None:
    source = tmp_path / "source"
    _, p = fixture(source)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise LRARefusal(code, "controlled infrastructure refusal")

    monkeypatch.setattr(workflow, "run_lra_request", fail)
    with pytest.raises(LRARefusal) as caught:
        run_joint_lra_ensemble(
            JointLRAPlan.from_dict(p),
            input_root=source,
            destination=tmp_path / "product",
        )
    assert caught.value.reason_code == code and not (tmp_path / "product").exists()


@requires_engine
def test_numerical_diagnostic_and_mass_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    _, p = fixture(source)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise LRARefusal(
            "no_valid_local_rings",
            "controlled numerical refusal",
            diagnostics={"finite_rings": 0},
        )

    monkeypatch.setattr(workflow, "run_lra_request", fail)
    result = run_joint_lra_ensemble(
        JointLRAPlan.from_dict(p), input_root=source, destination=tmp_path / "product"
    )
    m = result.manifest()
    assert m["denominators"]["refused_draw_bins"] == 4 and m["status"] == "incomplete"
    assert m["rows"][0]["error"]["diagnostics"] == {"finite_rings": 0}
    assert m["summaries"]["target"]["failed_mass"] == {"numerator": 1, "denominator": 1}
    assert m["summaries"]["target"]["mean"] is None


@requires_engine
def test_interrupted_partial_staging_not_in_product(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    _, p = fixture(source)

    def stop(*args: Any, **kwargs: Any) -> Any:
        path = kwargs["destination"]
        path.parent.mkdir(parents=True, exist_ok=True)
        (path.parent / "pending.txt").write_text("partial child evidence")
        raise KeyboardInterrupt

    monkeypatch.setattr(workflow, "run_lra_request", stop)
    result = run_joint_lra_ensemble(
        JointLRAPlan.from_dict(p), input_root=source, destination=tmp_path / "product"
    )
    m = result.manifest()
    assert m["interrupted"] is True and m["denominators"]["not_run_draw_bins"] == 4
    assert not any("pending" in name for name in m["files"])
    assert len(list(tmp_path.glob(".product.joint-attempts-*/pending.txt"))) == 1


@requires_engine
def test_actual_cold_warm_coupling_and_null_sd(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _, p = fixture(source)
    plan = JointLRAPlan.from_dict(p)
    cold = run_joint_lra_ensemble(
        plan,
        input_root=source,
        destination=tmp_path / "cold",
        cache_directory=tmp_path / "cache",
    )
    warm = run_joint_lra_ensemble(
        plan,
        input_root=source,
        destination=tmp_path / "warm",
        cache_directory=tmp_path / "cache",
    )
    a, b = cold.manifest(), warm.manifest()
    assert a["scientific_content_sha256"] == b["scientific_content_sha256"]
    assert a["denominators"]["successful_draw_bins"] == 4
    summary = a["summaries"]["target"]
    assert summary["mean"][0] == pytest.approx(2 / 5, abs=1e-12)
    assert summary["mean"][2] == pytest.approx(2 / 5, abs=1e-12)
    assert summary["population_covariance"][0][2] == pytest.approx(49 / 800, abs=1e-12)
    for row in a["rows"]:
        assert row["values"][0] == pytest.approx(row["values"][2], abs=1e-12)
        sd = (
            cold.directory / row["child"] / "numerical/local_love/cover_sd.csv"
        ).read_text()
        assert ",," in sd


@pytest.mark.parametrize("kind", ["missing_engine", "source_changed", "code_changed"])
@requires_engine
def test_global_preflight_and_postflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    source = tmp_path / "source"
    _, p = fixture(source)

    def missing() -> Any:
        raise LRARefusal("lra_extension_missing", "controlled absence")

    def child(*args: Any, **kwargs: Any) -> Any:
        if kind == "source_changed":
            (source / "raw_snapshot.txt").write_text("changed after admission")
        raise LRARefusal("no_valid_local_rings", "numerical refusal")

    def changed(*args: Any, **kwargs: Any) -> Any:
        raise LRARefusal("lra_code_changed_during_run", "controlled byte change")

    monkeypatch.setattr(workflow, "run_lra_request", child)
    if kind == "missing_engine":
        monkeypatch.setattr(workflow, "load_engine", missing)
    if kind == "code_changed":
        monkeypatch.setattr(workflow, "verify_code_identity", changed)
    with pytest.raises(LRARefusal) as caught:
        run_joint_lra_ensemble(
            JointLRAPlan.from_dict(p),
            input_root=source,
            destination=tmp_path / "product",
        )
    assert caught.value.reason_code in {
        "lra_extension_missing",
        "joint_source_changed",
        "evidence_digest_mismatch",
        "lra_code_changed_during_run",
    }
    assert not (tmp_path / "product").exists()


@requires_engine
def test_signal_after_child_publication_retains_completed_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    _, p = fixture(source)
    original = run_lra_request

    def published(*args: Any, **kwargs: Any) -> Any:
        original(*args, **kwargs)
        raise KeyboardInterrupt

    monkeypatch.setattr(workflow, "run_lra_request", published)
    result = run_joint_lra_ensemble(
        JointLRAPlan.from_dict(p), input_root=source, destination=tmp_path / "product"
    )
    m = result.manifest()
    assert m["interrupted"] is True
    assert m["denominators"] == {
        "requested_draw_bins": 4,
        "successful_draw_bins": 1,
        "refused_draw_bins": 0,
        "not_run_draw_bins": 3,
    }
    assert m["summaries"]["target"]["mean"] is None
