"""Rehashed retained contradictions cannot replace the original input graph."""

from importlib.util import find_spec
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.uncertainty.api import (
    JointLRAPlan,
    read_joint_lra_ensemble,
    run_joint_lra_ensemble,
)
from bijux_pollenomics.analysis.lra.uncertainty.contracts import (
    canonical,
    digest,
    parse_json,
)
from bijux_pollenomics.analysis.lra.uncertainty.reading import (
    inventory,
    scientific_identity,
)

from .test_contracts import fixture


@pytest.fixture(scope="module")
def product(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if find_spec("bijux_pollenomics_lra") is None:
        pytest.skip("Actual optional installed LRA engine required")
    root = tmp_path_factory.mktemp("joint-retained")
    _, p = fixture(root / "source")
    return run_joint_lra_ensemble(
        JointLRAPlan.from_dict(p),
        input_root=root / "source",
        destination=root / "product",
    ).directory


def rehash(path: Path, manifest: dict[str, Any]) -> str:
    manifest["files"] = inventory(path)
    manifest["scientific_content_sha256"] = digest(
        canonical(scientific_identity(manifest))
    )
    data = canonical(manifest)
    (path / "manifest.json").write_bytes(data)
    return digest(data)


@pytest.mark.parametrize(
    "kind",
    [
        "scope",
        "empty_code",
        "denominator_bool",
        "unknown_root",
        "unknown_source",
        "missing_row",
        "mass",
        "child_request_sha",
        "modeled_age",
        "value",
        "child_request",
        "false_failure",
    ],
)
def test_rehashed_contradiction_refuses(
    product: Path, tmp_path: Path, kind: str
) -> None:
    path = tmp_path / "copy"
    shutil.copytree(product, path)
    m = parse_json((path / "manifest.json").read_bytes())
    if kind == "scope":
        m["uncertainty_scope"]["empirical_coverage_verified"] = True
    elif kind == "empty_code":
        m["code_identity"] = {}
    elif kind == "denominator_bool":
        m["denominators"]["not_run_draw_bins"] = False
    elif kind == "unknown_root":
        (path / "extra.txt").write_text("unknown")
    elif kind == "unknown_source":
        (path / "source/extra.txt").write_text("unknown")
    elif kind == "missing_row":
        m["rows"].pop()
    elif kind == "mass":
        m["rows"][0]["mass"]["numerator"] = 2
    elif kind == "child_request_sha":
        m["rows"][0]["child_request_sha256"] = "0" * 64
    elif kind == "modeled_age":
        member = next((path / "source/__joint_realizations__").rglob("*.json"))
        value = parse_json(member.read_bytes())
        value["draw"]["ages_by_sample_id"]["local1"] = 60
        member.write_bytes(canonical(value))
    elif kind == "value":
        m["rows"][0]["values"][0] += 0.1
    elif kind == "child_request":
        member = path / m["rows"][0]["child"] / "request.json"
        value = parse_json(member.read_bytes())
        value["parameters"][0]["ppe"] = 17
        member.write_bytes(canonical(value))
    else:
        row = m["rows"][0]
        row.update(
            status="refused", reason_code="nonfinite_child_cover", detail="forged"
        )
        row.pop("coordinates")
        row.pop("values")
    checksum = rehash(path, m)
    with pytest.raises(LRARefusal):
        read_joint_lra_ensemble(path, expected_manifest_sha256=checksum)


def test_external_pin_and_owned_manifest(product: Path) -> None:
    checksum = digest((product / "manifest.json").read_bytes())
    result = read_joint_lra_ensemble(product, expected_manifest_sha256=checksum)
    copy = result.manifest()
    copy["status"] = "accepted"
    assert result.manifest()["status"] == "complete"
    with pytest.raises(LRARefusal):
        read_joint_lra_ensemble(product, expected_manifest_sha256="0" * 64)
