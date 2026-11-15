"""Ancillary attempts stay attached to owned roots through source publication."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
    capture_neotoma_dataset_facets,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    capture_neotoma_linked_resources,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from ..facets.parent_scope.native_sources import linked_scope_resolvers, source_inputs
from ..linked_resources.test_capture import evidence_for
from ..linked_resources.test_capture import plan as linked_plan
from ..linked_resources.test_capture import source as linked_source
from ..resources.native_payloads import response, spec


def arguments(family: str, root: Path) -> tuple[Any, dict[str, Any], Any]:
    workflow = import_module(
        f"bijux_pollenomics.collection.sources.neotoma.capture.{family}.workflow"
    )
    if family == "facets":
        plan, scope = source_inputs(root / "native-parent-inputs", (spec(),))
        return capture_neotoma_dataset_facets, {"plan": plan, "scope": scope}, workflow
    digest, sources = linked_source(root / "source-facets")
    return (
        capture_neotoma_linked_resources,
        {
            "plan": linked_plan(digest, targets=[("taxon", 1)]),
            "source_facets": sources,
            "evidence": evidence_for(sources),
            "scope_inputs": linked_scope_resolvers(sources),
        },
        workflow,
    )


@pytest.mark.parametrize("family", ["facets", "linked_resources"])
@pytest.mark.parametrize("replacement", ["directory", "symlink"])
@pytest.mark.parametrize("transport_failure", [False, True])
def test_ancillary_attempts_never_write_into_replaced_root(
    tmp_path: Path, family: str, replacement: str, transport_failure: bool
) -> None:
    capture, kwargs, _ = arguments(family, tmp_path)
    output = tmp_path / "capture"
    stage = build_staging_output_dir(output)
    original = tmp_path / "original-owned-stage"
    foreign = tmp_path / "foreign-writer"
    foreign.mkdir()
    (foreign / "preserve").write_bytes(b"foreign evidence")

    def fetch(url: str, **_: object) -> Any:
        stage.rename(original)
        if replacement == "directory":
            foreign.rename(stage)
        else:
            stage.symlink_to(foreign, target_is_directory=True)
        if transport_failure:
            raise TimeoutError("source request failed after root replacement")
        return response(url, b'{"status":"success","data":[]}')

    with pytest.raises((ValueError, OSError)):
        capture(output, fetch=fetch, **kwargs)
    foreign_root = stage if replacement == "directory" else foreign
    assert sorted(path.name for path in foreign_root.iterdir()) == ["preserve"]
    assert (foreign_root / "preserve").read_bytes() == b"foreign evidence"
    assert sorted(path.name for path in original.iterdir()) == (
        ["parent-scope.json", "request-plan.json"]
        if family == "facets"
        else ["request-plan.json"]
    )
    assert not output.exists()


@pytest.mark.parametrize("family", ["facets", "linked_resources"])
@pytest.mark.parametrize("leaf", ["body", "manifest"])
def test_ancillary_success_requires_actual_published_readback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, family: str, leaf: str
) -> None:
    capture, kwargs, workflow = arguments(family, tmp_path)
    output = tmp_path / "capture"
    publish = workflow.publish_new_output_tree

    def corrupt_after_publish(**publication: Any) -> None:
        publish(**publication)
        target = (
            next(output.glob("*.body"))
            if leaf == "body"
            else output / "capture-manifest.json"
        )
        target.write_bytes(target.read_bytes() + b"\n")

    monkeypatch.setattr(workflow, "publish_new_output_tree", corrupt_after_publish)
    with pytest.raises(ValueError, match="identity|byte limit|digest"):
        capture(
            output,
            fetch=lambda url, **_: response(url, b'{"status":"success","data":[]}'),
            **kwargs,
        )
    assert output.is_dir()
    assert (output / "capture-manifest.json").is_file()


@pytest.mark.parametrize("family", ["facets", "linked_resources"])
@pytest.mark.parametrize("terminal", ["success", "transport_failure", "refusal"])
def test_every_ancillary_write_uses_one_explicit_owned_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, family: str, terminal: str
) -> None:
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    capture, kwargs, workflow = arguments(family, tmp_path)
    output = tmp_path / "capture"
    writers = []
    members = []

    def audit(function: Any) -> Any:
        def call(*args: Any, **options: Any) -> Any:
            writer = options.get("writer")
            assert isinstance(writer, OwnedTreeWriter), (
                "Ancillary write omitted explicit owned writer"
            )
            writers.append(writer)
            if args and isinstance(args[0], Path):
                members.append(args[0].name)
            return function(*args, **options)

        return call

    for name in ["_write_json", "_retain_http_response", "_retain_transport_failure"]:
        monkeypatch.setattr(workflow, name, audit(getattr(workflow, name)))
    if terminal == "refusal":

        def refuse(*_: Any, **__: Any) -> Any:
            raise ValueError("intentional readback refusal")

        monkeypatch.setattr(
            workflow,
            "replay_neotoma_facet_capture"
            if family == "facets"
            else "replay_neotoma_linked_resources",
            refuse,
        )

    def fetch(url: str, **_: object) -> Any:
        if terminal == "transport_failure":
            raise TimeoutError("source unavailable")
        return response(url, b'{"status":"success","data":[]}')

    if terminal == "refusal":
        with pytest.raises(ValueError, match="intentional readback refusal"):
            capture(output, fetch=fetch, **kwargs)
        assert (build_staging_output_dir(output) / "refusal.json").is_file()
    else:
        capture(output, fetch=fetch, **kwargs)
    assert writers and all(writer is writers[0] for writer in writers)
    assert "request-plan.json" in members and "capture-manifest.json" in members
    if family == "facets":
        assert "parent-scope.json" in members
    if terminal == "refusal":
        assert "refusal.json" in members
