"""Generated public-constructor controls, without a model or scientific source read."""

from copy import deepcopy
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from types import ModuleType
from typing import Any, TypedDict, cast

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.basin_sensitivity.inputs import (
    BaselineInputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.parameter_sensitivity import (
    preparation,
)

SOURCE = next(p for p in Path(__file__).parents if (p / "uv.lock").is_file())


class CapturedContext(TypedDict, total=False):
    """The exact two heterogeneous containers captured by real normalization."""

    buffers: dict[str, bytes]
    scope: dict[str, Any]


def load(name: str, path: str) -> ModuleType:
    spec = spec_from_file_location(name, SOURCE / path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generated(
    tmp_path: Path,
) -> tuple[BaselineInputs, dict[str, Any], dict[str, bytes], dict[str, Any]]:
    fixture = load(
        "generated_normalization_fixture",
        "packages/bijux-pollenomics-dev/tests/source_completion/pollen_reconstruction/bokesjon_pilot/parameter_sensitivity/test_normalization.py",
    )
    parts = fixture.fixture()
    capture: CapturedContext = {}

    def retain(
        scope: dict[str, Any], buffers: dict[str, bytes], packet: bytes
    ) -> bytes:
        capture.update({"scope": scope, "buffers": buffers})
        return packet

    fixture.bind(parts, retain)  # Real normalization, not a patched product seam.
    host = load(
        "generated_host_fixture",
        "packages/bijux-pollenomics/tests/unit/analysis/lra/support.py",
    )
    root = tmp_path / "generated-source"
    root.mkdir()
    request = host.request_fixture(root, "lra")
    request["data_kind"] = "source_observations"
    request["taxa"] = ["Betula", "Ulmus"]
    request["parameters"] = deepcopy(parts[0]["parameters"])
    request["versions"] = dict.fromkeys(
        request["versions"], "generated contract; no empirical source"
    )
    for role in ["regional", "local"]:
        request[role]["samples"][0]["sample_id"] = "generated-pooled-" + role
    parameter = next(x for x in request["evidence"] if x["role"] == "parameters")
    body = json.dumps(
        {"role": "parameters", "parameters": request["parameters"]}
    ).encode()
    (root / parameter["path"]).write_bytes(body)
    parameter["sha256"] = sha256(body).hexdigest()
    evidence = {x["path"]: (root / x["path"]).read_bytes() for x in request["evidence"]}
    inputs = BaselineInputs(json.dumps(request).encode(), evidence, root, (), b"{}")
    reference = deepcopy(parts[2])
    reference["synthesized_rows"] += [
        {
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
        },
        {"taxon": "Ulmus", "region": "Europe", "nominal_rpp_available": False},
    ]
    return inputs, reference, capture["buffers"], capture["scope"]


def test_real_pure_normalization_and_preparation_compose(tmp_path: Path) -> None:
    inputs, reference, buffers, scope = generated(tmp_path)
    result = preparation.prepare(inputs, reference, buffers=buffers, scope=scope)
    assert result.plan.payload()["design"] == {"kind": "unweighted_sensitivity"}
    assert all(type(raw) is bytes for raw in result.members.values())
    by_id = {case["case_id"]: case for case in result.plan.payload()["cases"]}
    baseline = json.loads(
        result.members[by_id["landclim-nominal-baseline"]["request_ref"]["path"]]
    )
    changed = json.loads(
        result.members[by_id["europe-betula-nominal"]["request_ref"]["path"]]
    )
    assert baseline["parameters"] == inputs.request["parameters"]
    assert changed["parameters"][0]["ppe"] == 4.94
    assert changed["parameters"][0]["ppe_sd"] == baseline["parameters"][0]["ppe_sd"]
    assert changed["parameters"][1] == baseline["parameters"][1]
    assert changed["configuration"] == baseline["configuration"]


def test_prepare_refuses_mutable_original_evidence_body(tmp_path: Path) -> None:
    inputs, reference, buffers, scope = generated(tmp_path)
    name = next(x for x in inputs.evidence if "raw_snapshot" in x)
    # Deliberately violate the bytes contract to exercise its runtime refusal.
    cast(dict[str, object], inputs.evidence)[name] = bytearray(inputs.evidence[name])
    with pytest.raises(ValueError):
        preparation.prepare(inputs, reference, buffers=buffers, scope=scope)


def test_public_prepared_model_owns_borrowed_mapping(tmp_path: Path) -> None:
    inputs, reference, buffers, scope = generated(tmp_path)
    prepared = preparation.prepare(inputs, reference, buffers=buffers, scope=scope)
    original = dict(prepared.members)
    borrowed = dict(original)
    owned = preparation.PreparedSourceCases(
        prepared.plan, borrowed, prepared.normalization_json
    )
    borrowed.clear()
    assert dict(owned.members) == original
