"""Facet replay authenticates source identities, limits and every retained entity."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceLimits,
)

from ..resources.native_payloads import response, spec
from .native_payloads import BODY, owner, plan


def captured(root: Path) -> Any:
    return owner().capture_neotoma_dataset_facets(
        root,
        plan=plan(spec(), facets=("chronologies",)),
        fetch=lambda url, **_: response(url, BODY),
    )


@pytest.mark.parametrize(
    "damage", ["body", "receipt", "role", "facet", "version", "count", "extra"]
)
def test_replay_refuses_changed_body_or_declared_identity(
    tmp_path: Path, damage: str
) -> None:
    directory = tmp_path / "capture"
    result = captured(directory)
    manifest_path = directory / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    row = manifest["facets"][0]
    if damage == "body":
        (directory / row["attempts"][0]["body_file"]).write_bytes(b"{}")
    elif damage == "receipt":
        receipt = directory / row["attempts"][0]["receipt_file"]
        receipt.write_bytes(receipt.read_bytes() + b"\n")
    elif damage == "role":
        row["root_identity"]["exposure_role"] = "reserved_candidate_confirmation"
    elif damage == "facet":
        row["facet"] = "taxa"
    elif damage == "version":
        row["content_version"] = "doi_frozen"
    elif damage == "count":
        manifest["request_count"] = True
    else:
        row["unowned_assertion"] = True
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        owner().replay_neotoma_facet_capture(directory)
    if damage in {"body", "receipt"}:
        with pytest.raises(ValueError):
            owner().read_neotoma_facet_body(
                directory,
                expected_manifest_sha256=result.manifest_sha256,
                facet_key=result.facets[0]["facet_key"],
            )


@pytest.mark.parametrize(
    "limit", ["max_requests", "max_response_bytes", "max_total_bytes"]
)
def test_replay_enforces_stricter_caller_limits(tmp_path: Path, limit: str) -> None:
    directory = tmp_path / "capture"
    owner().capture_neotoma_dataset_facets(
        directory,
        plan=plan(spec(), facets=("projects", "taxa")),
        fetch=lambda url, **_: response(url, BODY),
    )
    limits = NeotomaResourceLimits(**{limit: 1})
    with pytest.raises(ValueError):
        owner().replay_neotoma_facet_capture(directory, limits=limits)


def test_replay_refuses_extra_or_symlinked_capture_files(tmp_path: Path) -> None:
    directory = tmp_path / "capture"
    captured(directory)
    extra = directory / "not-declared.body"
    extra.write_bytes(b"preserve")
    with pytest.raises(ValueError):
        owner().replay_neotoma_facet_capture(directory)
    extra.unlink()
    extra.symlink_to(directory / "request-plan.json")
    with pytest.raises(ValueError):
        owner().replay_neotoma_facet_capture(directory)


def test_body_reader_authenticates_the_buffer_returned_after_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "capture"
    result = captured(directory)
    body_path = directory / result.facets[0]["attempts"][0]["body_file"]
    original = Path.read_bytes
    reads = 0

    def changed_second_read(path: Path) -> bytes:
        nonlocal reads
        if path == body_path:
            reads += 1
            if reads > 1:
                return b'{"foreign":true}'
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", changed_second_read)
    with pytest.raises(ValueError):
        owner().read_neotoma_facet_body(
            directory,
            expected_manifest_sha256=result.manifest_sha256,
            facet_key=result.facets[0]["facet_key"],
        )
    assert sha256(original(body_path)).hexdigest() == sha256(BODY).hexdigest()


def test_refusal_label_cannot_launder_changed_body_with_original_receipt(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "capture"
    captured(directory)
    manifest_path = directory / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    entry = manifest["facets"][0]
    changed = b'{"foreign_body":true}'
    (directory / entry["attempts"][0]["body_file"]).write_bytes(changed)
    entry.pop("summary")
    entry.update(
        terminal_status="refused_http_receipt",
        reason="Neotoma metadata body identity or byte limit differs",
    )
    manifest.update(response_bytes=len(changed), partitions={"refused_http_receipt": 1})
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        owner().replay_neotoma_facet_capture(directory)
