"""Replay refuses forged proof closure, source swaps and changed actual buffers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from ..facets.parent_scope.native_sources import linked_scope_resolvers
from ..resources.native_payloads import response
from .test_capture import limits, owner, plan, source


def captured(tmp_path: Path) -> tuple[Path, Any, dict[str, Path]]:
    digest, sources = source(tmp_path / "facets")
    root = tmp_path / "linked"
    result = owner().capture_neotoma_linked_resources(
        root,
        plan=plan(digest),
        source_facets=sources,
        limits=limits(),
        fetch=lambda url, **k: response(url, b'{"status":"success","data":[]}'),
        scope_inputs=linked_scope_resolvers(sources),
    )
    return root, result, sources


def write(path: Path, value: Any) -> str:
    body = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return sha256(body).hexdigest()


def test_replay_and_body_read_authenticate_original_bytes(tmp_path: Path) -> None:
    root, result, sources = captured(tmp_path)
    replayed = owner().replay_neotoma_linked_resources(
        root,
        expected_manifest_sha256=result.manifest_sha256,
        source_facets=sources,
        limits=limits(),
        scope_inputs=linked_scope_resolvers(sources),
    )
    assert replayed == result
    body = owner().read_neotoma_linked_body(
        root,
        expected_manifest_sha256=result.manifest_sha256,
        target_key="contact-8720",
        source_facets=sources,
        limits=limits(),
        scope_inputs=linked_scope_resolvers(sources),
    )
    assert body.body == b'{"status":"success","data":[]}'
    assert body.body_sha256 == sha256(body.body).hexdigest()
    assert body.source_proofs


@pytest.mark.parametrize("part", ["body", "receipt", "source_body", "source_receipt"])
def test_changed_actual_source_buffers_are_refused(tmp_path: Path, part: str) -> None:
    root, result, sources = captured(tmp_path)
    if part.startswith("source"):
        directory = next(iter(sources.values()))
        suffix = ".body" if part == "source_body" else ".receipt.json"
        path = next(directory.glob(f"*{suffix}"))
    else:
        entry = result.resources[0]
        path = (
            root
            / entry["attempts"][-1]["body_file" if part == "body" else "receipt_file"]
        )
    path.write_bytes(b'{"foreign":true}')
    with pytest.raises(ValueError):
        owner().replay_neotoma_linked_resources(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            source_facets=sources,
            limits=limits(),
            scope_inputs=linked_scope_resolvers(sources),
        )


@pytest.mark.parametrize(
    "field",
    [
        "native_id",
        "json_pointer",
        "source_body_sha256",
        "source_receipt_sha256",
        "inherited_exposure_role",
        "root_dataset_id",
    ],
)
def test_legally_rehashed_plan_cannot_forge_native_proof(
    tmp_path: Path, field: str
) -> None:
    root, result, sources = captured(tmp_path)
    control = json.loads((root / "request-plan.json").read_bytes())
    proof = control["targets"][0]["source_proofs"][0]
    proof[field] = (
        "heldout_no_numerical_access"
        if field == "inherited_exposure_role"
        else 999
        if field in {"native_id", "root_dataset_id"}
        else "forged"
    )
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    manifest["plan_sha256"] = write(root / "request-plan.json", control)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError, match="proof|target|source"):
        owner().replay_neotoma_linked_resources(
            root,
            expected_manifest_sha256=digest,
            source_facets=sources,
            limits=limits(),
            scope_inputs=linked_scope_resolvers(sources),
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_source",
        "missing_source",
        "unknown_control",
        "unknown_manifest",
        "wrong_selection",
        "invented_ancestor",
    ],
)
def test_source_selection_and_owned_control_fields_are_exact(
    tmp_path: Path, mutation: str
) -> None:
    root, result, sources = captured(tmp_path)
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    control = json.loads((root / "request-plan.json").read_bytes())
    if mutation == "unknown_source":
        sources["f" * 64] = next(iter(sources.values()))
    elif mutation == "missing_source":
        sources.clear()
    elif mutation == "unknown_control":
        control["caller_roles"] = {"contact-8720": "development_resource_discovery"}
    elif mutation == "unknown_manifest":
        manifest["caller_proofs"] = []
    elif mutation == "wrong_selection":
        control["plan"]["targets"][0]["native_id"] = 999
    else:
        manifest["resources"][0]["reused_from"] = {"manifest_sha256": "f" * 64}
    manifest["plan_sha256"] = write(root / "request-plan.json", control)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError):
        owner().replay_neotoma_linked_resources(
            root,
            expected_manifest_sha256=digest,
            source_facets=sources,
            limits=limits(),
            scope_inputs=linked_scope_resolvers(sources),
        )


def test_stricter_caller_limits_refuse_historical_overrun(tmp_path: Path) -> None:
    root, result, sources = captured(tmp_path)
    with pytest.raises(ValueError):
        owner().replay_neotoma_linked_resources(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            source_facets=sources,
            limits=limits(1),
            scope_inputs=linked_scope_resolvers(sources),
        )


def test_actual_body_return_is_rechecked_after_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, result, sources = captured(tmp_path)
    module = __import__(
        owner().__name__ + ".replay", fromlist=["replay_neotoma_linked_resources"]
    )
    original = module.replay_neotoma_linked_resources

    def swap(*args: Any, **kwargs: Any) -> Any:
        value = original(*args, **kwargs)
        (root / result.resources[0]["attempts"][-1]["body_file"]).write_bytes(
            b'{"swapped":true}'
        )
        return value

    monkeypatch.setattr(module, "replay_neotoma_linked_resources", swap)
    with pytest.raises(ValueError):
        owner().read_neotoma_linked_body(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            target_key="contact-8720",
            source_facets=sources,
            limits=limits(),
            scope_inputs=linked_scope_resolvers(sources),
        )


@pytest.mark.parametrize("foreign", [False, True])
def test_legally_rehashed_receipt_cannot_change_target_or_add_authority(
    tmp_path: Path, foreign: bool
) -> None:
    root, result, sources = captured(tmp_path)
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    contact, publication = manifest["resources"][:2]
    reference = publication["attempts"][-1]
    record = json.loads(
        (
            root / (contact if foreign else publication)["attempts"][-1]["receipt_file"]
        ).read_bytes()
    )
    record["body_file"] = reference["body_file"]
    if not foreign:
        record["caller_native_owner"] = 999
    reference["receipt_sha256"] = write(root / reference["receipt_file"], record)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError):
        owner().replay_neotoma_linked_resources(
            root,
            expected_manifest_sha256=digest,
            source_facets=sources,
            limits=limits(),
            scope_inputs=linked_scope_resolvers(sources),
        )


def test_success_attests_actual_published_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    digest, sources = source(tmp_path / "facets")
    module = __import__(
        owner().__name__ + ".workflow", fromlist=["publish_new_output_tree"]
    )
    original = module.publish_new_output_tree

    def mutate(**kwargs: Any) -> Any:
        next(kwargs["staging_output_root"].glob("*.body")).write_bytes(
            b'{"foreign_stage":true}'
        )
        return original(**kwargs)

    monkeypatch.setattr(module, "publish_new_output_tree", mutate)
    with pytest.raises(ValueError):
        owner().capture_neotoma_linked_resources(
            tmp_path / "linked",
            plan=plan(digest),
            source_facets=sources,
            limits=limits(),
            fetch=lambda url, **k: response(url, b"{}"),
            scope_inputs=linked_scope_resolvers(sources),
        )
    assert any(
        path.read_bytes() == b'{"foreign_stage":true}'
        for path in (tmp_path / "linked").glob("*.body")
    )
