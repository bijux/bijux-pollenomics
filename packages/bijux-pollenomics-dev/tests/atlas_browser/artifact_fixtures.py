"""Synthetic byte-closure fixtures; saved-product semantics have their own tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

import pytest

from bijux_pollenomics_dev.ci.atlas_browser import artifact_candidate as audit
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    NATIVE_LRA_PROFILE,
    AtlasArtifactCandidate,
    AtlasScope,
    BrowserVerificationPlan,
)

from .fixtures import BUILD_ID


def encode(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def write(root: Path, member: str, payload: bytes) -> None:
    path = root / member
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def artifact_plan(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> BrowserVerificationPlan:
    """Build all content graphs while isolating only Git and product semantics."""
    source = root / "artifacts/source"
    objects: dict[str, str] = {}
    for name in audit.SOURCE_ROOTS:
        member = (
            name + "/fixture.py"
            if name.endswith(("src", "scientific-contracts"))
            else name
        )
        payload = (member + "\n").encode()
        write(source, member, payload)
        objects[member] = hashlib.sha1(
            b"blob " + str(len(payload)).encode() + b"\0" + payload
        ).hexdigest()
    monkeypatch.setattr(audit, "committed_source", lambda *_args: objects)
    monkeypatch.setattr(audit, "_verify_product", lambda *_args: None)
    product = {
        "files": {},
        "request_sha256": "1" * 64,
        "scientific_content_sha256": "2" * 64,
    }
    product_bytes = encode(product)
    product_sha = audit.sha256(product_bytes)
    geometry = {**product, "product_manifest_sha256": product_sha}
    geometry_bytes = encode(geometry)
    geometry_sha = audit.sha256(geometry_bytes)
    write(root, "artifacts/input/manifest.json", product_bytes)
    write(root, "artifacts/geometry.json", geometry_bytes)
    presentation = root / "artifacts/presentation"
    write(presentation, "product/manifest.json", product_bytes)
    write(presentation, "display-geometry.json", geometry_bytes)
    write(presentation, "map.html", b"<!doctype html>synthetic")
    write(presentation, "map_assets.json", b"{}")
    write(presentation, "data/é-\x7f-\ue000-\U00010000.json", b"{}")
    with zipfile.ZipFile(presentation / "product.zip", "w") as archive:
        archive.writestr("manifest.json", product_bytes)
    manifest = {
        **product,
        "schema_version": "lra-presentation.v1",
        "status": "generated_exploratory",
        "scientific_acceptance": "not_evaluated",
        "publication_authorized": False,
        "data_kind": "synthetic",
        "operation": "lra",
        "map_build_id": BUILD_ID,
        "product_manifest_sha256": product_sha,
        "display_geometry_sha256": geometry_sha,
        "files": {row["path"]: row["sha256"] for row in audit.inventory(presentation)},
    }
    write(presentation, "manifest.json", encode(manifest))
    candidate = AtlasArtifactCandidate(
        build_id=BUILD_ID,
        generator_repository_head="a" * 40,
        generator_repository_tree="b" * 40,
        generator_receipt="artifacts/generation.json",
        generator_receipt_sha256="c" * 64,
        presentation_root="artifacts/presentation",
        presentation_manifest_sha256=audit.sha256(encode(manifest)),
        presentation_inventory_sha256=audit.canonical_digest(
            audit.inventory(presentation)
        ),
        product_manifest_sha256=product_sha,
        display_geometry_sha256=geometry_sha,
    )
    output = {
        key: value
        for key, value in candidate.as_json().items()
        if key
        in {
            "presentation_root",
            "presentation_manifest_sha256",
            "presentation_inventory_sha256",
            "product_manifest_sha256",
            "display_geometry_sha256",
            "build_id",
        }
    }
    argv = [
        "/python",
        "-I",
        "-c",
        audit.GENERATOR_SCRIPT,
        str(source / "packages/bijux-pollenomics/src"),
        str(root / "artifacts/input"),
        product_sha,
        str(root / "artifacts/geometry.json"),
        geometry_sha,
        str(presentation),
    ]
    receipt: dict[str, Any] = {
        "schema_version": "atlas-artifact-generation.v1",
        "source_relation": "committed_tree",
        "generator_repository_head": "a" * 40,
        "generator_repository_tree": "b" * 40,
        "source_root": "artifacts/source",
        "source_files": audit.source_inventory(source, objects),
        "entry_point": audit.ENTRY_POINT,
        "runtime": {
            "python": "3.11.0",
            "implementation": "CPython",
            "executable": "/python",
            "executable_sha256": "d" * 64,
            "distributions": [{"name": "example", "version": "1"}],
        },
        "invocation": {"argv": argv, "cwd": str(source), "python_binary": "/python"},
        "inputs": {
            "product_directory": "artifacts/input",
            "geometry_path": "artifacts/geometry.json",
        },
        "output": output,
    }
    write(root, candidate.generator_receipt, encode(receipt))
    candidate = replace(
        candidate, generator_receipt_sha256=audit.sha256(encode(receipt))
    )
    browser = root / "browser"
    browser.write_bytes(b"browser")
    return BrowserVerificationPlan(
        root,
        root / "artifacts/browser",
        browser,
        candidate,
        (
            AtlasScope(
                "native",
                "artifacts/presentation/map.html",
                "artifacts/presentation/map_assets.json",
            ),
        ),
        NATIVE_LRA_PROFILE,
    )


def rewrite_receipt(
    plan: BrowserVerificationPlan, **updates: object
) -> BrowserVerificationPlan:
    assert isinstance(plan.candidate, AtlasArtifactCandidate)
    path = plan.repository_root / plan.candidate.generator_receipt
    value = json.loads(path.read_bytes())
    value.update(updates)
    path.write_bytes(encode(value))
    return replace(
        plan,
        candidate=replace(
            plan.candidate, generator_receipt_sha256=audit.sha256(path.read_bytes())
        ),
    )
