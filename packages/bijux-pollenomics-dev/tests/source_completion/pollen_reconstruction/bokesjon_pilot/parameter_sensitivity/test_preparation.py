"""Generated retained requests test a reusable nominal comparison connection."""

from copy import deepcopy
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.source_cases.admission import admit_source_cases
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.basin_sensitivity.inputs import (
    BaselineInputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.parameter_sensitivity import (
    preparation,
)

from .test_normalization import bind as bind_fixture
from .test_normalization import fixture as normalization_fixture


def generated_inputs(tmp_path):
    """Construct evidence-labelled source contracts without empirical source access."""
    repository = next(p for p in Path(__file__).parents if (p / "uv.lock").is_file())
    path = repository / "packages/bijux-pollenomics/tests/unit/analysis/lra/support.py"
    spec = spec_from_file_location("generated_host_contract_support", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / "original"
    root.mkdir()
    request = module.request_fixture(root, "lra")
    request["data_kind"] = "source_observations"
    request["taxa"] = ["Betula", "Ulmus"]
    request["parameters"] = normalization_fixture()[0]["parameters"]
    request["versions"] = dict.fromkeys(
        request["versions"], "generated contract, not empirical source"
    )
    parameter = next(r for r in request["evidence"] if r["role"] == "parameters")
    raw = json.dumps(
        {"role": "parameters", "parameters": request["parameters"]}
    ).encode()
    (root / parameter["path"]).write_bytes(raw)
    parameter["sha256"] = sha256(raw).hexdigest()
    for role in ["regional", "local"]:
        request[role]["samples"][0]["sample_id"] = "generated-pooled-" + role
    evidence = {r["path"]: (root / r["path"]).read_bytes() for r in request["evidence"]}
    return BaselineInputs(json.dumps(request).encode(), evidence, root, (), b"{}")


def arguments(tmp_path, monkeypatch):
    inputs = generated_inputs(tmp_path)
    binding = bind_fixture(normalization_fixture())
    monkeypatch.setattr(
        preparation.normalization, "bind", lambda *a, **k: deepcopy(binding)
    )
    selected = {
        "taxon": "Betula",
        "taxonomic_level": "genus",
        "region": "Europe",
        "source_workbook": "originals/synthesized-rpp.xlsx",
        "source_sheet": "Worksheet 1",
        "source_row": "6",
        "rpp_cell": "G6",
        "rpp_sd_cell": "H6",
        "rpp": "4.94",
        "nominal_rpp_available": True,
    }
    reference = {
        "synthesized_rows": [
            selected,
            {"taxon": "Ulmus", "region": "Europe", "nominal_rpp_available": False},
        ]
    }
    return inputs, reference


def test_prepared_plan_reaches_existing_source_admission(tmp_path, monkeypatch):
    inputs, reference = arguments(tmp_path, monkeypatch)
    original = inputs.request_bytes, deepcopy(inputs.evidence)
    prepared = preparation.prepare(inputs, reference, buffers={}, scope={})
    target = tmp_path / "case-inputs"
    prepared.materialize(target)
    assert prepared.plan.payload()["design"] == {"kind": "unweighted_sensitivity"}
    with admit_source_cases(
        prepared.plan, input_root=target, workspace=tmp_path / "private"
    ) as admitted:
        assert admitted.masses is None
        baseline = admitted.requests["landclim-nominal-baseline"].payload()
        changed = admitted.requests["europe-betula-nominal"].payload()
        assert baseline["parameters"] == inputs.request["parameters"]
        assert changed["parameters"][0]["ppe"] == 4.94
        assert changed["parameters"][0]["ppe_sd"] == baseline["parameters"][0]["ppe_sd"]
        assert changed["parameters"][1] == baseline["parameters"][1]
        for key in [
            "regional",
            "local",
            "rings",
            "configuration",
            "temporal_matching",
            "exclusions",
        ]:
            assert changed[key] == baseline[key] == inputs.request[key]
        assert all(r["native_full_pollen_N"] is None for r in admitted.coverage)
    assert original == (inputs.request_bytes, inputs.evidence)


@pytest.mark.parametrize(
    "damage",
    [
        "missing_ulmus",
        "filled_ulmus",
        "duplicate_betula",
        "wrong_cell",
        "wrong_nominal",
    ],
)
def test_parameter_selection_refuses_silent_repairs(tmp_path, monkeypatch, damage):
    inputs, reference = arguments(tmp_path, monkeypatch)
    rows = reference["synthesized_rows"]
    if damage == "missing_ulmus":
        rows.pop()
    elif damage == "filled_ulmus":
        rows[1]["nominal_rpp_available"] = True
    elif damage == "duplicate_betula":
        rows.append(deepcopy(rows[0]))
    elif damage == "wrong_cell":
        rows[0]["rpp_cell"] = "G7"
    else:
        rows[0]["rpp"] = "4.95"
    with pytest.raises(ValueError):
        preparation.prepare(inputs, reference, buffers={}, scope={})


def test_source_evidence_mutation_and_existing_destination_refuse(
    tmp_path, monkeypatch
):
    inputs, reference = arguments(tmp_path, monkeypatch)
    prepared = preparation.prepare(inputs, reference, buffers={}, scope={})
    target = tmp_path / "occupied"
    target.mkdir()
    (target / "foreign.txt").write_text("PRESERVE")
    with pytest.raises((ValueError, FileExistsError)):
        prepared.materialize(target)
    assert (target / "foreign.txt").read_text() == "PRESERVE"
    inputs.evidence[next(iter(inputs.evidence))] = b"changed source"
    with pytest.raises(ValueError):
        preparation.prepare(inputs, reference, buffers={}, scope={})
