"""Generated analytical products retain private inputs and publish derived views."""

from importlib import import_module
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal

from .support import fixture


def api():
    return import_module("bijux_pollenomics.analysis.lra.source_cases.api")


def test_two_cases_are_order_invariant_and_reader_needs_no_original_inputs(
    tmp_path: Path,
):
    root = tmp_path / "inputs"
    _, value = fixture(root)
    cls = api().SourceCasePlan
    first = api().run_source_lra_cases(
        cls.from_dict(value), input_root=root, destination=tmp_path / "first"
    )
    value["cases"].reverse()
    second = api().run_source_lra_cases(
        cls.from_dict(value), input_root=root, destination=tmp_path / "second"
    )
    assert (
        first.manifest()["scientific_content_sha256"]
        == second.manifest()["scientific_content_sha256"]
    )
    manifest = first.manifest()
    assert manifest["source_inputs_embedded"] is False
    assert manifest["scientific_acceptance"] == "not_evaluated"
    assert len(manifest["cases"]) == 2
    assert all(row["status"] == "success" for row in manifest["cases"])
    assert {path.name for path in first.directory.iterdir()} == {"manifest.json"}
    original = root.rename(tmp_path / "unavailable")
    assert (
        api()
        .read_source_lra_cases(
            first.directory, expected_manifest_sha256=first.manifest_sha256
        )
        .manifest()
        == manifest
    )
    assert original.is_dir()


def test_invalid_law_refuses_before_executor_and_preserves_prior(
    tmp_path: Path, monkeypatch
):
    root = tmp_path / "inputs"
    _, value = fixture(root)
    target = tmp_path / "prior"
    target.mkdir()
    (target / "retained").write_bytes(b"prior complete release")
    (root / "law.json").write_bytes(b"changed")
    workflow = import_module("bijux_pollenomics.analysis.lra.source_cases.workflow")
    calls = []
    monkeypatch.setattr(workflow, "run_lra_request", lambda *a, **k: calls.append(True))
    with pytest.raises((LRARefusal, ValueError)):
        api().run_source_lra_cases(
            api().SourceCasePlan.from_dict(value), input_root=root, destination=target
        )
    assert not calls and (target / "retained").read_bytes() == b"prior complete release"


def test_all_numerical_failures_keep_the_entire_design(tmp_path: Path, monkeypatch):
    root = tmp_path / "inputs"
    _, value = fixture(root)
    workflow = import_module("bijux_pollenomics.analysis.lra.source_cases.workflow")

    def refuse_case(*args, **kwargs):
        raise LRARefusal("lra_numerical_refusal", "generated refusal")

    monkeypatch.setattr(workflow, "run_lra_request", refuse_case)
    result = api().run_source_lra_cases(
        api().SourceCasePlan.from_dict(value),
        input_root=root,
        destination=tmp_path / "derived",
    )
    assert len(result.manifest()["cases"]) == 2
    for summary in result.manifest()["summaries"].values():
        assert summary["successful_mass"] == {"numerator": 0, "denominator": 1}
        assert summary["failed_mass"] == {"numerator": 1, "denominator": 1}
        assert summary["mean"] is None and summary["population_covariance"] is None


@pytest.mark.parametrize("code", ["zero_positive_love_cover", "nonfinite_love_cover"])
def test_love_cover_refusal_preserves_partial_design_mass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: str
) -> None:
    root = tmp_path / "inputs"
    _, value = fixture(root)
    workflow = import_module("bijux_pollenomics.analysis.lra.source_cases.workflow")
    original = workflow.run_lra_request
    calls = 0

    def child(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise LRARefusal(code, "controlled LOVE cover refusal")
        return original(*args, **kwargs)

    monkeypatch.setattr(workflow, "run_lra_request", child)
    result = api().run_source_lra_cases(
        api().SourceCasePlan.from_dict(value),
        input_root=root,
        destination=tmp_path / "product",
    )
    manifest = (
        api()
        .read_source_lra_cases(
            result.directory, expected_manifest_sha256=result.manifest_sha256
        )
        .manifest()
    )
    assert [row["status"] for row in manifest["cases"]] == ["refused", "success"]
    assert manifest["cases"][0]["reason_code"] == code
    for summary in manifest["summaries"].values():
        assert summary["failed_mass"] == {"numerator": 3, "denominator": 4}
        assert summary["successful_mass"] == {"numerator": 1, "denominator": 4}
        assert summary["mean"] is None and summary["population_covariance"] is None


def test_one_atom_matches_existing_deterministic_child(tmp_path: Path):
    from bijux_pollenomics.analysis.lra.execution.service import run_lra_request
    from bijux_pollenomics.analysis.lra.source_cases.results import child_vectors

    from .support import store

    root = tmp_path / "inputs"
    _, value = fixture(root)
    value["cases"] = value["cases"][:1]
    law = json.loads((root / "law.json").read_bytes())
    law["masses"] = [{"case_id": "nominal", "numerator": 1, "denominator": 1}]
    value["design"]["law_ref"] = store(root, "law.json", law)
    request = json.loads((root / "nominal.json").read_bytes())
    child = run_lra_request(request, input_root=root, destination=tmp_path / "direct")
    expected = child_vectors(child.directory, request, max_bytes=64 * 1024 * 1024)
    result = api().run_source_lra_cases(
        api().SourceCasePlan.from_dict(value),
        input_root=root,
        destination=tmp_path / "derived",
    )
    row = result.manifest()["cases"][0]
    assert {key: row[key] for key in expected} == expected
    for kind in ("raw", "adjusted"):
        assert (
            result.manifest()["summaries"][kind]["mean"] == expected[kind + "_values"]
        )


def test_global_failure_keeps_private_full_law_and_prior(tmp_path: Path, monkeypatch):
    root = tmp_path / "inputs"
    _, value = fixture(root)
    target = tmp_path / "prior"
    target.mkdir()
    (target / "kept").write_bytes(b"complete prior")
    workflow = import_module("bijux_pollenomics.analysis.lra.source_cases.workflow")
    error = OSError("generated native failure")

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(workflow, "run_lra_request", fail)
    with pytest.raises(OSError) as caught:
        api().run_source_lra_cases(
            api().SourceCasePlan.from_dict(value), input_root=root, destination=target
        )
    assert caught.value is error
    assert (target / "kept").read_bytes() == b"complete prior"
    from bijux_pollenomics.core.filesystem.recovery_storage import (
        resolve_publication_workspace_parent,
    )

    recovery = resolve_publication_workspace_parent(
        target, namespace="lra-source-cases"
    )
    ledgers = list(recovery.glob("*/failure/failure-ledger.json"))
    assert len(ledgers) == 1
    ledger = json.loads(ledgers[0].read_bytes())
    assert {row["case_id"]: row["mass"] for row in ledger["cases"]} == {
        "nominal": "1/4",
        "comparison": "3/4",
    }
    assert ledger["summaries"]["raw"]["mean"] is None


def test_original_source_changed_during_child_refuses_publication(
    tmp_path: Path, monkeypatch
):
    root = tmp_path / "inputs"
    _, value = fixture(root)
    target = tmp_path / "prior"
    target.mkdir()
    (target / "kept").write_bytes(b"prior complete")
    workflow = import_module("bijux_pollenomics.analysis.lra.source_cases.workflow")
    original = workflow.run_lra_request

    def changed(*args, **kwargs):
        child = original(*args, **kwargs)
        (root / "base.json").write_bytes(
            b"changed source after actual generated model call"
        )
        return child

    monkeypatch.setattr(workflow, "run_lra_request", changed)
    with pytest.raises((LRARefusal, ValueError)):
        api().run_source_lra_cases(
            api().SourceCasePlan.from_dict(value), input_root=root, destination=target
        )
    assert (target / "kept").read_bytes() == b"prior complete"


def test_public_facade_owns_source_cases_and_preserves_synthetic_api():
    from bijux_pollenomics.analysis.lra import api as public
    from bijux_pollenomics.analysis.lra.uncertainty.api import (
        JointLRAPlan,
        run_joint_lra_ensemble,
    )

    assert public.SourceCasePlan is api().SourceCasePlan
    assert public.run_source_lra_cases is api().run_source_lra_cases
    assert public.JointLRAPlan is JointLRAPlan
    assert public.run_joint_lra_ensemble is run_joint_lra_ensemble
