"""Real filesystem publication races and content identity boundaries."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from types import ModuleType

import pytest

from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
from bijux_pollenomics.analysis.lra.outputs.identity import capture_code_identity
from bijux_pollenomics.analysis.lra.outputs.publication import publish_result

from ..support import request_fixture


class Manifest:
    def scientific_identity(self) -> dict[str, str]:
        return {"identity": "synthetic"}


class Result:
    manifest = Manifest()

    def __init__(self, during_write: Callable[[], None] = lambda: None) -> None:
        self.during_write = during_write

    def write(self, root: Path) -> None:
        root.mkdir()
        (root / "reconstruction.csv").write_text(
            "Distance.weighting,Basin.type,coordinate,Alnus.mean,Betula.mean,"
            "Alnus.median,Betula.median,Alnus.q90,Betula.q90,Alnus.q10,Betula.q10,Alnus.sd,Betula.sd\n"
            "lsm unstable,lake,1,50,50,50,50,50,50,50,50,0,0\n"
        )
        (root / "deposition_factors.csv").write_text("index,K\nAlnus,1\nBetula,1\n")
        (root / "result_contract.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "result_type": "reveals",
                    "primary_artifact": "reconstruction.csv",
                    "units": {"cover": "percent", "distance": "metre"},
                }
            )
        )
        self.during_write()


def binding(root: Path) -> EngineBinding:
    code = root / "installed"
    code.mkdir()
    (code / "api.py").write_text('"""Synthetic installed module."""\n')
    api = ModuleType("synthetic")
    api.__file__ = str(code / "api.py")
    return EngineBinding("bijux-pollenomics-lra", "0.2.0", "python-numpy-scipy", api)


def test_publication_is_reproducible_and_explicitly_exploratory(tmp_path: Path) -> None:
    engine = binding(tmp_path)
    request = validate_request(request_fixture(tmp_path), input_root=tmp_path)
    identity = capture_code_identity(engine)
    products = [
        publish_result(
            Result(),
            engine,
            request,
            destination=tmp_path / name,
            input_root=tmp_path,
            code_identity=identity,
        )
        for name in ("first", "second")
    ]
    assert (
        products[0].scientific_content_sha256 == products[1].scientific_content_sha256
    )
    manifest = json.loads((products[0].directory / "manifest.json").read_text())
    assert manifest["scientific_acceptance"] == "not_evaluated"
    assert manifest["included_sample_count"] == 1
    assert manifest["temporal_matching"]["rule"] == "declared_bin_stationarity"
    assert (
        manifest["scientific_identity"]["engine_files"]
        == identity.payload()["engine_files"]
    )


def test_competing_empty_destination_is_never_replaced(tmp_path: Path) -> None:
    engine = binding(tmp_path)
    request = validate_request(request_fixture(tmp_path), input_root=tmp_path)
    destination = tmp_path / "product"
    created = []

    def compete() -> None:
        destination.mkdir()
        created.append(destination.stat().st_ino)

    with pytest.raises(LRARefusal) as error:
        publish_result(
            Result(compete),
            engine,
            request,
            destination=destination,
            input_root=tmp_path,
            code_identity=capture_code_identity(engine),
        )
    assert error.value.reason_code == "lra_output_exists"
    assert destination.stat().st_ino == created[0]
    assert list(destination.iterdir()) == []
    assert list(tmp_path.glob(".product.pending-*"))


def test_code_mutation_during_serialization_refuses_publication(tmp_path: Path) -> None:
    engine = binding(tmp_path)
    request = validate_request(request_fixture(tmp_path), input_root=tmp_path)
    destination = tmp_path / "product"
    identity = capture_code_identity(engine)

    def mutate() -> None:
        (tmp_path / "installed/api.py").write_text("changed code")

    with pytest.raises(LRARefusal) as error:
        publish_result(
            Result(mutate),
            engine,
            request,
            destination=destination,
            input_root=tmp_path,
            code_identity=identity,
        )
    assert error.value.reason_code == "lra_code_changed_during_run"
    assert not destination.exists()
