"""Scoped source readback authenticates parent evidence before numerical buffers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
    capture_neotoma_dataset_facets,
    read_neotoma_facet_body,
    replay_neotoma_facet_capture,
)

from ...resources.native_payloads import response, spec
from .native_sources import source_inputs


def test_scoped_replay_requires_original_input_resolvers(tmp_path: Path) -> None:
    plan, scope = source_inputs(tmp_path / "inputs", (spec(),))
    result = capture_neotoma_dataset_facets(
        tmp_path / "facets",
        plan=plan,
        scope=scope,
        fetch=lambda url, **_: response(url, b'{"status":"success","data":[]}'),
    )
    with pytest.raises(ValueError, match="scope"):
        replay_neotoma_facet_capture(
            tmp_path / "facets", expected_manifest_sha256=result.manifest_sha256
        )
    assert (
        replay_neotoma_facet_capture(
            tmp_path / "facets",
            expected_manifest_sha256=result.manifest_sha256,
            scope_inputs={plan.roster_sha256: scope},
        )
        == result
    )


def test_scoped_reader_authenticates_parent_before_opening_facet_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import replay

    plan, scope = source_inputs(tmp_path / "inputs", (spec(),))
    result = capture_neotoma_dataset_facets(
        tmp_path / "facets",
        plan=plan,
        scope=scope,
        fetch=lambda url, **_: response(url, b'{"status":"success","data":[]}'),
    )
    body_path = next((tmp_path / "facets").glob("*.body"))
    original = cast(Any, replay)._read

    def read(path: Path, bound: int) -> bytes:
        assert path != body_path, "Facet body opened before parent authentication"
        return cast(bytes, original(path, bound))

    monkeypatch.setattr(replay, "_read", read)
    with pytest.raises(ValueError, match="scope"):
        read_neotoma_facet_body(
            tmp_path / "facets",
            expected_manifest_sha256=result.manifest_sha256,
            facet_key=result.facets[0]["facet_key"],
        )


@pytest.mark.parametrize(
    "damage", ["role", "count", "native_source", "scope_reference", "missing_proof"]
)
def test_rehashed_parent_scope_cannot_fabricate_verified_obligations(
    tmp_path: Path, damage: str
) -> None:
    from hashlib import sha256
    import json

    plan, scope = source_inputs(tmp_path / "inputs", (spec(),))
    result = capture_neotoma_dataset_facets(
        tmp_path / "facets",
        plan=plan,
        scope=scope,
        fetch=lambda url, **_: response(url, b'{"status":"success","data":[]}'),
    )
    root = tmp_path / "facets"
    control = json.loads((root / "request-plan.json").read_bytes())
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    proof = json.loads((root / "parent-scope.json").read_bytes())
    if damage == "role":
        proof["parents"][0]["effective_scope_role"] = "heldout_no_numerical_access"
    elif damage == "count":
        proof["roster_resource_count"] = 999
    elif damage == "native_source":
        proof["parents"][0]["metadata_sources"][0]["receipt_sha256"] = "0" * 64
    elif damage == "scope_reference":
        del control["parent_scope"]
    else:
        (root / "parent-scope.json").unlink()
    if damage not in {"scope_reference", "missing_proof"}:
        (root / "parent-scope.json").write_text(json.dumps(proof))
        control["parent_scope"]["sha256"] = sha256(
            (root / "parent-scope.json").read_bytes()
        ).hexdigest()
    (root / "request-plan.json").write_text(json.dumps(control))
    manifest["plan_sha256"] = sha256(
        (root / "request-plan.json").read_bytes()
    ).hexdigest()
    (root / "capture-manifest.json").write_text(json.dumps(manifest))
    digest = sha256((root / "capture-manifest.json").read_bytes()).hexdigest()
    with pytest.raises((ValueError, FileNotFoundError)):
        replay_neotoma_facet_capture(
            root,
            expected_manifest_sha256=digest,
            scope_inputs={plan.roster_sha256: scope},
        )
    assert result.manifest_sha256 != digest


def test_batch_qualification_authenticates_metadata_closure_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        scope as scope_owner,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.qualification import (
        qualify_neotoma_facet_capture,
    )

    plan, scope = source_inputs(tmp_path / "inputs", (spec(),), facets=("taxa", "doi"))
    captured = capture_neotoma_dataset_facets(
        tmp_path / "facets",
        plan=plan,
        scope=scope,
        fetch=lambda url, **_: response(
            url, b'{"status":"success","data":[],"message":"source"}'
        ),
    )
    original = scope_owner.prepare_facet_parent_scope
    calls = []

    def prepare(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(scope_owner, "prepare_facet_parent_scope", prepare)
    result = qualify_neotoma_facet_capture(
        tmp_path / "facets",
        expected_manifest_sha256=captured.manifest_sha256,
        scope_inputs={plan.roster_sha256: scope},
    )
    assert len(result["entries"]) == 2
    assert calls == [1]
