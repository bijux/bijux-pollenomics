"""Bind the adjusted estimand to clipping without source rounding assumptions."""

from copy import deepcopy
import csv
from io import StringIO

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution.service import run_lra_request
from bijux_pollenomics.analysis.lra.source_cases import (
    contracts,
    reading,
    results,
    workflow,
)

from . import support


def _fixture_with_policy(root, monkeypatch, policy):
    original = support.request_fixture

    def fixed(root, operation):
        request = original(root, operation)
        request["local"]["samples"][0]["counts"] = [0, 100]
        request["configuration"]["love"]["analytical_cover_policy"] = policy
        return request

    monkeypatch.setattr(support, "request_fixture", fixed)
    return support.fixture(root)[1]


def test_source_raw_refuses_before_any_child(tmp_path, monkeypatch):
    root = tmp_path / "inputs"
    plan = _fixture_with_policy(root, monkeypatch, "source-raw")
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Incompatible policy reached an executor")

    monkeypatch.setattr(workflow, "run_lra_request", forbidden)
    with pytest.raises(LRARefusal):
        workflow.run_source_lra_cases(
            contracts.SourceCasePlan.from_dict(plan),
            input_root=root,
            destination=tmp_path / "derived",
        )
    assert not calls
    assert not (tmp_path / "derived").exists()


@pytest.fixture(scope="module")
def clipped_manifest(tmp_path_factory):
    root = tmp_path_factory.mktemp("generated-cover-policy")
    with pytest.MonkeyPatch.context() as patch:
        plan = _fixture_with_policy(root / "inputs", patch, "clip-and-renormalize")
        product = workflow.run_source_lra_cases(
            contracts.SourceCasePlan.from_dict(plan),
            input_root=root / "inputs",
            destination=root / "derived",
        )
    value = product.manifest()
    for row in value["cases"]:
        assert row["raw_values"][2] < 0
        assert row["adjusted_values"][2:] == pytest.approx([0, 1])
    return value


def _read_changed(tmp_path, value):
    value["summaries"] = results.design_summaries(value["cases"], weighted=True)
    value["scientific_content_sha256"] = reading.scientific_identity(value)
    raw = contracts.canonical(value)
    target = tmp_path / "altered-derived-contract"
    target.mkdir()
    (target / "manifest.json").write_bytes(raw)
    return reading.read_source_lra_cases(
        target, expected_manifest_sha256=contracts.digest(raw)
    )


@pytest.mark.parametrize("damage", ["local", "regional", "zero_surviving_mass"])
def test_rehashed_vectors_must_preserve_the_cover_relation(
    tmp_path, clipped_manifest, damage
):
    value = deepcopy(clipped_manifest)
    row = value["cases"][0]
    if damage == "local":
        row["adjusted_values"][2:] = [0.25, 0.75]
    elif damage == "regional":
        row["adjusted_values"][0] += 0.001
    else:
        row["raw_values"][2:] = [-1, 0]
    with pytest.raises(LRARefusal):
        _read_changed(tmp_path, value)


@pytest.mark.parametrize(
    "raw,adjusted",
    [
        ([1e308, 1e308], [0.5, 0.5]),
        ([1e308, -1e308], [1, 0]),
        ([5e-324, 5e-324], [0.5, 0.5]),
        ([-0.2, 1.2], [0, 1]),
        ([0.2, 0.8], [0.2 + 5e-13, 0.8 - 5e-13]),
    ],
)
def test_scaled_relation_accepts_extreme_raw_and_source_rounding(
    tmp_path, clipped_manifest, raw, adjusted
):
    value = deepcopy(clipped_manifest)
    # These are algebraic readback-contract examples, not engine output claims.
    for row in value["cases"]:
        row["raw_values"] = [0.33333, 0.66666, *raw]
        row["adjusted_values"] = [0.33333, 0.66666, *adjusted]
    assert _read_changed(tmp_path, value).manifest()["source_inputs_embedded"] is False


def test_legacy_source_raw_entrypoint_remains_supported(tmp_path, monkeypatch):
    root = tmp_path / "inputs"
    _fixture_with_policy(root, monkeypatch, "source-raw")
    import json

    request = json.loads((root / "nominal.json").read_bytes())
    child = run_lra_request(request, input_root=root, destination=tmp_path / "legacy")
    table = list(
        csv.DictReader(
            StringIO(
                (child.directory / "numerical/local_love/cover_mean.csv").read_text()
            )
        )
    )
    assert float(table[0][request["taxa"][0]]) < 0


def test_saved_reader_requires_no_optional_engine(tmp_path, clipped_manifest):
    from pathlib import Path
    import subprocess
    import sys

    product = _read_changed(tmp_path, deepcopy(clipped_manifest))
    source = Path(__file__).parents[7]
    program = """
import importlib.abc, pathlib, sys
source, target, checksum = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
class NoEngine(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "bijux_pollenomics_lra" or fullname.startswith("bijux_pollenomics_lra."):
            raise AssertionError("Readback attempted to import the optional engine")
sys.meta_path.insert(0, NoEngine())
sys.path.insert(0, str(source / "packages/bijux-pollenomics/src"))
def audit(event, args):
    if event in {"socket.connect", "socket.getaddrinfo"}:
        raise AssertionError("Generated readback forbids network")
    if event == "open" and isinstance(args[0], str):
        parts = pathlib.Path(args[0]).parts
        if any(p in {"data", "reports", "vendor", "reference", "-bijux-pollenomics-data", "-bijux-pollenomics-artifacts-to-keep", "zz-meta", "zz-meta-human"} for p in parts):
            raise AssertionError("Generated readback forbids retained source bodies")
sys.addaudithook(audit)
from bijux_pollenomics.analysis.lra.source_cases import reading
assert pathlib.Path(reading.__file__).is_relative_to(source / "packages/bijux-pollenomics/src")
assert reading.read_source_lra_cases(target, expected_manifest_sha256=checksum).manifest_sha256 == checksum
assert not any(name == "bijux_pollenomics_lra" or name.startswith("bijux_pollenomics_lra.") for name in sys.modules)
"""
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            program,
            str(source),
            str(product.directory),
            product.manifest_sha256,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
