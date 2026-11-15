"""Whole-unit source authority and publication buffers remain authenticated."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from ..resources.native_payloads import response
from .test_capture import limits, owner, prepared, write


def captured(tmp_path: Path) -> tuple[Path, Any, Path, dict[str, Path]]:
    plan, roster, sources = prepared(tmp_path)
    root = tmp_path / "units"
    result = owner().capture_neotoma_unit_resources(
        root,
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=lambda url, **k: response(url, b'{"status":"success","data":[]}'),
    )
    return root, result, roster, sources


def test_body_and_replay_return_authenticated_unit_buffers(tmp_path: Path) -> None:
    root, result, roster, sources = captured(tmp_path)
    assert (
        owner().replay_neotoma_unit_resources(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
        )
        == result
    )
    body = owner().read_neotoma_unit_body(
        root,
        expected_manifest_sha256=result.manifest_sha256,
        unit_key="speleothem-unit-100",
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
    )
    assert body.body == b'{"status":"success","data":[]}'
    assert body.scope["native_dataset_ids"] == [201, 202]


@pytest.mark.parametrize(
    "field",
    [
        "native_dataset_ids",
        "exposure_role",
        "site_id",
        "roster_obligations",
        "native_unit_source",
    ],
)
def test_rehashed_control_cannot_forge_unit_scope(tmp_path: Path, field: str) -> None:
    root, result, roster, sources = captured(tmp_path)
    control = json.loads((root / "request-plan.json").read_bytes())
    control["units"][0][field] = "forged"
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    manifest["plan_sha256"] = write(root / "request-plan.json", control)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError):
        owner().replay_neotoma_unit_resources(
            root,
            expected_manifest_sha256=digest,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
        )


@pytest.mark.parametrize(
    "member",
    ["roster", "metadata_body", "metadata_receipt", "unit_body", "unit_receipt"],
)
def test_changed_source_bytes_are_refused(tmp_path: Path, member: str) -> None:
    root, result, roster, sources = captured(tmp_path)
    if member == "roster":
        path = roster
    elif member.startswith("metadata"):
        path = next(
            next(iter(sources.values())).glob(
                "*.body" if member.endswith("body") else "*.receipt.json"
            )
        )
    else:
        path = (
            root
            / result.units[0]["attempts"][-1][
                "body_file" if member.endswith("body") else "receipt_file"
            ]
        )
    path.write_bytes(b'{"foreign":true}')
    with pytest.raises(ValueError):
        owner().replay_neotoma_unit_resources(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
        )


def test_actual_returned_buffer_is_checked_after_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, result, roster, sources = captured(tmp_path)
    module = __import__(
        owner().__name__ + ".replay", fromlist=["replay_neotoma_unit_resources"]
    )
    original = module.replay_neotoma_unit_resources

    def swap(*args: Any, **kwargs: Any) -> Any:
        value = original(*args, **kwargs)
        (root / result.units[0]["attempts"][-1]["body_file"]).write_bytes(
            b'{"foreign":true}'
        )
        return value

    monkeypatch.setattr(module, "replay_neotoma_unit_resources", swap)
    with pytest.raises(ValueError):
        owner().read_neotoma_unit_body(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            unit_key="speleothem-unit-100",
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
        )


def test_actual_publication_is_replayed_before_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, roster, sources = prepared(tmp_path)
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
        owner().capture_neotoma_unit_resources(
            tmp_path / "units",
            plan=plan,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
            fetch=lambda url, **k: response(url, b"{}"),
        )
    assert (
        next((tmp_path / "units").glob("*.body")).read_bytes()
        == b'{"foreign_stage":true}'
    )


@pytest.mark.parametrize(
    "damage",
    [
        "unknown_control",
        "unknown_manifest",
        "ancestry",
        "selection",
        "extra_metadata",
        "missing_metadata",
    ],
)
def test_owned_selection_and_source_resolvers_are_exact(
    tmp_path: Path, damage: str
) -> None:
    root, result, roster, sources = captured(tmp_path)
    control = json.loads((root / "request-plan.json").read_bytes())
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    if damage == "unknown_control":
        control["caller_roles"] = {
            "speleothem-unit-100": "development_resource_discovery"
        }
    elif damage == "unknown_manifest":
        manifest["caller_scope"] = {}
    elif damage == "ancestry":
        manifest["units"][0]["reused_from"] = {"manifest_sha256": "f" * 64}
    elif damage == "selection":
        control["plan"]["collection_unit_ids"] = [999]
    elif damage == "extra_metadata":
        sources["f" * 64] = next(iter(sources.values()))
    else:
        sources.clear()
    manifest["plan_sha256"] = write(root / "request-plan.json", control)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError):
        owner().replay_neotoma_unit_resources(
            root,
            expected_manifest_sha256=digest,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
        )


def test_stricter_unit_body_limit_does_not_weaken_metadata_source_scope(
    tmp_path: Path,
) -> None:
    root, result, roster, sources = captured(tmp_path)
    with pytest.raises(ValueError):
        owner().replay_neotoma_unit_resources(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            roster_path=roster,
            metadata_captures=sources,
            limits=replace(limits(), max_response_bytes=8),
        )
