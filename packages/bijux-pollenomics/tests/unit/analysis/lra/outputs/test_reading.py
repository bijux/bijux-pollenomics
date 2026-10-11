"""A product reader must detect partial, modified and misleading saved bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
from bijux_pollenomics.analysis.lra.outputs import reading
from bijux_pollenomics.analysis.lra.outputs.identity import capture_code_identity
from bijux_pollenomics.analysis.lra.outputs.publication import publish_result
from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product

from ..support import request_fixture
from .test_publication import Result, binding


def test_reader_preserves_generated_identity_and_returns_isolated_manifest(
    tmp_path: Path,
) -> None:
    engine = binding(tmp_path)
    product = publish_result(
        Result(),
        engine,
        validate_request(request_fixture(tmp_path), input_root=tmp_path),
        destination=tmp_path / "product",
        input_root=tmp_path,
        code_identity=capture_code_identity(engine),
    )
    verified = read_lra_product(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert verified.product == product
    copied = verified.manifest()
    copied["scientific_acceptance"] = "invented"
    assert verified.manifest()["scientific_acceptance"] == "not_evaluated"


@pytest.mark.parametrize(
    "change",
    [
        "numerical",
        "missing",
        "extra",
        "symlink",
        "claim",
        "duplicate",
        "identity",
        "expected",
    ],
)
def test_reader_refuses_corrupt_or_unexpected_product(
    tmp_path: Path, change: str
) -> None:
    engine = binding(tmp_path)
    product = publish_result(
        Result(),
        engine,
        validate_request(request_fixture(tmp_path), input_root=tmp_path),
        destination=tmp_path / "product",
        input_root=tmp_path,
        code_identity=capture_code_identity(engine),
    )
    root = product.directory
    path = root / "manifest.json"
    original = path.read_bytes()
    if change == "numerical":
        (root / "numerical/reconstruction.csv").write_text("wrong values")
    elif change == "missing":
        (root / "request.json").unlink()
    elif change == "extra":
        (root / "unlisted.csv").write_text("unexpected")
    elif change == "symlink":
        (root / "outside").symlink_to(tmp_path / "raw_snapshot.txt")
    elif change == "duplicate":
        path.write_bytes(original[:-2] + b',"status":"generated_exploratory"}\n')
    elif change in {"claim", "identity"}:
        manifest = json.loads(original)
        if change == "claim":
            manifest["scientific_acceptance"] = "approved"
        else:
            manifest["scientific_identity"]["request_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest))
    with pytest.raises(LRARefusal) as error:
        read_lra_product(
            root, expected_manifest_sha256="0" * 64 if change == "expected" else None
        )
    assert error.value.reason_code == "invalid_lra_product"


def test_partial_directory_cannot_be_reopened(tmp_path: Path) -> None:
    with pytest.raises(LRARefusal, match="manifest.json"):
        read_lra_product(tmp_path)


@pytest.mark.parametrize(
    "change", ["metadata", "during_read", "malformed_table", "nullable_sd"]
)
def test_reader_checks_request_metadata_and_table_shape_and_read_closure(
    tmp_path: Path, change: str
) -> None:
    engine = binding(tmp_path)
    product = publish_result(
        Result(),
        engine,
        validate_request(request_fixture(tmp_path), input_root=tmp_path),
        destination=tmp_path / "product",
        input_root=tmp_path,
        code_identity=capture_code_identity(engine),
    )
    root = product.directory
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    table = root / "numerical/reconstruction.csv"
    if change == "metadata":
        manifest["included_sample_count"] = 999
        manifest["units"]["regional_cover"] = "fraction"
    elif change in {"malformed_table", "nullable_sd"}:
        if change == "malformed_table":
            table.write_text("not,a,model\nNaN,Infinity,garbage\n")
        else:
            table.write_text(table.read_text().replace(",0,0\n", ",,\n"))
        digest = hashlib.sha256(table.read_bytes()).hexdigest()
        manifest["files"]["numerical/reconstruction.csv"] = digest
        manifest["scientific_identity"]["numerical_files"]["reconstruction.csv"] = (
            digest
        )
        identity_bytes = (
            json.dumps(
                manifest["scientific_identity"], sort_keys=True, separators=(",", ":")
            )
            + "\n"
        ).encode()
        manifest["scientific_content_sha256"] = hashlib.sha256(
            identity_bytes
        ).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    original = reading._hash
    content = table.read_bytes()
    changed = False

    def during_hash(value: bytes) -> str:
        nonlocal changed
        digest = original(value)
        if change == "during_read" and value == content and not changed:
            table.write_text("modified during read")
            changed = True
        return digest

    with patch.object(reading, "_hash", side_effect=during_hash):
        if change == "nullable_sd":
            assert read_lra_product(root).product.directory == root
        else:
            with pytest.raises(LRARefusal) as error:
                read_lra_product(root)
            assert error.value.reason_code == "invalid_lra_product"
    if change == "during_read":
        assert changed
