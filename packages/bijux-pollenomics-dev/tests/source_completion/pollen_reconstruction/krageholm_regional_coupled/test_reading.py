"""Literal source, inventory and file-custody controls on synthetic bytes only."""

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from .lineage import digest
from .reading import (
    csv_rows,
    decode,
    owned_artifact_path,
    pinned,
    product,
    read_file,
    relative_file,
)


@pytest.mark.parametrize(
    "body", [b'{"value":1,"value":2}', b'{"value":NaN}', b'{"value":Infinity}']
)
def test_literal_json_rejects_duplicate_keys_and_nonfinite_constants(
    body: bytes,
) -> None:
    with pytest.raises(ValueError):
        decode(body)


def test_json_native_integer_and_decimal_count_tokens_remain_distinct() -> None:
    row = decode(b'{"integer":4,"decimal":4.0,"boolean":true,"null":null}')
    assert type(row["integer"]) is int
    assert type(row["decimal"]) is float
    assert type(row["boolean"]) is bool
    assert row["null"] is None


def test_exact_source_pin_and_unaliased_file_read(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    body = b'{"count":3}'
    path.write_bytes(body)
    pin = {
        "path": "source.json",
        "bytes": len(body),
        "sha256": sha256(body).hexdigest(),
    }
    assert pinned(tmp_path, pin, 1024) == (body, {"count": 3})
    with pytest.raises(ValueError):
        pinned(tmp_path, dict(pin, bytes=len(body) + 1), 1024)
    with pytest.raises(ValueError):
        pinned(tmp_path, dict(pin, sha256="0" * 64), 1024)
    with pytest.raises(ValueError):
        read_file(path, 2)
    alias = tmp_path / "alias.json"
    alias.symlink_to(path)
    with pytest.raises(ValueError):
        read_file(alias, 1024)
    alias.unlink()
    alias.hardlink_to(path)
    with pytest.raises(ValueError):
        read_file(path, 1024)


@pytest.mark.parametrize("relative", ["../source.json", "/source.json"])
def test_members_cannot_escape_owner(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError):
        relative_file(tmp_path, relative)


def fake_product(tmp_path: Path) -> str:
    member = b'{"folds":[]}'
    (tmp_path / "folds.json").write_bytes(member)
    scientific: dict[str, Any] = {"folds": []}
    manifest = {
        "schema_version": "lra-experiment-product.v1",
        "scientific_payload": scientific,
        "scientific_content_sha256": digest(scientific),
        "files": {"folds.json": sha256(member).hexdigest()},
    }
    body = json.dumps(manifest).encode()
    (tmp_path / "manifest.json").write_bytes(body)
    return sha256(body).hexdigest()


def test_product_checks_all_members_and_payload(tmp_path: Path) -> None:
    pin = fake_product(tmp_path)
    manifest, files = product(tmp_path, pin)
    assert manifest["scientific_payload"] == {"folds": []}
    assert files == {"folds.json": b'{"folds":[]}'}


@pytest.mark.parametrize(
    "corruption", ["member", "extra", "missing", "payload", "symlink"]
)
def test_product_rejects_member_population_or_identity_tampering(
    tmp_path: Path, corruption: str
) -> None:
    pin = fake_product(tmp_path)
    if corruption == "member":
        (tmp_path / "folds.json").write_text("[]")
    elif corruption == "extra":
        (tmp_path / "unlisted.json").write_text("[]")
    elif corruption == "missing":
        (tmp_path / "folds.json").unlink()
    elif corruption == "symlink":
        (tmp_path / "folds.json").rename(tmp_path / "unlisted.json")
        (tmp_path / "folds.json").symlink_to(tmp_path / "unlisted.json")
    else:
        path = tmp_path / "manifest.json"
        manifest = json.loads(path.read_bytes())
        manifest["scientific_payload"]["folds"] = ["altered"]
        path.write_text(json.dumps(manifest))
        pin = sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        product(tmp_path, pin)


@pytest.mark.parametrize("body", [b"a,a\n1,2\n", b"a,b\n1\n", b"a,b\n1,2,3\n"])
def test_csv_requires_unique_rectangular_columns(body: bytes) -> None:
    with pytest.raises(ValueError):
        csv_rows(body)


def test_relative_and_absolute_artifact_locators_keep_one_study_owner(
    tmp_path: Path,
) -> None:
    owner = tmp_path / "artifacts/study"
    expected = owner / "predictions/batch.json"
    assert (
        owned_artifact_path(tmp_path, "artifacts/study/predictions/batch.json", owner)
        == expected
    )
    assert owned_artifact_path(tmp_path, str(expected), owner) == expected


@pytest.mark.parametrize(
    "locator",
    [
        "artifacts/study/../other/batch.json",
        "../artifacts/study/batch.json",
        "/outside/batch.json",
        "artifacts/other/batch.json",
        "reports/batch.json",
        "",
    ],
)
def test_artifact_locators_refuse_parent_traversal_absolute_escape_and_other_owners(
    tmp_path: Path, locator: str
) -> None:
    with pytest.raises(ValueError):
        owned_artifact_path(tmp_path, locator, tmp_path / "artifacts/study")


def test_absolute_artifact_locator_cannot_select_another_study(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        owned_artifact_path(
            tmp_path,
            str(tmp_path / "artifacts/other/batch.json"),
            tmp_path / "artifacts/study",
        )


@pytest.mark.parametrize("kind", ["member", "ancestor"])
def test_artifact_locator_refuses_symlink_member_or_ancestry(
    tmp_path: Path, kind: str
) -> None:
    owner = tmp_path / "artifacts/study"
    owner.mkdir(parents=True)
    if kind == "member":
        actual = owner / "actual.json"
        actual.write_text("{}")
        (owner / "batch.json").symlink_to(actual)
        locator = "artifacts/study/batch.json"
    else:
        (owner / "actual").mkdir()
        (owner / "linked").symlink_to(owner / "actual", target_is_directory=True)
        locator = "artifacts/study/linked/batch.json"
    with pytest.raises(ValueError):
        owned_artifact_path(tmp_path, locator, owner)
