"""Reference metadata replay binds exact routes, scalar kinds and returned bytes."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from ..resources.native_payloads import response
from .test_capture import owner, plan


def write(path: Path, value: Any) -> str:
    content = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(content)
    return sha256(content).hexdigest()


def captured(tmp_path: Path) -> tuple[Path, Any]:
    root = tmp_path / "capture"
    result = owner().capture_neotoma_reference_tables(
        root,
        plan=plan(),
        fetch=lambda url, **k: response(url, b'{"status":"success","data":[]}'),
    )
    return root, result


def test_replay_and_selected_buffer_preserve_exact_source_entity(
    tmp_path: Path,
) -> None:
    root, result = captured(tmp_path)
    assert (
        owner().replay_neotoma_reference_tables(
            root, expected_manifest_sha256=result.manifest_sha256
        )
        == result
    )
    body = owner().read_neotoma_reference_table_body(
        root, expected_manifest_sha256=result.manifest_sha256, table="variableunits"
    )
    assert (
        body.body == b'{"status":"success","data":[]}'
        and body.body_sha256 == sha256(body.body).hexdigest()
    )


@pytest.mark.parametrize(
    "damage",
    [
        "body",
        "receipt",
        "unknown_control",
        "unknown_manifest",
        "table",
        "role",
        "prefix",
        "ancestry",
        "absence",
    ],
)
def test_changed_sources_or_legally_rehashed_false_scope_is_refused(
    tmp_path: Path, damage: str
) -> None:
    root, result = captured(tmp_path)
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    control = json.loads((root / "request-plan.json").read_bytes())
    ref = manifest["tables"][0]["attempts"][0]
    if damage == "body":
        (root / ref["body_file"]).write_bytes(b'{"foreign":true}')
    elif damage == "receipt":
        (root / ref["receipt_file"]).write_bytes(b'{"foreign":true}')
    elif damage == "unknown_control":
        control["caller_url"] = "https://foreign.invalid"
    elif damage == "unknown_manifest":
        manifest["role_override"] = "development_resource_discovery"
    elif damage == "table":
        control["plan"]["tables"] = ["samples"]
    elif damage == "role":
        manifest["tables"][0]["metadata_role"] = "numerical_development"
    elif damage == "prefix":
        manifest["tables"][0]["summary"]["prefix_offset"] = 36
    elif damage == "ancestry":
        manifest["tables"][0]["reused_from"] = {"manifest_sha256": "f" * 64}
    else:
        manifest["tables"][0]["summary"]["absence_certified"] = True
    manifest["plan_sha256"] = write(root / "request-plan.json", control)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError):
        owner().replay_neotoma_reference_tables(root, expected_manifest_sha256=digest)


def test_stricter_caller_request_limit_is_enforced(tmp_path: Path) -> None:
    root, result = captured(tmp_path)
    with pytest.raises(ValueError):
        owner().replay_neotoma_reference_tables(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            limits=replace(owner().DEFAULT_REFERENCE_LIMITS, max_requests=1),
        )


def test_unknown_table_read_refuses_before_any_body_buffer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, result = captured(tmp_path)
    original = capture_opening()

    def guard(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path.suffix != ".body", "Unselected source body opened"
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, guard)
    with pytest.raises(ValueError):
        owner().read_neotoma_reference_table_body(
            root, expected_manifest_sha256=result.manifest_sha256, table="samples"
        )


def test_actual_buffer_is_rechecked_after_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, result = captured(tmp_path)
    module = __import__(
        owner().__name__ + ".replay", fromlist=["replay_neotoma_reference_tables"]
    )
    original = module.replay_neotoma_reference_tables

    def swap(*args: Any, **kwargs: Any) -> Any:
        value = original(*args, **kwargs)
        (root / result.tables[0]["attempts"][0]["body_file"]).write_bytes(
            b'{"foreign":true}'
        )
        return value

    monkeypatch.setattr(module, "replay_neotoma_reference_tables", swap)
    with pytest.raises(ValueError):
        owner().read_neotoma_reference_table_body(
            root, expected_manifest_sha256=result.manifest_sha256, table="variableunits"
        )


def test_success_reauthenticates_actual_published_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication import ownership

    module = ownership
    original = vars(module)["publish_new_output_tree"]

    def mutate(**kwargs: Any) -> Any:
        next(kwargs["staging_output_root"].glob("*.body")).write_bytes(
            b'{"foreign_stage":true}'
        )
        return original(**kwargs)

    monkeypatch.setattr(module, "publish_new_output_tree", mutate)
    with pytest.raises(ValueError):
        owner().capture_neotoma_reference_tables(
            tmp_path / "capture",
            plan=plan(),
            fetch=lambda url, **k: response(url, b"{}"),
        )
    assert any(
        p.read_bytes() == b'{"foreign_stage":true}'
        for p in (tmp_path / "capture").glob("*.body")
    )


def test_legally_rehashed_other_table_receipt_cannot_change_endpoint_owner(
    tmp_path: Path,
) -> None:
    root, result = captured(tmp_path)
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    original, changed = [row["attempts"][0] for row in manifest["tables"]]
    record = json.loads((root / original["receipt_file"]).read_bytes())
    record["body_file"] = changed["body_file"]
    changed["receipt_sha256"] = write(root / changed["receipt_file"], record)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError):
        owner().replay_neotoma_reference_tables(root, expected_manifest_sha256=digest)
